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

import opcodes
from opcodes import address_size, branch_size, memory_size

memory = [0] * memory_size
current_frame = 0
program_counter = 0
stack_base = 0
stack_pointer = 0
call_stack_base = 0
call_stack_pointer = 0

true = 255
false = 0

def push_byte(value):

    global stack_pointer
    memory[stack_pointer] = value
    stack_pointer += 1

def pop_byte():

    global stack_pointer
    stack_pointer -= 1
    return memory[stack_pointer]

def push_call_byte(value):

    global call_stack_pointer
    memory[call_stack_pointer] = value
    call_stack_pointer += 1

def pop_call_byte():

    global call_stack_pointer
    call_stack_pointer -= 1
    return memory[call_stack_pointer]

def get_instruction():

    global program_counter
    instruction = memory[program_counter]
    program_counter += 1
    return instruction
    
def get_operand():

    global program_counter
    operand = memory[program_counter]
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
        if memory[ptr1 + i] != memory[ptr2 + i]:
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
        if memory[ptr1 + i] != memory[ptr2 + i]:
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
        if memory[ptr1 + i] < memory[ptr2 + i]:
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
        if memory[ptr1 + i] > memory[ptr2 + i]:
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
        v = memory[ptr1 + i] + memory[ptr2 + i] + c
        c = v / 256
        v = v % 256
        memory[ptr1 + i] = v
        i -= 1
    
    _free_stack_space(size)

def subtract():

    size = get_operand()
    ptr2 = stack_pointer - size
    ptr1 = ptr2 - size
    
    i = 0
    c = 0
    while i < size:
        v = memory[ptr1 + i] - memory[ptr2 + i] + c
        c = v / 256
        v = v % 256
        memory[ptr1 + i] = v
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
            v = memory[ptr1 + i] * memory[ptr2 + j] + c
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
        memory[ptr1 + i] = total & 0xff
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
        memory[stack_pointer + i] = memory[current_frame + offset + i]
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
        memory[current_frame + offset + i] = memory[stack_pointer - size + i]
        i += 1
    
    stack_pointer -= size

def function_return():

    global program_counter
    
    address = 0
    i = 0
    while i < address_size:
        address = (address << 8) | pop_call_byte()
        i += 1
    
    program_counter = address

def function_call():

    global program_counter
    address_low = get_operand()
    address_high = get_operand()
    address = address_low | (address_high << 8)
    
    i = 0
    while i < address_size:
        push_call_byte(program_counter & 0xff)
        program_counter = program_counter >> 8
        i += 1
    
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
        memory[stack_pointer + i] = memory[stack_pointer + src + i]
        i -= 1
    
    stack_pointer += size

def end():

    raise StopIteration

lookup = {
    opcodes.load_number: load_number,
    opcodes.compare_equals: compare_equals,
    opcodes.compare_not_equals: compare_not_equals,
    opcodes.compare_less_than: compare_less_than,
    opcodes.compare_greater_than: compare_greater_than,
    opcodes.add: add,
    opcodes.subtract: subtract,
    opcodes.multiply: multiply,
    opcodes.divide: divide,
    opcodes.branch_if_false: branch_if_false,
    opcodes.branch_if_true: branch_if_true,
    opcodes.branch: branch,
    opcodes.load_local: load_local,
    opcodes.load_global: load_global,
    opcodes.assign_local: assign_local,
    opcodes.function_return: function_return,
    opcodes.function_call: function_call,
    opcodes.load_current_frame_address: load_current_frame_address,
    opcodes.store_stack_top_in_current_frame: store_stack_top_in_current_frame,
    opcodes.allocate_stack_space: allocate_stack_space,
    opcodes.free_stack_space: free_stack_space,
    opcodes.pop_current_frame_address: pop_current_frame_address,
    opcodes.copy_value: copy_value,
    opcodes.end: end
    }

# Simulator initialisation

def load(code, address):

    global call_stack_base, call_stack_pointer
    global program_counter
    global stack_base, stack_pointer
    global current_frame
    
    end = address + len(code)
    memory[address:end] = code
    
    program_counter = address
    call_stack_base = call_stack_pointer = end
    stack_base = current_frame = stack_pointer = end + 16 * address_size

def run():

    global program_counter, stack_pointer
    
    step = True
    
    while True:
    
        instruction = lookup[get_instruction()]
        print program_counter, instruction
        if instruction == end:
            break
        instruction()
        print "Call: ", memory[call_stack_base:call_stack_pointer]
        print "Value:", memory[stack_base:stack_pointer]
        if step:
            q = raw_input(">")
            if q == "c":
                step = False
    
    print memory[stack_base:stack_pointer]
