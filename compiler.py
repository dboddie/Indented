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

import pprint, string, sys
import generator, tokeniser
from tokeniser import read_token

# Token handling - lists of incoming tokens and those tentatively processed

tokens = []
used = []

# Variable and type definitions

global_variables = []
local_variables = []
current_size = 0

# Function definitions

functions = []

# Constant handling

def is_constant(token):

    if is_boolean(token):
        return True
    
    if is_number(token):
        return True
    
    if is_string(token):
        return True
    
    return False

def get_size(token):

    global current_size
    
    if is_boolean(token):
        current_size = 1
        return current_size
    
    if is_number(token):
        current_size = 4
        return current_size
    
    if is_string(token):
        current_size = len(token) - 2
        return current_size
    
    raise SyntaxError, "Unknown size for constant '%s' at line %i." % (token, tokeniser.line)

def is_boolean(token):

    return token == "True" or token == "False"

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

# Variable handling

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

def find_local_variable(token):

    index = 0
    for name, size in local_variables:
        if name == token:
            print "local variable", token
            return index
        index += 1
    
    return -1

def local_variable_offset(index):

    offset = 0
    while index > 0:
        index -= 1
        name, size = local_variables[index]
        offset += size
    
    return offset

def find_global_variable(token):

    for name, size in global_variables:
        if name == token:
            print "global variable", token
            return index
        index += 1
    
    return -1

def global_variable_offset(index):

    offset = 0
    while index > 0:
        index -= 1
        name, size = global_variables[index]
        offset += size
    
    return offset

# Function handling

def find_function(token):

    index = 0
    for name, parameters, variables, code in functions:
        if name == token:
            return index
        index += 1
    
    return -1

def function_address(token):

    address = 0
    for name, parameters, variables, code in functions:
        if name == token:
            return address
        address += len(code)
    
    return -1

# Token handling

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
            
            # Insert a placeholder branch instruction.
            address = generator.generate_if()
            
            if parse_body(stream):
                print "if"
                # Fill in the branch offset.
                generator.generate_target(address)
                return True
        
        raise SyntaxError, "Invalid if structure at line %i." % tokeniser.line
    
    elif token == "while":
    
        loop_address = len(generator.code)
        
        if parse_expression(stream):
            print "expression"
            
            # Insert a placeholder branch instruction.
            address = generator.generate_if()
            
            if parse_body(stream):
                print "while"
                # Generate a branch to the condition code.
                generator.generate_branch(loop_address)
                # Fill in the branch offset.
                generator.generate_target(address)
                return True
        
        raise SyntaxError, "Invalid while structure at line %i." % tokeniser.line
    
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

    top = len(used)
    token = get_token(stream)
    
    # Record the start of the generated code.
    code_start = len(generator.code)
    
    if token == "def":
    
        # Transfer the list of local variables to the global list.
        global_variables[:] = local_variables
        local_variables[:] = []
        
        token = get_token(stream)
        if not is_function_name(token):
            raise SyntaxError, "Invalid function name '%s' at line %i." % (
                token, tokeniser.line)
        
        function_name = token
        parameters = []
        
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
            parameters.append((name, get_size(token)))
        
        # Tentatively add the function to the list of definitions.
        functions.append((function_name, parameters, local_variables[:], None))
        
        if not parse_body(stream):
            raise SyntaxError, "Invalid function definition at line %i." % tokeniser.line
        
        generator.generate_return()
        
        # Append the function details to the list of definitions, taking a copy
        # of the local variables.
        code = generator.code[code_start:]
        generator.discard_code(code_start)
        
        # Replace the placeholder definition with the full one.
        functions.pop()
        functions.append((function_name, parameters, local_variables[:], code))
        
        # Restore the list of local variables.
        local_variables[:] = global_variables
        return True
    
    else:
        put_tokens(top)
        generator.discard_code(code_start)
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
    
        if not parse_operation(stream):
            # Not an operator, so back out of the operation, but allow the
            # expression. The operator function should have pushed tokens back
            # on the stack.
            break
    
    return True

