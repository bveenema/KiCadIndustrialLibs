#!/usr/bin/env python3
"""Symbol rules for KiCadIndustrialLibs.

Checks .kicad_sym libraries for the symbol rules used on new IEC parts:
reference and value centered at 0,0; keywords filled in; descriptions that
do not mention where a symbol came from; pins on a 200 mil (5.08 mm) grid,
150 mil (3.81 mm) long, bidirectional, with numbers shown and the inner end
on the body; manufacturer parts extend a generic symbol in the same library.

Existing violations are listed in tools/kicad-sym-lint-baseline.txt and do
not fail the run. symbol/Transformer-IEC.kicad_sym is never grandfathered
and cannot be suppressed.

    python tools/kicad_sym_lint.py [files...]
    python tools/kicad_sym_lint.py --write-baseline

Exit 1 when any error is not suppressed and not in the baseline.
"""
import argparse
import math
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("kicad_sym_lint needs PyYAML. pip install pyyaml")

GRID = 5.08  # 200 mil
PIN_STD = 3.81  # 150 mil
PIN_IO = 7.62  # 300 mil, PLC and panel IO cards
EPS = 0.02
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
NEW_LIB = "Transformer-IEC.kicad_sym"

RULES = (
    "parse",
    "field-center",
    "pin-grid",
    "pin-length",
    "keywords",
    "description",
    "extends-parent",
    "pin-number-visible",
    "pin-end-on-body",
    "pin-bidirectional",
)

MESSAGES = {
    "parse": "This library is not valid KiCad s-expression and was not checked.",
    "field-center": "Put Reference and Value at 0,0.",
    "pin-grid": "Move this pin onto the 5.08 mm (200 mil) grid.",
    "pin-length": "Pin length must be 3.81 mm (150 mil). PLC and panel IO symbols may use 7.62 mm (300 mil).",
    "keywords": "Fill in ki_keywords.",
    "description": "Write a description, and do not say what the symbol was derived from.",
    "extends-parent": "A manufacturer symbol extends a generic symbol in the same library. The parent has to exist.",
    "pin-number-visible": "Show pin numbers. Do not hide pin_numbers.",
    "pin-end-on-body": "The inner end of this pin does not meet the symbol body.",
    "pin-bidirectional": "Use bidirectional pins rather than passive, input, or output.",
    "suppress-missing-reason": "A kicad-sym-lint suppression has no reason.",
}

DERIVED_RE = re.compile(
    r"\b(derived from|extends|based on|copied from|upstream of|cloned from)\b",
    re.I,
)
SUPPRESS_RE = re.compile(
    r"kicad-sym-lint:\s*suppress\s+([a-z0-9-]+)(?:\s+reason:\s*([^\n\"]+))?",
    re.I,
)
IO_LIB = re.compile(r"^(PLC|Panel)(-|$)", re.I)


def tokenize(text):
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()":
            yield c
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n and text[j] != '"':
                if text[j] == "\\" and j + 1 < n:
                    buf.append(text[j + 1])
                    j += 2
                else:
                    buf.append(text[j])
                    j += 1
            yield ("S", "".join(buf))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in " \t\r\n()":
                j += 1
            yield text[i:j]
            i = j


def parse(text):
    stack = [[]]
    for tok in tokenize(text):
        if tok == "(":
            stack.append([])
        elif tok == ")":
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(tok[1] if isinstance(tok, tuple) else tok)
    if len(stack) != 1 or not stack[0]:
        raise ValueError("unbalanced s-expression")
    return stack[0][0]


def kids(node, name):
    return [c for c in node[1:] if isinstance(c, list) and c and c[0] == name]


def kid(node, name):
    found = kids(node, name)
    return found[0] if found else None


def atom(node, index, default=""):
    if node is None or len(node) <= index:
        return default
    return node[index]


