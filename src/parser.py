"""
AtomLogic Syntactic Analyzer (Parser)
=====================================

[MODIFICAÇÃO - ANÁLISE SINTÁTICA]
Define a gramática livre de contexto (CFG) LALR(1) da DSL AtomLogic usando PLY (ply.yacc),
substituindo as produções de expressões aritméticas do exemplo padrão por declarações
de circuitos digitais, portas lógicas e ações semânticas que constroem a AST.
"""

import ply.lex as lex
import ply.yacc as yacc
from src import lexical
from src.lexical import tokens


# [MODIFICAÇÃO - GRAMÁTICA / AÇÃO SEMÂNTICA]
# Produção inicial: reconhece o bloco CIRCUIT <nome> { <comandos> } e gera o nó raiz da AST.
def p_circuit(p):
    '''
    circuit : CIRCUIT ID LBRACE statement_list RBRACE
    '''
    p[0] = ('circuit', p[2], p[4])

# [MODIFICAÇÃO - GRAMÁTICA / AÇÃO SEMÂNTICA]
# Recursão à esquerda para acumular a lista de comandos do circuito.
def p_statement_list(p):
    '''
    statement_list : statement_list statement
                   | statement
    '''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

# [MODIFICAÇÃO - GRAMÁTICA]
# Produção de comando: declaração de entrada, declaração de saída ou atribuição de porta lógica.
def p_statement(p):
    '''
    statement : input_decl
              | output_decl
              | assign_stmt
    '''
    p[0] = p[1]

# [MODIFICAÇÃO - GRAMÁTICA / AÇÃO SEMÂNTICA]
# Declaração de sinais de entrada: INPUT id1, id2, ...;
def p_input_decl(p):
    '''
    input_decl : INPUT id_list SEMICOLON
    '''
    p[0] = ('inputs', p[2])

# [MODIFICAÇÃO - GRAMÁTICA / AÇÃO SEMÂNTICA]
# Declaração de sinais de saída: OUTPUT id1, id2, ...;
def p_output_decl(p):
    '''
    output_decl : OUTPUT id_list SEMICOLON
    '''
    p[0] = ('outputs', p[2])

# [MODIFICAÇÃO - GRAMÁTICA / AÇÃO SEMÂNTICA]
# Lista de identificadores separados por vírgula.
def p_id_list(p):
    '''
    id_list : id_list COMMA ID
            | ID
    '''
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]

# [MODIFICAÇÃO - GRAMÁTICA / AÇÃO SEMÂNTICA]
# Atribuição de saída de porta lógica a um fio/saída: sinal = GATE(...);
def p_assign_stmt(p):
    '''
    assign_stmt : ID EQUALS gate_expr SEMICOLON
    '''
    p[0] = ('assign', p[1], p[3])

# [MODIFICAÇÃO - GRAMÁTICA / AÇÃO SEMÂNTICA]
# Porta unária NOT(sinal) — aridade fixa de 1 operando garantida pela própria gramática.
def p_gate_expr_not(p):
    '''
    gate_expr : NOT LPAREN ID RPAREN
    '''
    p[0] = ('gate', 'NOT', [p[3]])

# [MODIFICAÇÃO - GRAMÁTICA / AÇÃO SEMÂNTICA]
# Portas binárias AND(sinal1, sinal2) e OR(sinal1, sinal2) — aridade fixa de 2 operandos.
def p_gate_expr_binary(p):
    '''
    gate_expr : AND LPAREN ID COMMA ID RPAREN
              | OR LPAREN ID COMMA ID RPAREN
    '''
    p[0] = ('gate', p[1], [p[3], p[5]])

# [MODIFICAÇÃO - TRATAMENTO DE ERRO SINTÁTICO]
# Reporta token inesperado com número de linha ou fim de arquivo prematuro (EOF).
def p_error(p):
    if p:
        print(f"Syntax error at token '{p.value}' (line {p.lineno})")
    else:
        print("Syntax error: unexpected end of file (EOF)")

# [CÓDIGO DE USUÁRIO - VISUALIZAÇÃO DA AST]
# Função auxiliar para exibir a Árvore Sintática Abstrata (AST) em formato hierárquico no terminal.
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
