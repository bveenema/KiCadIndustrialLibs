# Symbol guidelines

Rules for drawing a new KiCad symbol in this repository. They apply to every
library, not only transformers. Read this before drawing, and check the
pictures before pushing.

## House measurements

Taken from the existing `*-IEC` libraries (Actuators-IEC coils, Relay-IEC
contactor, Motor-IEC). Stroke width `0` is KiCad's default and renders at
0.1524 mm.

| What | Measured |
| --- | --- |
| Pin grid | 5.08 mm (200 mil) |
| Pin length | 3.81 mm (150 mil). 7.62 mm only on PLC and panel IO |
| Font | 1.27 mm |
| Stroke | width 0, renders 0.1524 mm |
| Default winding curl | 0.635 mm. Four curls fill one grid step |
| Tight winding curl | 0.508 mm. The semicircle measured on cable pigtail tails |
| Contactor terminal dot | circle radius 0.508 mm |
| Contactor pole pitch | 5.08 mm (L1, L2, L3) |
| One contactor pole | about 2.5 mm of ink. Circle diameter 1.016 mm, contact blade rises 1.27 mm, and the ink from the bottom of the terminal dot to the blade tip is 2.03 mm |
| AC coil body | 7.62 mm wide, 3.81 mm tall. Pins are 15.24 mm apart |
| Contactor_3P_AC poles | about 12.2 mm tall for three poles |

0.635 mm is the default winding curl. It is the chained semicircle on the
transformer windings and on the two-hump coil in the `PowerEntryModule`
symbols. The sine mark inside `AC Coil` is a smaller arc of the same radius,
not a winding curl. A file may round 0.635 to 0.63 or 0.64.

0.508 mm (20 mil) is the other measured curl. It is the semicircle on the
cable pigtail tails in `CablesConnectors` (`Pigtail_*`) and on the
AutomationDirect M12 cable symbols. Those drawings leave a 0.254 mm gap
between the semicircles, so they are not themselves a winding curl. A winding
that does chain at 0.508 mm is using that same tight curl. No larger chained
winding radius exists in these libraries.

Place a new symbol next to `Contactor_3P_AC` before deciding it is the right
size. A winding curl of 1.27 mm radius is twice the default, and the symbol
will look about twice as big as the contactor.

## Drawing a symbol

Generic symbols are drawn fresh. A new generic may borrow the curl radius,
the stroke width, and the text size from an existing `*-IEC` symbol. It does
not start from that symbol's graphics, and the description does not say where
the drawing came from.

## Where a symbol lives and what it is called

A `*-IEC` library holds generics only: symbols drawn to the IEC standards with
no manufacturer and no part number. A symbol with an `MFG` or `MPN` goes in a
`<Category>-<Manufacturer>` library, for example
`Transformer-Murrelektronik`. The lint rule `generic-lib-manufacturer` fails a
manufacturer part in a `*-IEC` library.

`extends` only works inside one file, so a manufacturer part cannot extend a
generic in a `*-IEC` library. A family base belongs in the manufacturer
library only when two or more orderable parts share one drawing. The base
has no `MFG` or `MPN`. Each part extends that base and overrides properties
only. One orderable part is its own symbol: the graphics, the pins, and
`ki_terminal_rows` sit on that symbol. The lint rule `single-variant-base`
fails a symbol that exactly one other symbol in the same file extends,
unless that symbol is a generic placed on the sheet (no `MFG` or `MPN`, in
a `*-IEC` library or a category library with no manufacturer suffix). A
description does not say what a symbol was derived from.

Name a manufacturer part after the manufacturer's own model designation, the
way the KiCad official libraries name parts by MPN. Remove spaces, replace
`/` and `...` with `-`, and append `_<order number>` when the number you order
by is not in the designation. Murrelektronik's `MST 0630-208...550/2x115`,
ordered as 86149, is `MST0630-208-550-2x115_86149`. Value is the symbol name.
Put the order number in `MPN` and the keywords so a search for it finds the
part.

## Datasheet

`Datasheet` links the document itself, not a product page or a home page.
Fetch the link before committing and check that it returns a PDF for that
exact part. Prefer the manufacturer's PDF when it carries the terminal
diagram; a distributor cut sheet often does not. The lint rule
`datasheet-document` accepts a URL whose path ends in `.pdf`, or a download URL
listed under `datasheet_downloads` in `tools/kicad-sym-lint.yaml` with a
reason. Add a pattern there only after fetching it and seeing the PDF. A
generic may leave `Datasheet` empty.

## Matching a manufacturer terminal diagram

A manufacturer part is drawn to the manufacturer's terminal diagram, the one
the installer will have open. Read it from the datasheet, not from memory or a
distributor table.

- Terminal numbers run in the same order as on the diagram. When the
  diagram crosses two leads so the terminals read in order, draw the
  crossover. On the Murrelektronik MST the secondary windings are 9-11 and
  10-12, and the inner leads cross so the terminals read 9, 10, 11, 12. A
  symbol that puts 9 and 11 side by side reads differently from the
  terminal strip and gets miswired.
