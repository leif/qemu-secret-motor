#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Youscope Emulator
#
#(c)2007 Felipe Sanches
#(c)2007 Leandro Lameiro
#licensed under GNU GPL v3 or later

# A bunch of bug fixes and enhancements
# Michael Sparmann, 2009

# Complete rewrite to plot memory adresses from qemu
# (C) 2011 Leif Ryge
# (C) 2011 Rodrigo R. Silva

import struct
import pygame
import os
import sys
import math
import time


MAPPINGS = []

def appendTo ( target ):
    def decorator ( fn ):
        target.append( fn )
        return fn
    return decorator

def scale ( inBits, outBits, value ):
    if inBits > outBits:
        return value >> (inBits - outBits)
    else:
        return value << (outBits - inBits)

@appendTo( MAPPINGS )
def linear ( inBits, outBits, value, reverse = False ):
    assert outBits % 2 == 0
    half = outBits / 2
    if reverse:
        x, y = value
        return scale( outBits, inBits, (y << half) + x )
    else:   
        word = scale( inBits, outBits, value )
        x = word & 255
        y = (word >> half) & (2**half - 1)
        return x, y

@appendTo( MAPPINGS )
def block ( inBits, outBits, value, reverse = False, (blockW, blockH) = (16,16) ):
    assert outBits % 2 == 0, "output range must be even"
    columns = (2 ** (outBits/2) ) / outBits
    assert columns * blockW * blockH * ( (2**(outBits/2)) / blockH ) == 2**outBits, (blockW,blockH,columns)
    assert (columns**2) * blockW * blockH == 2**outBits, (blockW,blockH,columns)
    if reverse:
        x, y   = value
        column = x / blockW
        row    = y / blockH
        blockX = x % blockW
        blockY = y % blockH
        blockN = column + row * columns
        return scale( outBits, inBits, blockN * blockW * blockH + blockY * blockW + blockX )
    else:
        word   = scale( inBits, outBits, value )
        blockN = word / blockW / blockH
        column = blockN % columns
        row    = blockN / columns
        blockX = word % blockW
        blockY = word / blockW % blockH
        x      = blockX + blockW * column
        y      = blockY + blockH * row
        return x, y

@appendTo( MAPPINGS )
def hilbert( inBits, outBits, value, reverse = False ):
    """
    Port of C code from en.wikipedia.org/wiki/Hilbert_curve
    """
    n = outBits ** 2
    if reverse:
        x,y = value
        d = 0
        s = n/2
        while s > 0:
            rx = (x & s) > 0
            ry = (y & s) > 0
            d += s * s * ((3 * rx) ^ ry)
            if ry == 0:
                if rx == 1:
                    x = s - 1 - x
                    y = s - 1 - y
                x, y = y, x
            s /= 2
        return scale( outBits, inBits, d )
    else:
        t = scale( inBits, outBits, value )
        x = y = 0
        s = 1
        while s<n:
            rx = 1 & (t/2)
            ry = 1 & (t ^ rx)
            if ry == 0:
                if rx == 1:
                    x = s-1 - x
                    y = s-1 - y
                x, y = y, x
            x += s * rx
            y += s * ry
            t /= 4
            s*=2
        return x,  y

def main ( mapFn ):
    #line defs
    FADE_RATE    = 1
    LINECOLOR    = ( 0, 255, 0, 100 )
    BACKGROUND   = ( 0, 0, 0, FADE_RATE )

    #point defs
    SIZE      = (512,256)
    DOT1COLOR = (63,255,191)
    DOT2COLOR = (15,127,47)
    DOT3COLOR = (11,95,35)
    DOT4COLOR = (7,31,23)
    DOT5COLOR = (3,23,11)
    DOT6COLOR = (1,15,5)
    DOT7COLOR = (0,7,3)
    GRIDCOLOR = (0,31,63)
    BGCOLOR = (0,63,91)
    ALPHA = 223
    DOTALPHA = 23

    pygame.init()

    pygame.key.set_repeat( 500, 1 )

    screen = pygame.display.set_mode(SIZE,pygame.HWSURFACE|pygame.ASYNCBLIT)
#    screen = pygame.display.set_mode((0,0),pygame.FULLSCREEN)
    pygame.display.set_caption('YouScope XY-Demo Osciloscope Emulator')

    image = pygame.Surface( SIZE, pygame.SRCALPHA )

    dot = pygame.Surface((7,7))
    dot.set_alpha(DOTALPHA)
    dot.fill(BGCOLOR)
    dot.fill(DOT7COLOR, pygame.Rect(0,0,7,7))
    dot.fill(DOT6COLOR, pygame.Rect(1,0,5,7))
    dot.fill(DOT6COLOR, pygame.Rect(0,1,7,5))
    dot.fill(DOT5COLOR, pygame.Rect(1,1,5,5))
    dot.fill(DOT4COLOR, pygame.Rect(2,1,3,5))
    dot.fill(DOT4COLOR, pygame.Rect(1,2,5,3))
    dot.fill(DOT3COLOR, pygame.Rect(2,2,3,3))
    dot.fill(DOT2COLOR, pygame.Rect(3,2,1,3))
    dot.fill(DOT2COLOR, pygame.Rect(2,3,3,1))
    dot.fill(DOT1COLOR, pygame.Rect(3,3,1,1))

