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
def mid18linear ( word ):
    x = (word >> 3) & 511
    y = (word >> 9) & 511
    return x, y

@appendTo( MAPPINGS )
def low18linear ( word ):
    x = word & 511
    y = (word >> 9) & 511
    return x, y

@appendTo( MAPPINGS )
def high18linear ( word ):
    x = (word >> 14) & 511
    y = (word >> 23)  & 511
    return x, y

@appendTo( MAPPINGS )
def high18block ( word ):
    value = word >> 14
    colWidth, colHeight = 16, 16
    columns = 32
    colX = value % colWidth
    colY = value / colWidth
    colN = colY / colHeight
    colXX = colN % columns
    colYY = colN / columns
    X = colX + (colWidth * colXX)
    Y = colY % colHeight + (colHeight * colYY)
    return X, Y

@appendTo( MAPPINGS )
def low18block ( word ):
    value = word & (2 ** 18 - 1)
    colWidth, colHeight = 16, 16
    columns = 32
    colX = value % colWidth
    colY = value / colWidth
    colN = colY / colHeight
    colXX = colN % columns
    colYY = colN / columns
    X = colX + (colWidth * colXX)
    Y = colY % colHeight + (colHeight * colYY)
    return X, Y

@appendTo( MAPPINGS )
def low18hilbert( word, n=128 ):
    """
    Attempt at porting C code from wikipedia. Doesn't work right.
    """
    t = word & (2 ** 18 - 1) # low 18
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
    return 4*(x), 4*(y)
   
def main ( mapFn ):
    #line defs
    SIZE         = (512,512)
    FADE_RATE    = 1
    LINECOLOR    = ( 0, 255, 0, 10 )
    BACKGROUND   = ( 0, 0, 0, FADE_RATE )

    #point defs
    SIZE = (512,512)
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

    screen = pygame.display.set_mode(SIZE,pygame.HWSURFACE|pygame.ASYNCBLIT)
    pygame.display.set_caption('YouScope XY-Demo Osciloscope Emulator')
    pygame.mouse.set_visible(0)

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

    stdin = os.fdopen( sys.stdin.fileno(), 'r', 0 )
    stdinIter = iter( lambda: stdin.read(4), '' )
    coords = None

    count = 0

    lastTime = time.time()

    for wordBytes in stdinIter:
        count+=1
        if count % 1000 == 0:
            now = time.time()
            print "%s per second" % (1000 / (now - lastTime),)
            lastTime = now
        for event in pygame.event.get():
            if event.type == pygame.QUIT: sys.exit()

        word = struct.unpack( 'I', wordBytes )[0]

        x, y = mapFn( word )

        oldCoords = coords    
        coords    = (x, y)
        
        if oldCoords != None:
            pygame.draw.line( image, LINECOLOR, coords, oldCoords )
            screen.blit(dot, (x-3,y-3), None, pygame.BLEND_ADD)

        screen.blit( image, (0,0) )
        
        image.fill( BACKGROUND )

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

