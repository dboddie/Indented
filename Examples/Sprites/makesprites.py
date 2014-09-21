#!/usr/bin/env python

"""
Copyright (C) 2011 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import Image

def read_sprite(lines, shifted = False):

    data = ""
    
    # Read 8 rows at a time.
    for row in range(0, len(lines), 8):
    
        if shifted:
            width = len(lines[0]) + 4
        else:
            width = len(lines[0])
        
        # Read 4 columns at a time.
        for column in range(0, width, 4):
        
            # Read the rows.
            for line in lines[row:row + 8]:
            
                if shifted:
                    line = [0, 0] + line + [0, 0]
                
                shift = 3
                byte = 0
                for pixel in line[column:column + 4]:
                
                    if pixel == 1:
                        byte = byte | (0x01 << shift)
                    elif pixel == 2:
                        byte = byte | (0x10 << shift)
                    elif pixel == 3:
                        byte = byte | (0x11 << shift)
                    
                    shift -= 1
                
                data += chr(byte)
    
    return data

sprites = [
    ((0,0,0,0,0,0,0,0),
     (0,0,0,0,0,0,0,0),
     (0,0,0,0,0,0,0,0),
     (0,0,0,0,0,0,0,0),
     (0,0,0,0,0,0,0,0),
     (0,0,0,0,0,0,0,0),
     (0,0,0,0,0,0,0,0),
     (0,0,0,0,0,0,0,0)),

    ((1,1,1,1,1,1,1,0),
     (1,1,1,1,1,1,1,0),
     (1,1,1,1,1,1,1,0),
     (0,0,0,0,0,0,0,0),
     (1,1,1,0,1,1,1,1),
     (1,1,1,0,1,1,1,1),
     (1,1,1,0,1,1,1,1),
     (0,0,0,0,0,0,0,0)),

    ((0,2,2,2,2,2,2,0),
     (2,2,1,1,1,1,2,2),
     (2,1,1,1,1,1,1,2),
     (2,1,3,1,1,3,1,2),
     (2,1,3,1,1,3,1,2),
     (2,1,1,1,1,1,1,2),
     (2,2,1,1,1,1,2,2),
     (0,2,2,2,2,2,2,0))
    ]

data = ""

for sprite in sprites:
    data += read_sprite(sprite)

open("SPRITES", "w").write(data)
