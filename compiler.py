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
import generator, opcodes, simulator, tokeniser
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
in_function = False

def debug_print(*args):
    return
    for arg in args:
        print arg,
    print

# System call definitions

system_call_parameters = [("address", opcodes.address_size),
                          ("A", opcodes.register_size),
                          ("X", opcodes.register_size),
                          ("Y", opcodes.register_size)]

# Constant and type handling

types = {"byte": 1, "int8": 1, "int16": 2, "int32": 4, "string": None}

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
        current_size = number_size(token)
        return current_size
    
    if is_string(token):
        current_size = len(token) - 2
        return current_size
    
    raise SyntaxError, "Unknown size for constant '%s' at line %i." % (token, tokeniser.line)

def is_boolean(token):

    return token == "True" or token == "False"

def boolean_value(token):

    if token == "True":
        return 255
    else:
        return 0

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
    
    if token[i:i + 2] == "0x":
        allowed = "0123456789abcdefABCDEF"
        i += 2
    else:
        allowed = "0123456789"
    
    while i < len(token):
        if token[i] not in allowed:
            return False
        i += 1
    
    return True

def number_size(token):

    base = get_number_base(token)
    if base == 16:
        start = token.find("0x")
        digits = len(token) - start - 2
        return (digits / 2) + (digits % 2)
    else:
        value = int(token, base)
    
    if value >= 0:
        if value < (1 << 8):
            return 1
        elif value < (1 << 16):
            return 2
        else:
            return 4
    else:
        if value >= (1 << 7) - (1 << 8):
            return 1
        elif value >= (1 << 15) - (1 << 16):
            return 2
        else:
            return 4

def get_number_base(token):

    if "0x" in token:
        return 16
    else:
        return 10

def is_string(token):

    if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
        return True

def is_type(token):

    return token in types

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
            debug_print("local variable", token)
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

    index = 0
    for name, size in global_variables:
        if name == token:
            debug_print("global variable", token)
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

def total_variable_size(variables):

    total_var_size = 0
    for name, size in variables:
        total_var_size += size
    
    return total_var_size

# Function handling

def find_function(token):

    index = 0
    for name, parameters, variables, code, rsize in functions:
        if name == token:
            return index
        index += 1
    
    return -1

def function_address(token):

    address = 0
    for name, parameters, variables, code, rsize in functions:
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
            debug_print("control")
        elif in_function and parse_return(stream):
            debug_print("return")
        elif parse_statement(stream):
            debug_print("statement")
        elif parse_separator(stream):
            # Handle blank lines.
            debug_print("separator (blank)")
        elif parse_dedent(stream):
            break
        else:
            return False
        
        has_body = True
    
    if not has_body:
        return False
    
    debug_print("body")
    return True

