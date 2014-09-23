"""
compiler.py - A compiler for a simple programming language.

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

# Code maintenance functions

def discard_code(address):

    code[:] = code[:address]

def fix_returns(code_start):

    target = len(code)
    i = code_start
    while i < target:
        instruction = code[i]
        if instruction == "exit_function":
            code[i] = branch_forward
            offset = target - i
            i += 1
            code[i] = offset
        i += 1

def link(functions, base_address):

    global code
    
    # The code for each function is appended to the main code.
    # Use a dictionary to record this for now, but consider other data
    # structures for other implementations.
    index = {}
    
    for name, parameters, local_variables, fn_code, return_size in functions:
    
        index[name] = len(code)
        code += fn_code
    
    i = 0
    while i < len(code):
    
        instruction = code[i]
        
        if instruction == "function_call":
        
            # Adjust the opcode.
            code[i] = function_call
            
            # Adjust the following address bytes to contain the address.
            name = code[i + 1]
            address = base_address + index[name]
            j = 0
            while j < address_size:
                i += 1
                code[i] = address & 0xff
                address = address >> 8
                j += 1
        i += 1

# Generation functions

def generate_number(token, size, base):

    global code
    value = int(token, base)
    code += [load_number, size]
    i = 0
    while i < size:
        code += [value & 0xff]
        value = value >> 8
        i += 1

def generate_boolean(value, size):

    global code
    code += [load_number, size]
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
    code += [compare_equals, size]

def generate_not_equals(size):

    global code
    code += [compare_not_equals, size]

def generate_less_than(size):

    global code
    code += [compare_less_than, size]

def generate_greater_than(size):

    global code
    code += [compare_greater_than, size]

def generate_add(size):

    global code
    code += [add, size]

def generate_subtract(size):

    global code
    code += [subtract, size]

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
    code += [bitwise_and, size1, size2]

def generate_left_shift(size):

    global code
    code += [left_shift, size]

def generate_right_shift(size):

    global code
    code += [right_shift, size]

def generate_if():

    global code
    offset = len(code)
    code += [branch_forward_if_false, None]
    return offset

def generate_else():

    global code
    offset = len(code)
    code += [branch_forward, None]
    return offset

def generate_while():

    global code
    offset = len(code)
    code += [branch_forward_if_false, None]
    return offset

def generate_target(address):

    global code
    offset = len(code) - address
    code[address + 1] = offset

def generate_branch(address):

    global code
    offset = address - len(code)
    if offset < 0:
        code += [branch_backward, -offset]
    else:
        code += [branch_forward, offset]

def generate_load_local(offset, size):

    global code
    code += [load_local, offset, size]

def generate_load_global(offset, size):

    global code
    code += [load_global, offset, size]

def generate_assign_local(offset, size):

    global code
    code += [assign_local, offset, size]

def generate_assign_global(offset, size):

    global code
    code += [assign_global, offset, size]

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
    if var_size > 0:
        code += [allocate_stack_space, var_size]

def generate_function_call(name):

    global code
    code += ["function_call", name]
    code += [0] * (address_size - 1)

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
    code += ["exit_function", None]

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
    code += [load_array_value, offset, size, index_size]

def generate_end():

    global code
    code += [end]
