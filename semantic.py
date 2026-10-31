"""
AtomLogic Semantic Analyzer
===========================

Purpose:
--------
Performs semantic analysis and electrical graph validation on the Abstract
Syntax Tree (AST) produced by the parser.

Validations:
------------
1. Symbol Table Management:
   - Registers INPUT, OUTPUT, and internal WIRE signals.
   - Detects duplicate signal declarations (e.g. INPUT A; OUTPUT A;).
2. Scope & Existence:
   - Ensures all gate input operands are declared inputs or driven by a gate.
   - Rejects undeclared / floating signals.
3. Electrical Rules:
   - Enforces Single-Driver rule (wires and outputs can only be driven once).
   - Protects input signals from being driven (cannot assign to an INPUT).
   - Validates gate arity (NOT requires 1 input; AND/OR require 2 inputs).
   - Checks for undriven outputs.
4. Dependency Graph & Cycle Detection:
   - Models circuit signal dependencies as a Directed Graph.
   - Verifies the circuit is a Directed Acyclic Graph (DAG) for combinational logic.
   - Reports exact feedback loop paths when cycles are discovered.
5. Topological Execution Ordering:
   - Computes sequential gate evaluation order for the simulation backend.
"""

from enum import Enum
from dataclasses import dataclass, field


class SemanticError(Exception):
    """Raised when a semantic, electrical, or graph validation rule is violated."""
    pass


class SymbolType(Enum):
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"
    WIRE = "WIRE"


@dataclass
class Symbol:
    name: str
    symbol_type: SymbolType
    is_driven: bool = False


class SymbolTable:
    """Stores and resolves signal identifiers within the circuit scope."""
    def __init__(self):
        self._symbols: dict[str, Symbol] = {}

    def define(self, name: str, symbol_type: SymbolType) -> Symbol:
        if name in self._symbols:
            existing = self._symbols[name]
            raise SemanticError(
                f"Duplicate declaration of signal '{name}'. "
                f"Already declared as {existing.symbol_type.value}."
            )
        symbol = Symbol(name=name, symbol_type=symbol_type)
        self._symbols[name] = symbol
        return symbol

    def resolve(self, name: str) -> Symbol | None:
        return self._symbols.get(name)

    def is_defined(self, name: str) -> bool:
        return name in self._symbols

    def get_inputs(self) -> list[str]:
        return [s.name for s in self._symbols.values() if s.symbol_type == SymbolType.INPUT]

    def get_outputs(self) -> list[str]:
        return [s.name for s in self._symbols.values() if s.symbol_type == SymbolType.OUTPUT]

    def get_wires(self) -> list[str]:
        return [s.name for s in self._symbols.values() if s.symbol_type == SymbolType.WIRE]

    def all_symbols(self) -> dict[str, Symbol]:
        return dict(self._symbols)


@dataclass
class GateInstance:
    """Represents a validated logic gate in the circuit."""
    target: str
    gate_type: str
    operands: list[str]


@dataclass
class ValidatedCircuit:
    """Complete semantic representation (Intermediate Representation) of the circuit."""
    name: str
    inputs: list[str]
    outputs: list[str]
    wires: list[str]
    gates: list[GateInstance]
    topological_gates: list[GateInstance] = field(default_factory=list)


