#!/usr/bin/env python

import os, pprint, sys
import compiler, generator, simulator, tokeniser
from arguments import find_option


if __name__ == "__main__":

    this_program, args = sys.argv[0], sys.argv[1:]
    run = find_option(args, "-r", 0)
    target, architecture = find_option(args, "-t", 1)
    output, file_name = find_option(args, "-o", 1)
    debug = find_option(args, "-d", 0)
    
    if len(args) != 1 or (not target and not run):
        sys.stderr.write(
            "Usage: %s [-r] [-t <target>] <file> [-o <output file>]\n\n"
            "-r    Run the generated code in a simulator.\n"
            "-t    Generate code for the specified <target> architecture.\n"
            "-o    Write the generated code to the specified <output file>.\n"
            "-d    Write debugging information to stdout.\n\n" % this_program)
        sys.exit(1)
    
    compiler.include_dir = os.path.join(os.path.split(this_program)[0], "include", architecture)
    
    stream = open(args[0])
    
    if architecture == "6502":
        from arch._6502 import linker, parsing
        compiler.parsing = parsing
        program_address = linker.get_program_address()
    elif run:
        program_address = 0
    else:
        sys.stderr.write("Unknown target architecture specified: %s\n" % architecture)
        sys.exit(1)
    
    try:
        start_address = compiler.parse_program(stream, program_address)
    except SyntaxError as exception:
        sys.stderr.write(str(exception) + "\n")
        sys.exit(1)
    
    print "Functions:"
    pprint.pprint(compiler.functions)
    
    print "Main variables:"
    pprint.pprint(compiler.local_variables)
    
    print "Main code:"
    addr = program_address
    for v in generator.code:
        print "%04x: %03i (%02x)" % (addr, v, v)
        addr += 1
    
    print "Opcode usage:"
    d = compiler.get_opcodes_used()
    freq = map(lambda (k, v): (v, k), d.items())
    freq.sort()
    for v, k in freq:
        print simulator.lookup[k], v
    
    if run:
        print "Loading"
        simulator.load(generator.code, program_address)
        print "Running"
        print simulator.run(start_address)
    
    if output:
        compiler.save_opcodes(file_name)
