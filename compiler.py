#!/usr/bin/env python

"""
compiler.py - A compiler for a simple programming language.

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

import sys
import tokeniser
from tokeniser import read_token

tokens = []
used = []

# Variable handling

global_variables = []
local_variables = []

def allocate_local(name, type):

    local_variables.append((name, type))

# Constant handling

def is_constant(token):

    if is_number(token):
        return True
    
    if is_string(token):
        return True
    
    return False

def is_number(token):

    if token[0] == "-":
        if len(token) == 1:
            return False
        else:
            i = 1
    else:
        i = 0
        
    while i < len(token):
        if token[i] not in "0123456789":
            return False
        i += 1
    
    return True

def is_string(token):

    if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
        return True

def get_token(stream):

    if tokens:
        token = tokens.pop(0)
    else:
        token = read_token(stream)
    
    # Transfer the token to the list of used tokens but also return it.
    used.append(token)
    return token

def put_tokens(index):

    tokens[:] = used[index:] + tokens
    used[:] = used[:index]

def discard_tokens():

    used[:] = []

# Parsing functions

def parse_def(stream):

    return False

"""
    token = get_token(stream)
    
    if token != "def":
        put_token(token)
        return False
    
    ###
"""

def parse_eof(stream):

    token = get_token(stream)
    return token == tokeniser.eof_token

def parse_expression(stream):

    "<expression> = <value> [<operator> <value>]+"
    
    if not parse_value(stream):
        return False
    
    while True:
    
        # Record the token index before each potential operation.
        top = len(used)
        
        if not parse_operator(stream):
            # Not an operator, so back out of the operation, but allow the
            # expression.
            put_tokens(top)
            break
        
        if not parse_value(stream):
            # Not a value, but one was expected, so report an error.
            raise SyntaxError, "Incomplete operation at line %i." % tokeniser.line
    
    return True

def parse_newline(stream):

    token = get_token(stream)
    return token == tokeniser.newline_token

def parse_operator(stream):

    '<operator> = "==" | "!=" | "<" | ">" | "+" | "-"'
    
    top = len(used)
    token = get_token(stream)
    
    if token == "==":
        print "equals", token
        return True
    
    elif token == "!=":
        print "not equals", token
        return True
    
    elif token == "<":
        print "less than", token
        return True
    
    elif token == ">":
        print "greater than", token
        return True
    
    elif token == "+":
        print "add", token
        return True
    
    elif token == "-":
        print "subtract", token
        return True
    
    put_tokens(top)
    return False

def parse_program(stream):

    while tokeniser.at_eof == False:
    
        if parse_statement(stream):
            print "statement"
        elif parse_separator(stream):
            print "separator"
        else:
            raise SyntaxError, "Unexpected input at line %i." % line

def parse_separator(stream):

    "<separator> = <newline> | <eof>"
    
    if parse_newline(stream):
        print "newline"
        return True
    elif parse_eof(stream):
        print "eof"
        return True
    else:
        return False

def parse_statement(stream):

    "<statement> = <expression> <separator>"
    
    top = len(used)
    
    if not parse_expression(stream):
        put_tokens(top)
        return False
    
    if parse_separator(stream):
        return True
    else:
        put_tokens(top)
        return False

def parse_value(stream):

    "<value> = <number> | <string>"
    
    top = len(used)
    token = get_token(stream)
    
    if is_number(token):
        print "constant", token
        return True
    
    elif is_string(token):
        print "constant", token
        return True
    
    else:
        for name, type in local_variables:
            if name == token:
                print "local variable", token
                return True
        
        for name, type in global_variables:
            if name == token:
                print "global variable", token
                return True
    
    put_tokens(top)
    return False

if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <file>\n" % sys.argv[0])
        sys.exit(1)
    
    stream = open(sys.argv[1])
    
    parse_program(stream)
    
    while True:
        token = read_token(stream)
        if token == tokeniser.eof_token:
            break
        
        print repr(token)
