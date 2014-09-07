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
compare_equals, \
compare_not_equals, \
compare_less_than, \
compare_greater_than, \
add, \
subtract, \
multiply, \
divide, \
branch_if_false, \
branch_if_true, \
branch, \
load_local, \
load_global, \
assign_local, \
function_return, \
function_call, \
load_current_frame_address, \
store_stack_top_in_current_frame, \
allocate_stack_space, \
free_stack_space, \
pop_current_frame_address, \
copy_value, \
end = range(0, 48, 2)

address_size = 2
branch_size = 1
