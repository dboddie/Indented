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
import compiler, opcodes

version = "0.1"

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
    
    load_address_string = filter(lambda x: x.startswith(".org"),
                                 open("6502/routines.oph").readlines())[0].split()[1]
    load_address = int(load_address_string[1:], 16)
    
    # Calculate the program address to enable linking to occur.
    program_address = load_address + opcodes.end + 2
    
    try:
        compiler.parse_program(stream)
    except SyntaxError as exception:
        sys.stderr.write(str(exception) + "\n")
        sys.exit(1)
    
    try:
        compiler.generator.link(compiler.functions, program_address)
    except KeyError as exception:
        sys.stderr.write(str(exception) + "\n")
        sys.exit(1)
    
    compiler.save_opcodes_oph("6502/program.oph")
    program_length = len(compiler.generator.code)
    print "Program is", program_length, "bytes long."
    
    system("ophis 6502/routines.oph -o CODE")
    code = open("CODE").read()
    
    # Set the execution address to be the address following the opcodes.
    files = [("CODE", load_address, program_address + program_length, code)]
    
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