- Two leads that cross without a junction dot are not connected. Do not
  put a dot on a crossover.
- Keep the diagram's grouping: separate windings stay separate, taps stay on
  the winding they come from, and the shield or earth terminal stays a
  separate pin.
- Every terminal on one strip sits in that strip's row, facing the same way,
  in strip order. That includes the shield and PE terminal. On the MST the
  primary strip is 1-8 then the shield, so PE is a ninth pin one grid step
  after 8, pointing the same way as 1-8, and the dashed shield line turns up
  into it.
- Declare the strips with a hidden `ki_terminal_rows` property on the symbol
  that carries the pins: pin numbers in strip order, strips separated by
  `;`. The MST is `1 2 3 4 5 6 7 8 PE; 9 10 11 12`. The lint rule
  `terminal-row` then fails a listed pin that is missing, off the row,
  facing another way, or out of order.

## Spacing between sections

How far apart separate windings may sit depends on how many winding sections
the symbol draws. A winding section is one chained run of curls.

- Three or more sections: one grid step (5.08 mm) at most. A part like the
  MST control transformer, with a two-section primary and two secondaries,
  gets wide quickly, so every section is drawn tight.
- Two sections: two grid steps (10.16 mm) at most. A current transformer
  with two secondaries has room, and its 10.16 mm spacing is intentional
  (Ben, 2026-11-20). Do not tighten the CTs.

The empty span between two windings on one baseline is checked by the lint
rule `winding-gap` with those limits. A wider gap needs a `ki_winding_gap`
property on that symbol with the gap in millimetres and a reason, in the same
form as `ki_winding_curl`. Pins stay on the 5.08 mm grid, so one empty grid
step is the tightest gap that still shows two windings.

Reference and Value sit at 0,0. Keywords are filled in. Pins are
bidirectional, 3.81 mm long, on the 5.08 mm grid, with numbers shown. The
inner end of each pin meets the body.

Keep graphics off the horizontal line through 0,0. The reference and the
value are drawn there, and a curl or a lead on that line is crossed by the
text.

## Recreating a published drawing

When a symbol is meant to look like a published drawing, such as a Radica
stencil:

1. Fetch the publisher's SVG. Do not redraw from memory of the picture.
2. Read the terminal coordinates out of the paths, including transforms.
3. Scale the SVG so a terminal pitch lands on the 5.08 mm grid. For the
   Radica IEC transformers, the 20-unit pitch between the two terminals of a
   winding is one grid step, which is 0.254 mm per SVG unit. At that scale
   the publisher's hump comes out at 0.635 mm, the house curl. If the radius
   does not come out at 0.635 mm, the scale is wrong.
4. Draw to that scaled picture. Legs that are straight in the source stay
   straight. A tap that leaves from between humps stays between humps. Curls
   face the same way.
5. A terminal that falls halfway between two grid points is not moved onto
   the end of the curl. Keep the 0.635 mm curl and repeat curls until every
   terminal is on a grid point. The Radica autotransformer tap is halfway
   across a 5.08 mm winding, so that winding is two grid steps wide and has
   eight curls, with the tap on the middle junction. The current-transformer
   gap scales to 2.54 mm, so the pins sit one grid step apart and the C is
   four curls. Do not enlarge the curl to hit the grid.
6. A vertical span that is not a multiple of 5.08 mm snaps to the nearest
   grid span that meets the pin inners. Prefer the smaller span when the
   symbol was already larger than the contactor. The Radica single-phase
   transformer is 50 units tall, 12.7 mm at this scale, so the graphic runs
   between the pin inners at ±6.35 mm and the pins sit at ±10.16 mm.

## Check before pushing

Render every changed symbol and look at the picture. `kicad-cli sym export svg`
then a PNG at a fixed pixels-per-millimetre, so the pictures share a scale.

For each symbol, put three pictures in a row:

- the publisher's SVG, scaled so its terminal pitch is 5.08 mm
- the new symbol, with the reference and value hidden so the geometry is visible
- an existing KIL symbol at the same scale. Use `Contactor_3P_AC` in
  Relay-IEC. Its poles are the size reference, and its coil unit carries the
  0.635 mm curl

Do not push while a curl is visibly larger than the contactor's curl, or
while a leg, a tap, or a join disagrees with the source. A lint pass is not
this check. The lint cannot see a picture.

## What the lint checks

`tools/kicad_sym_lint.py` checks the mechanical rules: fields at 0,0, pin
grid, pin length, pin type, visible pin numbers, the inner end on the body,
keywords, descriptions, a named parent that is missing from the library
(`extends-parent`), a base extended by exactly one symbol
(`single-variant-base`), and the radius of a winding curl, manufacturer
parts in a `*-IEC` library (`generic-lib-manufacturer`), datasheet links
that are not a document (`datasheet-document`), windings on one baseline
further apart than one grid step (two grid steps when the symbol has only
two winding sections) (`winding-gap`), and pins that break a symbol's
`ki_terminal_rows` (`terminal-row`). Severity is in
`tools/kicad-sym-lint.yaml`.

