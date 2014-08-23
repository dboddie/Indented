#!/usr/bin/env python

"""
Experimental parser/compiler for an indented Forth-like language.

Remaining issues:

 * Need to separate variable stack frames for function parameters and local
   variables.

 * Need to handle assignments to variables and comparisons between both
   constants and variables.

"""

import pprint, sys

# Compiler/interpreter internals

line = 1
newline = False
indent = 0
indent_stack = [0]
pending_token = ""
in_comment = False
in_string = False
at_eof = False
pending_operands = 0

indent_token = "\ti"
dedent_token = "\td"
newline_token = "\n"
assignment_token = "="

# Type sizes

number_size = 4

# Built-in compilation functions

def compile_def(stream, expected_parameters):

    global code_area, var_stack
    
    # Read the definition's name.
    name = read_token(stream)
    
    i = find_def(name)
    if i != -1:
        raise SyntaxError, "Definition already exists on line %i: '%s'" % (line, token)
    
    # Append a new frame to the variable stack.
    var_stack.append([])
    
    # Read the names of the parameters, each of which needs to supply a
    # default value.
    while newline == False:
    
        name_token = read_token(stream)
        
        token = read_token(stream)
        if token != assignment_token:
            raise SyntaxError, "Expected assignment for parameter in definition on line %i: '%s'" % (line, token)
        
        value_token = read_token(stream)
        if not is_constant(value_token):
            raise SyntaxError, "Default value for '%s' parameter is not a constant on line %i: '%s'" % (line, value_token)
        
        # Determine the size required for the value based on the constant type.
        if is_number(value_token):
            value_size = number_size
        else:
            raise SyntaxError, "Unhandled type for '%s' parameter on line %i: '%s'" % (name_token, line, value_token)
        
        var_stack[-1].append((name_token, value_size))
    
    # Skip newlines.
    while True:
        token = read_token(stream)
        if token != newline_token:
            break
    
    compile_body(token, stream)
    
    defs.append((name, code_area, var_stack[-1]))
    
    # Pop the stack frame from the local variables stack and clear the
    # temporary code area.
    var_stack.pop()
    code_area = []

def compile_body(token, stream):

    # Expect an indentation token.
    if token != indent_token:
        raise SyntaxError, "Expected indentation before body of structure on line %i." % line
    
    # Compile the body of the structure.
    while True:
        token = read_token(stream)
        if token == dedent_token:
            break
        compile_token(token)

def compile_call(stream, expected_parameters):

    for parameter in expected_parameters:
        token = read_token(stream)
        compile_token(token)

def compile_if(stream, expected_parameters):

    # Compile the condition.
    compile_line_tokens(stream)
    
    # Save the code area offset for later.
    branch_instruction_address = len(code_area)
    
    # Insert a branch instruction placeholder.
    code_area.append((branch_if_false, None))
    
    token = read_token(stream)
    compile_body(token, stream)
    
    # Replace the placeholder instruction stored earlier with a branch
    # instruction.
    offset = len(code_area) - branch_instruction_address
    code_area[branch_instruction_address] = (branch_if_false, offset)

def compile_equals(stream, expected_parameters):

    global pending_operands
    
    if pending_operands != 1:
        raise SyntaxError, "Unexpected number of arguments to operator on line %i." % line
    
    pending_operands -= 1
    
    # Compile the second argument to the comparison.
    token = read_token(stream)
    if not compile_token(token):
        raise SyntaxError, "Missing second argument to operator on line %i." % line
    
    code_area.append((compare_equals, None))

def compile_assign(stream, expected_parameters):

    print expected_parameters
    token = read_token(stream)
    return compile_token(token)

def compile_unknown(token, stream):

    global var_stack
    
    # Read the next token and check whether it is an assignment operator.
    next_token = read_token(stream)
    
    if next_token != assignment_token:
        raise SyntaxError, "Undefined object on line %i: '%s'" % (line, token)
    
    # Compile code to define an object with the name given by the token.
    if not compile_token(assignment_token):
        raise SyntaxError, "Invalid assignment to '%s' on line %i" % (token, line)
    
    # Ensure that there is enough space reserved for this variable.
    var_stack[-1].append((name_token, data_size()))
    
    return True

