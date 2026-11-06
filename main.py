"""
AtomLogic Compiler Driver (Main Entry Point)
============================================

Purpose:
--------
Orchestrates the entire compilation pipeline for the AtomLogic DSL, connecting
the Lexer (lexical.py), Parser (parser.py), and Semantic Analyzer (semantic.py)
into a unified compiler tool.

Usage:
------
    python main.py <circuit_file.atom> [options]

Options:
--------
    --tree, -t     Display the Abstract Syntax Tree (AST) visual tree.
    --ast,  -a     Display the raw AST tuples.
    --verbose, -v  Display detailed step-by-step pipeline output.
    --debug, -d    Enable parser debug mode (generates parser.out and parsetab.py).
    --help, -h     Display this help message.
    (no args)      Enter interactive terminal mode.
"""

import sys
import os
from pprint import pprint
import ply.lex as lex
import ply.yacc as yacc

from src import lexical
from src import parser as parser_module
from src import semantic
from src.semantic import ValidatedCircuit, SemanticError


class AtomLogicCompiler:
    """Unified driver managing the compiler pipeline stages."""

    def __init__(self, debug: bool = False, write_tables: bool = False):
        self.lexer = lex.lex(module=lexical)
        self.parser = yacc.yacc(
            module=parser_module,
            write_tables=write_tables,
            debug=debug,
        )

    def compile_source(
        self,
        source_code: str,
        verbose: bool = False,
        show_tree: bool = False,
        show_ast: bool = False,
    ) -> ValidatedCircuit | None:
        """
        Executes the 3-stage compilation pipeline:
        Stage 1: Lexical Analysis
        Stage 2: Syntactic Analysis & AST Construction
        Stage 3: Semantic Analysis & Graph/Cycle Validation
        """
        if verbose:
            print("\n" + "=" * 50)
            print("AtomLogic Compilation Pipeline Initiated")
            print("=" * 50)

        # ---------------------------------------------------------
        # Stage 1 & 2: Lexical & Syntactic Analysis (Parser)
        # ---------------------------------------------------------
        if verbose:
            print("[Stage 1/3] Running Lexical Scanner & LALR(1) Parser...")

        # Reset line tracking
        self.lexer.lineno = 1

        # Check for empty input
        if not source_code.strip():
            print("Compilation Error: Source code is empty.")
            return None

        ast = self.parser.parse(source_code, lexer=self.lexer)
        if not ast:
            # Syntax errors are reported by p_error in parser.py
            print("Compilation Error: Syntactic analysis failed.")
            return None

        if verbose:
            print("  ↳ Syntax valid. Abstract Syntax Tree (AST) generated.")

        if show_ast:
            print("\n--- Abstract Syntax Tree (Raw Tuples) ---")
            pprint(ast)

        if show_tree:
            print("\n--- Abstract Syntax Tree (Hierarchical Tree) ---")
            parser_module.print_ast_tree(ast)

        # ---------------------------------------------------------
        # Stage 3: Semantic Analysis & Electrical Graph Validation
        # ---------------------------------------------------------
        if verbose:
            print("\n[Stage 2/3] Running Semantic Analysis & Electrical Validation...")

        try:
            circuit = semantic.analyze_circuit(ast)
        except SemanticError as err:
            print(f"\nSemantic Error: {err}")
            return None

        if verbose:
            print("  ↳ Symbol table verified (inputs, outputs, wires).")
            print("  ↳ Single-driver and arity rules enforced.")
            print("  ↳ Dependency graph is a valid DAG (no feedback loops).")
            print("  ↳ Topological execution order computed.")

        # ---------------------------------------------------------
        # Stage 4: Compilation Summary
        # ---------------------------------------------------------
        print("\n" + "=" * 50)
        print(f"Compilation Successful: Circuit '{circuit.name}'")
        print("=" * 50)
        print(f"  • Inputs  ({len(circuit.inputs)}): {', '.join(circuit.inputs)}")
        print(f"  • Outputs ({len(circuit.outputs)}): {', '.join(circuit.outputs)}")
        if circuit.wires:
            print(f"  • Wires   ({len(circuit.wires)}): {', '.join(circuit.wires)}")
        print(f"  • Total Logic Gates: {len(circuit.gates)}")

        print("\nExecution Plan (Topological Order):")
        for idx, gate in enumerate(circuit.topological_gates, 1):
            args_str = ", ".join(gate.operands)
            print(f"  {idx}. {gate.target} = {gate.gate_type}({args_str})")
        print("=" * 50)

        return circuit


def run_interactive(compiler: AtomLogicCompiler, show_tree: bool, show_ast: bool):
    """Runs interactive REPL terminal mode."""
    print("=== AtomLogic Compiler — Interactive Mode ===")
    print("Type or paste your circuit definition.")
    print("Type 'END' on a new line or press Ctrl+D to compile.\n")

    lines = []
    try:
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
    except EOFError:
        pass

    code = "\n".join(lines).strip()
    if not code:
        print("No input provided. Exiting.")
        return

    compiler.compile_source(
        code,
        verbose=True,
        show_tree=show_tree,
        show_ast=show_ast,
    )


def main():
    # Parse CLI flags
    flags = [arg for arg in sys.argv[1:] if arg.startswith("-")]
    files = [arg for arg in sys.argv[1:] if not arg.startswith("-")]

    if "--help" in flags or "-h" in flags:
        print(__doc__)
        return

    show_tree = "--tree" in flags or "-t" in flags
    show_ast = "--ast" in flags or "-a" in flags
    verbose = "--verbose" in flags or "-v" in flags
    debug_mode = "--debug" in flags or "-d" in flags

    compiler = AtomLogicCompiler(debug=debug_mode, write_tables=debug_mode)

    # Mode 1: Compile file provided in arguments
    if files:
        filepath = files[0]
        try:
            with open(filepath, "r") as f:
                source_code = f.read()
        except FileNotFoundError:
            print(f"Error: File '{filepath}' not found.")
            sys.exit(1)

        print(f"Compiling '{filepath}'...")
        result = compiler.compile_source(
            source_code,
            verbose=verbose,
            show_tree=show_tree,
            show_ast=show_ast,
        )
        if not result:
            sys.exit(1)
        return

    # Mode 2: Interactive terminal mode
    run_interactive(compiler, show_tree=show_tree, show_ast=show_ast)


if __name__ == "__main__":
    main()
