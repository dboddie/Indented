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
from arguments import find_option

version = "0.3"

# Token handling - lists of incoming tokens and those tentatively processed

tokens = []
used = []

# Variable and type definitions

global_variables = []
local_variables = []
current_size = 0
current_element_size = 0
current_array = False

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

types = {"byte": 1, "int8": 1, "int16": 2, "int32": 4,
         "int8_array": 2, "int16_array": 2, "int32_array": 2, "string": 2}
array_types = {"int8_array": 1, "int16_array": 2, "int32_array": 4, "string": 1}

def is_constant(token):

    if is_boolean(token):
        return True
    
    if is_number(token):
        return True
    
    if is_string(token):
        return True
    
    return False

def get_size(token):

    global current_size, current_element_size, current_array
    
    if is_boolean(token):
        current_size = current_element_size = 1
        return current_size
    
    if is_number(token):
        current_size = current_element_size = number_size(token)
        return current_size
    
    if is_string(token):
        current_size = len(decode_string(token))
        current_element_size = array_types["string"]
        current_array = True
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
        return decode_string(token)
    else:
        return False

def is_type(token):

    return token in types

def decode_string(token):

    # Discard the leading and trailing quotation marks and convert any encoded
    # characters to bytes.
    new = ""
    i = 1
    
    while i < len(token) - 1:
        ch = token[i]
        if ch == "\\":
            j = i + 1
            if j == len(token) - 1:
                raise SyntaxError, "Incomplete escape at line %i." % tokeniser.line
            ch = token[j]
            if ch == "\\":
                new += ch
            elif ch == '"':
                new += ch
            elif ch == "n":
                new += "\n"
            elif ch == "r":
                new += "\r"
            elif ch == "n":
                new += "\n"
            elif ch == "t":
                new += "\t"
            elif ch == "x":
                k = 2
                total = 0
                while k > 0 and j < len(token) - 1:
                    j += 1
                    k -= 1
                    ch = token[j]
                    if ch in string.hexdigits:
                        total += (string.hexdigits.index(ch.lower()) << (k * 4))
                    else:
                        raise SyntaxError, "Invalid escape at line %i." % tokeniser.line
                if k != 0:
                    raise SyntaxError, "Invalid escape at line %i." % tokeniser.line
                new += chr(total)
            else:
                raise SyntaxError, "Invalid escape at line %i." % tokeniser.line
            i = j + 1
        else:
            new += ch
            i += 1
    
    return new

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
    for name, size, element_size, array in local_variables:
        if name == token:
            debug_print("local variable", token)
            return index
        index += 1
    
    return -1

def local_variable_offset(index):

    offset = 0
    while index > 0:
        index -= 1
        name, size, element_size, array = local_variables[index]
        offset += size
    
    return offset

def find_global_variable(token):

    index = 0
    for name, size, element_size, array in global_variables:
        if name == token:
            debug_print("global variable", token)
            return index
        index += 1
    
    return -1

def global_variable_offset(index):

    offset = 0
    while index > 0:
        index -= 1
        name, size, element_size, array = global_variables[index]
        offset += size
    
    return offset

def total_variable_size(variables):

    total_var_size = 0
    for name, size, element_size, array in variables:
        total_var_size += size
    
    return total_var_size

# Function handling

def find_function(token):

    index = 0
    for name, parameters, variables, address, rsize, return_array in functions:
        if name == token:
            return index
        index += 1
    
    return -1

def function_address(token):

    address = 0
    for name, parameters, variables, address, rsize, return_array in functions:
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
        if token.startswith(tokeniser.comment_token):
            while True:
                token = read_token(stream)
                if token == tokeniser.newline_token:
                    break
    
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

