# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for chzzk CLI."""

import platform
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Determine output name based on platform
system = platform.system().lower()
if system == "linux":
    exe_name = "chzzk-linux"
elif system == "windows":
    exe_name = "chzzk-windows"
elif system == "darwin":
    exe_name = "chzzk-macos"
else:
    exe_name = f"chzzk-{system}"

# Collect hidden imports for all required packages
hidden_imports = [
    # CLI framework
    *collect_submodules("typer"),
    *collect_submodules("click"),
    # Rich console
    *collect_submodules("rich"),
    # Textual TUI
    *collect_submodules("textual"),
    # HTTP client
    *collect_submodules("httpx"),
    *collect_submodules("httpcore"),
    # WebSocket
    *collect_submodules("websockets"),
    *collect_submodules("websocket"),
    # Socket.IO
    *collect_submodules("socketio"),
    *collect_submodules("engineio"),
    # Data validation
    *collect_submodules("pydantic"),
    *collect_submodules("pydantic_core"),
    # Async support
    *collect_submodules("anyio"),
    # SSL certificates
    "certifi",
    # Encoding
    "idna",
    # Environment variables
    "dotenv",
    # Markdown for textual
    "markdown_it",
]

# Collect data files
datas = [
    # SSL certificates
    *collect_data_files("certifi"),
    # Textual CSS and themes
    *collect_data_files("textual"),
]

# Add app.tcss from chzzk CLI
tcss_path = Path("src/chzzk/cli/tui/styles/app.tcss")
if tcss_path.exists():
    datas.append((str(tcss_path), "chzzk/cli/tui/styles"))

# Excluded modules to reduce binary size
excludes = [
    "tkinter",
    "_tkinter",
    "unittest",
    "email",
    "xml",
    "pydoc",
    "doctest",
    "argparse",
    "difflib",
    "inspect",
    "pdb",
    "profile",
    "pstats",
    "calendar",
    "gettext",
    # "pickle",  # Required by multiprocessing (used by prompt_toolkit)
    "PIL",
    "numpy",
    "pandas",
    "matplotlib",
    "scipy",
    "test",
    "tests",
]

a = Analysis(
    ["src/chzzk/cli/main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