def parse_control(stream):

    top = len(used)
    token = get_token(stream)
    
    if token == "if":
        if parse_expression(stream):
            debug_print("expression")
            
            if current_size != 1:
                raise SyntaxError, "Invalid condition type at line %i." % tokeniser.line
            
            # Insert a placeholder branch instruction.
            address = generator.generate_if()
            
            if parse_body(stream):
                debug_print("if")
                # Fill in the branch offset.
                generator.generate_target(address)
                return True
        
        raise SyntaxError, "Invalid if structure at line %i." % tokeniser.line
    
    elif token == "while":
    
        loop_address = len(generator.code)
        
        if parse_expression(stream):
            debug_print("expression")
            
            if current_size != 1:
                raise SyntaxError, "Invalid condition type at line %i." % tokeniser.line
            
            # Insert a placeholder branch instruction.
            address = generator.generate_while()
            
            if parse_body(stream):
                debug_print("while")
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

    global in_function
    
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
            if token != tokeniser.arguments_begin_token:
                raise SyntaxError, "Expected '(' after parameter name '%s' at line %i." % (
                    name, tokeniser.line)
            
            type_token = get_token(stream)
            if not is_type(type_token):
                raise SyntaxError, "Expected type after parameter name '%s' at line %i." % (
                    name, tokeniser.line)
            
            token = get_token(stream)
            if token != tokeniser.arguments_end_token:
                raise SyntaxError, "Expected ')' after type '%s' at line %i." % (
                    type_token, tokeniser.line)
        
            local_variables.append((name, types[type_token]))
            parameters.append((name, types[type_token]))
        
        # Tentatively add the function to the list of definitions.
        functions.append([function_name, parameters, local_variables[:], None, 0])
        
        # Indicate that we are parsing a function and reset the default return
        # size.
        in_function = True
        
        if not parse_body(stream):
            raise SyntaxError, "Invalid function definition at line %i." % tokeniser.line
        
        in_function = False
        
        # The code to handle the exit from the function follows the function
        # body. Return calls should be branches to here.
        
        generator.fix_returns(code_start)
        
        # Write code to handle exit from the function.
        
        # Note that the stack at this point will contain the following:
        # <local vars> <return value> <parent frame addr> <args> <local vars> <value>
        #                                                ^
        #                                       frame base address
        # We will recover the parent frame and copy the value from the top of the
        # child frame to the top of the parent frame, leaving the following:
        # <local vars> <return value>
        
        total_param_size = total_variable_size(parameters)
        total_var_size = total_variable_size(local_variables) - total_param_size
        return_size = functions[-1][-1]
        generator.generate_function_tidy(total_var_size + total_param_size,
                                         return_size)
        
        generator.generate_return()
        
        # Append the function details to the list of definitions, taking a copy
        # of the local variables.
        code = generator.code[code_start:]
        generator.discard_code(code_start)
        
        # Write code to handle entry into the function. We can only do this
        # after the body has been generated because we don't know the parameter
        # types beforehand.
        
        generator.generate_enter_frame(total_param_size, total_var_size)
        
        # Append the generated code to the function's code.
        code = generator.code[code_start:] + code
        generator.discard_code(code_start)
        
        # Replace the placeholder definition with the full one.
        functions.pop()
        functions.append((function_name, parameters, local_variables[:], code,
                          return_size))
        
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
    
    global current_size
    
    top = len(used)
    token = get_token(stream)
    
    index = find_function(token)
    if index == -1:
        put_tokens(top)
        return False
    
    token = get_token(stream)
    if token != tokeniser.arguments_begin_token:
        raise SyntaxError, "Function arguments must follow '(' at line %i.\n" % tokeniser.line
    
    function_name, parameters, variables, code, rsize = functions[index]
    
    # Generate code to record the address of the current frame in a frame base
    # address register, pushing the previous frame base address onto the stack
    # so that it can be recovered later.
    #    <local vars>
    # -> <local vars> <parent frame addr>
    #   ^-------------/
    
    generator.generate_push_parent_frame()
    
    # Parse the arguments corresponding to the function parameters. The result
    # at run-time will be a series of values stored on the stack.
    #    <local vars> <parent frame addr>
    # -> <local vars> <parent frame addr> <arguments>
    
    total_param_size = total_variable_size(parameters)
    
    for name, size in parameters:
    
        if not parse_expression(stream):
            raise SyntaxError, "Invalid argument to function '%s' at line %i.\n" % (token, tokeniser.line)
        
        if current_size != size:
            raise SyntaxError, "Incompatible types in argument to function '%s' at line %i.\n" % (token, tokeniser.line)
    
    token = get_token(stream)
    if token != tokeniser.arguments_end_token:
        raise SyntaxError, "Function arguments must be terminated with ')' at line %i.\n" % tokeniser.line
    
    # Use the previously stored information about the local variables to
    # determine how much space should be allocated on the stack.
    #    <local vars> <parent frame addr> <args>
    # -> <local vars> <parent frame addr> <args> <local vars>
    
    total_var_size = total_variable_size(variables) - total_param_size
    
    debug_print("function call", function_name)
    
    # Call the function then restore the address of the frame for the calling
    # scope. Pop the local variables and arguments from the stack, copying any
    # return value down in memory to the new stack top.
    #    <local vars> <parent frame addr> <args> <local vars> <return value>
    # -> <local vars> <return value>
    
    generator.generate_function_call(function_name)
    
    # Record the size of the return value to ensure that it is assigned or
    # discarded as necessary.
    current_size = rsize
    
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
    elif parse_system_call(stream):
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
    
    if current_size == 0:
        raise SyntaxError, "Operand 1 has zero size at line %i." % tokeniser.line
    
    size1 = current_size
    
    if not parse_operand(stream):
        # Not a value, but one was expected, so report an error.
        raise SyntaxError, "Incomplete operation at line %i." % tokeniser.line
    
    if current_size == 0:
        raise SyntaxError, "Operand 2 has zero size at line %i." % tokeniser.line
    
    if current_size != size1:
        raise SyntaxError, "Sizes of operands do not match at line %i." % tokeniser.line
    
    if token == "==":
        debug_print("equals", token)
        generator.generate_equals(current_size)
        current_size = 1
    
    elif token == "!=":
        debug_print("not equals", token)
        generator.generate_not_equals(current_size)
        current_size = 1
    
    elif token == "<":
        debug_print("less than", token)
        generator.generate_less_than(current_size)
        current_size = 1
    
    elif token == ">":
        debug_print("greater than", token)
        generator.generate_greater_than(current_size)
        current_size = 1
    
    elif token == "+":
        debug_print("add", token)
        generator.generate_add(current_size)
    
    elif token == "-":
        debug_print("subtract", token)
        generator.generate_subtract(current_size)
    
    elif token == "*":
        debug_print("multiply", token)
        generator.generate_multiply(current_size)
    
    elif token == "/":
        debug_print("divide", token)
        generator.generate_divide(current_size)
    
    return True

