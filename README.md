# AtomLogic

```text
    ___   __                  __              _     
   /   | / /_____  ____ ___  / /   ____  ____(_)____
  / /| |/ __/ __ \/ __ `__ \/ /   / __ \/ __ `/ / ___/
 / ___ / /_/ /_/ / / / / / / /___/ /_/ / /_/ / / /__  
/_/  |_\__/\____/_/ /_/ /_/_____/\____/\__, /_/\___/  
                                      /____/          
            Digital Circuit DSL & Compiler
```

**AtomLogic** is a declarative Domain-Specific Language (DSL) and compiler toolchain for modeling, validating, and simulating digital combinational logic circuits.

Instead of drawing schematics manually in graphical software, engineers and students define circuit inputs, outputs, intermediate signals, and logic gates textually in `.atom` source files. The compiler analyzes the syntax, validates electrical rules, enforces Directed Acyclic Graph (DAG) acyclicity, and produces a validated intermediate representation ready for simulation.

---

## Compiler Pipeline

AtomLogic implements the classical compiler frontend architecture using **Python 3.10+** and **PLY (Python Lex-Yacc)**:

1. **Lexical Analysis (`src/lexical.py` - `ply.lex`):**
   - Scans and tokenizes keywords (`CIRCUIT`, `INPUT`, `OUTPUT`), logic primitives (`AND`, `OR`, `NOT`), identifiers, delimiters, and assignment operators.
   - Discards single-line comments (`//.*`) and tracks line coordinates for precise diagnostics.

2. **Syntactic Analysis (`src/parser.py` - `ply.yacc`):**
   - Parses the token stream using an unambiguous **LALR(1)** shift-reduce engine with **0 conflicts**.
   - Constructs a structured Abstract Syntax Tree (AST) with an optional box-drawing visual tree renderer.

3. **Semantic Analysis & Electrical Graph Validation (`src/semantic.py`):**
   - **Symbol Table:** Tracks scopes for `INPUT`, `OUTPUT`, and internal `WIRE` signals; catches duplicate declarations.
   - **Electrical Rules:** Enforces gate arities (unary `NOT`, binary `AND`/`OR`) and the **Single-Driver Rule** (wires and outputs can only be driven once; inputs cannot be driven).
   - **Signal Integrity:** Prevents floating/undeclared signals and ensures all declared outputs are driven.
   - **Graph Theory & Cycle Detection:** Models signal flow as a directed graph and runs 3-state Depth-First Search (DFS) to reject combinational feedback loops.
   - **Topological Sorting:** Computes sequential evaluation order for downstream backends.

---

## Project Structure

```text
AtomLogic/
├── docs/
│   └── PROJECT_SPECIFICATION.md   # Architectural breakdown and design notes
├── examples/                      # Catalog of reference circuits and error test cases
│   ├── README.md                  # Detailed test case guide and error catalog
│   ├── valid_*.atom               # Valid circuits (Half Adder, Full Adder, MUX)
│   ├── error_lexical_*.atom       # Lexical scanner error examples
│   ├── error_syntax_*.atom        # Syntactic grammar error examples
│   └── error_semantic_*.atom      # Electrical and graph validation error examples
├── src/
│   ├── __init__.py                # Source package entry
│   ├── lexical.py                 # Lexer (ply.lex)
│   ├── parser.py                  # LALR(1) parser & AST visualizer (ply.yacc)
│   └── semantic.py                # Semantic analyzer & electrical DAG validator
├── circuit.atom                   # Canonical Half Adder circuit definition
├── main.py                        # Centralized compiler CLI driver
├── requirements.txt               # Project dependencies
└── README.md
```

---

## Installation & Setup

Requires **Python 3.10** or higher.