def compile_load_var(index):

    global code_area, pending_operands
    
    if pending_operands:
        raise SyntaxError, "Expected operator or end of statement on line %i." % line
    
    pending_operands += 1
    
    # Load the value of the variable referred to by the index into the variable
    # stack.
    name, data_size = var_stack[-1][index]
    
    i = 0
    offset = 0
    while i < index:
        offset += var_stack[-1][1]
    
    code_area.append((load_var_address, (offset, data_size)))

# Constant handling

def is_constant(token):

    if is_number(token):
        return True
    
    if is_string(token):
        return True
    
    return False

def compile_constant(token):

    if is_number(token):
        compile_number(token)
        return True
    
    if is_string(token):
        compile_string(token)
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

def compile_number(token):

    global pending_operands
    
    if pending_operands:
        raise SyntaxError, "Expected operator or end of statement on line %i." % line
    
    code_area.append((load_number, int(token)))
    pending_operands += 1

def is_string(token):

    if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
        return True

def compile_string(token):

    global pending_operands
    
    if pending_operands:
        raise SyntaxError, "Expected operator or end of statement on line %i." % line
    
    code_area.append((load_string, token[1:-1]))
    pending_operands += 1

def data_size():

    if code_area[-1][0] == load_number:
        return number_size
    elif code_area[-1][0] == load_string:
        return len(code_area[-1][1])
    else:
        raise SyntaxError, "Unknown data size."

# Built-in run-time functions

def load_number(value):

    global code_offset
    value_stack.append(value)
    code_offset += 1

def compare_equals(value):

    global code_offset
    code_offset += 1
    value_stack.append(value_stack.pop() == value_stack.pop())

def load_string(value):

    global code_offset
    value_stack.append(value)
    code_offset += 1

def branch_if_false(value):

    global code_offset
    if not value_stack.pop():
        code_offset += value
    else:
        code_offset += 1

def load_var_address(value):

    offset, size = value
    for i in range(size):
        value_stack.append(var_stack[i])

# Environment workspace

# Global definitions
defs = [("if", compile_if, []), ("==", compile_equals, []),
        ("=", compile_assign, []), ("def", compile_def, [])]
# Code compilation workspace and offset into code
code_area = []
code_offset = 0
# Run-time value handling
value_stack = []
# Local variable stack, for run-time variable storage, but also compile-time
# indexing of variables
var_stack = []

# Parsing/compilation functions

def find_def(token):

    i = len(defs) - 1
    while i >= 0:
    
        name, compile_fn, expected_parameters = defs[i]
        if token == name:
            return i
        
        i -= 1
    
    return -1

def find_var(token):

    i = len(var_stack[-1]) - 1
    while i >= 0:
    
        name, size = var_stack[-1][i]
        if name == token:
            return i
        
        i -= 1
    
    return -1

