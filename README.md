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

**AtomLogic** is a declarative Domain-Specific Language (DSL) and compiler toolchain for modeling, validating, and visualizing digital combinational logic circuits.

Instead of drawing schematics manually in graphical software, engineers and students define circuit inputs, outputs, intermediate signals, and logic gates textually in `.atom` source files. The compiler parses the syntax, validates electrical rules and Directed Acyclic Graph (DAG) acyclicity, and automatically generates IEEE-standard vector schematic diagrams using **netlistsvg**.

---

## Compiler Pipeline

AtomLogic implements a modular compiler architecture using **Python 3.10+**, **PLY (Python Lex-Yacc)**, and **netlistsvg**:

1. **Lexical Analysis (`src/lexical.py` - `ply.lex`):**
   - Scans and tokenizes keywords (`CIRCUIT`, `INPUT`, `OUTPUT`), logic primitives (`AND`, `OR`, `NOT`), identifiers, and operators.
   - Discards single-line comments (`//.*`) and tracks line coordinates for error diagnostics.

2. **Syntactic Analysis (`src/parser.py` - `ply.yacc`):**
   - Parses tokens using an unambiguous **LALR(1)** grammar (0 shift/reduce conflicts).
   - Builds an Abstract Syntax Tree (AST) with optional hierarchical box-drawing visualization.

3. **Semantic Analysis & DAG Validation (`src/semantic.py`):**
   - Enforces symbol declarations, gate arities, and signal integrity (floating signals, undriven outputs).
   - Validates the **Single-Driver Rule** and detects combinational feedback loops using 3-state DFS cycle detection.
   - Computes topological evaluation order for downstream execution and visualization.

4. **Schematic Visualization (`src/visualizer.py`):**
   - Translates validated circuits into Yosys Netlist JSON.
   - Invokes **netlistsvg** to render clean, publication-ready IEEE vector schematics with desktop SVG compatibility fixes.

---

## Project Structure

```text
AtomLogic/
├── docs/
│   ├── NETLISTSVG_INTEGRATION.md        # Netlistsvg pipeline architecture & schema
│   ├── PROJECT_SPECIFICATION.md         # Language specification and grammar rules
│   └── SVG_RENDERING_TROUBLESHOOTING.md # QtSvg/Gwenview rendering fix documentation
├── examples/                            # Catalog of reference circuits and error cases
│   └── README.md                        # Test suite guide and terminal error traces
├── src/
│   ├── __init__.py                      # Package entry point
│   ├── lexical.py                       # Lexer (ply.lex)
│   ├── parser.py                        # LALR(1) parser & AST visualizer (ply.yacc)
│   ├── semantic.py                      # Semantic analyzer & electrical DAG validator
│   └── visualizer.py                    # Netlistsvg vector schematic generator
├── circuit.atom                         # Canonical Half Adder circuit definition
├── main.py                              # Centralized compiler CLI driver
├── requirements.txt                     # Python dependencies
└── README.md
```

---

## Installation & Setup

Requires **Python 3.10+** and **Node.js** (for `netlistsvg` diagram rendering).

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
| `--svg` | `-s` | Renders circuit schematic diagram as SVG using netlistsvg |
| `--json` | | Exports the Yosys Netlist JSON used for rendering |
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

The [`examples/`](examples/) directory contains a complete catalog of sample `.atom` files, covering both valid reference circuits (Half Adder, Full Adder, Multiplexer) and intentional test cases demonstrating every lexical, syntactic, and semantic compiler diagnostic.

For detailed descriptions of each example along with expected compiler output and error traces, see [`examples/README.md`](examples/README.md).

---

## Technical Documentation (`docs/`)

The [`docs/`](docs/) directory preserves in-depth architectural specifications, design rationales, and engineering post-mortems encountered throughout the project.

For example, during the integration of the schematic visualizer, desktop image viewers (such as KDE Gwenview / `QtSvg`) failed to inherit CSS styling, causing logic gates to render with solid black interiors and wires to disappear completely. Detailed investigations, root-cause analyses, and solutions to issues of this nature are documented in this folder.

---

## Project Roadmap

- [x] Formal Language Specification & EBNF Grammar
- [x] Lexical Analyzer (`lex`)
- [x] LALR(1) Parser & AST Generation (`yacc`)
- [x] Semantic Analyzer, Electrical Validation, & DAG Cycle Detection
- [x] Diagram Visualizer (netlistsvg IEEE vector schematics)
- [ ] Exhaustive Truth Table Generator ($2^N$ input combinations)
- [ ] Standalone Python Simulation Code Generator
