"""Chunked inspection of the IBM AML dataset."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "phase1_data_foundation" / "outputs" / "reports"


def inspect_csv(path: Path, chunk_size: int = 50_000) -> dict:
    row_count = 0
    missing = Counter()
    label_counts = Counter()
    sample_rows: list[dict[str, str]] = []
    with path.open("r", encoding="utf-8-sig", newline="", errors="replace") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        for row in reader:
            row_count += 1
            if len(sample_rows) < 5:
                sample_rows.append(dict(row))
            for key, value in row.items():
                if value is None or value.strip() == "":
                    missing[key] += 1
            if "Is Laundering" in row:
                label_counts[row["Is Laundering"]] += 1
    return {
        "file": str(path.relative_to(ROOT)),
        "size_bytes": path.stat().st_size,
        "columns": fieldnames,
        "row_count": row_count,
        "missing_values": dict(missing),
        "is_laundering_counts": dict(label_counts),
        "sample_rows": sample_rows,
    }


def inspect_patterns(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    begin = [line for line in lines if line.startswith("BEGIN LAUNDERING ATTEMPT")]
    end = [line for line in lines if line.startswith("END LAUNDERING ATTEMPT")]
    return {
        "file": str(path.relative_to(ROOT)),
        "size_bytes": path.stat().st_size,
        "line_count": len(lines),
        "pattern_count": len(begin),
        "pattern_headers": begin,
        "matching_end_markers": len(end),
    }


def run(output_path: Path | None = None) -> dict:
    report = {
        "transactions": inspect_csv(RAW / "HI-Small_Trans.csv"),
        "accounts": inspect_csv(RAW / "HI-Small_accounts.csv"),
        "patterns": inspect_patterns(RAW / "HI-Small_Patterns.txt"),
    }
    destination = output_path or OUTPUT / "dataset_inspection.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    report = run(args.output)
    for key, value in report.items():
        print(f"{key}: {value.get('row_count', value.get('pattern_count'))} records")


if __name__ == "__main__":
    main()