def parse_array_index(stream):

    top = len(used)
    token = get_token(stream)
    
    if token != tokeniser.index_begin_token:
        put_tokens(top)
        return False
    
    if not parse_expression(stream):
        raise SyntaxError, "Invalid index value at line %i." % tokeniser.line
    
    token = get_token(stream)
    
    if token != tokeniser.index_end_token:
        raise SyntaxError, "Expected ']' at line %i." % tokeniser.line
    
    debug_print("array index")
    return True

def parse_body(stream):

    '<body> = <indent> (<control> | <return> | <statement>)+ <dedent>'
    
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

def parse_builtin_call(stream):

    '<built-in call> = "_addr" "(" [<argument>+] ")"'
    
    global current_size, current_element_size, current_array
    
    top = len(used)
    token = get_token(stream)
    
    if token != "_addr":
        put_tokens(top)
        return False
    
    token = get_token(stream)
    if token != tokeniser.arguments_begin_token:
        raise SyntaxError, "Arguments must follow '(' at line %i.\n" % tokeniser.line
    
    var_token = get_token(stream)
    if not is_variable(var_token):
        raise SyntaxError, "Argument must be a variable at line %i.\n" % tokeniser.line
    
    index = find_local_variable(var_token)
    if index != -1:
        name, size, element_size, array = local_variables[index]
        offset = local_variable_offset(index)
    
    token = get_token(stream)
    if token != tokeniser.arguments_end_token:
        raise SyntaxError, "Arguments must be terminated with ')' at line %i.\n" % tokeniser.line
    
    debug_print("addr call")
    
    generator.generate_get_variable_address(offset)
    
    # Set the size of the return value to ensure that it is assigned or
    # discarded as necessary.
    current_size = current_element_size = opcodes.address_size
    current_array = False
    
    return True

def parse_control(stream):

    '<control> = ("if" <expression> <body>) | ("while" <expression> <body>)'
    
    top = len(used)
    token = get_token(stream)
    
    if token == "if":
        if parse_expression(stream):
            debug_print("expression")
            
            if current_size != 1:
                raise SyntaxError, "Invalid condition type at line %i." % tokeniser.line
            
            # Insert a placeholder branch instruction.
            if_address = generator.generate_if()
            
            if not parse_body(stream):
                raise SyntaxError, "Invalid if body at line %i." % tokeniser.line
            
            debug_print("if")
            
            top = len(used)
            token = get_token(stream)
            if token == "else":
            
                # Add a placeholder branch to the if code.
                if_exit_address = generator.generate_else()
                
                # Fill in the branch offset for the if condition.
                generator.generate_target(if_address)
                
                if not parse_body(stream):
                    raise SyntaxError, "Invalid else body at line %i." % tokeniser.line
                
                # Fill in the branch offset for the if body.
                generator.generate_target(if_exit_address)
            
            else:
                # Put the token back in the queue.
                put_tokens(top)
                
                # Fill in the branch offset for the if condition.
                generator.generate_target(if_address)
            
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

    '<definition> = "def" <name> (<var name> "(" <var type> ")")+ <body>'
    
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
            
            local_variables.append((name, types[type_token],
                                    array_types.get(type_token, types[type_token]),
                                    type_token in array_types))
            parameters.append((name, types[type_token],
                               array_types.get(type_token, types[type_token]),
                               type_token in array_types))
        
        # Write code to handle entry into the function, passing a placeholder
        # value for the space required for local variables.
        total_param_size = total_variable_size(parameters)
        enter_address = len(generator.code)
        generator.generate_enter_frame(total_param_size, 0)
        
        # Tentatively add the function to the list of definitions with the
        # format:
        # <name> <parameters> <local variables> <address> <return size> <return array>
        functions.append([function_name, parameters, local_variables[:],
                          generator.base_address + enter_address, 0, False])
        
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
        
        total_var_size = total_variable_size(local_variables) - total_param_size
        
        # The return details are filled in by the parse_return function.
        return_size, return_array = functions[-1][-2:]
        
        generator.generate_function_tidy(total_var_size + total_param_size,
                                         return_size)
        
        generator.generate_return()
        
        # Fill in the size of the local variables. We can only do this after
        # the body has been generated because we don't know the sizes of the
        # types beforehand.
        generator.code[enter_address + 3] = total_var_size
        
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

    '<expression> = ["("] <operand> [<operator> <operand>]+ [")"]'
    
    top = len(used)
    token = get_token(stream)
    
    if token == "(":
        if not parse_expression(stream):
            raise SyntaxError, "Invalid expression at line %i." % tokeniser.line
        
        token = get_token(stream)
        if token != ")":
            raise SyntaxError, "Expected closing ')' at line %i." % tokeniser.line
        
    else:
        # Just look for an operand.
        put_tokens(top)
        
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

    '<function call> = <name> "(" [<argument>+] ")"'
    
    global current_size, current_element_size, current_array
    
    top = len(used)
    token = get_token(stream)
    
    index = find_function(token)
    if index == -1:
        put_tokens(top)
        return False
    
    token = get_token(stream)
    if token != tokeniser.arguments_begin_token:
        raise SyntaxError, "Function arguments must follow '(' at line %i.\n" % tokeniser.line
    
    function_name, parameters, variables, address, rsize, return_array = functions[index]
    
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
    
    for name, size, element_size, array in parameters:
    
        if not parse_expression(stream):
            raise SyntaxError, "Invalid argument to function '%s' at line %i.\n" % (function_name, tokeniser.line)
        
        if current_size != size:
            raise SyntaxError, "Incompatible types in argument to function '%s' at line %i.\n" % (function_name, tokeniser.line)
    
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
    
    generator.generate_function_call(address)
    
    # Record the size of the return value to ensure that it is assigned or
    # discarded as necessary.
    current_size = current_element_size = rsize
    current_array = return_array
    
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

