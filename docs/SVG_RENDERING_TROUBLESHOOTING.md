# SVG Rendering Troubleshooting: Desktop Viewers (QtSvg / Gwenview) & Dark Mode

This document records the diagnosis, technical root cause, and architectural resolution for the rendering anomaly observed when opening **netlistsvg** vector diagrams in desktop image viewers on Linux.

---

## 1. Problem Description

When compiling circuits with `--svg`, opening the resulting SVG file in Linux desktop image viewers (specifically **Gwenview** on KDE Plasma) exhibited the following visual anomalies:
1. **Solid Black Gate Interiors:** Logic gates (`AND`, `OR`, `NOT`) rendered as solid, opaque black geometric blocks rather than wireframe outlines.
2. **Invisible Interconnect Wires:** All signal lines (`<line>` elements) connecting inputs, gates, and outputs were completely missing from view.
3. **Floating Labels:** Signal and gate text labels (`A`, `B`, `K`, `S1`) appeared visibly, but seemed detached without any schematic wiring.

### The Diagnostic Paradox
When the exact same Netlist JSON was loaded into the online web-based `netlistsvg` simulator, the circuit rendered flawlessly with white gate interiors, visible black wires, and standard IEEE symbols.

---

## 2. Technical Root Cause Analysis

A systematic inspection of the desktop environment and SVG generation mechanics identified two converging factors:

### Factor 1: Desktop Engine Quirks (QtSvg / Gwenview vs. Web Browsers)
* The default image viewer on the system was **KDE Gwenview** (`org.kde.gwenview.desktop`).
* Gwenview and other Qt/KDE desktop applications rely on **QtSvg (`QSvgRenderer`)** to parse and display vector graphics.
* `QtSvg` implements the **SVG 1.2 Tiny specification**, which has minimal support for cascading stylesheets (CSS) embedded within `<style>` blocks.

### Factor 2: Netlistsvg Styling Mechanism & SVG Specification Fallbacks
By default, `netlistsvg` relies entirely on a single top-level CSS rule inside a `<style>` block to style the entire schematic:

```xml
<style>
  svg {
    stroke: #000;
    fill: none;
  }
</style>
```

The underlying conflict:
1. **CSS Inheritance Failure in QtSvg:** Unlike web browsers (Chromium / Gecko), `QtSvg` **does not propagate** the `svg` element's `stroke: #000; fill: none;` styles down to descendant nodes (`<line>` and `<path>`).
2. **W3C SVG Default Fallbacks:** Under the official W3C SVG specification, when an element lacks explicit styling or CSS matches, strict default values apply:
   * **For `<path>` (Gate Bodies):** The default fallback is **`fill: #000000` (solid black)** and `stroke: none`.  
     $\rightarrow$ *Result: Every gate body was filled with solid black.*
   * **For `<line>` (Wires):** The default fallback is **`stroke: none` (transparent)**.  
     $\rightarrow$ *Result: All interconnecting lines were not drawn, making wires completely invisible.*
   * **For `<circle>` (NOT Gate Inversion Bubbles):** The default fallback is **`fill: #000000`**.  
     $\rightarrow$ *Result: Inversion bubbles turned into solid black disks.*
   * **For `<text>` (Labels):** The default fallback fill is black, which is why text remained visible.

### Factor 3: Transparent Canvas in OS Dark Mode
By default, `netlistsvg` creates an SVG canvas with a transparent background. When opened in an operating system or viewer with Dark Mode enabled, the transparent canvas defaults to black or dark grey. Any black stroke (`#000000`) drawn on a dark canvas becomes imperceptible.

---

## 3. The Technical Solution: Universal Presentation Attribute Normalization

Rather than relying on viewer-dependent CSS engines, a post-processing normalization pass was implemented in [`src/visualizer.py`](../src/visualizer.py) via the `_postprocess_svg()` function.

The post-processor parses the raw SVG DOM using Python's `xml.etree.ElementTree` and injects **explicit inline XML presentation attributes** directly onto every node:

### 3.1 Solid Background Canvas
Injects a full-canvas background rectangle at the top of the SVG DOM:
```xml
<rect width="100%" height="100%" fill="#ffffff" stroke="none" />
```
This guarantees an opaque white background regardless of whether the operating system or application is configured for Dark Mode or Light Mode.

### 3.2 Explicit Attribute Injection per Element Type

1. **Interconnect Lines (`<line>`):**
   ```python
   elem.set("stroke", "#000000")
   elem.set("stroke-width", "1.5")
   elem.set("stroke-linecap", "round")
   elem.set("fill", "none")
   ```
   *Guarantees wires are rendered as crisp, solid 1.5px black lines.*

2. **Logic Gate Bodies & Pins (`<path>`):**
   ```python
   if "splitjoinBody" in cls:
       elem.set("fill", "#000000")
       elem.set("stroke", "none")
   else:
       elem.set("stroke", "#000000")
       elem.set("fill", "#ffffff")
       elem.set("stroke-width", "1.5")
       elem.set("stroke-linejoin", "round")
       elem.set("stroke-linecap", "round")
   ```
   *Gives gate bodies an opaque white interior with a defined black border, preventing wires behind them from showing through.*

3. **Inversion Bubbles vs. Junction Dots (`<circle>`):**
   ```python
   if "fill:#000" in style or r_val <= 2.5:
       # Wire branch junction dot
       elem.set("fill", "#000000")
       elem.set("stroke", "none")
   else:
       # NOT gate inversion bubble
       elem.set("fill", "#ffffff")
       elem.set("stroke", "#000000")
       elem.set("stroke-width", "1.5")
   ```
   *Distinguishes between solid black wire junctions and white-filled NOT inversion bubbles.*

4. **Text Labels (`<text>`):**
   ```python
   elem.set("fill", "#000000")
   elem.set("stroke", "none")
   ```

---

## 4. Verification & Compatibility

Following normalization, the emitted vector schematics conform to pure SVG standards and render uniformly across all target environments:

* **KDE Desktop:** Gwenview, Okular (QtSvg / SVG 1.2 Tiny).
* **GNOME Desktop:** Loupe, Eye of GNOME (librsvg).
* **Vector Editors:** Inkscape, GIMP, LibreOffice Draw.
* **IDEs & Previews:** VS Code SVG Preview (Light & Dark themes).
* **Web Browsers:** Chrome, Firefox, Safari, Edge.
