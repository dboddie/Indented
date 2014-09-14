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
import compiler

if __name__ == "__main__":

    for name in os.listdir("Examples"):
    
        print name,
        
        compiler.tokeniser.reset()
        reload(compiler)
        stream = open(os.path.join("Examples", name))
        
        try:
            compiler.parse_program(stream)
        except SyntaxError as exception:
            if name.endswith("fail.txt"):
                print "failed as expected"
            else:
                print "failed", str(exception)
        else:
            print "passed"