unary_operators = ("not", "-")

def parse_operand(stream):

    '<operand> = ["not" | "-"] <operand value>'
    
    top = len(used)
    token = get_token(stream)
    
    # Find an optional unary operator.
    if token in unary_operators:
        require_value = True
    else:
        put_tokens(top)
        require_value = False
    
    if parse_operand_value(stream):
    
        if token == tokeniser.logical_not_token:
            if current_size != 1:
                raise SyntaxError, "Invalid size for logical not operation at line %i." % tokeniser.line
            generator.generate_logical_not()
            return True
        
        elif token == tokeniser.minus_token:
            generator.generate_minus(current_size)
            return True
        
        else:
            return True
    
    elif require_value:
        raise SyntaxError, "An operand was expected after a unary operator at line %i." % tokeniser.line
    else:
        put_tokens(top)
        return False

def parse_operand_value(stream):

    '<operand value> = <value> | <variable> | <function call> | <system call>'
    
    if parse_value(stream):
        return True
    elif parse_variable(stream):
        return True
    elif parse_function_call(stream):
        return True
    elif parse_system_call(stream):
        return True
    elif parse_builtin_call(stream):
        return True
    else:
        return False

operators = ("==", "!=", "<", ">", "+", "-", "*", "/", "and", "or", "&", "<<", ">>")
asymmetric_operators = ("<<", ">>", "&")

