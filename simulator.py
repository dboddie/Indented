"""
simulator.py - Simulator for a simple compiler.

Copyright (C) 2014 David Boddie <david@boddie.org.uk>

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

stack_size = 256
stack = [0] * stack_size
stack_pointer = 0
stack_pointer_copy = 0

def save_local_stack_pointer(value):

    global stack_pointer, stack_pointer_copy
    stack_pointer_copy = stack_pointer

def allocate_local_stack_space(value):

    global stack_pointer
    stack_pointer += value

