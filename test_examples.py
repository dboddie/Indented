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
    "address-1.txt": [109, 121, 102, 105, 108, 101, 125, 14],
    "and-1.txt": [0, 31],
    "assignment-1.txt": [1],
    "assignment-2.txt": [1, 1],
    "assignment-3.txt": [3],
    "assignment-4.txt": [2],
    "assignment-5.txt": [255, 0],
    "assignment-6.txt": [30],
    "assignment-7.txt": [2, 8],
    "def-1.txt": [],
    "def-10.txt": [255],
    "def-11.txt": [6],
    "def-12.txt": [4],
    "def-13.txt": [4],
    "def-14.txt": [123, 0]
    }

if __name__ == "__main__":

    i = 2
    examples = os.listdir("Examples")
    examples.sort()
    for name in examples:
    
        try:
            stream = open(os.path.join("Examples", name))
        except IOError:
            continue
        
        print name,
        
        compiler.tokeniser.reset()
        reload(compiler)
        reload(generator)
        
        try:
            compiler.parse_program(stream)
        except SyntaxError as exception:
            if name.endswith("fail.txt"):
                print "failed as expected"
                continue
            else:
                print "failed", str(exception)
        else:
            print "passed"
        
        reload(simulator)
        load_address = 0x0e00 + opcodes.end + 2
        
        generator.link(compiler.functions, load_address)
        simulator.load(generator.code, load_address)
        
        result = simulator.run(step = False, verbose = False)
        try:
            expected = expected_results[name]
        except KeyError:
            print "Obtained:", result
            raise
        
        if result != expected:
            print "Expected:", expected
            print "Obtained:", result
