# Netlistsvg Circuit Visualizer Integration

This document details the architectural design, data pipeline, and technical implementation of the integration between the **AtomLogic** compiler and the **netlistsvg** toolchain for generating IEEE-standard vector circuit schematics (SVG).

---

## 1. Overview & Motivation

**AtomLogic** is a declarative Domain-Specific Language (DSL) and compiler for digital combinational logic circuits. Following lexical scanning, parsing, and semantic validation, the compiler produces a verified Intermediate Representation (IR), encapsulated by the `ValidatedCircuit` data model.

To generate graphical schematics of validated circuits, the open-source **netlistsvg** engine was integrated as the visualizer backend due to several key strengths:
* **Standard IEEE Logic Symbols:** Renders official IEEE logic gate representations for primitives (`AND`, `OR`, `NOT`).
* **Orthogonal Wire Routing:** Automatically routes interconnects using 90-degree angular paths via the Eclipse Layout Kernel (ELK), avoiding wire crossings and visual clutter.
* **Vector Graphics (SVG):** Emits scalable vector diagrams compatible with desktop viewers, documentation, and web browsers.

---

## 2. Compilation & Visualization Pipeline

The visualizer connects directly to the validated compiler frontend:

```text
Source Code (.atom)
         │
         ▼
┌─────────────────────────┐
│   Lexical & Syntactic   │  (src/lexical.py & src/parser.py)
│        Analysis         │
└─────────────────────────┘
         │  Abstract Syntax Tree (AST)
         ▼
┌─────────────────────────┐
│    Semantic Analysis    │  (src/semantic.py)
│  & Electrical Checks    │
└─────────────────────────┘
         │  ValidatedCircuit (IR with DAG guarantee & single drivers)
         ▼
┌─────────────────────────┐
│  Netlist JSON Serializer│  (src/visualizer.py: circuit_to_yosys_json)
└─────────────────────────┘
         │  Yosys-compatible Netlist JSON
         ▼
┌─────────────────────────┐
│  netlistsvg Rendering   │  (netlistsvg CLI / npx --yes netlistsvg)
└─────────────────────────┘
         │  Raw SVG output
         ▼
┌─────────────────────────┐
│  XML Post-Processing    │  (src/visualizer.py: _postprocess_svg)
│  Attribute Normalization│
└─────────────────────────┘
         │
         ▼
Output Vector Schematic (.svg)
```

> **Design Highlight:** While `netlistsvg` is traditionally coupled with the Yosys synthesis suite, AtomLogic does not require Yosys (a heavy C++ toolchain). Instead, `src/visualizer.py` implements a native Python serializer matching the Yosys Netlist JSON schema directly.

---

## 3. Mapping to the Yosys Netlist JSON Schema

The `netlistsvg` engine consumes a JSON document structured around module `ports`, logic `cells`, and wire `netnames`.

### 3.1 Signal Bit Allocation
Every distinct signal within the circuit (`inputs`, `outputs`, and internal `wires`) is mapped to a unique integer bit identifier (`bit_id`), starting at index `2`:

```python
signal_to_bit = {
    "A": 2,
    "B": 3,
    "Carry": 4,
    "Sum": 5,
    "or_ab": 6
}
```

### 3.2 Cell Mapping (`cells`)
AtomLogic logic gates map to canonical Yosys cell primitives:

| AtomLogic Gate | Yosys / Netlistsvg Type | Input Pin(s) | Output Pin |
| :--- | :---: | :---: | :---: |
| `AND(in1, in2)` | `$_AND_` | `A`, `B` | `Y` |
| `OR(in1, in2)`  | `$_OR_`  | `A`, `B` | `Y` |
| `NOT(in)`       | `$_NOT_` | `A`      | `Y` |

Each cell defines its port directions (`port_directions`) and connects its pins to the corresponding bit IDs (`connections`):

```json
"gate_1_Carry": {
  "type": "$_AND_",
  "port_directions": { "A": "input", "B": "input", "Y": "output" },
  "connections": {
    "A": [ 2 ],
    "B": [ 3 ],
    "Y": [ 4 ]
  }
}
```

### 3.3 Wire Labels & Interconnects (`netnames`)
To ensure intermediate wire labels (such as `or_ab` or `not_carry`) appear rendered along interconnect lines on the schematic, the serializer registers entries in the `netnames` block:

```json
"netnames": {
  "or_ab": {
    "hide_name": 0,
    "bits": [ 6 ]
  }
}
```

---

## 4. Execution & Orchestration (`src/visualizer.py`)

The public interface for visualization is `render_circuit_svg(circuit, output_svg_path, output_json_path)`:

1. **Netlist Generation:** Translates `ValidatedCircuit` into the in-memory dictionary and writes it to a `.json` file.
2. **Tool Discovery:**
   - Checks if `netlistsvg` is installed globally in the system `PATH` (`shutil.which("netlistsvg")`).
   - If absent, invokes Node's package runner: `npx --yes netlistsvg <input.json> -o <output.svg>`.
3. **Attribute Normalization:** Post-processes the raw SVG to ensure desktop renderer compatibility across operating systems and dark-mode themes (see `SVG_RENDERING_TROUBLESHOOTING.md`).
4. **Cleanup:** Removes the intermediate `.json` file automatically unless the user explicitly requested it via `--json`.

---

## 5. Command-Line Interface (`main.py`)

The visualizer is exposed through two CLI flags:

* **`--svg` (or `-s`):** Compiles the source and renders the SVG diagram.
* **`--json`:** Preserves the exported Yosys Netlist JSON for external analysis.

### Output Naming Convention
Generated files automatically derive their filenames from the source input file:

```bash
# Generates 'circuit.svg' and 'circuit.json'
python main.py circuit.atom --svg --json

# Generates 'examples/valid_full_adder.svg'
python main.py examples/valid_full_adder.atom --svg
```

In interactive REPL mode (where no input file exists), the compiler defaults to the circuit name declared in code (`f"{circuit.name}.svg"`).
