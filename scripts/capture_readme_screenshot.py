from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import textwrap
import tomllib
from pathlib import Path


DEFAULT_OUT = Path("docs/screenshots/readme-preview.png")


PROBE_SOURCE = r'''
from __future__ import annotations

import json
import os
import traceback
from pathlib import Path

from aqt import gui_hooks, mw
from aqt.qt import QTimer, QVBoxLayout, QWidget
from aqt.webview import AnkiWebView

RESULT_ENV = "ANKI_ADDON_WORKBENCH_RESULT"
SCREENSHOT_ENV = "ANKI_ADDON_WORKBENCH_SCREENSHOT"
SETTLE_MS = 1800
PREVIEW_WINDOW = None


def _pick_card():
    col = mw.col
    if col is None:
        raise RuntimeError("collection is unavailable")

    best = None
    for card_id in col.db.list("select id from cards order by id"):
        card = col.get_card(card_id)
        question = card.question()
        answer = card.answer()
        haystack = f"{question}\n{answer}".lower()
        score = 0
        if "<img" in question.lower() or "<svg" in question.lower():
            score += 100
        if "map" in haystack or "locator" in haystack:
            score += 25
        if "<img" in answer.lower() or "<svg" in answer.lower():
            score += 10
        candidate = (score, -int(card_id), card)
        if best is None or candidate > best:
            best = candidate

    if best is None:
        raise RuntimeError("no cards found in collection")
    return best[2]


def _write_result(payload):
    result_path = os.environ.get(RESULT_ENV)
    if result_path:
        Path(result_path).write_text(
            json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
        )


def _capture(card):
    global PREVIEW_WINDOW
    screenshot_path = os.environ.get(SCREENSHOT_ENV)
    if not screenshot_path:
        raise RuntimeError(f"${SCREENSHOT_ENV} is not set")

    path = Path(screenshot_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pixmap = PREVIEW_WINDOW.grab()
    if not pixmap.save(str(path), "PNG"):
        raise RuntimeError(f"failed to save screenshot to {path}")

    _write_result(
        {
            "ok": True,
            "probe": "readme_card_screenshot",
            "screenshot": str(path),
            "card_id": int(card.id),
            "note_id": int(card.nid),
            "template_ord": int(card.ord),
            "size": {"width": int(pixmap.width()), "height": int(pixmap.height())},
        }
    )
    mw.unloadProfileAndExit()


def _show_card():
    global PREVIEW_WINDOW
    try:
        card = _pick_card()
        PREVIEW_WINDOW = QWidget(mw)
        PREVIEW_WINDOW.setWindowTitle("README card preview")
        PREVIEW_WINDOW.resize(1040, 780)
        layout = QVBoxLayout(PREVIEW_WINDOW)
        layout.setContentsMargins(0, 0, 0, 0)
        web = AnkiWebView(PREVIEW_WINDOW, title="README card preview")
        layout.addWidget(web)
        web.stdHtml(
            f'<main class="card card{int(card.ord) + 1}">{card.question()}</main>',
            context=mw.reviewer,
        )
        PREVIEW_WINDOW.show()
        QTimer.singleShot(SETTLE_MS, lambda: _capture(card))
    except Exception as exc:
        _write_result(
            {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        mw.unloadProfileAndExit()


gui_hooks.main_window_did_init.append(lambda: QTimer.singleShot(800, _show_card))
'''


def _load_workbench_table(root: Path) -> dict[str, object]:
    with (root / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    table = data.get("tool", {}).get("anki-addon-workbench")
    if not isinstance(table, dict):
        raise SystemExit("pyproject.toml is missing [tool.anki-addon-workbench]")
    return table


def _toml_string(value: str | Path) -> str:
    return json.dumps(str(value))


def _write_temp_config(repo_root: Path, temp_root: Path, out: Path) -> Path:
    table = _load_workbench_table(repo_root)
    probe_dir = temp_root / "readme_screenshot_probe"
    probe_dir.mkdir(parents=True)
    (probe_dir / "__init__.py").write_text(PROBE_SOURCE, encoding="utf-8")

    seed_apkgs = table.get("seed_apkgs", [])
    if not isinstance(seed_apkgs, list) or not seed_apkgs:
        raise SystemExit("workbench seed_apkgs must be configured")
    resolved_apkgs = [(repo_root / str(path)).resolve() for path in seed_apkgs]
    missing = [path for path in resolved_apkgs if not path.exists()]
    if missing:
        joined = "\n".join(str(path) for path in missing)
        raise SystemExit(f"APKGs are missing; run `make apkg` first:\n{joined}")

    project_name = str(table.get("project_name") or repo_root.name)
    anki_version = str(table.get("anki_version") or "25.09")
    config = textwrap.dedent(
        f"""
        project_name = {_toml_string(project_name)}
        seed_apkgs = [{", ".join(_toml_string(path) for path in resolved_apkgs)}]
        probe_addon = {_toml_string(probe_dir)}
        probe_package = "zz_readme_screenshot_probe"
        anki_version = {_toml_string(anki_version)}
        deck_smoke_render_limit = 3
        """
    ).strip()

    config_path = temp_root / "anki-workbench.toml"
    config_path.write_text(f"{config}\n", encoding="utf-8")
    return config_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture a README card screenshot with anki-addon-workbench."
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--timeout", type=int, default=60)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    out = (repo_root / args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="anki-readme-shot-") as temp:
        temp_root = Path(temp)
        _write_temp_config(repo_root, temp_root, out)
        command = [
            sys.executable,
            "-m",
            "anki_addon_workbench",
            "--config-root",
            str(temp_root),
            "smoke",
            "--screenshot",
            str(out),
            "--timeout",
            str(args.timeout),
        ]
        completed = subprocess.run(command, check=False, text=True)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
