#!/usr/bin/env python3
"""Render Mermaid files or Markdown fences to validate syntax; no account required."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

VERSION = "12.0.0"


def extract(markdown):
    blocks = []
    fence = None
    body = []
    line_no = 0
    is_mermaid = False
    for i, line in enumerate(markdown.splitlines(), 1):
        if fence is None:
            m = re.match(r"^ {0,3}(`{3,}|~{3,})([^\r\n]*)$", line)
            if m:
                fence = m.group(1)
                is_mermaid = m.group(2).strip().lower() == "mermaid"
                body = []
                line_no = i + 1
        elif re.fullmatch(
            r" {0,3}" + re.escape(fence[0]) + r"{" + str(len(fence)) + r",}\s*", line
        ):
            if is_mermaid:
                blocks.append((line_no, "\n".join(body)))
            fence = None
        else:
            body.append(line)
    if fence and is_mermaid:
        raise ValueError("Unclosed Mermaid fence")
    return blocks


def render(text, timeout, executable=None, puppeteer_config=None):
    with tempfile.TemporaryDirectory(prefix="mermaid-validate-") as td:
        inp = Path(td) / "diagram.mmd"
        out = Path(td) / "diagram.svg"
        inp.write_text(text, encoding="utf-8")
        cmd = (
            [executable]
            if executable
            else [
                ("npx.cmd" if os.name == "nt" else "npx"),
                "-y",
                "@mermaid-js/mermaid-cli@" + VERSION,
            ]
        )
        cmd += ["-i", str(inp), "-o", str(out)]
        if puppeteer_config:
            cmd += ["-p", str(puppeteer_config)]
        try:
            p = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout, check=False
            )
        except subprocess.TimeoutExpired:
            return False, "Renderer timed out"
        except OSError:
            return False, "Renderer not found; install Node/npm or pass --mmdc"
        if p.returncode == 0 and out.exists() and out.stat().st_size > 0:
            return True, ""
        return False, (p.stderr or p.stdout or "No SVG was produced")[:4000]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--stdin", action="store_true")
    g.add_argument("--file", type=Path)
    g.add_argument("--markdown", type=Path)
    p.add_argument("--timeout", type=int, default=90)
    p.add_argument("--mmdc", help="Path to an installed mmdc executable")
    p.add_argument("--puppeteer-config", type=Path)
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    try:
        if a.timeout <= 0:
            raise ValueError("Timeout must be positive")
        text = (
            sys.stdin.read()
            if a.stdin
            else (a.file or a.markdown).read_text(encoding="utf-8")
        )
        diagrams = extract(text) if a.markdown else [(1, text)]
        if not diagrams or any(not t.strip() for _, t in diagrams):
            raise ValueError("No nonempty Mermaid diagrams found")
    except (OSError, ValueError) as e:
        print(str(e), file=sys.stderr)
        return 2
    results = []
    for line, text in diagrams:
        ok, error = render(text, a.timeout, a.mmdc, a.puppeteer_config)
        results.append({"line": line, "valid": ok, "error": error})
    if a.json:
        print(json.dumps(results, indent=2))
    else:
        for x in results:
            print(
                ("OK" if x["valid"] else "FAIL")
                + f" line {x['line']}"
                + (" " + x["error"] if x["error"] else "")
            )
    return 0 if all(x["valid"] for x in results) else 3


if __name__ == "__main__":
    raise SystemExit(main())
