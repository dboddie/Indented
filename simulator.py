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
from opcodes import address_size, branch_size, memory_size, shift_size

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

    size = get_operand()
    
    while size > 0:
        push_byte(get_operand())
        size -= 1

def load_byte():

    push_byte(get_operand())

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

def compare_equals_byte():

    if pop_byte() == pop_byte():
        push_byte(true)
    else:
        push_byte(false)

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

def compare_not_equals_byte():

    if pop_byte() != pop_byte():
        push_byte(true)
    else:
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

def compare_less_than_byte():

    if pop_byte() > pop_byte():
        push_byte(true)
    else:
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

def compare_greater_than_byte():

    if pop_byte() < pop_byte():
        push_byte(true)
    else:
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
        i += 1
    
    _free_stack_space(size)

def add_byte():

    push_byte((pop_byte() + pop_byte()) & 0xff)

def add_byte_constant():

    push_byte((pop_byte() + get_operand()) & 0xff)

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

def subtract_byte():

    v = pop_byte()
    push_byte((v - pop_byte()) % 256)

def subtract_byte_constant():

    push_byte((pop_byte() - get_operand()) % 256)

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

def logical_and():

    operand2 = pop_byte()
    operand1 = pop_byte()
    if operand1 and operand2:
        push_byte(true)
    else:
        push_byte(false)

def logical_or():

    operand2 = pop_byte()
    operand1 = pop_byte()
    if operand1 or operand2:
        push_byte(true)
    else:
        push_byte(false)

def logical_not():

    operand1 = pop_byte()
    if operand1:
        push_byte(false)
    else:
        push_byte(true)

def minus():

    size = get_operand()
    v = 0
    i = 0
    while i < size:
        v = (v << 8) | pop_byte()
        i += 1
    
    v = -v
    i = 0
    while i < size:
        push_byte(v & 0xff)
        i += 1

def bitwise_and():

    size1 = get_operand()
    size2 = get_operand()
    ptr2 = stack_pointer - size2
    ptr1 = ptr2 - size1
    
    i = 0
    while i < size2:
        memory[ptr1 + i] = memory[ptr1 + i] & memory[ptr2 + i]
        i += 1
    
    _free_stack_space(size1)

def left_shift():

    size = get_operand()
    ptr2 = stack_pointer - shift_size
    ptr1 = ptr2 - size
    
    # Assume just a single byte value.
    shift = memory[ptr2]
    
    i = 0
    a = 0
    while i < size:
        v = memory[ptr1 + i] << shift
        memory[ptr1 + i] = (v & 0xff) | a
        a = v >> 8
        i += 1
    
    _free_stack_space(shift_size)

def right_shift():

    size = get_operand()
    ptr2 = stack_pointer - shift_size
    ptr1 = ptr2 - size
    
    # Assume just a single byte value.
    shift = memory[ptr2]
    
    i = size - 1
    a = 0
    while i >= 0:
        v = memory[ptr1 + i]
        memory[ptr1 + i] = ((v >> shift) & 0xff) | a
        a = (v << (8 - shift)) & 0xff
        i -= 1
    
    _free_stack_space(shift_size)

def branch_forward_if_false():

    global program_counter
    offset = get_operand()
    
    if pop_byte() == false:
        program_counter += offset - 1 - branch_size

def branch_forward():

    global program_counter
    offset = get_operand()
    
    program_counter += offset - 1 - branch_size

def branch_backward_if_false():

    global program_counter
    offset = get_operand()
    
    if pop_byte() == false:
        program_counter -= offset + 1 + branch_size

def branch_backward():

    global program_counter
    offset = get_operand()
    
    program_counter -= offset + 1 + branch_size

def jump():

    global program_counter
    
    address = 0
    i = 0
    s = 0
    while i < address_size:
        address = address | (get_operand() << s)
        i += 1
        s += 8
    
    program_counter = address

def jump_if_false():

    global program_counter
    
    address = 0
    i = 0
    s = 0
    while i < address_size:
        address = address | (get_operand() << s)
        i += 1
        s += 8
    
    if pop_byte() == false:
        program_counter = address

def load_local():

    global stack_pointer
    offset = get_operand()
    size = get_operand()
    
    i = 0
    while i < size:
        memory[stack_pointer + i] = memory[current_frame + offset + i]
        i += 1
    
    stack_pointer += size

def load_local_byte():

    global stack_pointer
    offset = get_operand()
    
    memory[stack_pointer] = memory[current_frame + offset]
    
    stack_pointer += 1

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

def assign_local_byte():

    global stack_pointer
    offset = get_operand()
    
    memory[current_frame + offset] = memory[stack_pointer - 1]
    
    stack_pointer -= 1

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
    i = size - 1
    while i >= 0:
        memory[stack_pointer + i] = memory[stack_pointer + src + i]
        i -= 1
    
    stack_pointer += size

def sys_call():

    global sys_call_prompt
    
    size = get_operand()
    temp = size

    format = []
    while temp > 2:
        value = pop_byte()
        if temp == 5:
            Y = value
            format.insert(0, "%x" % Y)
        elif temp == 4:
            X = value
            format.insert(0, "%x" % X)
        elif temp == 3:
            A = value
            format.insert(0, "%x" % A)
        temp -= 1

    address_high = pop_byte()
    address_low = pop_byte()
    format.insert(0, "%x" % (address_low | (address_high << 8)))
    
    if sys_call_prompt:
        q = raw_input("system call (%s) returns? " % " ".join(format))
    else:
        q = None
    
    if not q:
        q = "0"
    v = int(q)
    i = 0
    while i < opcodes.system_call_return_size:
        push_byte(v & 0xff)
        v = v >> 8
        i += 1

