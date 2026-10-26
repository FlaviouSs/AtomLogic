"""
AtomLogic Lexical Analyzer (Lexer)
==================================

Purpose:
--------
Tokenizes the AtomLogic domain-specific language (DSL) for digital logic circuits.
Built using Python Lex-Yacc (PLY - ply.lex).

Tokens:
-------
- Keywords:       CIRCUIT, INPUT, OUTPUT
- Logic Gates:    AND, OR, NOT
- Identifiers:    ID ([a-zA-Z_][a-zA-Z0-9_]*)
- Delimiters:     EQUALS (=), COMMA (,), SEMICOLON (;), LPAREN ((), RPAREN ()), LBRACE ({), RBRACE (})     
- Comments:       // Single-line comments (discarded)
- Whitespace:     Spaces and tabs ignored, newlines tracked for line counting

"""

import ply.lex as lex

reserved = {
    # Statements
    'CIRCUIT': 'CIRCUIT',
    'INPUT': 'INPUT',
    'OUTPUT': 'OUTPUT',
    
    # Logical Gates
    'AND': 'AND',
    'OR': 'OR',
    'NOT': 'NOT',
}

tokens = [
    # Identifier
    'ID',
    
    # Delimiters and Operators
    'EQUALS',       # =
    'COMMA',        # ,
    'SEMICOLON',    # ;
    'LPAREN',       # (
    'RPAREN',       # )
    'LBRACE',       # {
    'RBRACE',       # }
] + list(reserved.values())


t_EQUALS = r'\='
t_COMMA = r'\,'
t_SEMICOLON = r'\;'
t_RPAREN = r'\)'
t_LPAREN = r'\('
t_RBRACE = r'\}'
t_LBRACE = r'\{'


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_COMMENT(t):
    r'//.*'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore  = ' \t'

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

def main(lex_object):

    lexer = lex_object

    while True:
        print("\nTokens scanner\t\t(Type 'exit' to stop!)")
        try:
            s = str(input("Type in your sentence -> "))
        except EOFError:
            break

        if s.strip() == "exit":
            break

        lexer.input(s)

        for tok in lexer:
            print(tok)

if __name__ == "__main__":

    lexer = lex.lex()

    main(lexer)