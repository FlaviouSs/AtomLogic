"""
AtomLogic Circuit Visualizer (Netlistsvg Backend)
=================================================

Translates a ValidatedCircuit IR into a Yosys-compatible Netlist JSON
and renders an IEEE-standard vector schematic using 'netlistsvg'.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from src.semantic import ValidatedCircuit


GATE_CELL_MAP = {
    "AND": ("$_AND_", ["A", "B"], "Y"),
    "OR": ("$_OR_", ["A", "B"], "Y"),
    "NOT": ("$_NOT_", ["A"], "Y"),
}


class VisualizationError(Exception):
    """Raised when netlist serialization or netlistsvg rendering fails."""
    pass


def circuit_to_yosys_json(circuit: ValidatedCircuit) -> dict:
    """
    Transforms a ValidatedCircuit into the Yosys Netlist JSON schema expected by netlistsvg.
    Assigns a unique integer bit ID to each electrical net (inputs, outputs, wires).
    """
    # 1. Collect all unique signals and assign unique numeric bit IDs (starting from 2)
    all_signals: list[str] = []
    all_signals.extend(circuit.inputs)
    all_signals.extend(circuit.outputs)
    for wire in circuit.wires:
        if wire not in all_signals:
            all_signals.append(wire)

    signal_to_bit: dict[str, int] = {
        name: bit_id for bit_id, name in enumerate(all_signals, start=2)
    }

    # 2. Build top-level module ports
    ports: dict[str, dict] = {}
    for inp in circuit.inputs:
        ports[inp] = {"direction": "input", "bits": [signal_to_bit[inp]]}
    for out in circuit.outputs:
        ports[out] = {"direction": "output", "bits": [signal_to_bit[out]]}

    # 3. Build logic gate cells
    cells: dict[str, dict] = {}
    for idx, gate in enumerate(circuit.gates, start=1):
        if gate.gate_type not in GATE_CELL_MAP:
            raise VisualizationError(f"Unsupported gate type for netlist rendering: '{gate.gate_type}'.")

        cell_type, in_ports, out_port = GATE_CELL_MAP[gate.gate_type]
        cell_name = f"gate_{idx}_{gate.target}"

        # Port directions
        port_directions = {port_name: "input" for port_name in in_ports}
        port_directions[out_port] = "output"

        # Signal connections to cell pins
        connections = {
            port_name: [signal_to_bit[operand]]
            for port_name, operand in zip(in_ports, gate.operands)
        }
        connections[out_port] = [signal_to_bit[gate.target]]

        cells[cell_name] = {
            "type": cell_type,
            "port_directions": port_directions,
            "connections": connections,
        }

    # 4. Build netnames so wire labels appear visibly on the schematic
    netnames: dict[str, dict] = {
        sig: {"hide_name": 0, "bits": [bit_id]}
        for sig, bit_id in signal_to_bit.items()
    }

    return {
        "creator": "AtomLogic Compiler",
        "modules": {
            circuit.name: {
                "ports": ports,
                "cells": cells,
                "netnames": netnames,
            }
        },
    }


def render_circuit_svg(
    circuit: ValidatedCircuit,
    output_svg_path: str,
    output_json_path: str | None = None,
) -> str:
    """
    Renders the circuit to an SVG file using netlistsvg.
    Falls back gracefully to 'npx --yes netlistsvg' if netlistsvg is not installed globally.
    """
    # 1. Generate Yosys netlist dictionary
    netlist_data = circuit_to_yosys_json(circuit)

    # 2. Determine JSON path (intermediate or permanent)
    if output_json_path:
        json_path = output_json_path
    else:
        json_path = str(Path(output_svg_path).with_suffix(".json"))

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(netlist_data, f, indent=2)

        # 3. Locate netlistsvg executable or use npx
        if shutil.which("netlistsvg"):
            cmd = ["netlistsvg", json_path, "-o", output_svg_path]
        elif shutil.which("npx"):
            cmd = ["npx", "--yes", "netlistsvg", json_path, "-o", output_svg_path]
        else:
            raise VisualizationError(
                "Neither 'netlistsvg' nor 'npx' was found in PATH. "
                "Please install Node.js and netlistsvg to generate SVG schematics."
            )

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise VisualizationError(
                f"netlistsvg failed with return code {result.returncode}:\n{result.stderr.strip()}"
            )

        # 4. Post-process SVG for universal rendering (fixes QtSvg/Gwenview and dark themes)
        _postprocess_svg(output_svg_path, bg_color="#ffffff")

    finally:
        # If user didn't explicitly request to save the JSON, remove the temporary JSON file
        if not output_json_path and os.path.exists(json_path):
            os.remove(json_path)

    return output_svg_path


def _postprocess_svg(svg_path: str, bg_color: str = "#ffffff") -> None:
    """
    Normalizes the generated SVG to ensure full compatibility across all viewers,
    especially desktop renderers like QtSvg (used by KDE Gwenview) and librsvg (used by GNOME).

    Why this is required:
    1. netlistsvg relies strictly on CSS `<style>svg { stroke: #000; fill: none; }</style>`.
    2. Desktop viewers like QtSvg / Gwenview do NOT inherit CSS stroke/fill from the root `svg` selector.
       According to the SVG standard, unstyled <path> defaults to solid black fill, and unstyled
       <line> defaults to stroke="none" (invisible).
    3. Transparent background makes black lines invisible in OS Dark Mode.

    This function:
    - Adds a solid background `<rect>` and background-color.
    - Explicitly sets `stroke`, `fill`, `stroke-width`, and `stroke-linecap` attributes on all
      `<line>`, `<path>`, `<circle>`, and `<text>` elements.
    """
    if not os.path.exists(svg_path):
        return

    import xml.etree.ElementTree as ET

    namespaces = {
        "": "http://www.w3.org/2000/svg",
        "xlink": "http://www.w3.org/1999/xlink",
        "s": "https://github.com/nturley/netlistsvg",
    }
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)

    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()

        def get_local_tag(elem):
            return elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        # Check if background rect already exists
        has_bg_rect = False
        for child in list(root):
            tag = get_local_tag(child)
            if tag == "rect" and child.get("width") == "100%" and child.get("height") == "100%":
                has_bg_rect = True
                break

        if not has_bg_rect:
            bg_rect = ET.Element(
                "rect",
                {
                    "width": "100%",
                    "height": "100%",
                    "fill": bg_color,
                    "stroke": "none",
                },
            )
            root.insert(0, bg_rect)

        for elem in root.iter():
            tag = get_local_tag(elem)
            cls = elem.get("class", "")

            if tag == "line":
                # Wires
                elem.set("stroke", "#000000")
                elem.set("stroke-width", "1.5")
                elem.set("stroke-linecap", "round")
                elem.set("fill", "none")

            elif tag == "path":
                # Gate bodies, input/output port pins
                if "splitjoinBody" in cls:
                    elem.set("fill", "#000000")
                    elem.set("stroke", "none")
                else:
                    elem.set("stroke", "#000000")
                    elem.set("fill", "#ffffff")
                    elem.set("stroke-width", "1.5")
                    elem.set("stroke-linejoin", "round")
                    elem.set("stroke-linecap", "round")

            elif tag == "circle":
                # Distinguish wire branch junctions (r <= 2) from NOT inversion bubbles (r >= 3)
                r_val = 0.0
                try:
                    r_val = float(elem.get("r", "0"))
                except ValueError:
                    pass

                style = elem.get("style", "")
                if "fill:#000" in style or r_val <= 2.5:
                    # Junction dot
                    elem.set("fill", "#000000")
                    elem.set("stroke", "none")
                else:
                    # Inversion bubble
                    elem.set("fill", "#ffffff")
                    elem.set("stroke", "#000000")
                    elem.set("stroke-width", "1.5")

            elif tag == "text":
                elem.set("fill", "#000000")
                elem.set("stroke", "none")

        tree.write(svg_path, encoding="utf-8", xml_declaration=False)

    except Exception:
        # Fallback to text replacement if XML parsing encounters unexpected formatting
        with open(svg_path, "r", encoding="utf-8") as f:
            content = f.read()

        if "<style>svg {" in content:
            content = content.replace(
                "<style>svg {",
                f"<style>svg {{\n    background-color: {bg_color};",
                1,
            )
        bg_rect_str = f'  <rect width="100%" height="100%" fill="{bg_color}" stroke="none"/>\n'
        if "</style>" in content and bg_rect_str.strip() not in content:
            content = content.replace("</style>", f"</style>\n{bg_rect_str}", 1)

        with open(svg_path, "w", encoding="utf-8") as f:
            f.write(content)
