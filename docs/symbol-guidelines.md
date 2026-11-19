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
| Winding curl radius | 0.635 mm |
| One curl's width | 1.27 mm. Four curls fill one grid step |
| Contactor terminal dot | circle radius 0.508 mm |
| Contactor pole pitch | 5.08 mm (L1, L2, L3) |
| One contactor pole | about 2.5 mm of ink. Circle diameter 1.016 mm, contact blade rises 1.27 mm, and the ink from the bottom of the terminal dot to the blade tip is 2.03 mm |
| AC coil body | 7.62 mm wide, 3.81 mm tall. Pins are 15.24 mm apart |
| Contactor_3P_AC poles | about 12.2 mm tall for three poles |

The 0.635 mm curl is the one on `AC Coil`, on the coil unit of
`Contactor_3P_AC`, and on the motor sine marks. A file may round it to 0.63
or 0.64. New curls are exactly 0.635 mm.

Place a new symbol next to `Contactor_3P_AC` before deciding it is the right
size. A winding curl that is 1.27 mm in radius is twice the house curl, and
the symbol will look about twice as big as the contactor.

## Drawing a symbol

Generic symbols are drawn fresh. A manufacturer part such as `86149` extends
its generic and only overrides properties. A new generic may borrow the curl
radius, the stroke width, and the text size from an existing `*-IEC` symbol.
It does not start from that symbol's graphics, and the description does not
say where the drawing came from.

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
keywords, descriptions, manufacturer parts that extend a generic, and arc
radius. An arc has to be 0.635 mm ± 0.02 mm. Severity is in
`tools/kicad-sym-lint.yaml`.

Existing violations are listed in `tools/kicad-sym-lint-baseline.txt`, one
line per symbol for the arc rule. `symbol/Transformer-IEC.kicad_sym` is not
in that file and cannot be suppressed.

These are not lint rules, because they cannot be checked reliably:

- Whether a drawing matches a source SVG. That is the picture check above.
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
