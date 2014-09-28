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
import cmdsyntax, UEFfile
import compiler, opcodes, simulator

version = "0.2"

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

def read_routines(lines):

    routines = []
    current = []
    
    for line in lines:
    
        l = line.lstrip()
        
        if ":" in line and line == l and not l.startswith(";"):
            # Start reading the new routine.
            if current:
                routines.append(current)
            
            current = [line]
        else:
            current.append(line)
    
    if current:
        routines.append(current)
    
    return routines

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

def write_header(f, routines):

    f.write("".join(routines[0]))

def write_routines(f, routines, names):

    for routine in routines:
        name = routine[0]
        if ":" in name:
            name = name[:name.find(":")]
            # Check for internal routines.
            if name.startswith("_"):
                f.write("".join(routine))
            elif name in names:
                f.write("".join(routine))

def write_lookup_tables(f, names):

    f.write("\nlookup_low:\n")
    for name in names:
        f.write(".byte <[%s - 1]\n" % name)
    
    f.write("\nlookup_high:\n")
    for name in names:
        f.write(".byte >[%s - 1]\n" % name)


if __name__ == "__main__":

    usage = "<program file> [<manifest file>] -o <new UEF file>"
    syntax = cmdsyntax.Syntax(usage)
    matches = syntax.get_args(sys.argv[1:])
    
    if len(matches) != 1:
    
        sys.stderr.write("Usage: %s %s\n" % (sys.argv[0], usage))
        sys.exit(1)
    
    match = matches[0]
    input_file = match["program file"]
    manifest_file = match.get("manifest file")
    out_uef_file = match["new UEF file"]
    
    stream = open(input_file)
    
    routines_oph = open("6502/routines.oph").readlines()
    for line in routines_oph:
        if line.startswith(".org"):
            load_address_string = line.split()[1]
            load_address = int(load_address_string[1:], 16)
            break
    else:
        sys.stderr.write("No address found in 6502/routines.oph file.\n")
        sys.exit(1)
    
    # Calculate the program address to enable linking to occur.
    program_address = load_address
    
    try:
        start_address = compiler.parse_program(stream, program_address)
    except SyntaxError as exception:
        sys.stderr.write(str(exception) + "\n")
        sys.exit(1)
    
    program_length = len(compiler.generator.code)
    print "Program is", program_length, "bytes long."
    
    # Write the program file, including only the required routines from the
    # routines.oph file.
    f = open("6502/program.oph", "w")
    
    used = compiler.get_opcodes_used()
    names = renumber_opcodes(used)
    
    routines = read_routines(routines_oph)
    write_header(f, routines)
    
    f.write("program:\n")
    compiler.save_opcodes_oph(f, start_address)
    
    write_routines(f, routines, names)
    write_lookup_tables(f, names)
    
    f.write("\n_stack:\n")
    
    f.close()
    
    system("ophis 6502/program.oph -o CODE")
    code = open("CODE").read()
    
    # Set the execution address to be the address following the opcodes.
    files = [("CODE", load_address, load_address + program_length, code)]
    
    if manifest_file:
    
        # Read the manifest file and include the files there in the file list.
        try:
            lines = open(manifest_file).readlines()
        except IOError:
            sys.stderr.write("Failed to read manifest file: %s\n" % manifest_file)
            sys.exit(1)
        
        manifest_dir = os.path.split(manifest_file)[0]
        
        for line in lines:
            pieces = line.strip().split()
            if len(pieces) == 4:
                source, obj, load, exec_ = pieces
                source_path = os.path.join(manifest_dir, source)
            else:
                obj, load, exec_ = pieces
            
            obj_path = os.path.join(manifest_dir, obj)
            if len(pieces) == 4:
                if source_path.endswith(".oph"):
                    system("ophis " + source_path + " -o " + obj_path)
                elif source_path.endswith(".py"):
                    system("python " + source_path + " -o " + obj_path)
            
            try:
                data = open(obj_path).read()
            except IOError:
                sys.stderr.write("Failed to open file found in manifest: %s\n" % obj_path)
                sys.exit(1)
            
            load = int(load[2:], 16)
            exec_ = int(exec_[2:], 16)
            files.append((obj, load, exec_, data))
    
    u = UEFfile.UEFfile(creator = 'build.py '+version)
    u.minor = 6
    u.target_machine = "Electron"
    
    u.import_files(0, files)
    
    # Insert a gap before each file.
    offset = 0
    for f in u.contents:
    
        # Insert a gap and some padding before the file.
        gap_padding = [(0x112, "\xdc\x05"), (0x110, "\xdc\x05"), (0x100, "\xdc")]
        u.chunks = u.chunks[:f["position"] + offset] + \
                   gap_padding + u.chunks[f["position"] + offset:]

        # Each time we insert a gap, the position of the file changes, so we
        # need to update its position and last position. This isn't really
        # necessary because we won't read the contents list again.
        offset += len(gap_padding)
        f["position"] += offset
        f["last position"] += offset
    
    # Write the new UEF file.
    try:
        u.write(out_uef_file, write_emulator_info = False)
    except UEFfile.UEFfile_error:
        sys.stderr.write("Couldn't write the new executable to %s.\n" % out_uef_file)
        sys.exit(1)
    
    # Exit
    sys.exit()
