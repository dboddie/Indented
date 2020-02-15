"""
linker.py - Functions for linking and packaging code to run on the 6502 CPU.

Copyright (C) 2015 David Boddie <david@boddie.org.uk>

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

import os, sys
import UEFfile

def system(command):

    if os.system(command):
        sys.exit(1)

def get_program_address():

    routines_oph = open("arch/_6502/routines.oph").readlines()
    for line in routines_oph:
        if line.startswith(".org"):
            load_address_string = line.split()[1]
            load_address = int(load_address_string[1:], 16)
            break
    else:
        sys.stderr.write("No address found in arch/_6502/routines.oph file.\n")
        sys.exit(1)
    
    # Calculate the program address to enable linking to occur.
    program_address = load_address
    
    return program_address
    
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

def write_opcodes(f, opcodes):

    i = 0
    while i < len(opcodes):
        line = []
        for opcode in opcodes[i:i + 24]:
            line.append(opcode & 0xff)
        f.write(".byte " + ", ".join(map(str, line)) + "\n")
        i += 24

def save_opcodes_oph(file_name_or_obj, program_address, start_address,
                     program_opcodes):

    if isinstance(file_name_or_obj, file):
        f = file_name_or_obj
    else:
        f = open(file_name_or_obj, "w")
    
    write_opcodes(f, program_opcodes[:start_address - program_address])
    f.write("; address = $%x\n" % start_address)
    f.write("program_start:\n")
    write_opcodes(f, program_opcodes[start_address - program_address:])
    f.write("\n")
    
    if not isinstance(file_name_or_obj, file):
        f.close()

def link(program_opcodes, program_address, start_address, routines_used,
         manifest_file, output_file, version):

    # Write the program file, including only the required routines from the
    # routines.oph file.
    f = open("arch/_6502/program.oph", "w")
    
    routines_oph = open("arch/_6502/routines.oph").readlines()
    routines = read_routines(routines_oph)
    write_header(f, routines)
    
    # Write the opcodes used in the program to the output file.
    f.write("program:\n")
    save_opcodes_oph(f, program_address, start_address, program_opcodes)
    
    # Write the routines corresponding to the opcodes and lookup tables for them.
    write_routines(f, routines, routines_used)
    write_lookup_tables(f, routines_used)
    
    f.write("\n_stack:\n")
    
    f.close()
    
    system("ophis arch/_6502/program.oph -o CODE")
    code = open("CODE").read()
    
    # Set the execution address to be the address following the opcodes.
    program_length = len(program_opcodes)
    files = [("CODE", program_address, program_address + program_length, code)]
    
    if manifest_file:
    
        # Read the manifest file and include the files there in the file list.
        try:
            lines = open(manifest_file).readlines()
        except IOError:
            sys.stderr.write("Failed to read manifest file: %s\n" % manifest_file)
            sys.exit(1)
        
        manifest_dir = os.path.split(manifest_file)[0]
        
        l = 1
        for line in lines:
            pieces = line.strip().split()
            if len(pieces) == 4:
                source, obj, load, exec_ = pieces
                source_path = os.path.join(manifest_dir, source)
            elif len(pieces) == 3:
                obj, load, exec_ = pieces
            else:
                sys.stderr.write("Invalid input in manifest file '%s' at line %i.\n" % (manifest_file, l))
                sys.exit(1)
            
            l += 1
            
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
    
    u = UEFfile.UEFfile(creator = 'Indented build.py ' + version)
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
    
    # Add a high tone and gap at the end.
    u.chunks += [(0x110, "\xdc\x02"), (0x112, "\xdc\x02")]
    
    # Write the new UEF file.
    try:
        u.write(output_file, write_emulator_info = False)
    except UEFfile.UEFfile_error:
        sys.stderr.write("Couldn't write the new executable to %s.\n" % output_file)
        sys.exit(1)
