# KiCad Industrial Libraries  
Schematic symbol libraries for industrial panel design.  

This is a collection of libraries intended for designing Industrial Control Panels.  

It is neither comprehensive nor complete, as libraries and symbols are added as they necessary or useful.  

Efforts are made to maintain consistency among symbols so they appear cohesive on a schematic. The drawing rules are in [docs/symbol-guidelines.md](docs/symbol-guidelines.md): the house curl and pin grid, how to scale a published drawing onto that grid, and the side-by-side check against the source and against `Contactor_3P_AC` before a push.  

## Atomic vs Non-Atomic Libraries
Definition: Atomic Library - A library in which each symbol represents a unique component. For example, a symbol for a Turck PLC (TBEN-L4-PLC). This contrasts with generic symbols, such as a capacitor, resistor, or terminal block, can represent variety of real components.  

In this repository, both atomic and non-atomic libraries are included. For instance, _Cables_Connectors.lib_ is a non-atomic library, smaller in size and suitable for representing cables and connectors from any supplier. In contrast, _Cables_Connectors-AutomationDirect.lib_ and _Cables_Connectors-McMaster.lib_ are atomic libraries, larger in size and represent part numbers from those suppliers. Atomic libraries have their datasheet and Mfg fields pre-filled, whereas-atomic libraries do not.

## Libraries

Each file in `symbol/` is one KiCad symbol library. The name of the file is the library name. `Transformer-IEC` holds generic IEC transformer, autotransformer, current-transformer, and control-transformer symbols. `Transformer-Murrelektronik` holds Murrelektronik parts, starting with the MST 630 VA control transformer `MST0630-208-550-2x115_86149` (AutomationDirect 86149). `*-IEC` libraries hold generics only; a part with a manufacturer goes in a `<Category>-<Manufacturer>` library.

## Symbol lint

`tools/kicad_sym_lint.py` checks symbol libraries for field placement, pin grid, pin length, pin type, visible pin numbers, winding-curl radius, keywords, descriptions, a named parent missing from the library, a base extended by exactly one symbol (`single-variant-base`), manufacturer parts in a `*-IEC` library, datasheet links that are not a document, windings spaced wider than one grid step (two grid steps on a symbol with only two winding sections), and terminal-strip pins that leave their declared row (`ki_terminal_rows`). A winding curl is a chained run of semicircles. The default radius is 0.635 mm, and 0.508 mm is approved for the tight cable-pigtail curl. Severity is set in `tools/kicad-sym-lint.yaml`. The picture check in the guidelines is separate. The linter cannot tell whether a drawing matches its source.

Violations that already existed are listed in `tools/kicad-sym-lint-baseline.txt` and do not fail the check. Delete a line when that symbol is fixed. `symbol/Transformer-IEC.kicad_sym` and `symbol/Transformer-Murrelektronik.kicad_sym` are not grandfathered. Install the same check as a commit hook with `pre-commit install`. CI runs `pre-commit run --all-files`.  
