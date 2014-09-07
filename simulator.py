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

address_size = 2
branch_size = 1
stack_size = 256
stack = [0] * stack_size
current_frame = 0
stack_pointer = 0

code = []
program_counter = 0

call_stack = []

true = 255
false = 0

def push_byte(value):

    global stack_pointer
    stack[stack_pointer] = value
    stack_pointer += 1

def pop_byte():

    global stack_pointer
    stack_pointer -= 1
    return stack[stack_pointer]

def get_instruction():

    global program_counter
    instruction = code[program_counter]
    program_counter += 1
    return instruction
    
def get_operand():

    global program_counter
    operand = code[program_counter]
    program_counter += 1
    return operand

# Instructions

def load_number():

    value = get_operand()
    size = get_operand()
    
    while size > 0:
        push_byte(value & 0xff)
        value = value >> 8
        size -= 1

def compare_equals():

    size = get_operand()
    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = 0
    while i < size:
        if stack[ptr1 + i] != stack[ptr2 + i]:
            _free_stack_space(size * 2)
            push_byte(false)
            return
        i += 1
    
    _free_stack_space(size * 2)
    push_byte(true)

def compare_not_equals():

    size = get_operand()
    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = 0
    while i < size:
        if stack[ptr1 + i] != stack[ptr2 + i]:
            _free_stack_space(size * 2)
            push_byte(true)
            return
        i += 1
    
    _free_stack_space(size * 2)
    push_byte(false)

def compare_less_than():

    size = get_operand()
    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = size - 1
    while i >= 0:
        if stack[ptr1 + i] < stack[ptr2 + i]:
            _free_stack_space(size * 2)
            push_byte(true)
            return
        i -= 1
    
    _free_stack_space(size * 2)
    push_byte(false)

def compare_greater_than():

    size = get_operand()
    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = size - 1
    while i >= 0:
        if stack[ptr1 + i] > stack[ptr2 + i]:
            _free_stack_space(size * 2)
            push_byte(true)
            return
        i -= 1
    
    _free_stack_space(size * 2)
    push_byte(false)

def add():

    size = get_operand()
    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = 0
    c = 0
    while i < size:
        v = stack[ptr1 + i] + stack[ptr2 + i] + c
        c = v / 256
        v = v % 256
        stack[ptr1 + i] = v
        i -= 1
    
    _free_stack_space(size)

def subtract():

    size = get_operand()
    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = 0
    c = 0
    while i < size:
        v = stack[ptr1 + i] - stack[ptr2 + i] + c
        c = v / 256
        v = v % 256
        stack[ptr1 + i] = v
        i += 1
    
    _free_stack_space(size)

def multiply():

    size = get_operand()
    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = 0
    s1 = 0
    total = 0
    while i < size:
        j = 0
        s2 = 0
        while j < size:
            c = 0
            v = stack[ptr1 + i] * stack[ptr2 + j] + c
            total += v << (s1 + s2)
            c = v / 256
            v = v % 256
            j += 1
            s2 += 8
        
        i += 1
        s1 += 8
    
    # Leave a truncated value on the stack.
    i = 0
    while i < size:
        stack[ptr1 + i] = total & 0xff
        total = total >> 8
        i += 1
    
    _free_stack_space(size)

def divide(value):

    pass

def branch_if_false():

    global program_counter
    offset = get_operand()
    
    if pop_byte() == false:
        program_counter += offset - 1 - branch_size

def branch_if_true():

    global program_counter
    offset = get_operand()
    
    if pop_byte() == true:
        program_counter += offset - 1 - branch_size

def branch():

    global program_counter
    offset = get_operand()
    
    program_counter += offset - 1 - branch_size

def load_local():

    global stack_pointer
    offset = get_operand()
    size = get_operand()
    
    i = 0
    while i < size:
        stack[stack_pointer + i] = stack[current_frame + offset + i]
        i += 1
    
    stack_pointer += size

def load_global():

    offset = get_operand()
    size = get_operand()

def assign_local():

    global stack_pointer
    offset = get_operand()
    size = get_operand()
    
    i = 0
    while i < size:
        stack[current_frame + offset + i] = stack[stack_pointer - size + i]
        i += 1
    
    stack_pointer -= size

def function_return():

    global program_counter
    program_counter = call_stack.pop()

def function_call():

    global program_counter
    address_low = get_operand()
    address_high = get_operand()
    address = address_low | (address_high << 8)
    
    call_stack.append(program_counter)
    program_counter = address

def load_current_frame_address():

    address = current_frame
    i = 0
    while i < address_size:
        push_byte(address & 0xff)
        address = address >> 8
        i += 1

def store_stack_top_in_current_frame():

    global current_frame
    param_size = get_operand()
    
    current_frame = stack_pointer - param_size
    print current_frame

def allocate_stack_space():

    size = get_operand()
    _allocate_stack_space(size)

def _allocate_stack_space(size):

    global stack_pointer
    stack_pointer += size

def free_stack_space():

    size = get_operand()
    _free_stack_space(size)

def _free_stack_space(size):

    global stack_pointer
    stack_pointer -= size

def pop_current_frame_address():

    global current_frame
    address = 0
    i = 0
    while i < address_size:
        address = (address << 8) | pop_byte()
        i += 1
    
    current_frame = address

def copy_value():

    global stack_pointer
    offset = get_operand()
    size = get_operand()
    
    src = offset + address_size
    dest = -size
    i = size - 1
    while i >= 0:
        stack[stack_pointer + i] = stack[stack_pointer + src + i]
        i -= 1
    
    stack_pointer += size

def end():

    raise StopIteration

# Simulator initialisation

def load(all_code):

    global code
    code = all_code

def run():

    global program_counter, stack_pointer
    program_counter = 0
    stack_pointer = 0
    
    step = True
    
    while True:
    
        instruction = get_instruction()
        print program_counter, instruction
        if instruction == end:
            break
        instruction()
        print stack[:stack_pointer]
        if step:
            q = raw_input(">")
            if q == "c":
                step = False
    
    print stack[:stack_pointer]
