import sys
from pprint import pprint
import ply.lex as lex
import ply.yacc as yacc
import lexical
from lexical import tokens


def p_circuit(p):
    '''
    circuit : CIRCUIT ID LBRACE statement_list RBRACE
    '''
    p[0] = ('circuit', p[2], p[4])

def p_statement_list(p):
    '''
    statement_list : statement_list statement
                   | statement
    '''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_statement(p):
    '''
    statement : input_decl
              | output_decl
              | assign_stmt
    '''
    p[0] = p[1]

def p_input_decl(p):
    '''
    input_decl : INPUT id_list SEMICOLON
    '''
    p[0] = ('inputs', p[2])

def p_output_decl(p):
    '''
    output_decl : OUTPUT id_list SEMICOLON
    '''
    p[0] = ('outputs', p[2])

def p_id_list(p):
    '''
    id_list : id_list COMMA ID
            | ID
    '''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

def p_assign_stmt(p):
    '''
    assign_stmt : ID EQUALS gate_expr SEMICOLON
    '''
    p[0] = ('assign', p[1], p[3])

def p_gate_expr_not(p):
    '''
    gate_expr : NOT LPAREN ID RPAREN
    '''
    p[0] = ('gate', 'NOT', [p[3]])

def p_gate_expr_binary(p):
    '''
    gate_expr : AND LPAREN ID COMMA ID RPAREN
              | OR LPAREN ID COMMA ID RPAREN
    '''
    p[0] = ('gate', p[1], [p[3], p[5]])

def p_error(p):
    if p:
        print(f"Syntax error at token '{p.value}' (line {p.lineno})")
    else:
        print("Syntax error: unexpected end of file (EOF)")

def print_ast_tree(node, prefix="", is_last=True):
    """
    Renders the Abstract Syntax Tree (AST) in a visual hierarchical tree format
    using Unicode box-drawing characters.
    """
    if not isinstance(node, tuple):
        return

    tag = node[0]

    # Root: CircuitNode
    if tag == "circuit":
        name, statements = node[1], node[2]
        print(f"CircuitNode: \"{name}\"")
        for i, stmt in enumerate(statements):
            print_ast_tree(stmt, prefix="", is_last=(i == len(statements) - 1))

    # Declaration nodes
    elif tag == "inputs":
        marker = "└── " if is_last else "├── "
        print(f"{prefix}{marker}InputsNode: {node[1]}")

    elif tag == "outputs":
        marker = "└── " if is_last else "├── "
        print(f"{prefix}{marker}OutputsNode: {node[1]}")

    # Assignment node: target = gate_expr
    elif tag == "assign":
        target, gate = node[1], node[2]
        marker = "└── " if is_last else "├── "
        print(f"{prefix}{marker}AssignNode: \"{target}\"")
        child_prefix = prefix + ("    " if is_last else "│   ")
        print_ast_tree(gate, child_prefix, is_last=True)

    # Gate expression node: GATE(inputs...)
    elif tag == "gate":
        op, operands = node[1], node[2]
        marker = "└── " if is_last else "├── "
        print(f"{prefix}{marker}GateNode: {op}")
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, operand in enumerate(operands):
            op_marker = "└── " if i == len(operands) - 1 else "├── "
            print(f"{child_prefix}{op_marker}Operand: \"{operand}\"")

def main():
    lexer = lex.lex(module=lexical)
    parser = yacc.yacc()

    # Parse CLI flags and positional arguments
    flags = [arg for arg in sys.argv[1:] if arg.startswith('-')]
    files = [arg for arg in sys.argv[1:] if not arg.startswith('-')]

    show_tree = '--tree' in flags or '-t' in flags
    show_both = '--both' in flags or '-b' in flags

    def display_ast(ast):
        if not ast:
            return
        if show_both:
            print("\nGenerated Abstract Syntax Tree (Raw Tuples):")
            pprint(ast)
            print("\nGenerated Abstract Syntax Tree (Tree View):")
            print_ast_tree(ast)
        elif show_tree:
            print("\nGenerated Abstract Syntax Tree (Tree View):")
            print_ast_tree(ast)
        else:
            print("\nGenerated Abstract Syntax Tree (AST):")
            pprint(ast)

    # Case 1: File provided as argument
    if files:
        filepath = files[0]
        try:
            with open(filepath, 'r') as f:
                code = f.read()
            print(f"Parsing file: {filepath}\n")
            ast = parser.parse(code, lexer=lexer)
            display_ast(ast)
        except FileNotFoundError:
            print(f"Error: File '{filepath}' not found.")
        return

    # Case 2: Interactive terminal mode
    print("=== AtomLogic Parser Interactive Mode ===")
    print("Type/paste your circuit code.")
    print("Type 'END' on a new line or press Ctrl+D to parse.")
    print("Flags: use --tree (-t) for tree view, or --both (-b) for both views.\n")

    lines = []
    try:
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
    except EOFError:
        pass

    user_code = "\n".join(lines).strip()

    print("\n--- Parsing Result ---")
    ast = parser.parse(user_code, lexer=lexer)
    display_ast(ast)

if __name__ == "__main__":
    main()
