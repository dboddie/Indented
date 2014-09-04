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
current_frame = 0
stack_pointer = 0
stack_pointer_copy = 0

true = 255
false = 0

def push_byte(value):

    global stack_pointer
    stack[stack_pointer] = value
    stack_pointer += 1

def pop_byte():

    global stack_pointer
    stack_pointer -= 1

def load_number(info):

    value, size = value
    while size > 0:
        push_byte(value & 0xff)
        value = value >> 8

def compare_equals(size):

    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = size - 1
    while i > 0:
        if stack[ptr1 + i] != stack[ptr2 + i]:
            free_stack_space(size * 2)
            push_byte(false)
        i -= 1
    
    free_stack_space(size * 2)
    push_byte(true)

def compare_not_equals(size):

    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = size - 1
    while i > 0:
        if stack[ptr1 + i] == stack[ptr2 + i]:
            free_stack_space(size * 2)
            push_byte(false)
        i -= 1
    
    free_stack_space(size * 2)
    push_byte(true)

def compare_less_than(value):

    pass

def compare_greater_than(value):

    pass

def add(value):

    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = size - 1
    c = 0
    while i > 0:
        v = stack[ptr1 + i] + stack[ptr2 + i]
        c = v / 256
        v = v % 256
        stack[ptr1 + i] = v + c
        i -= 1
    
    free_stack_space(size)

def subtract(value):

    pass

def multiply(value):

    pass

def divide(value):

    pass

def branch_if_false(offset):

    pass

def branch(offset):

    pass

def load_local(value):

    offset, size = value

def load_global(value):

    offset, size = value

def assign_local(info):

    offset, size = info

def function_return(size):

    pass

def function_call(name):

    pass

def load_current_frame_address():

    pass

def store_stack_top_in_current_frame():

    pass

def allocate_stack_space(size):

    pass

def free_stack_space(size):

    pass

def pop_current_frame_address():

    pass