`single-variant-base` fails when exactly one symbol in the file extends
another, and the parent is not a generic placed on the sheet. The message
is: base symbols need 2+ variants, flatten it. Two or more extenders is a
family base. A description stays silent about where the drawing came from.
The `description` rule fails text that says the symbol was derived from,
extends, or was copied from another symbol.

A winding curl is a run of 2 or more semicircular arcs of equal radius whose
endpoints meet and lie on one straight line.

- An arc is a semicircle when the distance between its ends is the diameter:
  within 0.05 mm of twice the radius of the circle through the arc's start,
  mid, and end.
- Two arcs meet when they share an endpoint within 0.05 mm. The same
  semicircle copied into another unit is one arc, not two.
- The endpoints of the run lie within 0.05 mm of one straight line. Radii in
  the run match within 0.02 mm.

A single semicircle, a quarter circle, the sine mark in a coil box, a
terminal dot, a contact blade, and an arrow are not winding curls. The rule
does not look at them.

The default radius is 0.635 mm. 0.508 mm is also approved, for the tight
curl measured on cable pigtail tails. Any other radius on a winding curl is
an error unless that symbol carries an exception.

Put the exception on the symbol that contains the arcs. One property per
extra radius. The value is the radius in millimetres, then `reason:` and a
written reason:

```
(property "ki_winding_curl" "1.27 reason: the source pitch cannot land on the grid at 0.635 mm"
	(at 0 0 0)
	(effects
		(font
			(size 1.27 1.27)
		)
		(hide yes)
	)
)
```

The reason is required. The radius has to be the one you drew, within 0.02
mm. This is an approval of that size on that symbol, including in
`Transformer-IEC`. A `kicad-sym-lint: suppress` comment does not approve a
curl, and that library still cannot suppress the rule.

Existing violations of the other rules are listed in
`tools/kicad-sym-lint-baseline.txt`. `symbol/Transformer-IEC.kicad_sym` and
`symbol/Transformer-Murrelektronik.kicad_sym` are not in that file and cannot
be suppressed. The earlier arc check flagged
every non-0.635 arc, including arcs that are not windings. Those baseline
lines are gone, because the winding-curl definition does not flag them.

These are not lint rules, because they cannot be checked reliably:

- Whether a drawing matches a source SVG or a manufacturer terminal
  diagram, including crossovers. That is the picture check above.
- Whether a datasheet URL actually returns the right PDF. The lint only checks
  the shape of the link. Fetch it.
- A body-size budget against pin count. A three-phase row is wider than a
  one-phase coil on purpose, and a PLC body is large on purpose. The
  contactor comparison is the size check.
- Circle radius. Terminal dots are 0.508 mm and device bodies are several
  millimetres, so one allowed set does not describe both.

## What went wrong on Transformer-IEC

The first drawings had no scale reference and the curls were not compared to
the source SVG.

The curls were drawn at 1.27 mm radius, twice the house curl, and the pins
sat at ±15.24 mm. Next to `Contactor_3P_AC` the symbols were about twice the
size. Mapping the Radica 20-unit terminal pitch onto 5.08 mm makes the same
hump 0.635 mm. That comparison was skipped, so the size error was invisible
until the symbols were placed on a sheet.

The autotransformer was also the wrong shape. Radica draws small humps
between a straight 1N/2N trunk and a straight 1L leg, with 2L leaving from
between the humps. The first drawing put large humps on a horizontal bar and
brought 2L off the left end of that bar. The source path was not measured,
so the tap moved to the wrong junction.

Do the measurement and the side-by-side render first. A symbol that has not
been seen next to the source and next to the contactor is not ready to push.

## What went wrong on 86149

The first Murrelektronik 86149 symbol was put in `Transformer-IEC` as a child
of the generic. Review found four problems, and each one is now a rule:

- A manufacturer part sat in an IEC generic library. It moved to
  `Transformer-Murrelektronik` and the `generic-lib-manufacturer` lint rule
  fails the next one.
- `Datasheet` was the Murrelektronik shop page, not the PDF. It now links
  Murrelektronik's Product-PDF, which has the terminal diagram, and the
  `datasheet-document` rule fails a product page.
- The primary sections and the two secondaries were two grid steps apart,
  so the symbol was wider than it needed to be. They are now one grid step
  apart, and the `winding-gap` rule fails a wider gap on any symbol with three
  or more winding sections.
- The secondaries were drawn as 9-11 and 10-12 side by side. Murrelektronik
  crosses the inner leads so the strip reads 9, 10, 11, 12. The symbol now
  draws the crossover. The lint cannot see that; the picture check against
  the manufacturer diagram can.
- PE sat on its own level at the right, pointing left, while Murrelektronik's
  strip runs 1-8 then the shield. PE is now in the 1-8 row, and the
  `terminal-row` rule fails a strip pin that leaves its row or its order once
  the symbol declares `ki_terminal_rows`.
