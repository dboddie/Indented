"""
generator.py - Code generator for a simple compiler.

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

from opcodes import *
from tokeniser import eof_token, read_token

# Generated code

code = []
base_address = 0

# Code maintenance functions

def discard_code(address):

    code[:] = code[:address]

def fix_returns(code_start):

    target = len(code)
    i = code_start
    while i < target:
        instruction = code[i]
        if instruction == "exit_function":
            code[i] = jump
            address = base_address + target
            j = 0
            while j < address_size:
                code[i + j + 1] = address & 0xff
                address = address >> 8
                j += 1
            i += j
        i += 1

# Generation functions

def generate_number(token, size, base):

    global code
    value = int(token, base)
    if size > 1:
        code += [load_number, size]
    else:
        code += [load_byte]
    
    i = 0
    while i < size:
        code += [value & 0xff]
        value = value >> 8
        i += 1

def generate_boolean(value, size):

    global code
    if size > 1:
        code += [load_number, size]
    else:
        code += [load_byte]
    
    i = 0
    while i < size:
        code += [value & 0xff]
        value = value >> 8
        i += 1

def generate_string(token, size):

    global code
    code += [load_number, size]
    i = 0
    while i < size:
        code += [ord(token[i])]
        i += 1

def generate_equals(size):

    global code
    if size > 1:
        code += [compare_equals, size]
    else:
        code += [compare_equals_byte]

def generate_not_equals(size):

    global code
    if size > 1:
        code += [compare_not_equals, size]
    else:
        code += [compare_not_equals_byte]

def generate_less_than(size):

    global code
    if size > 1:
        code += [compare_less_than, size]
    else:
        code += [compare_less_than_byte]

def generate_greater_than(size):

    global code
    if size > 1:
        code += [compare_greater_than, size]
    else:
        code += [compare_greater_than_byte]

def generate_add(size):

    global code
    if size > 1:
        code += [add, size]
    elif code[-2] == load_byte:
        code[-2] = add_byte_constant
    else:
        code += [add_byte]

def generate_subtract(size):

    global code
    if size > 1:
        code += [subtract, size]
    elif code[-2] == load_byte:
        code[-2] = subtract_byte_constant
    else:
        code += [subtract_byte]

def generate_multiply(size):

    global code
    code += [multiply, size]

def generate_divide(size):

    global code
    code += [divide, size]

def generate_logical_and():

    global code
    code += [logical_and]

def generate_logical_or():

    global code
    code += [logical_or]

def generate_logical_not():

    global code
    code += [logical_not]

def generate_minus(size):

    global code
    code += [minus, size]

def generate_bitwise_and(size1, size2):

    global code
    if size1 > 1 or size2 > 1:
        code += [bitwise_and, size1, size2]
    elif code[-2] == load_byte:
        code[-2] = bitwise_and_byte_constant
    else:
        code += [bitwise_and_byte]

def generate_bitwise_or(size1, size2):

    global code
    if size1 > 1 or size2 > 1:
        code += [bitwise_or, size1, size2]
    elif code[-2] == load_byte:
        code[-2] = bitwise_or_byte_constant
    else:
        code += [bitwise_or_byte]

def generate_bitwise_eor(size1, size2):

    global code
    if size1 > 1 or size2 > 1:
        code += [bitwise_eor, size1, size2]
    elif code[-2] == load_byte:
        code[-2] = bitwise_eor_byte_constant
    else:
        code += [bitwise_eor_byte]

def generate_bitwise_not(size):

    global code
    if size > 1:
        code += [load_number, size]
        i = 0
        while i < size:
            code += [0xff]
            i += 1
        code += [bitwise_eor, size, size]
    else:
        code += [load_byte, 0xff, bitwise_eor_byte]

def generate_left_shift(size):

    global code
    code += [left_shift, size]

def generate_right_shift(size):

    global code
    code += [right_shift, size]

def generate_if():

    global code
    offset = len(code)
    code += [jump_if_false, None, None]
    return offset

def generate_else():

    global code
    offset = len(code)
    code += [jump, None, None]
    return offset

def generate_while():

    global code
    offset = len(code)
    code += [jump_if_false, None, None]
    return offset

def generate_target(address):

    global code
    target = base_address + len(code)
    i = 0
    while i < address_size:
        code[address + i + 1] = target & 0xff
        target = target >> 8
        i += 1

def generate_branch(address):

    global code
    offset = address - len(code)
    if offset < 0:
        if offset > -255:
            code += [branch_backward, -offset]
            return
    else:
        if offset <= 255:
            code += [branch_forward, offset]
            return
    
    code += [jump]
    address += base_address
    i = 0
    while i < address_size:
        code += [address & 0xff]
        address = address >> 8
        i += 1

def generate_load_local(offset, size):

    global code
    if size > 1:
        code += [load_local, offset, size]
    else:
        code += [load_local_byte, offset]

def generate_load_global(offset, size):

    global code
    if size > 1:
        code += [load_global, offset, size]
    else:
        code += [load_global_byte, offset]

def generate_assign_local(offset, size):

    global code
    if size > 1:
        code += [assign_local, offset, size]
    else:
        code += [assign_local_byte, offset]

def generate_assign_global(offset, size):

    global code
    if size > 1:
        code += [assign_global, offset, size]
    else:
        code += [assign_global_byte, offset]

def generate_discard_value(size):

    global code
    if size > 0:
        code += [free_stack_space, size]

def generate_return():

    global code
    code += [function_return]

def generate_allocate_stack_space(size):

    global code
    code += [allocate_stack_space, size]

def generate_push_parent_frame():

    global code
    
    # Push the current frame register onto the value stack.
    code += [load_current_frame_address]

def generate_enter_frame(param_size, var_size):

    global code
    
    # Put the stack top address, minus the number of bytes for the parameters
    # in the current frame register.
    code += [store_stack_top_in_current_frame, param_size]
    
    # Allocate enough space for the local variables.
    code += [allocate_stack_space, var_size]

def generate_function_call(address):

    global code
    code += [function_call]
    i = 0
    while i < address_size:
        code += [address & 0xff]
        address = address >> 8
        i += 1

def generate_function_tidy(total_size, return_size):

    global code
    
    # Pop bytes from the value stack that correspond to the parameters, local
    # variables and return value.
    code += [free_stack_space, total_size + return_size]
    
    # Restore the previous frame address from the stack.
    code += [pop_current_frame_address]
    
    # Copy the return value from the top of the stack to the top of the
    # parent frame. This will automatically include the size of the frame
    # address that was on the stack.
    if return_size > 0:
        code += [copy_value, total_size, return_size]

def generate_exit_function():

    global code
    code += ["exit_function", None, None]

def generate_system_call(total_args_size):

    global code
    
    # The arguments themselves should have already been pushed onto the stack.
    # The total size allows us to generate code to extract them.
    code += [sys_call, total_args_size]

def generate_get_variable_address(offset):

    global code
    code += [get_variable_address, offset]

def generate_load_array_value(offset, size, index_size):

    global code
    if index_size > 1 or size > 1:
        code += [load_array_value, offset, index_size, size]
    else:
        code += [load_array_byte_value, offset]

def generate_store_array_value(offset, size, index_size):

    global code
    if index_size > 1 or size > 1:
        code += [store_array_value, offset, index_size, size]
    else:
        code += [store_array_byte_value, offset]

def generate_load_memory_value(size):

    global code
    if size > 1:
        code += [load_memory_value, size]
    else:
        code += [load_memory_byte_value]

def generate_store_memory_value(size):

    global code
    if size > 1:
        code += [store_memory_value, size]
    else:
        code += [store_memory_byte_value]

def generate_end():

    global code
    code += [end]
