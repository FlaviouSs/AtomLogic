# AtomLogic Example Circuits

This directory contains reference and test circuits for the AtomLogic DSL, including valid designs and circuits intentionally designed to trigger specific compiler errors.

---

## 1. Valid Circuits (Success)

These circuits pass lexical, syntactic, and semantic validation, generating topological execution plans:

| File | Description | Inputs | Outputs | Gates |
| :--- | :--- | :---: | :---: | :---: |
| [`valid_half_adder.atom`](valid_half_adder.atom) | Canonical Half Adder synthesized with primitive gates | 2 | 2 | 4 |
| [`valid_full_adder.atom`](valid_full_adder.atom) | 1-bit Full Adder with carry-in and carry-out | 3 | 2 | 9 |
| [`valid_multiplexer.atom`](valid_multiplexer.atom) | 2-to-1 Multiplexer (MUX) using selection line | 3 | 1 | 4 |

**Run example:**
```bash
python main.py examples/valid_full_adder.atom --tree
```

---

## 2. Lexical Error Examples (Scanner Violations)

Triggered when the source text contains characters or symbols not recognized by the lexer:

| File | Error Trigger | Expected Output |
| :--- | :--- | :--- |
| [`error_lexical_invalid_char.atom`](error_lexical_invalid_char.atom) | Contains illegal characters `@` and `$` | `Illegal character '@'` |
| [`error_lexical_unsupported_operator.atom`](error_lexical_unsupported_operator.atom) | Uses C-style operator `&` instead of DSL gate `AND(...)` | `Illegal character '&'` |

---

## 3. Syntactic Error Examples (Grammar Violations)

Triggered when the token stream violates Context-Free Grammar (CFG) rules in LALR(1) parsing:

| File | Error Trigger | Expected Output |
| :--- | :--- | :--- |
| [`error_syntax_missing_semicolon.atom`](error_syntax_missing_semicolon.atom) | Omitted `;` after declaration | `Syntax error at token 'OUTPUT'` |
| [`error_syntax_malformed_gate.atom`](error_syntax_malformed_gate.atom) | Missing closing parenthesis `)` in gate call | `Syntax error at token ';'` |
| [`error_syntax_missing_brace.atom`](error_syntax_missing_brace.atom) | Omitted closing brace `}` | `Syntax error: unexpected end of file (EOF)` |

---

## 4. Semantic Error Examples (Domain & Graph Violations)

Syntactically valid scripts that violate electrical or graph-theoretic rules:

| File | Error Trigger | Expected Output |
| :--- | :--- | :--- |
| [`error_semantic_undeclared_signal.atom`](error_semantic_undeclared_signal.atom) | Operand `C` was never declared | `Semantic Error: Undeclared signal 'C' used...` |
| [`error_semantic_duplicate_signal.atom`](error_semantic_duplicate_signal.atom) | Signal `A` declared both as `INPUT` and `OUTPUT` | `Semantic Error: Duplicate declaration of signal 'A'...` |
| [`error_semantic_single_driver.atom`](error_semantic_single_driver.atom) | Signal `w1` driven by multiple gates | `Semantic Error: Single-Driver Violation...` |
| [`error_semantic_cycle.atom`](error_semantic_cycle.atom) | Feedback loop `x -> y -> x` | `Semantic Error: Combinational feedback loop (cycle) detected...` |
| [`error_semantic_undriven_output.atom`](error_semantic_undriven_output.atom) | Declared output `Sum` is never driven | `Semantic Error: Output signal 'Sum' was declared but is never driven...` |