def parse_program(stream):

    while tokeniser.at_eof == False:
    
        if parse_control(stream):
            discard_tokens()
            debug_print("control")
        elif parse_definition(stream):
            discard_tokens()
            debug_print("definition")
        elif parse_statement(stream):
            discard_tokens()
            debug_print("statement")
        elif parse_separator(stream):
            # Handle blank lines.
            discard_tokens()
            debug_print("separator (blank)")
        else:
            raise SyntaxError, "Unexpected input at line %i." % tokeniser.line
    
    generator.generate_end()
    
    # Insert code to reserve space for variables.
    main_code = generator.code[:]
    generator.discard_code(0)
    generator.generate_allocate_stack_space(total_variable_size(local_variables))
    generator.code += main_code

def parse_return(stream):

    '<return> = "return" [<expression>]'
    
    ### Handle value-less returns and ensure that all returns in a function
    ### body consistently use the same type.
    
    top = len(used)
    token = get_token(stream)
    
    if token != "return":
        put_tokens(top)
        return False
    
    if not in_function:
        raise SyntaxError, "Cannot use return from outside function at line %i." % tokeniser.line
    
    if parse_separator(stream):
        # No return value supplied. Set the return value size to zero.
        functions[-1][-1] = 0
    
    elif parse_expression(stream):
        functions[-1][-1] = current_size
    
    else:
        raise SyntaxError, "Invalid return from function at line %i." % tokeniser.line
    
    generator.generate_exit_function()
    return True

def parse_separator(stream):

    "<separator> = <newline> | <eof>"
    
    if parse_newline(stream):
        debug_print("newline")
        return True
    elif parse_eof(stream):
        debug_print("eof")
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
            debug_print("assignment")
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
        
        if current_size == 0:
            raise SyntaxError, "No value to assign at line %i." % tokeniser.line
        
        debug_print("define", var_token)
        ### We need a way to determine if the variable is local or global.
        local_variables.append((var_token, current_size))
        index = find_local_variable(var_token)
        offset = local_variable_offset(index)
        generator.generate_assign_local(offset, current_size)
    
    else:
        # Discard the resulting value on the top of the stack.
        generator.generate_discard_value(current_size)
    
    return True

