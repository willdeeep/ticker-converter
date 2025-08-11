#!/usr/bin/env python3
"""Utility to clean up old stored data files to keep only the latest."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class FileInfo:
    """Information about a parsed file."""

    key: str
    timestamp: datetime
    path: Path

    @classmethod
    def from_path(cls, file_path: Path) -> Optional["FileInfo"]:
        """Create FileInfo from file path if valid format.

        Args:
            file_path: Path to the file

        Returns:
            FileInfo instance or None if invalid format
        """
        filename = file_path.stem  # without extension
        parts = filename.split("_")

        if len(parts) >= 3:
            symbol = parts[0]
            data_type = parts[1]
            timestamp_str = "_".join(parts[2:])

            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                key = f"{symbol}_{data_type}_{file_path.suffix}"
                return cls(key=key, timestamp=timestamp, path=file_path)
            except ValueError:
                print(f"⚠️  Skipping file with unexpected format: {file_path.name}")

        return None


@dataclass
class CleanupStats:
    """Statistics from cleanup operation."""

    files_removed: int = 0
    space_saved_bytes: int = 0

    @property
    def space_saved_kb(self) -> float:
        """Space saved in kilobytes."""
        return self.space_saved_bytes / 1024


class DataCleaner:
    """Handles cleanup of old data files."""

    SUPPORTED_EXTENSIONS = {".json", ".parquet"}
    EXCLUDED_DIRS = {
        ".venv",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "htmlcov",
        "node_modules",
    }

    def __init__(self, base_path: Path):
        """Initialize cleaner with base directory.

        Args:
            base_path: Base directory to clean
        """
        self.base_path = base_path

    def find_data_files(self) -> list[Path]:
        """Find all data files in the directory."""
        data_files = []

        for file_path in self.base_path.rglob("*"):
            if (
                file_path.is_file()
                and file_path.suffix in self.SUPPORTED_EXTENSIONS
                and not any(part in self.EXCLUDED_DIRS for part in file_path.parts)
            ):
                data_files.append(file_path)

        return sorted(data_files)

    def group_files_by_type(self) -> dict[str, list[FileInfo]]:
        """Group files by symbol, data type, and extension."""
        file_groups = {}

        for file_path in self.find_data_files():
            file_info = FileInfo.from_path(file_path)
            if file_info:
                if file_info.key not in file_groups:
                    file_groups[file_info.key] = []
                file_groups[file_info.key].append(file_info)

        return file_groups

    def remove_old_files(self, file_groups: dict[str, list[FileInfo]]) -> CleanupStats:
        """Remove old files keeping only the latest for each group.

        Args:
            file_groups: Grouped files by type

        Returns:
            Cleanup statistics
        """
        stats = CleanupStats()

        for key, files in file_groups.items():
            if len(files) > 1:
                # Sort by timestamp (newest first)
                files.sort(key=lambda x: x.timestamp, reverse=True)

                # Keep the newest, remove the rest
                latest_file = files[0]
                old_files = files[1:]

                print(f"\n📁 {key}:")
                print(f"   Keeping: {latest_file.path.name}")

                for old_file in old_files:
                    file_size = old_file.path.stat().st_size
                    size_kb = file_size / 1024
                    print(f"   Removing: {old_file.path.name} ({size_kb:.1f} KB)")

                    old_file.path.unlink()
                    stats.files_removed += 1
                    stats.space_saved_bytes += file_size

        return stats

    def show_directory_status(self) -> None:
        """Display current directory status after cleanup."""
        print("\nCurrent directory status:")
        remaining_files = self.find_data_files()

        for file_path in remaining_files:
            size_kb = file_path.stat().st_size / 1024
            relative_path = file_path.relative_to(self.base_path)
            print(f"   📄 {relative_path} ({size_kb:.1f} KB)")

    def cleanup(self) -> None:
        """Perform complete cleanup operation."""
        print("🧹 Cleaning Up Old Data Files")
        print("=" * 35)

        # Group files by symbol and data type
        file_groups = self.group_files_by_type()

        if not file_groups:
            print("No data files found to clean up.")
            return

        # Remove old files
        stats = self.remove_old_files(file_groups)

        # Show results
        if stats.files_removed == 0:
            print("No old files found - directory is already clean!")
        else:
            print("\nCleanup complete!")
            print(f"   Files removed: {stats.files_removed}")
            print(f"   Space saved: {stats.space_saved_kb:.1f} KB")

        # Show current directory status
        self.show_directory_status()


def cleanup_old_files() -> None:
    """Keep only the most recent file for each symbol/data_type combination."""
    base_path = Path("raw_data_output")

    if not base_path.exists():
        print("No stored data found in 'raw_data_output' directory")
        return

    cleaner = DataCleaner(base_path)
    cleaner.cleanup()


if __name__ == "__main__":
    cleanup_old_files()
