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

@appendTo( MAPPINGS )
def linear ( word, reverse = False ):
    if reverse:
        x, y = word
        return (y << 8) + x
    else:   
        x = word & 255
        y = (word >> 8) & 255
        return x, y

@appendTo( MAPPINGS )
def block ( word, reverse = False, bits = 16 ):
    blockWidth, blockHeight = 16, 16
    columns = 16
    blockWidth, blockHeight = 8, 128
    columns = 32
    assert columns * blockWidth * blockHeight * ( (2**(bits/2)) / blockHeight ) == 2**bits
    if reverse:
        x, y = word
        rowN = y / blockHeight
        
    else:
        value = word & (2 ** 16 - 1)
        blockN = value / blockWidth / blockHeight
        blockX = blockN % columns
        blockY = blockN / columns
        localX = value % blockWidth
        localY = value / blockWidth % blockHeight
        X = localX + (blockWidth * blockX)
        Y = localY + (blockHeight * blockY)
        return X, Y

@appendTo( MAPPINGS )
def hilbert( t, n=128 ):
    """
    Attempt at porting C code from wikipedia. Doesn't work right.
    """
    x = y = 0
    s = 1
    while s<n:
        s*=2
        rx = 1 & (t/2)
        ry = 1 & (t ^ rx)
        if ry == 0:
            if rx == 1:
                x = n-1 - x
                y = n-1 - y
            x, y = y, x
        x += s * rx
        y += s * ry
        t /= 4
    return 4*x, 4*y

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

    zoomBits  = 0
    zoomPos   = 0
    zoomStart = 0
    zoomEnd   = 0

    for wordBytes in stdinIter:
        count+=1
        if count % 1000 == 0:
            now = time.time()
#            print "%s per second" % (1000 / (now - lastTime),)
            lastTime = now
        for event in pygame.event.get():
#            if event.type in [pygame.QUIT, pygame.MOUSEBUTTONDOWN]:
            adjusted = False
            if event.type in [pygame.QUIT]:
                #os.kill(os.getpid(), 9)
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x,y = pygame.mouse.get_pos()
                if x < 256:
                    click1d = mapFn( (x,y), reverse = True ) << 16
                    zoomPos = click1d >> ( 32 - zoomBits )
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

                if zoomBits > 16:
                    zoomBits = 16
                elif zoomBits < 0:
                    zoomBits = 0
                
                maxPos = (2 ** zoomBits) - 1

                if zoomPos > maxPos:
                    zoomPos = maxPos
                elif zoomPos < 0:
                    zoomPos = 0

                adjusted = True
            
            if adjusted:
                zoomStart   = zoomPos << ( 32 - zoomBits )
                zoomEnd     = zoomStart + (2 ** (32 - zoomBits) )
                zoomStart16 = zoomPos << (16 - zoomBits)
                zoomEnd16   = zoomStart16 + (2 ** (16 - zoomBits)) - 1

                zoomBoxStartX, zoomBoxStartY = mapFn(zoomStart16)
                zoomBoxEndX, zoomBoxEndY     = mapFn(zoomEnd16)
                zoomBoxWidth                 = zoomBoxEndX - zoomBoxStartX
                zoomBoxHeight                = zoomBoxEndY - zoomBoxStartY
                zoomBoxCoords                = ( zoomBoxStartX, zoomBoxStartY, zoomBoxWidth, zoomBoxHeight )

                zoomPosBin = bin(zoomPos | 2**zoomBits)[-zoomBits:] if zoomBits else ""
                print "[%s%s%s] zoom shows addresses %x through %x" % (
                    zoomPosBin, "_"*16, "?"*(32-zoomBits-16),
                    zoomStart, zoomEnd )
                print "zoom:", zoomStart16, zoomEnd16, zoomBoxCoords
                image.fill( (0,255,0), pygame.Rect( *zoomBoxCoords ) )

#        sys.stderr.write(wordBytes)

        word = struct.unpack( 'I', wordBytes )[0]

        highWord = word >> 16
        x, y = mapFn( highWord )

        oldHighCoords = highCoords
        highCoords    = (x, y)

        if oldHighCoords != None:
            pygame.draw.line( image, LINECOLOR, highCoords, oldHighCoords )
            screen.blit(dot, (x-3,y-3), None, pygame.BLEND_ADD)

        if zoomStart < word < zoomEnd:
            lowWord = word & ( ( 2 ** 16 - 1 ) << (16 - zoomBits) )
            lowWord = lowWord >> ( 16 - zoomBits )

            x, y = mapFn( lowWord )
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

