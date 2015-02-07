#!/usr/bin/env python

"""
Copyright (C) 2012 David Boddie <david@boddie.org.uk>

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

import os, stat, struct, sys
import UEFfile
import compiler, opcodes, simulator
from arguments import find_option

# The version is obtained from the compiler module.
version = compiler.version

def system(command):

    if os.system(command):
        sys.exit(1)

def address_length_end(address, data):

    address_low = address & 0xff
    address_high = address >> 8
    length = len(data)
    length_low = length & 0xff
    length_high = length >> 8
    end = address + length
    end_low = end & 0xff
    end_high = end >> 8
    return address_low, address_high, length_low, length_high, end_low, end_high

def renumber_opcodes(used):

    items = used.items()
    items.sort()
    
    # Renumber the opcodes.
    mapping = {}
    i = 0
    for opcode, frequency in items:
        mapping[opcode] = i
        i += 1
    
    # Replace the old opcodes with the renumbered ones.
    i = 0
    while i < len(compiler.generator.code):
        value = compiler.generator.code[i]
        compiler.generator.code[i] = mapping.get(value, value)
        i += 1
    
    names = []
    for opcode, frequency in items:
        names.append(simulator.lookup[opcode].__name__)
    
    return names


if __name__ == "__main__":

    this_program, args = sys.argv[0], sys.argv[1:]
    target, architecture = find_option(args, "-t", 1)
    output, output_file = find_option(args, "-o", 1)
    
    if not 1 <= len(args) <= 2:
        sys.stderr.write(
            "Usage: %s <program file> [<manifest file>] -t <target> -o <output file>\n\n"
            "-t    Generate code for the specified <target> architecture.\n"
            "-o    Write the generated code to the specified <output file>.\n\n" % this_program)
        sys.exit(1)
    
    input_file = args.pop(0)
    if args:
        manifest_file = args.pop(0)
    else:
        manifest_file = None
    
    stream = open(input_file)
    
    if architecture == "6502":
        from 6502 import linker
        program_address = linker.get_program_address()
    
    try:
        start_address = compiler.parse_program(stream, program_address)
    except SyntaxError as exception:
        sys.stderr.write(str(exception) + "\n")
        sys.exit(1)
    
    program_length = len(compiler.generator.code)
    print "Program is", program_length, "bytes long."
    
    # Find the opcodes used and the corresponding routines for them.
    opcodes_used = compiler.get_opcodes_used()
    routines_used = renumber_opcodes(opcodes_used)
    
    linker.link(routines, manifest_file, output_file)
    
    # Exit
    sys.exit()