def get_variable_address():

    offset = get_operand()
    address = current_frame + offset
    
    i = 0
    while i < address_size:
        push_byte(address & 0xff)
        address = address >> 8
        i += 1

def load_array_value():

    offset = get_operand()
    index_size = get_operand()
    size = get_operand()
    
    index = 0
    i = 0
    while i < index_size:
        index = (index << 8) | pop_byte()
        i += 1
    
    offset = offset + (index * size)
    i = 0
    while i < size:
        push_byte(memory[current_frame + offset + i])
        i += 1

def load_array_byte_value():

    offset = get_operand()
    index = pop_byte()
    offset = offset + index
    push_byte(memory[current_frame + offset])
    
def store_array_value():

    offset = get_operand()
    index_size = get_operand()
    size = get_operand()
    
    element_ptr = stack_pointer - size
    index_ptr = element_ptr - index_size
    
    index = 0
    i = index_size
    while i > 0:
        i -= 1
        index = (index << 8) | memory[index_ptr + i]
    
    offset = offset + (index * size)
    i = size
    while i > 0:
        i -= 1
        memory[current_frame + offset + i] = memory[element_ptr + i]
    
    _free_stack_space(size + index_size)

def store_array_byte_value():

    offset = get_operand()
    
    element_ptr = stack_pointer - 1
    index_ptr = element_ptr - 1
    
    index = memory[index_ptr]
    
    offset = offset + index
    memory[current_frame + offset] = memory[element_ptr]
    
    _free_stack_space(2)

def end():

    raise StopIteration

lookup = {
    opcodes.load_number: load_number,
    opcodes.load_byte: load_byte,
    opcodes.compare_equals: compare_equals,
    opcodes.compare_equals_byte: compare_equals_byte,
    opcodes.compare_not_equals: compare_not_equals,
    opcodes.compare_not_equals_byte: compare_not_equals_byte,
    opcodes.compare_less_than: compare_less_than,
    opcodes.compare_less_than_byte: compare_less_than_byte,
    opcodes.compare_greater_than: compare_greater_than,
    opcodes.compare_greater_than_byte: compare_greater_than_byte,
    opcodes.add: add,
    opcodes.add_byte: add_byte,
    opcodes.add_byte_constant: add_byte_constant,
    opcodes.subtract: subtract,
    opcodes.subtract_byte: subtract_byte,
    opcodes.subtract_byte_constant: subtract_byte_constant,
    opcodes.multiply: multiply,
    opcodes.divide: divide,
    opcodes.logical_and: logical_and,
    opcodes.logical_or: logical_or,
    opcodes.logical_not: logical_not,
    opcodes.minus: minus,
    opcodes.bitwise_and: bitwise_and,
    opcodes.left_shift: left_shift,
    opcodes.right_shift: right_shift,
    opcodes.branch_forward_if_false: branch_forward_if_false,
    opcodes.branch_forward: branch_forward,
    opcodes.branch_backward_if_false: branch_backward_if_false,
    opcodes.branch_backward: branch_backward,
    opcodes.jump_if_false: jump_if_false,
    opcodes.jump: jump,
    opcodes.load_local: load_local,
    opcodes.load_local_byte: load_local_byte,
    opcodes.load_global: load_global,
    opcodes.assign_local: assign_local,
    opcodes.assign_local_byte: assign_local_byte,
    opcodes.function_return: function_return,
    opcodes.function_call: function_call,
    opcodes.load_current_frame_address: load_current_frame_address,
    opcodes.store_stack_top_in_current_frame: store_stack_top_in_current_frame,
    opcodes.allocate_stack_space: allocate_stack_space,
    opcodes.free_stack_space: free_stack_space,
    opcodes.pop_current_frame_address: pop_current_frame_address,
    opcodes.copy_value: copy_value,
    opcodes.sys_call: sys_call,
    opcodes.get_variable_address: get_variable_address,
    opcodes.load_array_value: load_array_value,
    opcodes.load_array_byte_value: load_array_byte_value,
    opcodes.store_array_value: store_array_value,
    opcodes.store_array_byte_value: store_array_byte_value,
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
    
    call_stack_base = call_stack_pointer = end
    stack_base = current_frame = stack_pointer = end + 16 * address_size

def run(start_address, step = True, verbose = True):

    global program_counter, stack_pointer, sys_call_prompt
    
    program_counter = start_address
    sys_call_prompt = step
    
    while True:
    
        instruction_address = program_counter
        instruction = lookup[get_instruction()]
        if verbose:
            print "%04x" % instruction_address, instruction
        if instruction == end:
            break
        instruction()
        if verbose:
            print "Call: ", " ".join(map(lambda x: "%02x" % x, memory[call_stack_base:call_stack_pointer]))
            print "Value:", " ".join(map(lambda x: "%02x" % x, memory[stack_base:stack_pointer]))
        if step:
            q = raw_input(">")
            if q == "c":
                step = False
    
    return memory[stack_base:stack_pointer]