def parse_system_call(stream):

    '<system call> = _call [<argument>+]'
    
    global current_size
    
    top = len(used)
    token = get_token(stream)
    
    if token != tokeniser.system_call_token:
        put_tokens(top)
        return False
    
    token = get_token(stream)
    if token != tokeniser.arguments_begin_token:
        raise SyntaxError, "Function arguments must follow '(' at line %i.\n" % tokeniser.line
    
    # Parse the arguments corresponding to the system call parameters.
    # These take the form <address> <A> <X> <Y>.
    
    total_args_size = 0
    
    for name, size in system_call_parameters:
    
        top = len(used)
        token = get_token(stream)
        
        if token == tokeniser.arguments_end_token:
            # If we encounter a closing parenthesis, check that at least the
            # address has been given.
            if name != "address":
                # Recover the token and break.
                put_tokens(top)
                break
            else:
                raise SyntaxError, "System call lacks an address at line %i.\n" % tokeniser.line
        else:
            # Recover the token.
            put_tokens(top)
        
        if not parse_expression(stream):
            raise SyntaxError, "Invalid system call argument for parameter '%s' at line %i.\n" % (name, tokeniser.line)
        
        if current_size != size:
            raise SyntaxError, "Incompatible types in system call argument for parameter '%s' at line %i.\n" % (name, tokeniser.line)
        
        total_args_size += size
    
    token = get_token(stream)
    if token != tokeniser.arguments_end_token:
        raise SyntaxError, "System call arguments must be terminated with ')' at line %i.\n" % tokeniser.line
    
    debug_print("system call")
    
    # Call the system routine with the total size of the arguments supplied.
    # This enables the generated code to retrieve the arguments from the stack.
    
    generator.generate_system_call(total_args_size)
    
    # Set the size of the return value to ensure that it is assigned or
    # discarded as necessary.
    current_size = opcodes.system_call_return_size
    
    return True

def parse_value(stream):

    "<value> = <number> | <string>"
    
    global current_size
    
    top = len(used)
    token = get_token(stream)
    
    if is_number(token):
        debug_print("constant", token)
        size = get_size(token)
        base = get_number_base(token)
        generator.generate_number(token, size, base)
    
    elif is_boolean(token):
        debug_print("constant", token)
        size = get_size(token)
        generator.generate_boolean(boolean_value(token), size)
    
    elif is_string(token):
        debug_print("constant", token)
        size = get_size(token)
        generator.generate_string(token, size)
    
    else:
        put_tokens(top)
        return False
    
    current_size = size
    return True

def parse_variable(stream):

    global current_size
    
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
        current_size = size
        return True
    
    index = find_global_variable(token)
    if index != -1:
        name, size = global_variables[index]
        offset = global_variable_offset(index)
        generator.generate_load_global(offset, size)
        current_size = size
        return True
    
    put_tokens(top)
    return False

def save_opcodes_oph(file_name):

    f = open(file_name, "w")
    i = 0
    while i < len(generator.code):
        opcodes = []
        for opcode in generator.code[i:i + 24]:
            if opcode < 0:
                opcode = 256 + opcode
            opcodes.append(opcode)
        f.write(".byte " + ", ".join(map(str, opcodes)) + "\n")
        i += 24
    f.close()

def save_opcodes(file_name):

    f = open(file_name, "wb")
    f.write("".join(map(chr, generator.code)))
    f.close()


if __name__ == "__main__":

    if not 2 <= len(sys.argv) <= 3:
        sys.stderr.write("Usage: %s [-r | -s] <file>\n" % sys.argv[0])
        sys.exit(1)
    
    stream = open(sys.argv[-1])
    run = sys.argv[1] == "-r"
    save = sys.argv[1] == "-s"
    
    load_address = 0x0e00 + opcodes.end + 2
    
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
    
    print "Linking"
    try:
        generator.link(functions, load_address)
    except KeyError as exception:
        sys.stderr.write(str(exception) + "\n")
        sys.exit(1)
    
    print "Main code:"
    pprint.pprint(generator.code)
    
    if run:
        print "Loading"
        simulator.load(generator.code, load_address)
        print "Running"
        simulator.run()
    
    if save:
        save_opcodes_oph("6502/program.oph")