#    dot = pygame.Surface((1,1))
#    dot.set_alpha(DOTALPHA)
#    dot.fill(BGCOLOR)
#    dot.fill((0,255,0), pygame.Rect(0,0,1,1))

    stdin = os.fdopen( sys.stdin.fileno(), 'r', 0 )
    stdinIter = iter( lambda: stdin.read(4), '' )
    highCoords = None
    lowCoords  = None

    count = 0

    lastTime = time.time()

    wordSize   = 32
    windowSize = 16
    zoomBits   = 0
    zoomPos    = 0
    zoomStart  = 0
    zoomEnd    = 0

    for wordBytes in stdinIter:
        count+=1
        if count % 1000 == 0:
            now = time.time()
#            print "%s per second" % (1000 / (now - lastTime),)
            lastTime = now
        for event in pygame.event.get():
            adjusted = False
            if event.type in [pygame.QUIT]:
#           if event.type in [pygame.QUIT, pygame.MOUSEBUTTONDOWN]:
                #os.kill(os.getpid(), 9)
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x,y = pygame.mouse.get_pos()
                if x < 256:
                    click1d = mapFn( wordSize, 16, (x,y), reverse = True )
                    zoomPos = click1d >> ( wordSize - zoomBits )
                    adjusted = True
            elif event.type == pygame.KEYDOWN:
                pressed = pygame.key.get_pressed()
                if pressed[ pygame.K_UP ]:
                    zoomPos += 1
                elif pressed[ pygame.K_DOWN ]:
                    zoomPos -= 1
                elif pressed[ pygame.K_LEFT ]:
                    zoomBits -= 1
                    zoomPos >>= 1
                elif pressed[ pygame.K_RIGHT ]:
                    zoomBits += 1
                    zoomPos <<= 1
                elif pressed[ pygame.K_COMMA ]:
                    windowSize -= 1
                elif pressed[ pygame.K_PERIOD ]:
                    windowSize += 1

                if windowSize > wordSize:
                    windowSize = wordSize
                elif windowSize < 1:
                    windowSize = 1

                maxZoomBits = wordSize - windowSize

                if zoomBits > maxZoomBits:
                    zoomBits = maxZoomBits
                elif zoomBits < 0:
                    zoomBits = 0
                
                maxZoomPos = (2 ** zoomBits) - 1

                if zoomPos > maxZoomPos:
                    zoomPos = maxZoomPos
                elif zoomPos < 0:
                    zoomPos = 0

                adjusted = True
            
            if adjusted:
                droppedBits = maxZoomBits - zoomBits
                zoomStart   = zoomPos << ( wordSize - zoomBits )
                zoomEnd     = zoomStart + (2 ** (wordSize - zoomBits) )
#                zoomStart16 = zoomPos << droppedBits
#                zoomEnd16   = zoomStart16 + (2 ** droppedBits ) - 1

#                zoomBoxStartX, zoomBoxStartY = mapFn(windowSize, 16, zoomStart16, False)
#                zoomBoxEndX, zoomBoxEndY     = mapFn(windowSize, 16, zoomEnd16, False)
#                zoomBoxWidth                 = zoomBoxEndX - zoomBoxStartX
#                zoomBoxHeight                = zoomBoxEndY - zoomBoxStartY
#                zoomBoxCoords                = ( zoomBoxStartX, zoomBoxStartY, zoomBoxWidth, zoomBoxHeight )

                zoomPosBin = bin(zoomPos | 2**zoomBits)[-zoomBits:] if zoomBits else ""
                print "[%s%s%s] address range %x - %x (%s bits)" % (
                    zoomPosBin, "_"*windowSize, "?"*(droppedBits),
                    zoomStart, zoomEnd-1, windowSize )
#                print zoomStart16, zoomEnd16, zoomBoxCoords
#                image.fill( (0,255,0), pygame.Rect( *zoomBoxCoords ) )
                prevPoint = zoomStart
                for point in range( zoomStart, zoomEnd,  (2**16)*4):
                    pygame.draw.line( image, LINECOLOR, mapFn( wordSize, 16, prevPoint, False) , mapFn( wordSize, 16, point, False ) )
                    prevPoint = point
                    screen.blit(dot, (x-3,y-3), None, pygame.BLEND_ADD)

#        sys.stderr.write(wordBytes)

        word = struct.unpack( 'I', wordBytes )[0]

        x, y = mapFn( inBits = wordSize, outBits = 16, value = word, reverse = False )

        oldHighCoords = highCoords
        highCoords    = (x, y)

        if oldHighCoords != None:
            pygame.draw.line( image, LINECOLOR, highCoords, oldHighCoords )
            screen.blit(dot, (x-3,y-3), None, pygame.BLEND_ADD)

        if zoomStart < word < zoomEnd:
            lowWord = word & ( ( 2 ** windowSize - 1 ) << (maxZoomBits - zoomBits) )
            lowWord = lowWord >> ( maxZoomBits - zoomBits )

            x, y = mapFn( inBits = windowSize, outBits = 16, value = lowWord, reverse = False )
            x += 256

            oldLowCoords = lowCoords
            lowCoords    = (x, y)

            if oldLowCoords != None:
                pygame.draw.line( image, LINECOLOR, lowCoords, oldLowCoords )
                screen.blit(dot, (x-3,y-3), None, pygame.BLEND_ADD)

        screen.blit( image, (0,0) )

        image.fill( BACKGROUND )

        if count % 10 == 0:
            pygame.display.flip()


if __name__ == "__main__":
    try:
        mapFn = globals()[ sys.argv[1] ]

    except:
        print "usage: %s <%s>" % (
            sys.argv[0],
            "|".join( k for k,v in globals().items() if v in MAPPINGS )
            )
    else:
        main( mapFn )

