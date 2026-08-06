#!/usr/bin/env python3
"""Validate this repo's composite action metadata.

actionlint cannot lint composite `action.yml` files - it parses them as
workflows and fails on the missing `on`/`jobs` sections - so the checks that
matter for this repo live here instead:

  1. Each `action.yml` is valid YAML with the keys a composite action needs.
  2. Every `run:` block is syntactically valid bash (`bash -n`). These actions
     are essentially one large shell script each, so this is the main guard.
  3. Every `inputs.<name>` referenced in a `run:` block is actually declared.
  4. Every `with:` key in the README's workflow examples is a real input.
     Catches the class of bug where the README documented `auto-commit`, which
     no action ever declared, so it was silently dropped at runtime.

Usage: python3 .github/scripts/validate-actions.py
Requires PyYAML.
"""

import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
ACTIONS = {
    "action.yml": REPO / "action.yml",
    "review/action.yml": REPO / "review" / "action.yml",
}
README = REPO / "README.md"

# `uses:` values in README examples mapped to the action whose inputs apply.
USES_TO_ACTION = {
    "mobb-dev/action": "action.yml",
    "./": "action.yml",
    "mobb-dev/action/review": "review/action.yml",
    "./review": "review/action.yml",
}

errors: list[str] = []


def error(msg: str) -> None:
    errors.append(msg)
    print(f"::error::{msg}")


def load_actions() -> dict[str, dict]:
    docs = {}
    for label, path in ACTIONS.items():
        if not path.is_file():
            error(f"{label}: file is missing")
            continue
        try:
            docs[label] = yaml.safe_load(path.read_text())
        except yaml.YAMLError as exc:
            error(f"{label}: invalid YAML: {exc}")
    return docs


def check_structure(label: str, doc: dict) -> None:
    for key in ("name", "description", "inputs", "outputs", "runs"):
        if key not in doc:
            error(f"{label}: missing top-level key '{key}'")
    runs = doc.get("runs") or {}
    if runs.get("using") != "composite":
        error(f"{label}: runs.using must be 'composite', got {runs.get('using')!r}")
    if not runs.get("steps"):
        error(f"{label}: runs.steps is empty")


def check_shell_syntax(label: str, doc: dict) -> None:
    """`bash -n` every run block. Note `${{ ... }}` is tolerated by bash's
    parser, so the expressions do not need to be stripped first."""
    for i, step in enumerate(doc.get("runs", {}).get("steps", [])):
        script = step.get("run")
        if not script:
            continue
        proc = subprocess.run(
            ["bash", "-n"], input=script, text=True, capture_output=True
        )
        if proc.returncode != 0:
            error(f"{label}: runs.steps[{i}].run is not valid bash: {proc.stderr.strip()}")
        else:
            print(f"ok  {label}: runs.steps[{i}].run parses as bash")


def check_input_references(label: str, doc: dict) -> None:
    declared = set(doc.get("inputs") or {})
    referenced = set()
    for step in doc.get("runs", {}).get("steps", []):
        blob = yaml.safe_dump(step)
        referenced.update(re.findall(r"inputs\.([A-Za-z0-9_-]+)", blob))
    for name in sorted(referenced - declared):
        error(f"{label}: references inputs.{name} but never declares it")
    for name in sorted(declared - referenced):
        error(f"{label}: declares input '{name}' but never uses it")
    if referenced and not (referenced - declared) and not (declared - referenced):
        print(f"ok  {label}: all {len(declared)} inputs declared and used")


def check_readme_examples(docs: dict[str, dict]) -> None:
    """Parse ```yaml blocks in the README and check `with:` keys against the
    inputs of whichever action the step `uses:`."""
    if not README.is_file():
        error("README.md is missing")
        return
    blocks = re.findall(r"```ya?ml\n(.*?)```", README.read_text(), re.S)
    checked = 0
    for block in blocks:
        try:
            doc = yaml.safe_load(block)
        except yaml.YAMLError as exc:
            error(f"README.md: example is not valid YAML: {exc}")
            continue
        if not isinstance(doc, dict):
            continue
        for job in (doc.get("jobs") or {}).values():
            for step in (job or {}).get("steps") or []:
                if not isinstance(step, dict):
                    continue
                uses = str(step.get("uses", ""))
                target = USES_TO_ACTION.get(uses.split("@")[0].rstrip("/") or uses)
                if target is None or target not in docs:
                    continue
                declared = set(docs[target].get("inputs") or {})
                for key in step.get("with") or {}:
                    if key not in declared:
                        error(
                            f"README.md: example passes '{key}' to {uses}, which "
                            f"{target} does not declare as an input"
                        )
                checked += 1
    print(f"ok  README.md: checked `with:` keys of {checked} example step(s)")


def main() -> int:
    docs = load_actions()
    for label, doc in docs.items():
        check_structure(label, doc)
        check_shell_syntax(label, doc)
        check_input_references(label, doc)
    check_readme_examples(docs)

    if errors:
        print(f"\n{len(errors)} problem(s) found.", file=sys.stderr)
        return 1
    print("\nAll composite action metadata checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
