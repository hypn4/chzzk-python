#!/usr/bin/env python
"""Local build script for chzzk CLI executable."""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
)
logger = logging.getLogger(__name__)


def get_executable_name() -> str:
    """Get the expected executable name based on platform."""
    system = platform.system().lower()
    names = {
        "linux": "chzzk-linux",
        "windows": "chzzk-windows.exe",
        "darwin": "chzzk-macos",
    }
    return names.get(system, f"chzzk-{system}")


def clean_directories() -> None:
    """Clean previous build and dist directories."""
    root = Path(__file__).parent.parent
    build_dir = root / "build"
    dist_dir = root / "dist"

    for directory in [build_dir, dist_dir]:
        if directory.exists():
            logger.info("Cleaning %s...", directory)
            shutil.rmtree(directory)


def build_executable() -> Path | None:
    """Build the executable using PyInstaller."""
    root = Path(__file__).parent.parent
    spec_file = root / "chzzk.spec"

    if not spec_file.exists():
        logger.error("Error: %s not found", spec_file)
        return None

    logger.info("Building executable with PyInstaller...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", str(spec_file), "--clean"],
        cwd=root,
    )

    if result.returncode != 0:
        logger.error("Error: PyInstaller build failed")
        return None

    # Find the output executable
    dist_dir = root / "dist"
    exe_name = get_executable_name()
    exe_path = dist_dir / exe_name

    if exe_path.exists():
        return exe_path

    # Try without extension on Windows (in case .exe wasn't added)
    if platform.system().lower() == "windows":
        exe_path_no_ext = dist_dir / exe_name.replace(".exe", "")
        if exe_path_no_ext.exists():
            return exe_path_no_ext

    return None


def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def main() -> int:
    """Main build function."""
    logger.info("=== chzzk CLI Build Script ===\n")

    # Clean previous builds
    clean_directories()

    # Build executable
    exe_path = build_executable()

    if exe_path is None:
        logger.error("\nBuild failed!")
        return 1

    # Report results
    file_size = exe_path.stat().st_size
    logger.info("\n=== Build Complete ===")
    logger.info("Output: %s", exe_path)
    logger.info("Size: %s", format_size(file_size))

    # Quick verification
    logger.info("\nVerifying executable...")
    result = subprocess.run(
        [str(exe_path), "--version"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        logger.info("Version: %s", result.stdout.strip())
    else:
        logger.warning("Warning: Could not verify executable version")
        if result.stderr:
            logger.warning("stderr: %s", result.stderr.strip())

    return 0


if __name__ == "__main__":
    sys.exit(main())
