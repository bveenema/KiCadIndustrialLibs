# KiCad Industrial Libraries

Schematic symbol libraries for industrial panel design.

Before drawing or changing a symbol, read [docs/symbol-guidelines.md](docs/symbol-guidelines.md). It has the house dimensions, how to scale a published drawing onto the 5.08 mm pin grid, and the side-by-side render check required before a push.

`tools/kicad_sym_lint.py` checks the mechanical rules, including winding-curl radius. A winding curl is a chained run of semicircles. The default is 0.635 mm. It does not check that a drawing matches its source, and it does not check arcs that are not windings. The picture check in the guidelines does that. `symbol/Transformer-IEC.kicad_sym` and `symbol/Transformer-Murrelektronik.kicad_sym` are not grandfathered.

## Rules for agents

- `*-IEC` libraries hold generics only. A part with a manufacturer or part number goes in a `<Category>-<Manufacturer>` library. A family base in that file is for two or more variants. A single part is a standalone symbol. See "Where a symbol lives" in the guidelines.
- A base extended by exactly one symbol in the same file fails `single-variant-base`, unless that symbol is a generic placed on the sheet. Base symbols need 2+ variants; flatten a one-variant base. Descriptions do not say what a symbol was derived from.
- Name a manufacturer part after the manufacturer's model designation (spaces removed, `/` and `...` become `-`), with `_<order number>` appended when the order number is not in it. Value is the symbol name.
- `Datasheet` is a direct link to the part's PDF. Fetch it and confirm it is a PDF for that exact part before you commit. A shop or product page is not a datasheet.
- Draw a manufacturer part to the manufacturer's terminal diagram, including crossed leads. Terminal order on the symbol matches the terminal strip. Render it next to that diagram before pushing.
- Every terminal on one strip, shield and PE included, sits in that strip's row, facing the same way, in strip order. Declare the strips with `ki_terminal_rows` (for example `1 2 3 4 5 6 7 8 PE; 9 10 11 12`) on any part drawn from a terminal diagram, so the `terminal-row` lint checks them.
- Keep separate windings one grid step (5.08 mm) apart when the symbol has three or more winding sections, and at most two grid steps (10.16 mm) when it has two. The two-winding current transformers keep 10.16 mm on purpose; do not tighten them. Any wider gap needs a `ki_winding_gap` property with a reason.
- When a review finds a mistake that a check could catch, add a lint rule with tests in `tools/test_kicad_sym_lint.py`. When it cannot be checked mechanically, add it to the guidelines and to this list.
- Run `pre-commit run --all-files` and `python -m unittest test_kicad_sym_lint.py` in `tools/` before pushing. Both run in CI.