def fnum(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def prop_value(node, name):
    for prop in kids(node, "property"):
        if len(prop) > 2 and prop[1] == name:
            return prop[2] if isinstance(prop[2], str) else ""
    return ""


def prop_node(node, name):
    for prop in kids(node, "property"):
        if len(prop) > 2 and prop[1] == name:
            return prop
    return None


def on_grid(value):
    return abs(value / GRID - round(value / GRID)) * GRID < 0.01


def near(a, b, tol=0.05):
    return abs(a - b) <= tol


class Finding:
    def __init__(self, rule, path, where):
        self.rule = rule
        self.path = path
        self.where = where

    @property
    def message(self):
        return MESSAGES[self.rule]

    def key(self):
        return f"{self.rule}\t{self.path}\t{self.where}"

    def format(self):
        return f"{self.rule}\t{self.path}\t{self.where}\t{self.message}"


def load_config(path):
    data = {}
    if path.is_file():
        data = yaml.safe_load(path.read_text()) or {}
    severity = {rule: "error" for rule in RULES}
    for rule, level in (data.get("severity") or {}).items():
        if rule in severity and level in ("error", "warn", "off"):
            severity[rule] = level
    suppress = []
    for item in data.get("suppress") or []:
        if isinstance(item, dict):
            suppress.append(item)
    return severity, suppress


def load_baseline(path):
    keys = set()
    if not path.is_file():
        return keys
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 3:
            keys.add("\t".join(parts[:3]))
    return keys


def reason_ok(reason):
    return bool(reason and str(reason).strip())


def file_suppressions(text):
    found = []
    for match in SUPPRESS_RE.finditer(text):
        found.append((match.group(1), (match.group(2) or "").strip(), match.start()))
    return found


def symbol_spans(text):
    spans = []
    for match in re.finditer(r'\(symbol\s+"([^"]+)"', text):
        name = match.group(1)
        if re.search(r"_\d+_\d+$", name):
            continue
        start = match.start()
        depth = 0
        i = start
        in_str = False
        while i < len(text):
            c = text[i]
            if in_str:
                if c == "\\":
                    i += 2
                    continue
                if c == '"':
                    in_str = False
                i += 1
                continue
            if c == '"':
                in_str = True
            elif c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    spans.append((name, start, i + 1))
                    break
            i += 1
    return spans


def top_symbols(tree):
    if not isinstance(tree, list):
        return []
    return [c for c in tree[1:] if isinstance(c, list) and c and c[0] == "symbol"]


def is_unit(name):
    return bool(re.search(r"_\d+_\d+$", name))


def rel(path):
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def locked(path):
    return path.name == NEW_LIB or path.as_posix().endswith("/" + NEW_LIB) or str(path).endswith(NEW_LIB)


def pin_inner(x, y, length, angle):
    """Body end of a KiCad pin. `at` is the connection point; the pin is drawn
    from there along `angle` (0 = +x, 90 = +y) into the body.
    """
    rad = math.radians(angle)
    return (x + length * math.cos(rad), y + length * math.sin(rad))


def body_primitives(symbol):
    segs = []

    def add_rect(x1, y1, x2, y2):
        pts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            segs.append(("seg", a, b))

    def walk(node):
        if not isinstance(node, list) or not node:
            return
        kind = node[0]
        if kind == "rectangle":
            start, end = kid(node, "start"), kid(node, "end")
            if start is not None and end is not None:
                add_rect(fnum(start[1]), fnum(start[2]), fnum(end[1]), fnum(end[2]))
        elif kind == "polyline":
            pts = kid(node, "pts")
            if pts is not None:
                xy = [(fnum(p[1]), fnum(p[2])) for p in kids(pts, "xy")]
                for a, b in zip(xy, xy[1:]):
                    segs.append(("seg", a, b))
        elif kind == "circle":
            center, radius = kid(node, "center"), kid(node, "radius")
            if center is not None and radius is not None:
                segs.append(("circle", (fnum(center[1]), fnum(center[2]), fnum(radius[1]))))
        elif kind == "arc":
            start, mid, end = kid(node, "start"), kid(node, "mid"), kid(node, "end")
            if start is not None and mid is not None and end is not None:
                segs.append((
                    "arc",
                    (fnum(start[1]), fnum(start[2])),
                    (fnum(mid[1]), fnum(mid[2])),
                    (fnum(end[1]), fnum(end[2])),
                ))
        if kind != "pin":
            for child in node[1:]:
                if isinstance(child, list):
                    walk(child)

    walk(symbol)
    return segs


def dist_point_seg(px, py, a, b):
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    denom = dx * dx + dy * dy
    if denom == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / denom))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def arc_samples(start, mid, end, steps=16):
    """Approximate a KiCad three-point arc. KiCad arcs are circular."""
    (x1, y1), (x2, y2), (x3, y3) = start, mid, end

    def circ(a, b, c):
        (ax, ay), (bx, by), (cx, cy) = a, b, c
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        if abs(d) < 1e-9:
            return None
        a2 = ax * ax + ay * ay
        b2 = bx * bx + by * by
        c2 = cx * cx + cy * cy
        ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
        uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
        return ux, uy, math.hypot(ax - ux, ay - uy)

    center = circ(start, mid, end)
    if center is None:
        return [start, mid, end]
    cx, cy, r = center
    if r < 1e-6:
        return [start, mid, end]
    a1 = math.atan2(y1 - cy, x1 - cx)
    a2 = math.atan2(y2 - cy, x2 - cx)
    a3 = math.atan2(y3 - cy, x3 - cx)

    def wrap(delta):
        while delta <= -math.pi:
            delta += 2 * math.pi
        while delta > math.pi:
            delta -= 2 * math.pi
        return delta

    # Travel start -> mid -> end, so the mid point picks the direction.
    d12 = wrap(a2 - a1)
    d23 = wrap(a3 - a2)
    total = d12 + d23
    pts = []
    for i in range(steps + 1):
        ang = a1 + total * (i / steps)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def near_body(point, prims, tol=0.6):
    if not prims:
        return False
    px, py = point
    for prim in prims:
        kind = prim[0]
        if kind == "seg":
            if dist_point_seg(px, py, prim[1], prim[2]) <= tol:
                return True
        elif kind == "circle":
            cx, cy, r = prim[1]
            if abs(math.hypot(px - cx, py - cy) - r) <= tol:
                return True
        elif kind == "arc":
            samples = arc_samples(prim[1], prim[2], prim[3])
            for a, b in zip(samples, samples[1:]):
                if dist_point_seg(px, py, a, b) <= tol:
                    return True
    return False


