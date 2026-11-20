"""Winding-curl checks for tools/kicad_sym_lint.py.

    python -m unittest tools/test_kicad_sym_lint.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kicad_sym_lint as lint


def semicircle(x, radius, y=0.0, sign=1):
    return (
        f"(arc (start {x} {y}) (mid {x + radius} {y + sign * radius}) "
        f"(end {x + 2 * radius} {y}) (stroke (width 0) (type default)) "
        f"(fill (type none)))"
    )


def chain(radius, count=2):
    parts = []
    x = 0.0
    for index in range(count):
        sign = 1 if index % 2 == 0 else -1
        parts.append(semicircle(x, radius, sign=sign))
        x += 2 * radius
    return parts


def library(arcs, extra=""):
    body = "\n".join(arcs)
    return f"""(kicad_symbol_lib
  (version 20241209)
  (symbol "CurlFixture"
    (property "Reference" "T" (at 0 0 0) (effects (font (size 1.27 1.27))))
    (property "Value" "CurlFixture" (at 0 0 0) (effects (font (size 1.27 1.27))))
    (property "Description" "fixture" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "ki_keywords" "test" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    {extra}
    (symbol "CurlFixture_0_1"
      {body}
    )
  )
)
"""


def arc_findings(text):
    tree = lint.parse(text)
    symbol = lint.top_symbols(tree)[0]
    findings = []
    lint.check_symbol(Path("fixture.kicad_sym"), symbol, "fixture.kicad_sym", findings)
    return [item for item in findings if item.rule == "arc-radius"]


class WindingCurlTests(unittest.TestCase):
    def test_default_curl_passes(self):
        self.assertEqual(arc_findings(library(chain(0.635, 4))), [])

    def test_approved_alternate_passes(self):
        # 0.508 mm is the tight curl measured on cable pigtail tails.
        self.assertEqual(arc_findings(library(chain(0.508, 3))), [])

    def test_unapproved_size_fails(self):
        found = arc_findings(library(chain(1.27, 2)))
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].rule, "arc-radius")
        self.assertIn("1.270", found[0].where)

    def test_exception_allows_unapproved_size(self):
        extra = (
            '(property "ki_winding_curl" '
            '"1.27 reason: the source pitch needs a wider hump on this symbol" '
            "(at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))"
        )
        self.assertEqual(arc_findings(library(chain(1.27, 2), extra)), [])

    def test_exception_without_reason_does_not_pass(self):
        extra = (
            '(property "ki_winding_curl" "1.27" '
            "(at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))"
        )
        self.assertEqual(len(arc_findings(library(chain(1.27, 2), extra))), 1)

    def test_gapped_semicircles_are_not_a_winding(self):
        # Cable pigtails leave a 0.254 mm gap. That is not a chained curl.
        gapped = [semicircle(0, 0.508), semicircle(0.508 * 2 + 0.254, 0.508)]
        self.assertEqual(arc_findings(library(gapped)), [])

    def test_non_winding_arc_is_ignored(self):
        # One semicircle is not a run. A shallow arc is not a semicircle.
        lone = [semicircle(0, 1.27)]
        shallow = [
            "(arc (start 0 0) (mid 0.5 0.2) (end 1 0) "
            "(stroke (width 0) (type default)) (fill (type none)))"
        ]
        self.assertEqual(arc_findings(library(lone)), [])
        self.assertEqual(arc_findings(library(shallow)), [])
        self.assertIsNone(lint.semicircle_radius((0, 0), (0.5, 0.2), (1, 0)))


def symbol_library(name, props="", body=""):
    return f"""(kicad_symbol_lib
  (version 20241209)
  (symbol "{name}"
    (property "Reference" "T" (at 0 0 0) (effects (font (size 1.27 1.27))))
    (property "Value" "{name}" (at 0 0 0) (effects (font (size 1.27 1.27))))
    (property "Description" "fixture" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "ki_keywords" "test" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    {props}
    (symbol "{name}_0_1"
      {body}
    )
  )
)
"""


def findings_for(text, filename, rule):
    tree = lint.parse(text)
    found = []
    for symbol in lint.top_symbols(tree):
        lint.check_symbol(Path(filename), symbol, filename, found)
    return [item for item in found if item.rule == rule]


def chain_at(x0, radius, count, y=0.0):
    parts = []
    x = x0
    for index in range(count):
        parts.append(semicircle(x, radius, y=y, sign=1 if index % 2 == 0 else -1))
        x += 2 * radius
    return parts


class GenericLibraryTests(unittest.TestCase):
    MFG = '(property "MFG" "Murrelektronik" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'

    def test_manufacturer_part_in_iec_library_fails(self):
        text = symbol_library("86149", self.MFG)
        self.assertEqual(len(findings_for(text, "Transformer-IEC.kicad_sym", "generic-lib-manufacturer")), 1)

    def test_manufacturer_part_in_manufacturer_library_passes(self):
        text = symbol_library("86149", self.MFG)
        self.assertEqual(findings_for(text, "Transformer-Murrelektronik.kicad_sym", "generic-lib-manufacturer"), [])

    def test_generic_in_iec_library_passes(self):
        text = symbol_library("Transformer 1P")
        self.assertEqual(findings_for(text, "Transformer-IEC.kicad_sym", "generic-lib-manufacturer"), [])

    def test_manufacturer_library_is_locked(self):
        self.assertTrue(lint.locked(Path("symbol/Transformer-Murrelektronik.kicad_sym")))
        self.assertTrue(lint.locked(Path("symbol/Transformer-IEC.kicad_sym")))
        self.assertFalse(lint.locked(Path("symbol/Relay-IEC.kicad_sym")))


class DatasheetTests(unittest.TestCase):
    MURR = r"^https://shop\.murrelektronik\.com/index\.php\?anid=\d+_\d+&cl=details&fnc=outputSpecSheet"

    def test_empty_and_tilde_pass(self):
        self.assertTrue(lint.datasheet_ok(""))
        self.assertTrue(lint.datasheet_ok("~"))

    def test_pdf_passes(self):
        self.assertTrue(lint.datasheet_ok("https://cdn.automationdirect.com/static/specs/cutsheet/86149_cutsheet.pdf"))
        self.assertTrue(lint.datasheet_ok("https://rexel-cdn.com/Products/Allen-Bradley/700-HA33A1.pdf?i=6B33"))

    def test_product_page_fails(self):
        # The first 86149 symbol pointed here. It is the shop page, not the PDF.
        self.assertFalse(lint.datasheet_ok("https://shop.murrelektronik.com/86149"))
        self.assertFalse(lint.datasheet_ok("https://www.murrelektronik.com"))
        self.assertFalse(lint.datasheet_ok("https://www.murrelektronik.com/"))

    def test_text_is_not_a_url(self):
        self.assertFalse(lint.datasheet_ok("700-HL Solid State Relay Output"))

    def test_approved_download_passes(self):
        url = "https://shop.murrelektronik.com/index.php?anid=000000000000086149_1&cl=details&fnc=outputSpecSheet&lang=1"
        self.assertFalse(lint.datasheet_ok(url, []))
        self.assertTrue(lint.datasheet_ok(url, [self.MURR]))

    def test_rule_reports_symbol(self):
        props = '(property "Datasheet" "https://shop.murrelektronik.com/86149" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
        text = symbol_library("Fixture", props)
        self.assertEqual(len(findings_for(text, "fixture.kicad_sym", "datasheet-document")), 1)


class WindingGapTests(unittest.TestCase):
    def body(self, gap):
        # Two four-curl windings on one baseline, gap mm of empty line between.
        first = chain_at(0.0, 0.635, 4)
        second = chain_at(5.08 + gap, 0.635, 4)
        return "\n".join(first + second)

    def test_one_grid_step_passes(self):
        text = symbol_library("Fixture", body=self.body(5.08))
        self.assertEqual(findings_for(text, "fixture.kicad_sym", "winding-gap"), [])

    def test_two_grid_steps_fail(self):
        # The first Control Transformer 1P left 10.16 mm between 3 and 4.
        text = symbol_library("Fixture", body=self.body(10.16))
        found = findings_for(text, "fixture.kicad_sym", "winding-gap")
        self.assertEqual(len(found), 1)
        self.assertIn("10.16", found[0].where)

    def test_windings_on_different_lines_pass(self):
        first = chain_at(0.0, 0.635, 4)
        second = chain_at(25.4, 0.635, 4, y=-7.62)
        text = symbol_library("Fixture", body="\n".join(first + second))
        self.assertEqual(findings_for(text, "fixture.kicad_sym", "winding-gap"), [])

    def test_exception_allows_gap(self):
        props = '(property "ki_winding_gap" "10.16 reason: fixture" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
        text = symbol_library("Fixture", props, self.body(10.16))
        self.assertEqual(findings_for(text, "fixture.kicad_sym", "winding-gap"), [])

    def test_exception_without_reason_is_reported(self):
        props = '(property "ki_winding_gap" "10.16" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'
        text = symbol_library("Fixture", props, self.body(10.16))
        self.assertEqual(len(findings_for(text, "fixture.kicad_sym", "winding-gap")), 1)
        self.assertEqual(len(findings_for(text, "fixture.kicad_sym", "suppress-missing-reason")), 1)


class ControlTransformerTests(unittest.TestCase):
    """Regression checks on the redrawn control transformer."""

    def pins(self, lib, name):
        path = lint.ROOT / "symbol" / lib
        tree = lint.parse(path.read_text())
        for symbol in lint.top_symbols(tree):
            if symbol[1] == name:
                found = {}
                for pin in lint.pins_of(symbol):
                    at = lint.kid(pin, "at")
                    found[lint.atom(lint.kid(pin, "number"), 1)] = (float(at[1]), float(at[2]))
                return found
        self.fail(f"{name} not in {lib}")

    def test_secondary_reads_9_10_11_12(self):
        # Murrelektronik crosses the inner leads, so 10 sits between 9 and 11.
        for lib, name in (
            ("Transformer-Murrelektronik.kicad_sym", "MST_208-550_2x115"),
            ("Transformer-IEC.kicad_sym", "Control Transformer 1P"),
        ):
            pins = self.pins(lib, name)
            xs = [pins[n][0] for n in ("9", "10", "11", "12")]
            self.assertEqual(xs, sorted(xs), name)

    def test_no_manufacturer_part_in_transformer_iec(self):
        text = (lint.ROOT / "symbol" / "Transformer-IEC.kicad_sym").read_text()
        self.assertNotIn('(property "MFG"', text)
        self.assertNotIn('(property "MPN"', text)


def pin_text(x, y, angle, number):
    return (f'(pin bidirectional line (at {x} {y} {angle}) (length 3.81) '
            f'(name "~" (effects (font (size 1.27 1.27)))) '
            f'(number "{number}" (effects (font (size 1.27 1.27)))))')


class TerminalRowTests(unittest.TestCase):
    ROWS = '(property "ki_terminal_rows" "1 2 PE; 9 10 11" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))'

    def text(self, pins, props=None):
        return symbol_library("Fixture", self.ROWS if props is None else props, "\n".join(pins))

    def found(self, pins, props=None):
        return findings_for(self.text(pins, props), "fixture.kicad_sym", "terminal-row")

    def good(self):
        return [
            pin_text(-5.08, 10.16, 270, "1"), pin_text(0, 10.16, 270, "2"),
            pin_text(5.08, 10.16, 270, "PE"),
            pin_text(-5.08, -10.16, 90, "9"), pin_text(0, -10.16, 90, "10"),
            pin_text(5.08, -10.16, 90, "11"),
        ]

    def test_pe_in_the_row_passes(self):
        self.assertEqual(self.found(self.good()), [])

    def test_pe_off_to_the_side_fails(self):
        # The first MST drawing had PE on the right at y=0, pointing left.
        pins = self.good()
        pins[2] = pin_text(10.16, 0, 180, "PE")
        found = self.found(pins)
        self.assertEqual(len(found), 1)
        self.assertIn(":PE", found[0].where)

    def test_pe_lower_but_same_direction_fails(self):
        pins = self.good()
        pins[2] = pin_text(5.08, 5.08, 270, "PE")
        self.assertEqual(len(self.found(pins)), 1)

    def test_out_of_order_fails(self):
        # 9, 11, 10, 12 side by side reads differently from the strip.
        pins = self.good()
        pins[4] = pin_text(5.08, -10.16, 90, "10")
        pins[5] = pin_text(0, -10.16, 90, "11")
        found = self.found(pins)
        self.assertEqual([f.where for f in found], ["Fixture#row2:order"])

    def test_missing_pin_fails(self):
        self.assertEqual(len(self.found(self.good()[:5])), 1)

    def test_no_property_is_not_checked(self):
        pins = self.good()
        pins[2] = pin_text(10.16, 0, 180, "PE")
        self.assertEqual(self.found(pins, props=""), [])

    def test_real_transformers_declare_rows(self):
        for lib, name in (
            ("Transformer-Murrelektronik.kicad_sym", "MST_208-550_2x115"),
            ("Transformer-IEC.kicad_sym", "Control Transformer 1P"),
        ):
            tree = lint.parse((lint.ROOT / "symbol" / lib).read_text())
            symbol = [s for s in lint.top_symbols(tree) if s[1] == name][0]
            self.assertIn("PE", lint.prop_value(symbol, "ki_terminal_rows"))
            self.assertEqual(lint.terminal_row_findings(symbol, name), [])


if __name__ == "__main__":
    unittest.main()