```bash
# 1. Clone repository
git clone https://github.com/flaviouss/AtomLogic.git
cd AtomLogic

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage & CLI Options

### 1. Compile a Circuit Source File
```bash
python main.py circuit.atom
```

### 2. Command-Line Flags

| Flag | Short | Description |
| :--- | :---: | :--- |
| `--tree` | `-t` | Displays the hierarchical box-drawing AST visualization |
| `--ast` | `-a` | Dumps the raw Python tuple AST representation |
| `--verbose` | `-v` | Displays detailed step-by-step pipeline execution logs |
| `--debug` | `-d` | Enables PLY debug mode, generating `src/parser.out` and `src/parsetab.py` |
| `--help` | `-h` | Shows usage instructions and available options |

**Example with hierarchical AST tree and verbose logs:**
```bash
python main.py circuit.atom --tree --verbose
```

### 3. Interactive Terminal Mode (REPL)
Run without file arguments to enter interactive mode:
```bash
python main.py
```
Paste or type your circuit, then type `END` on a new line (or press `Ctrl+D`) to compile.

---

## DSL Syntax by Example

A canonical Half Adder written in the AtomLogic DSL (`circuit.atom`):

```dsl
CIRCUIT HalfAdder {
    INPUT A, B;
    OUTPUT Sum, Carry;

    Carry = AND(A, B);
    or_ab = OR(A, B);
    not_carry = NOT(Carry);
    Sum = AND(or_ab, not_carry);
}
```

---

## Example Circuits & Error Catalog

The [`examples/`](examples/) folder provides reference circuits and intentional negative test cases demonstrating every compiler error:

* **Valid Circuits:**
  * [`valid_half_adder.atom`](examples/valid_half_adder.atom): Canonical Half Adder (4 gates).
  * [`valid_full_adder.atom`](examples/valid_full_adder.atom): 1-bit Full Adder with carry-in and carry-out (9 gates).
  * [`valid_multiplexer.atom`](examples/valid_multiplexer.atom): 2-to-1 Multiplexer (4 gates).
* **Lexical Errors:**
  * [`error_lexical_invalid_char.atom`](examples/error_lexical_invalid_char.atom): Illegal characters (`@`, `$`).
  * [`error_lexical_unsupported_operator.atom`](examples/error_lexical_unsupported_operator.atom): Unsupported operators (`&`).
* **Syntactic Errors:**
  * [`error_syntax_missing_semicolon.atom`](examples/error_syntax_missing_semicolon.atom): Omitted statement delimiter (`;`).
  * [`error_syntax_malformed_gate.atom`](examples/error_syntax_malformed_gate.atom): Unclosed parenthesis in gate expression.
  * [`error_syntax_missing_brace.atom`](examples/error_syntax_missing_brace.atom): Premature EOF / unclosed block (`}`).
* **Semantic Errors:**
  * [`error_semantic_undeclared_signal.atom`](examples/error_semantic_undeclared_signal.atom): Undeclared operand signal.
  * [`error_semantic_duplicate_signal.atom`](examples/error_semantic_duplicate_signal.atom): Duplicate signal declarations.
  * [`error_semantic_single_driver.atom`](examples/error_semantic_single_driver.atom): Multi-driver wire contention.
  * [`error_semantic_cycle.atom`](examples/error_semantic_cycle.atom): Combinational feedback loop (cycle detection).
  * [`error_semantic_undriven_output.atom`](examples/error_semantic_undriven_output.atom): Undriven output port.

See [`examples/README.md`](examples/README.md) for full descriptions and terminal output traces.

---

## Project Roadmap

- [x] Formal Language Specification & EBNF Grammar
- [x] Lexical Analyzer (`lex`)
- [x] LALR(1) Parser & AST Generation (`yacc`)
- [x] Semantic Analyzer, Electrical Validation, & DAG Cycle Detection
- [ ] Exhaustive Truth Table Generator ($2^N$ input combinations)
- [ ] Diagram Visualizer (Graphviz DOT & SchemDraw logic schematics)
- [ ] Standalone Python Simulation Code Generator
