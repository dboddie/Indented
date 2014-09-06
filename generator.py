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

from simulator import *
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
        instruction, value = code[i]
        if instruction == "exit_function":
            code[i] = (branch, target - i)
        i += 1

def link(functions):

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
        instruction, value = code[i]
        if instruction == function_call:
            code[i] = (function_call, index[value])
        i += 1

# Generation functions

def generate_number(token, size):

    value = int(token)
    code.append((load_number, (value, size)))

def generate_equals(size):

    code.append((compare_equals, size))

def generate_not_equals(size):

    code.append((compare_not_equals, size))

def generate_less_than(size):

    code.append((compare_less_than, size))

def generate_greater_than(size):

    code.append((compare_greater_than, size))

def generate_add(size):

    code.append((add, size))

def generate_subtract(size):

    code.append((subtract, size))

def generate_multiply(size):

    code.append((multiply, size))

def generate_divide(size):

    code.append((divide, size))

def generate_if():

    offset = len(code)
    code.append([branch_if_false, None])
    return offset

def generate_while():

    offset = len(code)
    code.append([branch_if_false, None])
    return offset

def generate_target(address):

    offset = len(code) - address
    code[address][1] = offset

def generate_branch(address):

    offset = address - len(code)
    code.append((branch, offset))

def generate_load_local(offset, size):

    code.append((load_local, (offset, size)))

def generate_load_global(offset, size):

    code.append((load_global, (offset, size)))

def generate_assign_local(offset, size):

    code.append((assign_local, (offset, size)))

def generate_assign_global(offset, size):

    code.append((assign_global, (offset, size)))

def generate_discard_value(size):

    if size > 0:
        code.append((free_stack_space, size))

def generate_return():

    code.append((function_return, None))

def generate_allocate_stack_space(size):

    code.append((allocate_stack_space, size))

def generate_push_parent_frame():

    # Push the current frame register onto the value stack.
    code.append((load_current_frame_address, None))

def generate_enter_frame(param_size, var_size):

    # Put the stack top address, minus the number of bytes for the parameters
    # in the current frame register.
    code.append((store_stack_top_in_current_frame, param_size))
    
    # Allocate enough space for the local variables.
    if var_size > 0:
        code.append((allocate_stack_space, var_size))

def generate_function_call(name):

    code.append((function_call, name))

def generate_function_tidy(total_size, return_size):

    # Pop bytes from the value stack that correspond to the parameters, local
    # variables and return value.
    code.append((free_stack_space, total_size + return_size))
    
    # Restore the previous frame address from the stack.
    code.append((pop_current_frame_address, None))
    
    # Copy the return value from the top of the stack to the top of the
    # parent frame. This will automatically include the size of the frame
    # address that was on the stack.
    if return_size > 0:
        code.append((copy_value, (total_size, return_size)))

def generate_exit_function():

    code.append(("exit_function", None))

def generate_end():

    code.append((end, None))
