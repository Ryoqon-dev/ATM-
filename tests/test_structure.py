"""Regression checks for layer boundaries and source-checkout execution."""
import ast
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src" / "atm_app"


class StructureTests(unittest.TestCase):
    def test_layer_dependencies_point_toward_domain(self):
        allowed = {
            "domain": {"domain", "shared"},
            "shared": {"shared"},
            "application": {"application", "domain", "shared"},
            "infrastructure": {"infrastructure", "domain", "shared"},
            "presentation": {"presentation", "application", "domain", "shared"},
        }
        for layer, dependencies in allowed.items():
            for path in (PACKAGE / layer).rglob("*.py"):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                package = path.parent.relative_to(ROOT / "src").parts
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom):
                        if node.level:
                            base = package[:len(package) - node.level + 1]
                            names = [".".join(base + tuple((node.module or "").split(".")))]
                        else:
                            names = [node.module or ""]
                    else:
                        continue
                    for name in names:
                        with self.subTest(path=path.name, dependency=name):
                            if name.startswith("atm_app."):
                                self.assertIn(name.split(".")[1], dependencies)
                            if layer != "presentation":
                                self.assertFalse(name == "tkinter" or name.startswith("tkinter."))

    def test_launcher_works_from_an_unrelated_directory(self):
        environment = dict(os.environ)
        environment.pop("PYTHONPATH", None)
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(ROOT / "run_atm.py"), "--check"],
                cwd=directory, env=environment, capture_output=True, text=True, encoding="utf-8",
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("3개", result.stdout)

    def test_bad_seed_check_fails_without_starting_gui(self):
        with tempfile.TemporaryDirectory() as directory:
            seed = Path(directory) / "broken.json"
            seed.write_text('{"accounts":[]}', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-X", "utf8", str(ROOT / "run_atm.py"), "--check", "--seed", str(seed)],
                cwd=directory, capture_output=True, text=True, encoding="utf-8",
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("초기화 실패", result.stderr)

    def test_source_package_has_no_legacy_layer_directories(self):
        self.assertFalse((ROOT / "atm_app").exists())
        self.assertFalse((PACKAGE / "ui").exists())
        self.assertFalse((PACKAGE / "services").exists())
        for layer in ("application", "domain", "presentation", "infrastructure", "shared"):
            self.assertTrue((PACKAGE / layer / "__init__.py").is_file())
