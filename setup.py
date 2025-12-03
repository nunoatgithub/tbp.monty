# Copyright 2025 Thousand Brains Project
# Copyright 2024 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

"""Setup script with protobuf code generation.

This setup script automatically generates Python code from .proto files during build.
To customize or extend:
1. Add new proto files to PROTO_CONFIG
2. Add new build steps to the pre_build_steps list
3. Modify protoc options in generate_protobuf_code()
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py


# ============================================================================
# Configuration - Modify these to customize protobuf generation
# ============================================================================

PROTO_CONFIG = {
    "proto_path": "src",
    "python_out": "src",
    "pyi_out": "src",
    "proto_files": [
        # Note: Order matters - compile dependencies first
        "src/tbp/monty/simulators/protocol/v1/basic_types.proto",
        "src/tbp/monty/simulators/protocol/v1/habitat.proto",
        "src/tbp/monty/simulators/protocol/v1/protocol.proto",
    ],
}


# ============================================================================
# Build Step Functions - Easy to extend with new build steps
# ============================================================================

def generate_protobuf_code(project_root: Path, config: dict) -> bool:
    """Generate Python code from .proto files.

    Args:
        project_root: Root directory of the project
        config: Dictionary with keys: proto_path, python_out, pyi_out, proto_files

    Returns:
        True if successful, False otherwise
    """
    proto_path = project_root / config["proto_path"]
    python_out = project_root / config["python_out"]
    pyi_out = project_root / config["pyi_out"]

    for proto_file_rel in config["proto_files"]:
        proto_file = project_root / proto_file_rel

        if not proto_file.exists():
            print(f"Warning: {proto_file_rel} not found, skipping", file=sys.stderr)
            continue

        print(f"Generating protobuf from {proto_file_rel}")

        # Build protoc command - modify flags here to customize generation
        cmd = [
            sys.executable,
            "-m",
            "grpc_tools.protoc",
            f"--proto_path={proto_path}",
            f"--python_out={python_out}",
            f"--pyi_out={pyi_out}",
            str(proto_file),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            print(f"Protoc error: {result.stderr}", file=sys.stderr)
            return False

        print(f"✓ Generated {proto_file.stem}_pb2.py")

    return True


# ============================================================================
# Build Hook - Register build steps here
# ============================================================================

def run_pre_build_steps(project_root: Path) -> None:
    """Run all pre-build steps.

    Add new build steps to this list to extend the build process.
    """
    pre_build_steps = [
        ("Protobuf code generation", lambda: generate_protobuf_code(project_root, PROTO_CONFIG)),
        # Add more build steps here as tuples: (description, callable)
        # Example: ("Custom step", lambda: my_custom_function(args)),
    ]

    for step_name, step_func in pre_build_steps:
        print(f"Running: {step_name}")
        if not step_func():
            print(f"Failed: {step_name}", file=sys.stderr)
            sys.exit(1)


class BuildPyCommand(_build_py):
    """Custom build command that runs pre-build steps."""

    def run(self):
        """Run pre-build steps, then continue with standard build."""
        run_pre_build_steps(Path(__file__).parent)
        super().run()


# ============================================================================
# Setup
# ============================================================================

setup(
    cmdclass={
        'build_py': BuildPyCommand,
    },
)