def hidden_pin_numbers(symbol):
    numbers = kid(symbol, "pin_numbers")
    if numbers is None:
        return False
    hide = kid(numbers, "hide")
    if hide is None:
        return False
    return atom(hide, 1, "yes") != "no"


def number_hidden(pin):
    number = kid(pin, "number")
    if number is None:
        return False
    effects = kid(number, "effects")
    if effects is None:
        return False
    return kid(effects, "hide") is not None


def at_origin(prop):
    at = kid(prop, "at")
    if at is None or len(at) < 3:
        return False
    if not near(fnum(at[1]), 0.0) or not near(fnum(at[2]), 0.0):
        return False
    if len(at) > 3 and not near(fnum(at[3]), 0.0):
        return False
    return True


def pins_of(symbol):
    found = []

    def walk(node):
        if not isinstance(node, list) or not node:
            return
        if node[0] == "pin":
            found.append(node)
            return
        for child in node[1:]:
            if isinstance(child, list):
                walk(child)

    walk(symbol)
    return found


def index_libraries(paths):
    index = {}
    for path in paths:
        try:
            tree = parse(path.read_text(errors="replace"))
        except ValueError:
            continue
        for symbol in top_symbols(tree):
            if len(symbol) > 1 and isinstance(symbol[1], str) and not is_unit(symbol[1]):
                index[(path, symbol[1])] = symbol
    return index


