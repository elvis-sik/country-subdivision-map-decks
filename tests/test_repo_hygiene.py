from __future__ import annotations

import json
import py_compile
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_PATH = "/" + str(Path("Users") / "elvis" / "Code" / "anki-studying")

SKIP_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".uv-cache",
    ".venv",
    ".venv-apkg",
    "__pycache__",
    "backups",
    "build",
    "coverage",
    "dist",
    "drafts",
    "input",
    "media",
    "node_modules",
    "out",
    "templates",
    "tmp",
}

SKIP_PREFIXES = {
    "data/derived/",
    "data/raw/",
    "polymath/",
}

PORTABLE_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".mjs",
    ".py",
    ".sh",
    ".toml",
    ".ts",
    ".yaml",
    ".yml",
}


def git_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return [Path(line) for line in result.stdout.splitlines() if line]


def is_skipped(path: Path) -> bool:
    as_posix = path.as_posix()
    return bool(SKIP_PARTS.intersection(path.parts)) or any(
        as_posix.startswith(prefix) for prefix in SKIP_PREFIXES
    )


def readable_text(path: Path) -> str | None:
    try:
        return (ROOT / path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


class RepositoryHygieneTest(unittest.TestCase):
    def test_readme_exists(self) -> None:
        self.assertTrue(
            any((ROOT / name).exists() for name in ("README.md", "README.rst", "README")),
            "repository should have a README",
        )

    def test_claude_imports_agents_when_present(self) -> None:
        agents = ROOT / "AGENTS.md"
        if not agents.exists():
            self.skipTest("AGENTS.md is not present")
        claude = ROOT / "CLAUDE.md"
        self.assertTrue(claude.exists(), "CLAUDE.md should exist when AGENTS.md exists")
        self.assertIn("@AGENTS.md", claude.read_text(encoding="utf-8"))

    def test_no_workspace_absolute_paths_in_portable_files(self) -> None:
        offenders: list[str] = []
        for path in git_files():
            if is_skipped(path) or path.suffix not in PORTABLE_SUFFIXES:
                continue
            text = readable_text(path)
            if text is not None and WORKSPACE_PATH in text:
                offenders.append(path.as_posix())

        self.assertEqual([], offenders, "portable files should use relative paths")

    def test_tracked_json_files_parse(self) -> None:
        for path in git_files():
            if is_skipped(path) or path.suffix != ".json":
                continue
            with self.subTest(path=path.as_posix()):
                text = readable_text(path)
                if text is None:
                    self.skipTest(f"{path} is not UTF-8 text")
                json.loads(text)

    def test_tracked_python_files_compile(self) -> None:
        for path in git_files():
            if is_skipped(path) or path.suffix != ".py":
                continue
            with self.subTest(path=path.as_posix()):
                py_compile.compile(str(ROOT / path), doraise=True)


def run_path_check() -> int:
    suite = unittest.TestSuite()
    suite.addTest(
        RepositoryHygieneTest("test_no_workspace_absolute_paths_in_portable_files")
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    if sys.argv[1:] == ["--path-only"]:
        raise SystemExit(run_path_check())
    unittest.main()
