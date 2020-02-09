import compiler, generator, opcodes, tokeniser

# System call definitions

system_call_parameters = [("address", opcodes.address_size),
                          ("A", opcodes.register_size),
                          ("X", opcodes.register_size),
                          ("Y", opcodes.register_size)]

def parse_system_call(stream):

    '<system call> = _call "(" <address> [<A> [<X> [<Y>]]] ")"'
    
    top = len(compiler.used)
    token = compiler.get_token(stream)
    
    if token != tokeniser.system_call_token:
        compiler.put_tokens(top)
        return False
    
    token = compiler.get_token(stream)
    if token != tokeniser.arguments_begin_token:
        raise SyntaxError("Arguments must follow '(' at line %i.\n" % tokeniser.line)
    
    # Parse the arguments corresponding to the system call parameters.
    # These take the form <address> <A> <X> <Y>.
    
    total_args_size = 0
    
    i = 0
    while i < len(system_call_parameters):
    
        name, size = system_call_parameters[i]
        
        top = len(compiler.used)
        token = compiler.get_token(stream)
        
        if token == tokeniser.arguments_end_token:
            # If we encounter a closing parenthesis, check that at least the
            # address has been given.
            if name != "address":
                # Recover the token and break.
                compiler.put_tokens(top)
                break
            else:
                raise SyntaxError("System call lacks an address at line %i.\n" % tokeniser.line)
        else:
            # Recover the token.
            compiler.put_tokens(top)
        
        if i > 0:
            token = compiler.get_token(stream)
            if token != ",":
                raise SyntaxError("Expected a comma before system call argument '%s' at line %i.\n" % (name, tokeniser.line))
        
        if not compiler.parse_expression(stream):
            raise SyntaxError("Invalid system call argument for parameter '%s' at line %i.\n" % (name, tokeniser.line))
        
        if compiler.current_size != size:
            raise SyntaxError("Incompatible types in system call argument for parameter '%s' at line %i.\n" % (name, tokeniser.line))
        
        total_args_size += size
        
        i += 1
    
    token = compiler.get_token(stream)
    if token != tokeniser.arguments_end_token:
        raise SyntaxError("Arguments must be terminated with ')' at line %i.\n" % tokeniser.line)
    
    compiler.debug_print("system call", system_call_parameters)
    
    # Call the system routine with the total size of the arguments supplied.
    # This enables the generated code to retrieve the arguments from the stack.
    
    generator.generate_system_call(total_args_size)
    
    # Set the size of the return value to ensure that it is assigned or
    # discarded as necessary.
    compiler.current_size = compiler.current_element_size = opcodes.system_call_return_size
    compiler.current_array = False
    
    return True
