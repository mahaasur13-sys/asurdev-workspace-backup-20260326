#!/usr/bin/env python3
"""
Archive or remove the duplicate asurdev/ directory.

Usage:
    python archive_asurdev.py [--dry-run] [--delete] [--backup-dir PATH]

Options:
    --dry-run      Only show what would be done, without making changes.
    --delete       Permanently delete the asurdev/ folder (no backup).
    --backup-dir   Destination for archive (default: ./archived).
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Remove duplicate asurdev/ folder.")
    parser.add_argument("--dry-run", action="store_true", help="Show actions without executing.")
    parser.add_argument("--delete", action="store_true", help="Permanently delete the folder (no archive).")
    parser.add_argument("--backup-dir", default="archived", help="Directory to store archived copies (default: archived).")
    args = parser.parse_args()

    project_root = Path.cwd()
    source = project_root / "asurdev"

    if not source.exists():
        print("❌ 'asurdev/' directory not found. Nothing to do.")
        return

    if args.delete:
        if args.dry_run:
            print(f"🔍 [DRY RUN] Would permanently delete {source}")
        else:
            try:
                shutil.rmtree(source)
                print(f"✅ Deleted {source}")
            except Exception as e:
                print(f"❌ Failed to delete {source}: {e}")
                sys.exit(1)
    else:
        # Archive
        backup_root = project_root / args.backup_dir
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = backup_root / f"asurdev_{timestamp}"

        if args.dry_run:
            print(f"🔍 [DRY RUN] Would move {source} -> {dest}")
        else:
            try:
                backup_root.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest))
                print(f"✅ Archived {source} to {dest}")
            except Exception as e:
                print(f"❌ Failed to archive {source}: {e}")
                sys.exit(1)

    # Optional: check for remaining imports from asurdev in the main project
    print("\n📄 Checking for possible imports from asurdev in the main project...")
    main_project = project_root / "AstroFinSentinelV5"
    if main_project.exists():
        imports_found = []
        for py_file in main_project.rglob("*.py"):
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if "asurdev" in line and "import" in line and not line.strip().startswith("#"):
                            imports_found.append((py_file.relative_to(main_project), line.strip()))
            except Exception:
                continue
        if imports_found:
            print("⚠️  Found references to 'asurdev' in the main project. Please review:")
            for rel_path, line in imports_found[:10]:  # limit output
                print(f"   - {rel_path}: {line}")
        else:
            print("✅ No imports from asurdev detected.")
    else:
        print("⚠️  'AstroFinSentinelV5/' not found; cannot scan for imports.")

    print("\n✅ Operation completed.")

if __name__ == "__main__":
    main()