def parse_operation(stream):

    '<operation> = "==" | "!=" | "<" | ">" | "+" | "-" | "*" | "/" | "and" | "or" | "&" | "<<" | ">>" <operand>'
    
    global current_size, current_element_size, current_array
    
    top = len(used)
    token = get_token(stream)
    
    if token not in operators:
        put_tokens(top)
        return False
    
    if current_size == 0:
        raise SyntaxError, "Operand 1 has zero size at line %i." % tokeniser.line
    
    size1 = current_size
    
    if not parse_expression(stream):
        # Not an expression, but one was expected, so report an error.
        raise SyntaxError, "Incomplete operation at line %i." % tokeniser.line
    
    if current_size == 0:
        raise SyntaxError, "Operand 2 has zero size at line %i." % tokeniser.line
    
    if token not in asymmetric_operators and current_size != size1:
        raise SyntaxError, "Sizes of operands do not match at line %i." % tokeniser.line
    
    if token == "==":
        debug_print("equals", token)
        generator.generate_equals(current_size)
        current_size = current_element_size = 1
        current_array = False
    
    elif token == "!=":
        debug_print("not equals", token)
        generator.generate_not_equals(current_size)
        current_size = current_element_size = 1
        current_array = False
    
    elif token == "<":
        debug_print("less than", token)
        generator.generate_less_than(current_size)
        current_size = current_element_size = 1
        current_array = False
    
    elif token == ">":
        debug_print("greater than", token)
        generator.generate_greater_than(current_size)
        current_size = current_element_size = 1
        current_array = False
    
    elif token == "+":
        debug_print("add", token)
        generator.generate_add(current_size)
        current_array = False
    
    elif token == "-":
        debug_print("subtract", token)
        generator.generate_subtract(current_size)
        current_array = False
    
    elif token == "*":
        debug_print("multiply", token)
        generator.generate_multiply(current_size)
        current_array = False
    
    elif token == "/":
        debug_print("divide", token)
        generator.generate_divide(current_size)
        current_array = False
    
    elif token == "and":
    
        if current_size != 1:
            raise SyntaxError, "Operands have an invalid size for logical and operation at line %i." % tokeniser.line
        
        debug_print("and", token)
        generator.generate_logical_and()
        current_size = current_element_size = 1
        current_array = False
    
    elif token == "or":
    
        if current_size != 1:
            raise SyntaxError, "Operands have an invalid size for logical or operation at line %i." % tokeniser.line
        
        debug_print("or", token)
        generator.generate_logical_or()
        current_size = current_element_size = 1
        current_array = False
    
    # The bitwise AND operation truncates the result to the size of the second
    # operand.
    
    elif token == "&":
    
        debug_print("&", token)
        generator.generate_bitwise_and(size1, current_size)
        current_array = False
    
    # The shift operators are also asymmetric, with the second operand
    # typically being only a single byte, but the result is the same size as
    # the first operand.
    
    elif token == "<<":
    
        if current_size != opcodes.shift_size:
            raise SyntaxError, "Invalid size for shift at line %i." % tokeniser.line
        
        debug_print("<<", token)
        current_size = current_element_size = size1
        current_array = False
        generator.generate_left_shift(current_size)
    
    elif token == ">>":
    
        if current_size != opcodes.shift_size:
            raise SyntaxError, "Invalid size for shift at line %i." % tokeniser.line
        
        debug_print(">>", token)
        current_size = current_element_size = size1
        current_array = False
        generator.generate_right_shift(current_size)
    
    return True

