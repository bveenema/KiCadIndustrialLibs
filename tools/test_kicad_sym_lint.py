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


if __name__ == "__main__":
    unittest.main()
