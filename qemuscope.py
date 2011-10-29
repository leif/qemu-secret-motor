#!/usr/bin/env python
#
# Youcope Emulator
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

SIZE         = (512,512)
FADE_RATE    = 1
LINECOLOR    = ( 0, 255, 0 )
BACKGROUND   = ( 0, 0, 0, FADE_RATE )

pygame.init()

screen = pygame.display.set_mode(SIZE,pygame.HWSURFACE|pygame.ASYNCBLIT)
pygame.mouse.set_visible(0)

image = pygame.Surface( SIZE, pygame.SRCALPHA )

stdin     = os.fdopen( sys.stdin.fileno(), 'r', 0 )
stdinIter = iter( lambda: stdin.read(4), '' )

coords = None

for wordBytes in stdinIter:
    
    word = struct.unpack( 'I', wordBytes )[0]

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
    
    x = (word >> 3) & 511
    y = (word >> 9) & 511
    
    #if (x,y) == (0,0):
    #    continue

    oldCoords = coords    
    coords    = (x, y)
    
    #print oldCoords
    #print coords
    
    if oldCoords != None:
        pygame.draw.line( image, LINECOLOR, coords, oldCoords )

    screen.blit( image, (0,0) )
    
    image.fill( BACKGROUND )

    pygame.display.flip()