def parse_program(stream, base_address):

    '<program> = [<definition> | <control> | <statement>]+'
    
    generator.base_address = base_address
    
    top = len(used)
    
    while tokeniser.at_eof == False:
    
        if parse_definition(stream):
            discard_tokens()
            debug_print("definition")
        else:
            put_tokens(top)
            break
    
    # Insert code to reserve space for variables.
    start_address = len(generator.code)
    generator.generate_allocate_stack_space(0)
    
    while tokeniser.at_eof == False:
    
        if parse_control(stream):
            discard_tokens()
            debug_print("control")
        elif parse_definition(stream):
            raise SyntaxError, "Cannot mix function definitions and code at line %i." % tokeniser.line
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
    
    # Fill in the size of the local variable space.
    generator.code[start_address + 1] = total_variable_size(local_variables)
    
    return generator.base_address + start_address

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
        # No return value supplied. Set the return value size to zero and the
        # return array value to False.
        functions[-1][-2:] = [0, False]
    
    elif parse_expression(stream):
        functions[-1][-2:] = [current_size, current_array]
    
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

    '<statement> = [<name> "="] <expression> <separator>'
    
    global current_size, current_element_size, current_array
    
    top = len(used)
    address = len(generator.code)
    
    assignment = None
    
    # The statement may be an assignment.
    var_token = get_token(stream)
    
    if is_variable(var_token):
    
        # If the variable is already defined and has an array type then check
        # for an index.
        index = find_local_variable(var_token)
        
        if index != -1:
            # Local variable
            name, size, element_size, array = local_variables[index]
            offset = local_variable_offset(index)
            
            if array and parse_array_index(stream):
                # Record the size of the array index.
                index_size = current_size
                assignment = "local array"
            else:
                assignment = "local"
        else:
            # Global variable
            index = find_global_variable(var_token)
            if index != -1:
                name, size, element_size, array = global_variables[index]
                offset = global_variable_offset(index)
                
                if array and parse_array_index(stream):
                    # Record the size of the array index.
                    index_size = current_size
                    assignment = "global array"
                else:
                    assignment = "global"
            else:
                # Currently undefined variable
                assignment = "undefined"
        
        # Check for the assignment operator.
        token = get_token(stream)
        if token == tokeniser.assignment_token:
            debug_print("assignment")
        else:
            put_tokens(top)
            assignment = None
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
    
    if assignment == "local array":
        if element_size != current_size:
            raise SyntaxError, "Type mismatch in indexed assignment at line %i." % tokeniser.line
        generator.generate_store_array_value(offset, element_size, index_size)
        current_size = current_element_size = element_size
        current_array = True
    
    elif assignment == "local":
        if size != current_size:
            raise SyntaxError, "Type mismatch in assignment at line %i." % tokeniser.line
        generator.generate_assign_local(offset, size)
        current_size = current_element_size = size
        current_array = False
    
    elif assignment == "global array":
        if element_size != current_size:
            raise SyntaxError, "Type mismatch in indexed assignment at line %i." % tokeniser.line
        generator.generate_store_array_value(offset, element_size, index_size)
        current_size = current_element_size = element_size
        current_array = True
    
    elif assignment == "global":
        if size != current_size:
            raise SyntaxError, "Type mismatch in assignment at line %i." % tokeniser.line
        generator.generate_assign_global(offset, size)
        current_size = current_element_size = size
        current_array = False
    
    elif assignment == "undefined":
        if current_size == 0:
            raise SyntaxError, "No value to assign at line %i." % tokeniser.line
        
        debug_print("define", var_token)
        ### We need a way to determine if the variable is local or global.
        local_variables.append((var_token, current_size, current_element_size,
                                current_array))
        index = find_local_variable(var_token)
        offset = local_variable_offset(index)
        generator.generate_assign_local(offset, current_size)
    
    else:
        # Discard the resulting value on the top of the stack.
        generator.generate_discard_value(current_size)
    
    return True

def parse_system_call(stream):

    '<system call> = _call "(" <address> [<A> [<X> [<Y>]]] ")"'
    
    global current_size, current_element_size, current_array
    
    top = len(used)
    token = get_token(stream)
    
    if token != tokeniser.system_call_token:
        put_tokens(top)
        return False
    
    token = get_token(stream)
    if token != tokeniser.arguments_begin_token:
        raise SyntaxError, "Arguments must follow '(' at line %i.\n" % tokeniser.line
    
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
        raise SyntaxError, "Arguments must be terminated with ')' at line %i.\n" % tokeniser.line
    
    debug_print("system call")
    
    # Call the system routine with the total size of the arguments supplied.
    # This enables the generated code to retrieve the arguments from the stack.
    
    generator.generate_system_call(total_args_size)
    
    # Set the size of the return value to ensure that it is assigned or
    # discarded as necessary.
    current_size = current_element_size = opcodes.system_call_return_size
    current_array = False
    
    return True

def parse_value(stream):

    "<value> = <number> | <string>"
    
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
        decoded_string = decode_string(token)
        generator.generate_string(decoded_string, size)
    
    else:
        put_tokens(top)
        return False
    
    return True

