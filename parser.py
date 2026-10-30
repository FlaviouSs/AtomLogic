import sys
from pprint import pprint
import ply.lex as lex
import ply.yacc as yacc
import lexical
from lexical import tokens

"""
Current Grammar Definition (EBNF):
----------------------------------
circuit        ::= "CIRCUIT" ID "{" statement_list "}"
statement_list ::= statement+
statement      ::= input_decl | output_decl | assign_stmt
input_decl     ::= "INPUT" id_list ";"
output_decl    ::= "OUTPUT" id_list ";"
id_list        ::= ID ("," ID)*
assign_stmt    ::= ID "=" gate_expr ";"
gate_expr      ::= "NOT" "(" ID ")" | ("AND" | "OR") "(" ID "," ID ")"
"""

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

def main():
    lexer = lex.lex(module=lexical)
    parser = yacc.yacc()

    # Case 1: File provided as argument
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            with open(filepath, 'r') as f:
                code = f.read()
            print(f"Parsing file: {filepath}\n")
            ast = parser.parse(code, lexer=lexer)
            print("\nGenerated Abstract Syntax Tree (AST):")
            pprint(ast)
        except FileNotFoundError:
            print(f"Error: File '{filepath}' not found.")
        return

    # Case 2: Interactive terminal mode
    print("=== AtomLogic Parser Interactive Mode ===")
    print("Type/paste your circuit code.")
    print("Type 'END' on a new line or press Ctrl+D to parse.")
    print("Or press Enter on an empty line to parse a built-in demo circuit.\n")

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
    if ast:
        print("\nGenerated Abstract Syntax Tree (AST):")
        pprint(ast)

if __name__ == "__main__":
    main()
