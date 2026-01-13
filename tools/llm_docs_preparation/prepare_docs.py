# Copyright 2025 Thousand Brains Project
# Copyright 2024 Numenta Inc.
#
# Copyright may exist in Contributors' modifications
# and/or contributions to the work.
#
# Use of this source code is governed by the MIT
# license that can be found in the LICENSE file or at
# https://opensource.org/licenses/MIT.

import shutil
from pathlib import Path


def generate_tree(directory, prefix="", is_last=True, tree_lines=None):
    """Generate a tree structure of directories and markdown files.

    Args:
        directory: Path object of the directory to traverse
        prefix: String prefix for indentation
        is_last: Boolean indicating if this is the last item in current level
        tree_lines: List to accumulate tree lines

    Returns:
        List of strings representing the tree structure
    """
    if tree_lines is None:
        tree_lines = []

    # Get all items in directory, sorted (directories first, then files)
    items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))

    # Filter to only include directories and .md files
    items = [item for item in items if item.is_dir() or item.suffix == '.md']

    for i, item in enumerate(items):
        is_last_item = (i == len(items) - 1)
        connector = "└── " if is_last_item else "├── "
        tree_lines.append(f"{prefix}{connector}{item.name}")

        if item.is_dir():
            extension = "    " if is_last_item else "│   "
            generate_tree(item, prefix + extension, is_last_item, tree_lines)

    return tree_lines


def copy_markdown_files(source_dir, output_dir):
    """Copy all markdown files from source directory to output directory.

    Args:
        source_dir: Path to the source docs directory
        output_dir: Path to the output directory

    Returns:
        Number of files copied
    """
    count = 0
    for md_file in source_dir.rglob("*.md"):
        if md_file.is_file():
            shutil.copy2(md_file, output_dir / md_file.name)
            count += 1
    return count


def collect_markdown_content(directory, output_lines, depth=0, prefix=""):
    """Recursively collect markdown file contents organized by directory structure.

    Args:
        directory: Path object of the directory to traverse
        output_lines: List to accumulate output lines
        depth: Current depth in directory hierarchy
        prefix: String prefix for tree structure
    """
    # Get all items in directory, sorted (directories first, then files)
    items = sorted(directory.iterdir(), key=lambda x: (not x.is_dir(), x.name))

    # Filter to only include directories and .md files
    items = [item for item in items if item.is_dir() or item.suffix == '.md']

    for i, item in enumerate(items):
        is_last_item = (i == len(items) - 1)
        connector = "└── " if is_last_item else "├── "

        if item.is_file() and item.suffix == '.md':
            # Add tree entry
            output_lines.append(f"{prefix}{connector}{item.name}")
            output_lines.append("")

            # Add file content
            try:
                content = item.read_text(encoding='utf-8')
                output_lines.append(content)
                output_lines.append("")
                output_lines.append("=" * 80)
                output_lines.append("")
            except Exception as e:
                output_lines.append(f"Error reading file: {e}")
                output_lines.append("")

        elif item.is_dir():
            # Add directory entry
            output_lines.append(f"{prefix}{connector}{item.name}/")
            output_lines.append("")

            # Recurse into directory
            extension = "    " if is_last_item else "│   "
            collect_markdown_content(item, output_lines, depth + 1, prefix + extension)


def main():
    # Define paths relative to script location
    script_dir = Path(__file__).parent
    docs_dir = script_dir.parent.parent / "docs"
    output_dir = script_dir / "output"

    # Clear and recreate output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Copying markdown files from {docs_dir} to {output_dir}...")

    # Copy all markdown files (flattened)
    file_count = copy_markdown_files(docs_dir, output_dir)
    print(f"Copied {file_count} markdown files.")

    # Generate directory tree
    print("Generating index.txt...")
    tree_lines = ["docs/"]
    generate_tree(docs_dir, "", True, tree_lines)

    # Write index.txt
    index_file = output_dir / "index.txt"
    with index_file.open("w", encoding="utf-8") as f:
        f.write("\n".join(tree_lines))

    print(f"Index created at {index_file}")

    # Generate consolidated markdown file
    print("Generating consolidated_docs.md...")
    output_lines = [
        "# Thousand Brains Project - Complete Documentation",
        "",
        "This file contains all markdown documentation from the docs/ directory,",
        "organized by the directory structure.",
        "",
        "## Directory Structure",
        "",
    ]

    # Add the tree
    output_lines.extend(tree_lines)
    output_lines.append("")
    output_lines.append("=" * 80)
    output_lines.append("")
    output_lines.append("## Documentation Content")
    output_lines.append("")
    output_lines.append("docs/")
    output_lines.append("")

    # Collect all markdown content
    collect_markdown_content(docs_dir, output_lines)

    # Write consolidated file
    consolidated_file = output_dir / "CONSOLIDATED_DOCS.md"
    with consolidated_file.open("w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))

    print(f"Consolidated documentation created at {consolidated_file}")
    print("Done!")


if __name__ == "__main__":
    main()
