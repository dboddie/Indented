Language Experiment - Simple Language with Meaningful Indentation
=================================================================

This repository contains a compiler for a simple language that uses
indentation to assign meaning to blocks of code in a similar way to the
Python programming language.

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
successfully created as a result. This can be loaded into any emulator that
understand these files, such as Elkulator, and will present the compiled
program as a file on a cassette tape. The user can run the program from BBC
BASIC by typing the following:

*TAPE
*RUN

The first command is only needed if the default filing system is not the
cassette filing system.

