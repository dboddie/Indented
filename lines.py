#!/usr/bin/env python

import sys

# Built-in compilation functions

def compile_def(stream):

    # Record the indentation level of the def keyword.
    ind = indent - 4
    
    # Read the definition's name.
    name = read_token(stream)
    
    # Read the names of the parameters.
    while newline == False:
        read_token(stream)

def compile_if(stream):

    # Record the indentation level of the if keyword.
    ind = indent - 3
    
    # Compile the condition.
    compile_line_tokens(stream, ind + 1)
    
    # Insert a branch instruction placeholder.
    code_area.append("branch if false to")
    
    # Compile the body of the structure.
    while indent > ind:
        compile_line_tokens(stream, ind + 1)

def compile_equals(stream):

    # Record the indentation level.
    ind = indent - 3
    
    compile_token(stream, ind + 1)
    code_area.append((compare_equals, None))

# Built-in run-time functions

def load_constant(value):

    value_stack.append(value)

def compare_equals(value):

    return value_stack.pop() == value_stack.pop()


# Environment workspace

defs = [("if", compile_if), ("==", compile_equals)]
code_area = []
value_stack = []

# Compiler/interpreter internals

newline = False
indent = 0
pending_token = ""


# Parsing/compilation functions

def add_def(token):

    defs.append(token)

def read_token(stream):

    global indent, newline, pending_token
    
    if newline == True:
        indent = 0
    
    newline = False
    
    if pending_token:
        token = pending_token
        pending_token = ""
        indent += len(pending_token) + 1
        return token
    
    token = ""
    
    while True:
    
        ch = stream.read(1)
        indent += 1
        
        if ch == " ":
            break
        elif ch == "\n":
            newline = True
            break
        
        token += ch
    
    return token

def compile_line_tokens(stream, min_indent):

    "Compiles tokens until the end of the line."
    
    while newline == False:
        compile_token(stream, min_indent)

def compile_token(stream, min_indent):

    global indent, pending_token
    
    token = read_token(stream)
    if not token:
        return
    
    print min_indent, indent - len(token) - 1, token
    if indent - len(token) - 1 < min_indent:
        # If the token is not indented sufficiently then it is part of another
        # control flow struction, so we do not compile it but store it for
        # later processing.
        pending_token = token
        indent -= len(token) + 1
        return
    
    if is_constant(token):
        compile_constant(token)
        return
    
    i = 0
    while i < len(defs):
    
        name, compile_fn = defs[i]
        if token == name:
            compile_fn(stream)
            return
        
        i += 1
    
    raise ValueError, repr(token)

# Constant handling

def is_constant(token):

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

def compile_constant(token):

    code_area.append((load_constant, int(token)))

# Executation of code

def execute():

    "Execute the code in the temporary code area."
    global code_area, value_stack
    
    for instruction, operand in code_area:
        print instruction, operand, "->", instruction(operand)
    
    code_area = []
    value_stack = []


# Main program and compiler loop

if __name__ == "__main__":

    if not 1 <= len(sys.argv) <= 2:
        sys.stderr.write("Usage: %s [file]\n" % sys.argv[0])
        sys.exit(1)
    
    elif len(sys.argv) == 2:
        stream = open(sys.argv[1])
    
    else:
        stream = sys.stdin
    
    while True:
        compile_token(stream, 0)
        if newline:
            execute()