def read_token(stream):

    global at_eof, indent, indent_stack, line, in_comment, in_string, newline
    global pending_token
    
    # If at the end of the file then emit dedent tokens until the indentation
    # level is zero, then emit newline tokens.
    if at_eof:
        if indent < indent_stack[-1]:
            indent_stack.pop()
            return dedent_token
        else:
            return newline_token
    
    # If we have encountered tokens and the indentation level is less than
    # previously then emit a dedent token.
    if not newline and indent < indent_stack[-1]:
        indent_stack.pop()
        return dedent_token
    
    # If there is (the start of) a pending token then use this as the basis for
    # the next token.
    if pending_token:
        token = pending_token
        pending_token = ""
    else:
        token = ""
    
    # If the token is a newline then emit this immediately.
    if token == newline_token:
        return token
    
    while True:
    
        ch = stream.read(1)
        
        if not ch:
            # At the end of a file, set a flag and start emitting dedent tokens
            # unless the indentation is already zero.
            at_eof = True
            if indent > 0:
                indent_stack.pop()
                return dedent_token
            else:
                return newline_token
        elif ch == " ":
            # Spaces separate tokens unless in a string. Emit the current token
            # if already started; otherwise continue reading.
            if newline:
                indent += 1
            elif in_string or in_comment:
                token += ch
            elif token:
                break
        elif ch == "\n":
            # Newlines reset the indentation level and end comments and
            # strings. Emit any current token and queue a newline token, or
            # just emit the newline token if there is no current token.
            end_statement()
            line += 1
            
            if token:
                pending_token = newline_token
                break
            else:
                return newline_token
        else:
            # Any non-whitespace characters are treated separately.
            
            # Test for comments and the beginnings and ends of strings.
            if ch == "#":
                in_comment = True
            elif ch == '"':
                in_string = not in_string
            
            if newline:
                # For the first token on a new line, ensure that the
                # appropriate indent and dedent tokens are emitted and queue
                # the latest character read as the beginning of a new token.
                newline = False
                
                if indent > indent_stack[-1]:
                    # Emit an indent token and keep the character for later.
                    pending_token = ch
                    indent_stack.append(indent)
                    return indent_token
                elif indent < indent_stack[-1]:
                    # Emit an dedent token and keep the character for later.
                    pending_token = ch
                    indent_stack.pop()
                    return dedent_token
            
            # Extend the current token with the new character.
            token += ch
    
    return token

def compile_line_tokens(stream):

    "Compiles tokens until the end of the line."
    
    while True:
        token = read_token(stream)
        if not compile_token(token):
            raise SyntaxError, "Unexpected token on line %i: %s" % (line, repr(token))
        if token == newline_token:
            break

def end_statement():

    global indent, in_comment, in_string, newline, pending_operands
    
    indent = 0
    newline = True
    in_comment = False
    in_string = False
    pending_operands = 0

def compile_token(token):

    global pending_operands
    
    if not token:
        return False
    
    if token == dedent_token:
        # If the token is not indented sufficiently then it is part of another
        # control flow structure.
        return False
    
    if token == newline_token:
        # End the current statement. An incomplete statement is a syntax error.
        pending_operands = 0
        return True
    
    if compile_constant(token):
        return True
    
    if token.startswith("#"):
        return True
    
    # Try to find a definition that matches the token.
    i = find_def(token)
    if i >= 0:
        name, compile_fn, expected_parameters = defs[i]
        compile_fn(stream, expected_parameters)
        return True
    
    # Try to find a variable name that matches the token.
    i = find_var(token)
    if i >= 0:
        return compile_load_var(i)
    
    # Try to interpret the unknown token as the start of an assignment.
    if compile_unknown(token, stream):
        return True
    
    raise SyntaxError, repr(token)

# Execution of code

def execute():

    "Execute the code in the temporary code area."
    global code_area, code_offset, pending_operands, value_stack
    
    code_offset = 0
    while code_offset < len(code_area):
        instruction, operand = code_area[code_offset]
        print instruction, operand, "->",
        instruction(operand)
        print value_stack
    
    code_area = []
    value_stack = []
    pending_operands = 0


# Main program and compiler loop

if __name__ == "__main__":

    if not 1 <= len(sys.argv) <= 2:
        sys.stderr.write("Usage: %s [file]\n" % sys.argv[0])
        sys.exit(1)
    
    elif len(sys.argv) == 2:
        stream = open(sys.argv[1])
        
        while not at_eof:
            compile_line_tokens(stream)
    
    else:
        stream = sys.stdin
        
        while not at_eof:
            print "> ",
            compile_line_tokens(stream)
            if newline:
                execute()
    
    print "Definitions"
    pprint.pprint(defs)
    print
    print "Local variables"
    print var_stack
    print
    print "Code area"
    print code_area
    print
