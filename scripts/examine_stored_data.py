#!/usr/bin/env python3
"""Utility to examine existing stored data without making API calls."""

import json
from pathlib import Path

import pandas as pd


def process_file(file_path: Path, base_path: Path) -> None:
    """Process a single stored data file and display its information."""
    print(f"\n📄 Examining: {file_path.relative_to(base_path)}")

    try:
        # Load based on file extension
        if file_path.suffix == ".json":
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        else:  # .parquet
            df = pd.read_parquet(file_path)

        # Show file stats
        file_size_kb = file_path.stat().st_size / 1024
        print(f"   Records: {len(df)}")
        print(f"   📅 Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"   💾 File size: {file_size_kb:.1f} KB")
        print(f"   📋 Columns: {list(df.columns)}")

        # Show latest values if numeric columns exist
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            display_latest_values(df)

    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"   Error loading file: {e}")


def display_latest_values(df) -> None:
    """Display the latest values for financial columns."""
    latest_row = df.iloc[-1]
    print("   💰 Latest values:")
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        if col in latest_row:
            value = latest_row[col]
            if col == "Volume":
                print(f"      {col}: {value:,.0f}")
            else:
                print(f"      {col}: ${value:.2f}")


def examine_stored_data():
    """Examine data that has already been stored locally."""

    base_path = Path("raw_data_output")

    if not base_path.exists():
        print("No stored data found in 'raw_data_output' directory")
        print("   Run 'python examine_data.py' first to fetch and store data")
        return

    print("🔍 Examining Stored Data (No API Calls)")
    print("=" * 45)

    # Find all stored files
    json_files = list(base_path.rglob("*.json"))
    parquet_files = list(base_path.rglob("*.parquet"))

    print(
        f"📁 Found {len(json_files)} JSON files and {len(parquet_files)} Parquet files"
    )

    # Examine each file
    for file_path in sorted(json_files + parquet_files):
        process_file(file_path, base_path)

    print("\nStored data examination complete!")
    print("This used 0 API calls - all data loaded from local files")


if __name__ == "__main__":
    examine_stored_data()
