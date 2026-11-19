# KiCad Industrial Libraries

Schematic symbol libraries for industrial panel design.

Before drawing or changing a symbol, read [docs/symbol-guidelines.md](docs/symbol-guidelines.md). It has the house dimensions, how to scale a published drawing onto the 5.08 mm pin grid, and the side-by-side render check required before a push.

`tools/kicad_sym_lint.py` checks the mechanical rules, including winding-curl radius. A winding curl is a chained run of semicircles. The default is 0.635 mm. It does not check that a drawing matches its source, and it does not check arcs that are not windings. The picture check in the guidelines does that. `symbol/Transformer-IEC.kicad_sym` is not grandfathered.