def check_symbol(path, symbol, where_file, findings):
    if len(symbol) < 2 or not isinstance(symbol[1], str):
        return
    name = symbol[1]
    if is_unit(name):
        return
    lib_name = path.stem
    extends = kid(symbol, "extends")
    parent_name = atom(extends, 1, "") if extends is not None else ""

    for field in ("Reference", "Value"):
        prop = prop_node(symbol, field)
        if prop is None or not at_origin(prop):
            findings.append(Finding("field-center", where_file, f"{name}#{field}"))

    keywords = prop_value(symbol, "ki_keywords").strip()
    if not keywords:
        findings.append(Finding("keywords", where_file, name))

    description = prop_value(symbol, "Description").strip()
    if not description or DERIVED_RE.search(description):
        findings.append(Finding("description", where_file, name))

    mpn = prop_value(symbol, "MPN").strip()
    mfg = prop_value(symbol, "MFG").strip()
    if mpn or mfg:
        if not parent_name:
            findings.append(Finding("extends-parent", where_file, name))
    if parent_name:
        # Filled in by the caller once the library index is known. Marker only.
        symbol_parent = (path, parent_name)
        if symbol_parent[1] == name:
            findings.append(Finding("extends-parent", where_file, name + "#self"))

    if hidden_pin_numbers(symbol):
        findings.append(Finding("pin-number-visible", where_file, name))

    prims = body_primitives(symbol)
    allow_io = PIN_IO if IO_LIB.match(lib_name) else None
    # The new transformer library is standard symbols: 150 mil only.
    if path.name == NEW_LIB:
        allow_io = None
    for pin in pins_of(symbol):
        at = kid(pin, "at")
        length = kid(pin, "length")
        number = kid(pin, "number")
        num = atom(number, 1, "?") if number is not None else "?"
        tag = f"{name}#{num}"
        if number_hidden(pin):
            findings.append(Finding("pin-number-visible", where_file, tag))
        ptype = atom(pin, 1, "")
        if ptype != "bidirectional":
            findings.append(Finding("pin-bidirectional", where_file, tag))
        if at is None or len(at) < 3:
            findings.append(Finding("pin-grid", where_file, tag))
            continue
        x, y = fnum(at[1]), fnum(at[2])
        if not on_grid(x) or not on_grid(y):
            findings.append(Finding("pin-grid", where_file, tag))
        if length is None:
            findings.append(Finding("pin-length", where_file, tag))
            continue
        plen = fnum(atom(length, 1))
        ok_len = near(plen, PIN_STD, 0.05) or (allow_io is not None and near(plen, allow_io, 0.05))
        if not ok_len:
            findings.append(Finding("pin-length", where_file, tag))
        angle = fnum(at[3]) if len(at) > 3 else 0.0
        inner = pin_inner(x, y, plen, angle)
        if prims and not near_body(inner, prims):
            findings.append(Finding("pin-end-on-body", where_file, tag))


def check_parents(path, symbols, where_file, findings):
    names = set()
    for symbol in symbols:
        if len(symbol) > 1 and isinstance(symbol[1], str):
            names.add(symbol[1])
    for symbol in symbols:
        if len(symbol) < 2 or not isinstance(symbol[1], str) or is_unit(symbol[1]):
            continue
        extends = kid(symbol, "extends")
        if extends is None:
            continue
        parent = atom(extends, 1, "")
        if parent not in names:
            findings.append(Finding("extends-parent", where_file, symbol[1]))


def check_file(path, findings):
    text = path.read_text(errors="replace")
    where = rel(path)
    try:
        tree = parse(text)
    except ValueError:
        findings.append(Finding("parse", where, path.name))
        return
    symbols = top_symbols(tree)
    for symbol in symbols:
        check_symbol(path, symbol, where, findings)
    check_parents(path, symbols, where, findings)


def where_symbol(where):
    return where.split("#", 1)[0]


def file_matches(wanted, path):
    wanted = str(wanted).replace("\\", "/").lstrip("./")
    path = str(path).replace("\\", "/")
    return path == wanted or path.endswith("/" + wanted)


def symbol_matches(wanted, where):
    return where_symbol(where) == wanted