def parse_variable(stream):

    global current_size, current_element_size, current_array
    
    top = len(used)
    token = get_token(stream)
    
    if not is_variable(token):
        put_tokens(top)
        return False
    
    index = find_local_variable(token)
    if index != -1:
        name, size, element_size, array = local_variables[index]
        offset = local_variable_offset(index)
        
        if array and parse_array_index(stream):
            index_size = current_size
            generator.generate_load_array_value(offset, element_size, index_size)
            current_size = current_element_size = element_size
            # The element of an array is not an array.
            current_array = False
        else:
            generator.generate_load_local(offset, size)
            current_size = current_element_size = size
            current_array = array
        
        return True
    
    index = find_global_variable(token)
    if index != -1:
        name, size, element_size, array = global_variables[index]
        offset = global_variable_offset(index)
        
        if array and parse_array_index(stream):
            index_size = current_size
            generator.generate_load_array_value(offset, element_size, index_size)
            current_size = current_element_size = element_size
            # The element of an array is not an array.
            current_array = False
        else:
            generator.generate_load_global(offset, size)
            current_size = current_element_size = size
            current_array = array
        
        current_array = False
        return True
    
    put_tokens(top)
    return False

def save_opcodes_oph(file_name_or_obj, start_address):

    if isinstance(file_name_or_obj, file):
        f = file_name_or_obj
    else:
        f = open(file_name_or_obj, "w")
    
    i = 0
    while i < len(generator.code):
        opcodes = []
        for opcode in generator.code[i:i + 24]:
            opcodes.append(opcode & 0xff)
        f.write(".byte " + ", ".join(map(str, opcodes)) + "\n")
        i += 24
    
    f.write(".alias program_start_low  $%02x\n" % (start_address & 0xff))
    f.write(".alias program_start_high $%02x\n" % (start_address >> 8))
    f.write("\n")
    
    if not isinstance(file_name_or_obj, file):
        f.close()

def save_opcodes(file_name):

    f = open(file_name, "wb")
    f.write("".join(map(chr, map(lambda x: x & 0xff, generator.code))))
    f.close()

def get_opcodes_used():

    d = {}
    
    for v in generator.code:
        if v > 255:
            d[v] = d.get(v, 0) + 1
    
    return d


if __name__ == "__main__":

    this_program, args = sys.argv[0], sys.argv[1:]
    run = find_option(args, "-r", 0)
    target, architecture = find_option(args, "-t", 1)
    output, file_name = find_option(args, "-o", 1)
    
    if len(args) != 1:
        sys.stderr.write(
            "Usage: %s [-r] [-t <target>] <file> [-o <output file>]\n\n"
            "-r    Run the generated code in a simulator.\n"
            "-t    Generate code for the specified <target> architecture.\n"
            "-o    Write the generated code to the specified <output file>.\n\n" % this_program)
        sys.exit(1)
    
    stream = open(args[0])
    
    load_address = 0x0e00
    
    try:
        start_address = parse_program(stream, load_address)
    except SyntaxError as exception:
        sys.stderr.write(str(exception) + "\n")
        sys.exit(1)
    
    print "Functions:"
    pprint.pprint(functions)
    
    print "Main variables:"
    pprint.pprint(local_variables)
    
    print "Main code:"
    addr = load_address
    for v in generator.code:
        print "%04x: %03i (%02x)" % (addr, v, v)
        addr += 1
    
    print "Opcode usage:"
    d = get_opcodes_used()
    freq = map(lambda (k, v): (v, k), d.items())
    freq.sort()
    for v, k in freq:
        print simulator.lookup[k], v
    
    if run:
        print "Loading"
        simulator.load(generator.code, load_address)
        print "Running"
        print simulator.run(start_address)
    
    if output:
        save_opcodes_oph(file_name, start_address)
