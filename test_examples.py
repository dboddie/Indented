#!/usr/bin/env python

"""
test_examples.py - Tests the code examples.

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

import os, sys
import compiler, generator, opcodes, simulator

expected_results = {
    "address-1.txt": [109, 121, 102, 105, 108, 101, 127, 14],
    "addition-1.txt": [],
    "addition-3.txt": [],
    "addition-4.txt": [],
    "and-1.txt": [0, 31],
    "and-2.txt": [255, 31, 31, 63, 63],
    "and-3.txt": [2],
    "assignment-1.txt": [1],
    "assignment-2.txt": [1, 1],
    "assignment-3.txt": [3],
    "assignment-4.txt": [2],
    "assignment-5.txt": [255, 0],
    "assignment-6.txt": [30],
    "assignment-7.txt": [2, 8],
    "assignment-8.txt": [74, 101, 108, 108, 111],
    "assignment-9.txt": [65, 66, 67, 68, 69, 70, 6],
    "def-1.txt": [],
    "def-2.txt": [],
    "def-3.txt": [],
    "def-4.txt": [],
    "def-5.txt": [],
    "def-6.txt": [],
    "def-7.txt": [1, 2, 6],
    "def-8.txt": [123, 255],
    "def-9.txt": [],
    "def-10.txt": [255],
    "def-11.txt": [6],
    "def-12.txt": [4],
    "def-13.txt": [4],
    "def-14.txt": [123, 0],
    "def-15.txt": [],
    "def-16.txt": [],
    "def-17.txt": [],
    "def-18.txt": [5],
    "eor-1.txt": [255, 31, 224, 32, 255],
    "expression-1.txt": [],
    "expression-2.txt": [],
    "expression-3.txt": [],
    "expression-4.txt": [0, 0, 0, 255],
    "expression-5.txt": [0, 255, 255, 255],
    "expression-6.txt": [255, 0, 0, 0, 255, 0, 0, 255, 0, 0, 255, 0, 0, 0],
    "expression-7.txt": [255, 0, 255, 0, 255, 255, 255, 255, 0, 255, 255, 255, 255, 0],
    "expression-8.txt": [255, 255, 1, 255],
    "expression-9.txt": [3],
    "expression-10.txt": [],
    "if-1.txt": [],
    "if-2.txt": [],
    "if-3.txt": [],
    "if-4.txt": [],
    "if-5.txt": [1],
    "if-6.txt": [2],
    "if-8.txt": [1],
    "minus-1.txt": [123, 133],
    "minus-2.txt": [158],
    "minus-3.txt": [1, 252],
    "not-1.txt": [255, 31, 210, 4, 0, 224, 45, 251],
    "not-2.txt": [121, 1, 0, 0],
    "or-1.txt": [255, 31, 255, 63, 255],
    "shift-1.txt": [61, 0, 1, 152, 0, 34],
    "string-1.txt": [72, 101, 108, 108, 111],
    "string-2.txt": [72, 101, 108, 108, 111, 0, 119, 111, 114, 108, 100],
    "string-3.txt": [],
    "string-4.txt": [72, 101, 108, 108, 111, 32, 119, 111, 114, 108, 100, 123],
    "string-5.txt": [83, 116, 114, 105, 110, 103, 83],
    "string-6.txt": [83, 116, 114, 105, 110, 103, 6, 103],
    "string-7.txt": [83, 116, 114, 105, 110, 103, 6, 103],
    "string-8.txt": [65, 66, 67, 68, 69, 70],
    "string-9.txt": [83, 116, 114, 105, 110, 103, 6],
    "subtract-1.txt": [10, 12, 254],
    "subtract-2.txt": [2, 0, 3, 0, 255, 255],
    "while-2.txt": [0],
    "while-3.txt": [1, 88],
    "while-4.txt": [1, 14]
    }

skip = [
    "inline-asm-1.txt",
    "inline-asm-2.txt",
    "inline-asm-3.txt",
    "while-1-fail.txt"  # does not terminate
    ]

compile_only = [
    "sys-1.txt",
    "sys-2.txt",
    "sys-3.txt",
    "sys-4.txt",
    "sys-5.txt",
    "sys-6.txt",
    "sys-7.txt",
    "sys-8.txt",
    "sys-9.txt",
    "sys-10.txt",
    "sys-11.txt",
    "sys-12.txt",
    "sys-13.txt",
    "sys-14.txt",
    "sys-15.txt",
    "sys-16.txt",
    "sys-18.txt"
    ]

if __name__ == "__main__":

    i = 2
    examples = os.listdir("Examples")
    examples.sort()
    for name in examples:
    
        try:
            stream = open(os.path.join("Examples", name))
        except IOError:
            continue
        
        if name in skip:
            print "Skipping", name
            continue
        
        print name,
        
        compiler.tokeniser.reset()
        reload(compiler)
        reload(generator)
        load_address = 0x0e00 + (opcodes.end - 256 + 1) * 2
        
        try:
            start_address = compiler.parse_program(stream, load_address)
        except SyntaxError as exception:
            if name.endswith("fail.txt"):
                print "failed as expected"
                continue
            else:
                print "failed", str(exception)
                sys.exit(1)
        else:
            print "passed"
        
        if name in compile_only:
            print "Not running", name
            continue
        
        reload(simulator)
        
        simulator.load(generator.code, load_address)
        
        result = simulator.run(start_address, step = False, verbose = False)
        try:
            expected = expected_results[name]
        except KeyError:
            print "Obtained:", result
            raise
        
        if result != expected:
            print "Expected:", expected
            print "Obtained:", result
