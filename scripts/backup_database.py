#!/usr/bin/env python3
"""
Manual database backup script for LifeHunter.

Creates a timestamped backup of the SQLite database.

Usage:
    python scripts/backup_database.py
    python scripts/backup_database.py --output /path/to/backup.db
    python scripts/backup_database.py --keep 7   # Keep only last 7 backups
"""

import argparse
import glob
import os
import shutil
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="Backup the LifeHunter database")
    parser.add_argument("--output", help="Output path for backup file")
    parser.add_argument(
        "--keep",
        type=int,
        default=30,
        help="Number of recent backups to keep (default: 30, 0 = keep all)",
    )
    args = parser.parse_args()

    from src.config.config import get_config

    config = get_config()
    db_path = config.database_path

    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        sys.exit(1)

    # Determine backup path
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    if args.output:
        backup_path = args.output
    else:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"lifehunter_{ts}.db")

    # Copy database file
    shutil.copy2(db_path, backup_path)
    size_kb = os.path.getsize(backup_path) / 1024

    print(f"✅ Backup created: {backup_path} ({size_kb:.1f} KB)")

    # Cleanup old backups
    if args.keep > 0:
        pattern = os.path.join(backup_dir, "lifehunter_*.db")
        backups = sorted(glob.glob(pattern))
        to_delete = backups[: max(0, len(backups) - args.keep)]
        for old in to_delete:
            os.remove(old)
            print(f"   Removed old backup: {old}")

        if to_delete:
            print(f"   Kept {args.keep} most recent backups.")


if __name__ == "__main__":
    main()
