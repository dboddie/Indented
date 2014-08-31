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

def discard_code(address):

    code[:] = code[:address]

def generate_locals(local_variables):

    code = []
    code.append((save_local_stack_pointer, None))
    
    offset = 0
    for name, type in local_variables:
    
        code.append((allocate_local_stack_space, type.size))
    
    return code

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

def generate_target(address):

    offset = len(code) - address
    code[address][1] = offset

def generate_branch(address):

    offset = address - (len(code) + 1)
    code.append((branch, offset))

def generate_load_local(offset, size):

    code.append((load_local, (offset, size)))

def generate_load_global(offset, size):

    code.append((load_global, (offset, size)))

def generate_assign_local(offset, size):

    code.append((assign_local, (offset, size)))

def generate_assign_global(offset, size):

    code.append((assign_global, (offset, size)))
