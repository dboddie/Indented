#!/usr/bin/env python

"""
tokeniser.py - Tokeniser for a simple compiler.

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

line = 1
newline = False
indent = 0
indent_stack = [0]
pending_token = ""
in_comment = False
in_string = False
at_eof = False

indent_token = "\ti"
dedent_token = "\td"
newline_token = "\n"
assignment_token = "="
eof_token = "\te"
arguments_begin_token = "("
arguments_end_token = ")"
system_call_token = "_call"

def reset():

    global at_eof, in_comment, in_string, indent, indent_stack, line, newline
    global pending_token
    
    line = 1
    newline = False
    indent = 0
    indent_stack = [0]
    pending_token = ""
    in_comment = False
    in_string = False
    at_eof = False

def read_token(stream):

    global at_eof, indent, indent_stack, line, in_comment, in_string, newline
    global pending_token
    
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
    if token in (newline_token, arguments_begin_token, arguments_end_token):
        return token
    
    while True:
    
        ch = stream.read(1)
        
        if not ch:
            # At the end of a file, set a flag and start emitting dedent tokens
            # unless the indentation is already zero.
            if indent < indent_stack[-1]:
                indent_stack.pop()
                pending_token = dedent_token
            else:
                pending_token = eof_token
            
            if not token:
                token = pending_token
                pending_token = ""
            
            if token == eof_token:
                at_eof = True
            
            break
        
        elif ch == "\t" or ch == " ":
            # Substitute four spaces for each tab.
            if ch == "\t":
                ch = "    "
            
            # Spaces separate tokens unless in a string. Emit the current token
            # if already started; otherwise continue reading.
            if newline:
                indent += len(ch)
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
        
        elif ch == "(" or ch == ")":
            # Opening and closing parentheses are emitted as separate tokens.
            if token:
                pending_token = ch
                break
            else:
                return ch
        
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

def end_statement():

    global indent, in_comment, in_string, newline
    
    indent = 0
    newline = True
    in_comment = False
    in_string = False


if __name__ == "__main__":

    import sys
    
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <file>\n" % sys.argv[0])
        sys.exit(1)
    
    stream = open(sys.argv[1])
    
    while not at_eof:
        print repr(read_token(stream))
