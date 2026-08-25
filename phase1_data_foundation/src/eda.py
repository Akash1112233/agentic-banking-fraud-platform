"""Chunked exploratory analysis for the IBM AML dataset."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from preprocess import read_transaction_chunks


ROOT = Path(__file__).resolve().parents[2]
RAW_TRANSACTIONS = ROOT / "data" / "raw" / "HI-Small_Trans.csv"
OUTPUT = ROOT / "phase1_data_foundation" / "outputs"


def run(transaction_path: Path = RAW_TRANSACTIONS, output_dir: Path = OUTPUT, chunksize: int = 250_000) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    counts = Counter()
    currencies = Counter()
    formats = Counter()
    hours = Counter()
    amount_by_label: dict[str, list[float]] = {"0": [], "1": []}
    total = 0
    amount_sum = 0.0
    amount_min = float("inf")
    amount_max = float("-inf")

    for chunk in read_transaction_chunks(str(transaction_path), chunksize=chunksize):
        total += len(chunk)
        labels = chunk["Is Laundering"].fillna(-1).astype(int).astype(str)
        counts.update(labels)
        currencies.update(chunk["Receiving Currency"].dropna().astype(str))
        formats.update(chunk["Payment Format"].dropna().astype(str))
        hours.update(chunk["Hour"].dropna().astype(int).astype(str))
        amounts = chunk["Amount Received"].dropna()
        if not amounts.empty:
            amount_sum += float(amounts.sum())
            amount_min = min(amount_min, float(amounts.min()))
            amount_max = max(amount_max, float(amounts.max()))
        for label in ("0", "1"):
            values = chunk.loc[labels == label, "Amount Received"].dropna().tolist()
            amount_by_label[label].extend(values[:20_000])

    summary = {
        "transaction_count": total,
        "label_counts": dict(counts),
        "laundering_rate": (counts.get("1", 0) / total) if total else 0.0,
        "receiving_currency_counts": dict(currencies),
        "payment_format_counts": dict(formats),
        "hour_counts": dict(sorted(hours.items(), key=lambda item: int(item[0]))),
        "amount_received": {
            "sum": amount_sum,
            "min": None if amount_min == float("inf") else amount_min,
            "max": None if amount_max == float("-inf") else amount_max,
        },
    }
    (output_dir / "reports").mkdir(exist_ok=True)
    (output_dir / "reports" / "eda_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    _bar(dict(counts), "AML label distribution", "Label (0=legitimate, 1=laundering)", output_dir / "figures" / "label_distribution.png")
    _bar(dict(formats), "Payment format distribution", "Payment format", output_dir / "figures" / "payment_formats.png", rotate=35)
    _bar(dict(hours), "Transactions by hour", "Hour of day", output_dir / "figures" / "transactions_by_hour.png")
    _hist(amount_by_label, "Amount received by label", "Amount received", output_dir / "figures" / "amount_by_label.png")
    return summary


def _bar(values: dict, title: str, xlabel: str, path: Path, rotate: int = 0) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = list(values)
    numbers = [values[label] for label in labels]
    plt.figure(figsize=(10, 5))
    plt.bar(labels, numbers)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Count")
    plt.xticks(rotation=rotate, ha="right" if rotate else "center")
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()


def _hist(values: dict[str, list[float]], title: str, xlabel: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(10, 5))
    for label, numbers in values.items():
        if numbers:
            plt.hist(numbers, bins=50, alpha=0.6, label=label)
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel("Sampled count")
    plt.legend(title="Is Laundering")
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--chunksize", type=int, default=250_000)
    args = parser.parse_args()
    summary = run(chunksize=args.chunksize)
    print(f"Analyzed {summary['transaction_count']:,} transactions")
    print(f"Laundering rate: {summary['laundering_rate']:.6%}")


if __name__ == "__main__":
    main()
