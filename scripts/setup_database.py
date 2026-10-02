#!/usr/bin/env python3
"""
Database initialization script for LifeHunter.

Creates all tables and populates seed data (skills, achievements, titles).
Run once before starting the application for the first time.

Usage:
    python scripts/setup_database.py
    python scripts/setup_database.py --reset   # Drop and recreate all tables
"""

import argparse
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    parser = argparse.ArgumentParser(description="Initialize the LifeHunter database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all existing tables before recreating them (WARNING: deletes all data!)",
    )
    args = parser.parse_args()

    print("LifeHunter Database Setup")
    print("=" * 40)

    from src.models import Base, engine
    from src.db.init_db import create_all_tables, seed_initial_data

    if args.reset:
        print("⚠️  Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("   Tables dropped.")

    print("Creating database tables...")
    create_all_tables()
    print("   Tables created.")

    print("Seeding initial data (skills, achievements, titles)...")
    seed_initial_data()
    print("   Seed data inserted.")

    print()
    print("✅ Database setup complete!")
    print(f"   Database: {engine.url}")


if __name__ == "__main__":
    main()
