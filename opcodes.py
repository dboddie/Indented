"""
opcodes.py - Opcodes for a simple virtual machine.

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

load_number, \
load_byte, \
compare_equals, \
compare_equals_byte, \
compare_not_equals, \
compare_not_equals_byte, \
compare_less_than, \
compare_less_than_byte, \
compare_greater_than, \
compare_greater_than_byte, \
add, \
add_byte, \
add_byte_constant, \
subtract, \
subtract_byte, \
subtract_byte_constant, \
multiply, \
divide, \
logical_and, \
logical_or, \
logical_not, \
minus, \
bitwise_and, \
bitwise_and_byte, \
bitwise_and_byte_constant, \
bitwise_or, \
bitwise_or_byte, \
bitwise_or_byte_constant, \
bitwise_eor, \
bitwise_eor_byte, \
bitwise_eor_byte_constant, \
left_shift, \
right_shift, \
branch_forward_if_false, \
branch_forward, \
branch_backward_if_false, \
branch_backward, \
jump_if_false, \
jump, \
load_local, \
load_local_byte, \
load_global, \
assign_local, \
assign_local_byte, \
function_return, \
function_call, \
load_current_frame_address, \
store_stack_top_in_current_frame, \
allocate_stack_space, \
free_stack_space, \
pop_current_frame_address, \
copy_value, \
sys_call, \
get_variable_address, \
load_array_value, \
load_array_byte_value, \
store_array_value, \
store_array_byte_value, \
load_memory_value, \
load_memory_byte_value, \
store_memory_value, \
store_memory_byte_value, \
end = range(256, 256 + 63)

address_size = 2
branch_size = 1
memory_size = 32768
register_size = 1
system_call_return_size = 4
shift_size = 1
