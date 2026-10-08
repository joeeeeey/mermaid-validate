import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import validate_mermaid as cli


class Behavior(unittest.TestCase):
    def test_multiple_fences_and_nested_example(self):
        md = "```markdown\n```mermaid\ngraph TD\n```\n~~~~mermaid\ngraph TD\n A-->B\n~~~~\n```mermaid\ngraph LR\n X-->Y\n```"
        self.assertEqual(len(cli.extract(md)), 2)

    def test_unclosed_fence(self):
        with self.assertRaises(ValueError):
            cli.extract("```mermaid\ngraph TD")

    def test_timeout(self):
        import subprocess

        with patch(
            "validate_mermaid.subprocess.run",
            side_effect=subprocess.TimeoutExpired("mmdc", 1),
        ):
            self.assertEqual(cli.render("graph TD", 1)[0], False)

    def test_renderer_failure(self):
        with patch(
            "validate_mermaid.subprocess.run",
            return_value=MagicMock(returncode=1, stderr="Parse error", stdout=""),
        ):
            self.assertEqual(cli.render("invalid", 1), (False, "Parse error"))

    def test_missing_svg_is_failure(self):
        with patch(
            "validate_mermaid.subprocess.run",
            return_value=MagicMock(returncode=0, stderr="", stdout=""),
        ):
            self.assertFalse(cli.render("graph TD", 1)[0])
