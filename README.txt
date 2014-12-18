Language Experiment - Simple Language with Meaningful Indentation
=================================================================

This repository contains a compiler for a simple language that uses
indentation to assign meaning to blocks of code in a similar way to the
Python programming language. However, the language is only superficially like
the Python language since it lacks many high level features and uses type
declarations to provide information to the compiler.

The features of the language are partly documented in the overview.txt file
which can be found in the Documents directory.

The compiler generates bytecodes for use with a set of accompanying 6502
routines to interpret those bytecodes. Both the routines and bytecodes are
combined together during the assembly process. A build tool automates this
process and also creates a UEF file for use in emulators.

Building an example
-------------------

To show how to use the build tool, we will show how to build one of the
examples in the Examples directory. The Sprites subdirectory contains a
program file, a manifest file, a helper script and some 6502 assembly
language routines: sprites.txt, manifest, makesprites.py and plotting.oph
respectively.

The build tool needs to know about the program and manifest files. To build
the example from the repository root directory, enter the following at the
command line:

./build.py Examples/Sprites/sprites.txt Examples/Sprites/manifest -o sprites.uef

The build tool runs the compiler on the sprites.txt source file and reads the
manifest file to discover the other files. The sprites.uef file should be
successfully created as a result. This can be loaded into any emulator for
8-bit Acorn computers that understands this type of file, such as Elkulator.

The compiled program will be presented as a file on a cassette tape. Run the
program from BBC BASIC by typing the following:

*TAPE
*RUN

The first command is only needed if the default filing system is not the
cassette filing system.

Copyright and License Information
---------------------------------

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
