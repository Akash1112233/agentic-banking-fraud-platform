"""Run the complete Phase 1 data foundation workflow."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from eda import run as run_eda  # noqa: E402
from inspect_dataset import run as run_inspection  # noqa: E402


def main() -> None:
    print("Inspecting dataset files...")
    report = run_inspection()
    print(f"Transactions: {report['transactions']['row_count']:,}")
    print(f"Accounts: {report['accounts']['row_count']:,}")
    print(f"Patterns: {report['patterns']['pattern_count']:,}")
    print("Running chunked exploratory analysis...")
    summary = run_eda()
    print(f"Analyzed transactions: {summary['transaction_count']:,}")
    print(f"Laundering rate: {summary['laundering_rate']:.6%}")
    print("Phase 1 completed. Reports are in phase1_data_foundation/outputs/reports.")


if __name__ == "__main__":
    main()
