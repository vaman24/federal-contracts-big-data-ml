#!/usr/bin/env python3
"""Validate committed notebook evidence without requiring Spark or cloud data."""

from __future__ import annotations

import ast
import csv
import json
import math
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
RESULTS_DIR = ROOT / "results"

EXPECTED_NOTEBOOKS = {
    "01_data_cleaning_and_feature_engineering.ipynb",
    "02_date_quality_validation.ipynb",
    "03_exploratory_data_analysis.ipynb",
    "04_offers_model_evaluation.ipynb",
    "05_award_value_model_training_and_evaluation.ipynb",
}

SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub token": re.compile(r"gh[pousr]_[A-Za-z0-9]{30,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "Google API key": re.compile(r"AIza[0-9A-Za-z_-]{35}"),
}


def source_text(cell: dict) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def is_notebook_magic(code: str) -> bool:
    """Return True for IPython/Dataproc magic cells that are not plain Python."""
    for line in code.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        return stripped.startswith(("%", "!"))
    return False


def validate_notebooks(errors: list[str]) -> None:
    found = {path.name for path in NOTEBOOK_DIR.glob("*.ipynb")}
    if found != EXPECTED_NOTEBOOKS:
        errors.append(
            "notebook inventory mismatch: "
            f"missing={sorted(EXPECTED_NOTEBOOKS - found)}, "
            f"unexpected={sorted(found - EXPECTED_NOTEBOOKS)}"
        )

    for path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        try:
            notebook = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON ({exc})")
            continue

        if notebook.get("nbformat") != 4:
            errors.append(f"{path.relative_to(ROOT)}: expected nbformat 4")

        serialized = json.dumps(notebook, ensure_ascii=False)
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(serialized):
                errors.append(f"{path.relative_to(ROOT)}: possible {label}")

        for index, cell in enumerate(notebook.get("cells", []), start=1):
            if cell.get("cell_type") != "code":
                continue

            code = source_text(cell)
            if code.strip() and not is_notebook_magic(code):
                try:
                    ast.parse(code, filename=f"{path.name}:cell-{index}")
                except SyntaxError as exc:
                    errors.append(
                        f"{path.relative_to(ROOT)} cell {index}: syntax error "
                        f"at line {exc.lineno}: {exc.msg}"
                    )

            for output in cell.get("outputs", []):
                if output.get("output_type") == "error":
                    errors.append(
                        f"{path.relative_to(ROOT)} cell {index}: committed error output"
                    )
                data = output.get("data", {})
                if any("sparkmonitor" in key.lower() for key in data):
                    errors.append(
                        f"{path.relative_to(ROOT)} cell {index}: Spark-monitor payload"
                    )


def read_csv(name: str, errors: list[str]) -> list[dict[str, str]]:
    path = RESULTS_DIR / name
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    except OSError as exc:
        errors.append(f"{path.relative_to(ROOT)}: cannot read ({exc})")
        return []

    if not rows:
        errors.append(f"{path.relative_to(ROOT)}: no metric rows")
    return rows


def close(actual: str, expected: float, tolerance: float = 1e-4) -> bool:
    try:
        return math.isclose(float(actual), expected, rel_tol=0.0, abs_tol=tolerance)
    except (TypeError, ValueError):
        return False


def validate_metrics(errors: list[str]) -> None:
    offers = read_csv("offers_model_metrics.csv", errors)
    selected_offer = next(
        (
            row
            for row in offers
            if row.get("split") == "test"
            and row.get("model") == "Decision Tree"
            and row.get("selected_on_validation", "").lower() == "true"
        ),
        None,
    )
    if selected_offer is None:
        errors.append("offers metrics: selected 2024 Decision Tree row is missing")
    else:
        if selected_offer.get("records") != "1656042":
            errors.append("offers metrics: unexpected 2024 test record count")
        if not close(selected_offer.get("mae", ""), 10.602442, 1e-6):
            errors.append("offers metrics: unexpected Decision Tree MAE")
        if not close(selected_offer.get("r2", ""), 0.933798, 1e-6):
            errors.append("offers metrics: unexpected Decision Tree R2")

    awards = read_csv("award_value_model_metrics.csv", errors)
    selected_award = next(
        (
            row
            for row in awards
            if row.get("split") == "test"
            and row.get("model") == "Linear Regression"
            and row.get("selected_on_validation", "").lower() == "true"
        ),
        None,
    )
    if selected_award is None:
        errors.append("award metrics: selected 2024 Linear Regression row is missing")
    elif not close(selected_award.get("r2", ""), 0.0016267983, 1e-9):
        errors.append("award metrics: unexpected Linear Regression R2")


def main() -> int:
    errors: list[str] = []
    validate_notebooks(errors)
    validate_metrics(errors)

    if errors:
        print("Portfolio validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        f"Validated {len(EXPECTED_NOTEBOOKS)} notebooks and both result tables: OK"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
