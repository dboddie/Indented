#!/usr/bin/env python

"""
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

import os, stat, struct, sys

if __name__ == "__main__":

    usage = "<manifest file>"
    
    if not 1 <= len(sys.argv) <= 2:
    
        sys.stderr.write("Usage: %s %s\n" % (sys.argv[0], usage))
        sys.exit(1)
    
    if len(sys.argv) == 2:
        manifest_file = sys.argv[1]
        
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
                source, obj, load, exec_ = line.strip().split()
                path = os.path.join(manifest_dir, obj)
                if os.path.exists(path):
                    print "Removing", path
                    os.remove(path)
    
    if os.path.exists("CODE"):
        print "Removing CODE"
        os.remove("CODE")
    
    program_oph = os.path.join("6502", "program.oph")
    if os.path.exists(program_oph):
        print "Removing", program_oph
        os.remove(program_oph)
    
    # Exit
    sys.exit()