def suppressed(finding, file_text, spans, yaml_suppress):
    # A broken file is always an error. Severity, baseline, and suppressions
    # cannot hide it.
    if finding.rule == "parse":
        return None
    if locked(Path(finding.path)):
        return None
    for item in yaml_suppress:
        if item.get("rule") != finding.rule:
            continue
        wanted_file = item.get("file")
        if wanted_file and not file_matches(wanted_file, finding.path):
            continue
        wanted_symbol = item.get("symbol")
        if wanted_symbol and not symbol_matches(wanted_symbol, finding.where):
            continue
        if not reason_ok(item.get("reason", "")):
            return "missing"
        return "yaml"
    for rule, reason, pos in file_suppressions(file_text):
        if rule != finding.rule:
            continue
        owner = None
        for name, start, end in spans:
            if start <= pos < end:
                owner = name
                break
        if owner and not symbol_matches(owner, finding.where):
            continue
        if not reason_ok(reason):
            return "missing"
        return "inline"
    return None


def default_paths():
    folder = ROOT / "symbol"
    return sorted(folder.glob("*.kicad_sym"))


def main():
    parser = argparse.ArgumentParser(description="KiCadIndustrialLibs symbol linter")
    parser.add_argument("files", nargs="*")
    parser.add_argument("--write-baseline", action="store_true")
    parser.add_argument("--config", default=str(HERE / "kicad-sym-lint.yaml"))
    parser.add_argument("--baseline", default=str(HERE / "kicad-sym-lint-baseline.txt"))
    args = parser.parse_args()
    severity, yaml_suppress = load_config(Path(args.config))
    baseline_path = Path(args.baseline)
    baseline = load_baseline(baseline_path)
    if args.files:
        paths = [Path(p) for p in args.files]
    else:
        paths = default_paths()
    findings = []
    for item in yaml_suppress:
        if item.get("rule") and not reason_ok(item.get("reason", "")):
            findings.append(Finding(
                "suppress-missing-reason",
                item.get("file") or "tools/kicad-sym-lint.yaml",
                item.get("rule") or "suppress",
            ))
    for path in paths:
        if path.suffix != ".kicad_sym" or not path.is_file():
            continue
        check_file(path, findings)
        text = path.read_text(errors="replace")
        for rule, reason, _pos in file_suppressions(text):
            if not reason_ok(reason):
                findings.append(Finding("suppress-missing-reason", rel(path), rule))
    if args.write_baseline:
        lines = [
            "# Existing violations. rule, path, where. Delete a line when you fix that one.",
            "# symbol/Transformer-IEC.kicad_sym is not listed and is not grandfathered.",
        ]
        for finding in findings:
            if finding.rule == "parse":
                continue
            if severity.get(finding.rule, "error") == "off":
                continue
            if finding.path.endswith(NEW_LIB):
                continue
            lines.append(finding.key())
        baseline_path.write_text("\n".join(lines) + "\n")
        print(f"wrote {len(lines) - 2} baseline entries to {baseline_path}")
        return 0
    texts = {}
    spans = {}
    errors = 0
    warned = 0
    kept = 0
    for finding in findings:
        level = "error" if finding.rule == "parse" else severity.get(finding.rule, "error")
        if level == "off":
            continue
        path = ROOT / finding.path if not Path(finding.path).is_absolute() else Path(finding.path)
        if path not in texts and path.is_file():
            texts[path] = path.read_text(errors="replace")
            spans[path] = symbol_spans(texts[path])
        how = suppressed(finding, texts.get(path, ""), spans.get(path, []), yaml_suppress)
        if how == "missing":
            extra = Finding("suppress-missing-reason", finding.path, finding.rule)
            print(extra.format(), file=sys.stderr)
            errors += 1
            continue
        if how:
            continue
        if finding.rule != "parse" and finding.key() in baseline and not finding.path.endswith(NEW_LIB):
            kept += 1
            continue
        print(f"{level}\t{finding.format()}", file=sys.stderr)
        if level == "error":
            errors += 1
        else:
            warned += 1
    if kept:
        print(f"kicad-sym-lint: {kept} baseline violation(s) not blocking")
    if errors:
        print(f"kicad-sym-lint: {errors} error(s), {warned} warning(s)", file=sys.stderr)
        return 1
    print(f"kicad-sym-lint: ok ({warned} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