def parse_function_call(stream):

    '<function call> = <name> [<argument>+]'
    
    top = len(used)
    token = get_token(stream)
    
    index = find_function(token)
    if index == -1:
        put_tokens(top)
        return False
    
    # Generate code to record the address of the top of the value stack in a
    # frame base address register, pushing the previous frame base address onto
    # the stack so that it can be recovered later.
    #    <local variables>
    # -> <local variables> <parent frame address>
    #   ^------------------/
    generator.generate_enter_frame()
    
    function_name, parameters, variables, code = functions[index]
    total_size = 0
    
    # Parse the arguments corresponding to the function parameters. The result
    # at run-time will be a series of values stored on the stack.
    #  <local variables> <parent frame address> <arguments>
    # ^------------------/
    for name, size in parameters:
    
        if not parse_expression(stream):
            raise SyntaxError, "Invalid argument to function '%s' at line %i.\n" % (token, tokeniser.line)
        
        if current_size != size:
            raise SyntaxError, "Incompatible types in argument to function '%s' at line %i.\n" % (token, tokeniser.line)
        
        total_size += size
    
    # Use the previously stored information about the local variables to
    # determine how much space should be allocated on the stack.
    #  <local variables> <parent frame address> <arguments> <local variables>
    # ^------------------/
    total_var_size = 0
    for name, size in variables:
        total_var_size += size
    
    print "function call", function_name
    
    ### Handle return values.
    
    # Call the function then pop the parameters and local variables from the
    # stack, and restore the address of the frame for the calling scope.
    #    <local variables> <parent frame address> <arguments> <local variables>
    #   ^------------------/
    # -> <local variables>
    generator.generate_function_call(function_name, total_var_size, total_size)
    
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
    elif parse_variable(stream):
        return True
    elif parse_function_call(stream):
        return True
    else:
        return False

operators = ("==", "!=", "<", ">", "+", "-", "*", "/")

def parse_operation(stream):

    '<operation> = "==" | "!=" | "<" | ">" | "+" | "-" | "*" | "/" <operand>'
    
    global current_size
    
    top = len(used)
    token = get_token(stream)
    
    if token not in operators:
        put_tokens(top)
        return False
    
    if not parse_operand(stream):
        # Not a value, but one was expected, so report an error.
        raise SyntaxError, "Incomplete operation at line %i." % tokeniser.line
    
    if token == "==":
        print "equals", token
        generator.generate_equals(current_size)
        current_size = 1
    
    elif token == "!=":
        print "not equals", token
        generator.generate_not_equals(current_size)
        current_size = 1
    
    elif token == "<":
        print "less than", token
        generator.generate_less_than(current_size)
        current_size = 1
    
    elif token == ">":
        print "greater than", token
        generator.generate_greater_than(current_size)
        current_size = 1
    
    elif token == "+":
        print "add", token
        generator.generate_add(current_size)
    
    elif token == "-":
        print "subtract", token
        generator.generate_subtract(current_size)
    
    elif token == "*":
        print "multiply", token
        generator.generate_multiply(current_size)
    
    elif token == "/":
        print "divide", token
        generator.generate_divide(current_size)
    
    return True

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
    address = len(generator.code)
    
    assignment = False
    
    # The statement may be an assignment.
    var_token = get_token(stream)
    if is_variable(var_token):
    
        token = get_token(stream)
        if token == tokeniser.assignment_token:
            print "assignment"
            assignment = True
        else:
            put_tokens(top)
    else:
        put_tokens(top)
    
    # The (rest of the) statement is an expression.
    
    if not parse_expression(stream):
        put_tokens(top)
        generator.discard_code(address)
        return False
    
    if not parse_separator(stream):
        put_tokens(top)
        generator.discard_code(address)
        return False
    
    if assignment:
    
        index = find_local_variable(var_token)
        if index != -1:
            name, size = local_variables[index]
            offset = local_variable_offset(index)
            generator.generate_assign_local(offset, size)
            return True
        
        index = find_global_variable(var_token)
        if index != -1:
            name, size = global_variables[index]
            offset = global_variable_offset(index)
            generator.generate_assign_global(offset, size)
            return True
        
        print "define", var_token
        ### We need a way to determine if the variable is local or global.
        local_variables.append((var_token, current_size))
        index = find_local_variable(var_token)
        offset = local_variable_offset(index)
        generator.generate_assign_local(offset, current_size)
    
    else:
        # Discard the resulting value on the top of the stack.
        generator.generate_discard_value(current_size)
    
    return True

def parse_value(stream):

    "<value> = <number> | <string>"
    
    top = len(used)
    token = get_token(stream)
    
    if is_number(token):
        print "constant", token
        generator.generate_number(token, get_size(token))
        return True
    
    elif is_string(token):
        print "constant", token
        return True
    
    else:
        put_tokens(top)
        return False

def parse_variable(stream):

    top = len(used)
    token = get_token(stream)
    
    if not is_variable(token):
        put_tokens(top)
        return False
    
    index = find_local_variable(token)
    if index != -1:
        name, size = local_variables[index]
        offset = local_variable_offset(index)
        generator.generate_load_local(offset, size)
        return True
    
    index = find_global_variable(token)
    if index != -1:
        name, size = global_variables[index]
        offset = global_variable_offset(index)
        generator.generate_load_global(offset, size)
        return True
    
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
        sys.exit(1)
    
    print "Functions:"
    pprint.pprint(functions)
    
    print "Main variables:"
    pprint.pprint(local_variables)
    
    print "Main code:"
    pprint.pprint(generator.code)
