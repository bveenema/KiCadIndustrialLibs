# Changelog

## Unreleased

- Add `symbol/Transformer-IEC.kicad_sym`.
  Generic symbols, drawn to the Radica IEC figures: Transformer 1P, Transformer 3P, Transformer 3P Bank, AutoTransformer 1P, AutoTransformer 1P Voltage Regulation, AutoTransformer 3P, Current Transformer, Current Transformer 1 Core 2 Windings, Current Transformer 2 Cores 2 Windings.
  Reference prefix is `T` for every symbol, including current transformers. That is the IEC 81346-2 class letter for transformers. Radica labels the same symbols `T1`.
  `Control Transformer 1P` is a single-phase multi-tap control transformer with two secondary windings and an electrostatic shield. Radica's IEC page has a multi-tap transformer, a screened transformer, and a three-winding transformer, and none of those is this part. `86149` extends `Control Transformer 1P`.
  86149 terminals, from the Murrelektronik product PDF (screw terminals 1–8 input, 9–12 output, PE) and the AutomationDirect multi-voltage connection table: primary pins 1–8, secondary pins 9–12, shield pin `PE`. For 400 VAC connect 1 and 6 and jumper 2–4. For 115 VAC connect 9 and 12 and jumper 9–10 and 11–12.
  The primary is two windings, not one chain. Section A is 1 (end), 2 (tap), 3 (end). Section B is 4 (end), 5, 6, 7 (taps), 8 (end). The humps stop between 3 and 4. That is the internal diagram on the AutomationDirect wiring page.
- Add `tools/kicad_sym_lint.py`, run from pre-commit and CI. Existing violations are grandfathered in `tools/kicad-sym-lint-baseline.txt`. The new transformer library is not.
