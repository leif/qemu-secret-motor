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

#line defs
SIZE         = (512,512)
FADE_RATE    = 0
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

grid = pygame.Surface(SIZE)
grid.set_alpha(ALPHA)
grid.fill(BGCOLOR)

for x in range(10):
    pygame.draw.line(grid, GRIDCOLOR, (x*SIZE[0]/10,0), (x*SIZE[0]/10,SIZE[0]))

for y in range(8):
    pygame.draw.line(grid, GRIDCOLOR, (0 , y*SIZE[1]/8), (SIZE[0] , y*SIZE[1]/8))

pygame.draw.line(grid, GRIDCOLOR, (SIZE[0]/2,0), (SIZE[0]/2,SIZE[0]), 3)
pygame.draw.line(grid, GRIDCOLOR, (0 , SIZE[1]/2), (SIZE[0] , SIZE[1]/2), 3)

for x in range(100):
    pygame.draw.line(grid, GRIDCOLOR, (x*SIZE[0]/100,SIZE[1]/2-3), (x*SIZE[0]/100,SIZE[1]/2+3))

for y in range(80):
    pygame.draw.line(grid, GRIDCOLOR, (SIZE[0]/2 - 3, y*SIZE[1]/80), (SIZE[0]/2 + 3, y*SIZE[1]/80))

stdin = os.fdopen( sys.stdin.fileno(), 'r', 0 )
stdinIter = iter( lambda: stdin.read(4), '' )
coords = None

for wordBytes in stdinIter:
    
    word = struct.unpack( 'I', wordBytes )[0]

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()

    x = (word >> 3) & 511
    y = (word >> 9) & 511
    
    oldCoords = coords    
    coords    = (x, y)
    
    #print oldCoords
    #print coords
    
    if oldCoords != None:
        pygame.draw.line( image, LINECOLOR, coords, oldCoords )
        screen.blit(dot, (x-3,y-3), None, pygame.BLEND_ADD)

    screen.blit( image, (0,0) )
    
    image.fill( BACKGROUND )

    pygame.display.flip()
