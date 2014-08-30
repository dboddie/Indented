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

import string, sys
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

def get_size(token):

    if is_number(token):
        return True
    
    if is_string(token):
        return True
    
    raise SyntaxError, "Unknown size for constant '%s' at line %i." % (token, tokeniser.line)

def is_function_name(token):

    return is_variable(token)

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

variable_chars = string.letters + string.digits + "_"

def is_variable(token):

    if is_number(token):
        return False
    
    i = 0
    while i < len(token):
        if token[i] not in variable_chars:
            return False
        i += 1
    
    return True

def find_variable(token):

    for name, type in local_variables:
        if name == token:
            print "local variable", token
            return True
    
    for name, type in global_variables:
        if name == token:
            print "global variable", token
            return True
    
    return False

def get_token(stream):

    if tokens:
        token = tokens.pop(0)
    else:
        token = read_token(stream)
    
    # Transfer the token to the list of used tokens but also return it.
    used.append(token)
    
    #print_tokens()
    return token

def put_tokens(index):

    tokens[:] = used[index:] + tokens
    used[:] = used[:index]
    #print_tokens()

def discard_tokens():

    used[:] = []
    #print_tokens()

def print_tokens():

    used_str = " ".join(map(repr, used))
    print used_str, " ".join(map(repr, tokens))
    print " "*len(used_str) + "^"

# Parsing functions

def parse_body(stream):

    if not parse_indent(stream):
        return False
    
    has_body = False
    while True:
    
        if parse_control(stream):
            print "control"
        elif parse_statement(stream):
            print "statement"
        elif parse_separator(stream):
            # Handle blank lines.
            print "separator (blank)"
        elif parse_dedent(stream):
            break
        else:
            return False
        
        has_body = True
    
    if not has_body:
        return False
    
    print "body"
    return True

def parse_control(stream):

    top = len(used)
    token = get_token(stream)
    
    if token == "if":
        if parse_expression(stream):
            print "expression"
            if parse_body(stream):
                print "if"
                return True
        
        raise SyntaxError, "Invalid if structure at line %i." % tokeniser.line
    
    put_tokens(top)
    return False

def parse_dedent(stream):

    top = len(used)
    while True:
    
        token = get_token(stream)
        if token == tokeniser.newline_token:
            pass
        elif token == tokeniser.dedent_token:
            break
        else:
            put_tokens(top)
            return False
    
    return True

def parse_definition(stream):

    # Clear the list of local variables.
    local_variables[:] = []
    
    top = len(used)
    token = get_token(stream)
    
    if token == "def":
    
        token = get_token(stream)
        if not is_function_name(token):
            raise SyntaxError, "Invalid function name '%s' at line %i." % (
                token, tokeniser.line)
        
        # Read the parameters, appending the names and types to the list of
        # local variables.
        while True:
        
            token = get_token(stream)
            if token == tokeniser.newline_token:
                break
            
            elif not is_variable(token):
                raise SyntaxError, "Invalid parameter name '%s' at line %i." % (
                    token, tokeniser.line)
            
            name = token
            token = get_token(stream)
            if token != tokeniser.assignment_token:
                raise SyntaxError, "Expected '=' after parameter name '%s' at line %i." % (
                    name, tokeniser.line)
        
            token = get_token(stream)
            if not is_constant(token):
                raise SyntaxError, "Expected constant after parameter name '%s' at line %i." % (
                    name, tokeniser.line)
            
            local_variables.append((name, get_size(token)))
        
        if not parse_body(stream):
            raise SyntaxError, "Invalid function definition at line %i." % tokeniser.line
        
        return True
    
    else:
        put_tokens(top)
        return False

def parse_eof(stream):

    top = len(used)
    token = get_token(stream)
    
    if token == tokeniser.eof_token:
        return True
    else:
        put_tokens(top)
        return False

def parse_expression(stream):

    "<expression> = <operand> [<operator> <operand>]+"
    
    if not parse_operand(stream):
        return False
    
    while True:
    
        # Record the token index before each potential operation.
        top = len(used)
        
        if not parse_operator(stream):
            # Not an operator, so back out of the operation, but allow the
            # expression. The operator function should have pushed tokens back
            # on the stack.
            break
        
        if not parse_operand(stream):
            # Not a value, but one was expected, so report an error.
            raise SyntaxError, "Incomplete operation at line %i." % tokeniser.line
    
    return True

def parse_indent(stream):

    top = len(used)
    while True:
    
        token = get_token(stream)
        if token == tokeniser.newline_token:
            pass
        elif token == tokeniser.indent_token:
            break
        else:
            put_tokens(top)
            return False
    
    return True

def parse_newline(stream):

    top = len(used)
    token = get_token(stream)
    
    if token == tokeniser.newline_token:
        return True
    else:
        put_tokens(top)
        return False

def parse_operand(stream):

    "<operand> = <value> | <function call>"
    
    if parse_value(stream):
        return True
    elif parse_variable(stream, define = False):
        return True
    #elif parse_function_call(stream):
    #    return True
    else:
        return False

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
    
        if parse_control(stream):
            discard_tokens()
            print "control"
        elif parse_definition(stream):
            discard_tokens()
            print "definition"
        elif parse_statement(stream):
            discard_tokens()
            print "statement"
        elif parse_separator(stream):
            # Handle blank lines.
            discard_tokens()
            print "separator (blank)"
        else:
            raise SyntaxError, "Unexpected input at line %i." % tokeniser.line

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
    
    # The statement may be an assignment.
    if parse_variable(stream, define = True):
    
        token = get_token(stream)
        if token == "=":
            print "assignment"
        else:
            put_tokens(top)
    
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
        put_tokens(top)
        return False

def parse_variable(stream, define):

    global local_variables
    
    top = len(used)
    token = get_token(stream)
    
    if not is_variable(token):
        put_tokens(top)
        return False
    
    if find_variable(token):
        return True
    
    if define:
        print "define", token
        ### We need a way to determine if the variable is local or global.
        local_variables.append((token, None))
        return True
    else:
        put_tokens(top)
        return False


if __name__ == "__main__":

    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <file>\n" % sys.argv[0])
        sys.exit(1)
    
    stream = open(sys.argv[1])
    
    try:
        parse_program(stream)
    except SyntaxError as exception:
        sys.stderr.write(str(exception) + "\n")