class SemanticAnalyzer:
    """Traverses and validates the Abstract Syntax Tree (AST)."""

    VALID_GATES: dict[str, int] = {
        "NOT": 1,
        "AND": 2,
        "OR": 2,
    }

    def __init__(self):
        self.symbol_table = SymbolTable()
        self.gates: list[GateInstance] = []
        self.drivers: dict[str, GateInstance] = {}
        self.dependency_graph: dict[str, list[str]] = {}

    def analyze(self, ast: tuple) -> ValidatedCircuit:
        """
        Main entry point for semantic analysis.
        Expects an AST of format: ('circuit', <name>, [<statements>])
        """
        if not ast or not isinstance(ast, tuple) or ast[0] != "circuit":
            raise SemanticError("Malformed AST: Root must be a 'circuit' node.")

        _, circuit_name, statements = ast

        # Pass 1: Register Port Declarations (INPUT, OUTPUT)
        self._process_declarations(statements)

        # Pass 2: Process Gate Assignments & Enforce Single-Driver Rule
        self._process_assignments(statements)

        # Pass 3: Validate Signal Existence & Undriven Signals
        self._validate_signals()

        # Pass 4: Build Dependency Graph & Detect Combinational Cycles (DAG check)
        self._detect_cycles()

        # Pass 5: Compute Topological Evaluation Order
        topological_gates = self._compute_topological_order()

        return ValidatedCircuit(
            name=circuit_name,
            inputs=self.symbol_table.get_inputs(),
            outputs=self.symbol_table.get_outputs(),
            wires=self.symbol_table.get_wires(),
            gates=self.gates,
            topological_gates=topological_gates,
        )

    def _process_declarations(self, statements: list):
        """Processes INPUT and OUTPUT port declarations."""
        has_inputs = False
        has_outputs = False

        for stmt in statements:
            match stmt:
                case ("inputs", signal_list):
                    has_inputs = True
                    for signal in signal_list:
                        self.symbol_table.define(signal, SymbolType.INPUT)

                case ("outputs", signal_list):
                    has_outputs = True
                    for signal in signal_list:
                        self.symbol_table.define(signal, SymbolType.OUTPUT)

                case ("assign", _, _):
                    pass  # Handled in Pass 2

                case _:
                    raise SemanticError(f"Unknown statement structure: {stmt}")

        if not has_inputs:
            raise SemanticError("Circuit has no input declarations (INPUT).")
        if not has_outputs:
            raise SemanticError("Circuit has no output declarations (OUTPUT).")

    def _process_assignments(self, statements: list):
        """Processes gate assignments, validates gate arity and single-driver rule."""
        for stmt in statements:
            match stmt:
                case ("assign", target_wire, ("gate", gate_type, operands)):
                    # Check gate type validity
                    if gate_type not in self.VALID_GATES:
                        raise SemanticError(f"Unsupported logic gate '{gate_type}'.")

                    # Check gate arity
                    expected_arity = self.VALID_GATES[gate_type]
                    if len(operands) != expected_arity:
                        raise SemanticError(
                            f"Gate '{gate_type}' expects {expected_arity} operand(s), "
                            f"but received {len(operands)}: {operands}."
                        )

                    # Single-Driver Rule Check:
                    # 1. Cannot drive an INPUT signal
                    target_symbol = self.symbol_table.resolve(target_wire)
                    if target_symbol and target_symbol.symbol_type == SymbolType.INPUT:
                        raise SemanticError(
                            f"Invalid driver: Cannot drive input signal '{target_wire}'."
                        )

                    # 2. Cannot drive the same wire or output multiple times
                    if target_wire in self.drivers:
                        raise SemanticError(
                            f"Single-Driver Violation: Signal '{target_wire}' is driven by "
                            f"multiple gates."
                        )

                    # Register as internal WIRE if not already an OUTPUT
                    if not target_symbol:
                        target_symbol = self.symbol_table.define(target_wire, SymbolType.WIRE)

                    # Mark symbol as driven
                    target_symbol.is_driven = True

                    gate_instance = GateInstance(
                        target=target_wire,
                        gate_type=gate_type,
                        operands=operands,
                    )
                    self.gates.append(gate_instance)
                    self.drivers[target_wire] = gate_instance

                    # Build signal dependency graph: target depends on each operand
                    # Signal flow: operand -> target
                    for operand in operands:
                        self.dependency_graph.setdefault(operand, []).append(target_wire)

    def _validate_signals(self):
        """Ensures all referenced signals exist and that outputs are driven."""
        # 1. Check all operands are valid declared inputs or driven wires
        for gate in self.gates:
            for operand in gate.operands:
                sym = self.symbol_table.resolve(operand)
                if not sym:
                    raise SemanticError(
                        f"Undeclared signal '{operand}' used in gate {gate.gate_type} "
                        f"for output '{gate.target}'."
                    )
                if sym.symbol_type in (SymbolType.OUTPUT, SymbolType.WIRE) and not sym.is_driven:
                    raise SemanticError(
                        f"Signal '{operand}' is used as an operand but has no driver."
                    )

        # 2. Check all OUTPUTs are driven
        for out_name in self.symbol_table.get_outputs():
            sym = self.symbol_table.resolve(out_name)
            if sym and not sym.is_driven:
                raise SemanticError(
                    f"Output signal '{out_name}' was declared but is never driven by any gate."
                )

    def _detect_cycles(self):
        """
        Detects feedback loops / cycles in the combinational logic using DFS.
        Combinational circuits must be Directed Acyclic Graphs (DAGs).
        """
        # Graph mapping: wire -> list of wires it depends on
        # If target = GATE(A, B), target depends on A and B
        dep_map: dict[str, list[str]] = {}
        for gate in self.gates:
            dep_map[gate.target] = list(gate.operands)

        visited: dict[str, int] = {}  # 0: unvisited, 1: visiting (current branch), 2: visited

        def dfs(node: str, path: list[str]):
            visited[node] = 1
            path.append(node)

            for dependency in dep_map.get(node, []):
                state = visited.get(dependency, 0)
                if state == 1:
                    # Cycle found!
                    cycle_start = path.index(dependency)
                    cycle = path[cycle_start:] + [dependency]
                    cycle_str = " -> ".join(cycle)
                    raise SemanticError(
                        f"Combinational feedback loop (cycle) detected: {cycle_str}."
                    )
                elif state == 0:
                    dfs(dependency, path)

            path.pop()
            visited[node] = 2

        for node in list(dep_map.keys()):
            if visited.get(node, 0) == 0:
                dfs(node, [])

    def _compute_topological_order(self) -> list[GateInstance]:
        """
        Orders gates topologically so that a gate is evaluated only after
        all of its input operands have been evaluated.
        """
        available_signals = set(self.symbol_table.get_inputs())
        ordered_gates: list[GateInstance] = []
        remaining_gates = list(self.gates)

        while remaining_gates:
            progress = False
            for gate in list(remaining_gates):
                if all(operand in available_signals for operand in gate.operands):
                    ordered_gates.append(gate)
                    available_signals.add(gate.target)
                    remaining_gates.remove(gate)
                    progress = True
                    break

            if not progress:
                # Should not occur if cycle detection passed, but acts as a safety guard
                unresolved = [g.target for g in remaining_gates]
                raise SemanticError(
                    f"Could not topologically order remaining gates: {unresolved}."
                )

        return ordered_gates


def analyze_circuit(ast: tuple) -> ValidatedCircuit:
    """Convenience helper function to run semantic analysis on an AST."""
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(ast)
