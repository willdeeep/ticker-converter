#!/usr/bin/env python3
"""Utility to clean up old stored data files to keep only the latest."""

from datetime import datetime
from pathlib import Path


def parse_file_info(file_path: Path) -> tuple[str, datetime] | None:
    """Parse file information to extract symbol, data type, and timestamp."""
    filename = file_path.stem  # without extension
    parts = filename.split("_")

    if len(parts) >= 3:
        symbol = parts[0]
        data_type = parts[1]
        timestamp_str = "_".join(parts[2:])

        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            key = f"{symbol}_{data_type}_{file_path.suffix}"
            return key, timestamp
        except ValueError:
            print(f"⚠️  Skipping file with unexpected format: {file_path.name}")

    return None


def group_files_by_type(base_path: Path) -> dict[str, list[tuple[datetime, Path]]]:
    """Group files by symbol, data type, and extension."""
    file_groups = {}

    for file_path in base_path.rglob("*"):
        if file_path.is_file() and file_path.suffix in [".json", ".parquet"]:
            file_info = parse_file_info(file_path)
            if file_info:
                key, timestamp = file_info
                if key not in file_groups:
                    file_groups[key] = []
                file_groups[key].append((timestamp, file_path))

    return file_groups


def remove_old_files(file_groups: dict) -> tuple[int, int]:
    """Remove old files keeping only the latest for each group."""
    files_removed = 0
    space_saved = 0

    for key, files in file_groups.items():
        if len(files) > 1:
            # Sort by timestamp (newest first)
            files.sort(key=lambda x: x[0], reverse=True)

            # Keep the newest, remove the rest
            latest_file = files[0][1]
            old_files = [f[1] for f in files[1:]]

            print(f"\n📁 {key}:")
            print(f"   Keeping: {latest_file.name}")

            for old_file in old_files:
                file_size = old_file.stat().st_size
                print(f"   Removing: {old_file.name} ({file_size/1024:.1f} KB)")
                old_file.unlink()
                files_removed += 1
                space_saved += file_size

    return files_removed, space_saved


def show_directory_status(base_path: Path) -> None:
    """Display current directory status after cleanup."""
    print("\nCurrent directory status:")
    remaining_files = [f for f in base_path.rglob("*") if f.is_file()]

    for file_path in sorted(remaining_files):
        size_kb = file_path.stat().st_size / 1024
        print(f"   📄 {file_path.relative_to(base_path)} ({size_kb:.1f} KB)")


def cleanup_old_files():
    """Keep only the most recent file for each symbol/data_type combination."""
    base_path = Path("raw_data_output")

    if not base_path.exists():
        print("No stored data found in 'raw_data_output' directory")
        return

    print("🧹 Cleaning Up Old Data Files")
    print("=" * 35)

    # Group files by symbol and data type
    file_groups = group_files_by_type(base_path)

    # Remove old files
    files_removed, space_saved = remove_old_files(file_groups)

    if files_removed == 0:
        print("No old files found - directory is already clean!")
    else:
        print("\nCleanup complete!")
        print(f"   Files removed: {files_removed}")
        print(f"   Space saved: {space_saved/1024:.1f} KB")

    # Show current directory status
    show_directory_status(base_path)


if __name__ == "__main__":
    cleanup_old_files()
