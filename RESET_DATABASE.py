#!/usr/bin/env python3
"""
DATABASE RESET SCRIPT
=====================
This script will DELETE ALL DATA from the database and recreate empty tables.

WARNING: This action is IRREVERSIBLE! All users, subscriptions, teams, and
usage data will be permanently deleted.

Usage:
    python RESET_DATABASE.py
"""

import os
import re
import sqlite3
import sys

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), 'marketing_panel.db')
VERSION_FILE = os.path.join(os.path.dirname(__file__), 'config', 'database_version.py')


def increment_database_version():
    """Increment the DATABASE_VERSION in config/database_version.py"""
    try:
        with open(VERSION_FILE, 'r') as f:
            content = f.read()

        # Find current version
        match = re.search(r'DATABASE_VERSION\s*=\s*(\d+)', content)
        if match:
            current_version = int(match.group(1))
            new_version = current_version + 1

            # Replace the version
            new_content = re.sub(
                r'DATABASE_VERSION\s*=\s*\d+',
                f'DATABASE_VERSION = {new_version}',
                content
            )

            with open(VERSION_FILE, 'w') as f:
                f.write(new_content)

            print(f"\nDatabase version incremented: {current_version} -> {new_version}")
            print("Users will see a wipe notice when they visit the site.")
            return True
        else:
            print("\nWarning: Could not find DATABASE_VERSION in config file.")
            return False

    except FileNotFoundError:
        print(f"\nWarning: Version file not found: {VERSION_FILE}")
        return False
    except Exception as e:
        print(f"\nWarning: Could not increment version: {e}")
        return False


def reset_database():
    """Delete all data and recreate the database tables."""

    print("=" * 60)
    print("           DATABASE RESET SCRIPT")
    print("=" * 60)
    print()
    print(f"Database: {DB_PATH}")
    print()
    print("WARNING: This will permanently delete:")
    print("  - All users")
    print("  - All subscriptions")
    print("  - All business teams and members")
    print("  - All usage records")
    print("  - All saved user data")
    print()
    print("This action CANNOT be undone!")
    print()

    # Confirm action
    confirm = input("Type 'RESET' to confirm database reset: ").strip()

    if confirm != 'RESET':
        print("\nReset cancelled. No changes were made.")
        return False

    print("\nResetting database...")

    try:
        # Check if database exists
        if not os.path.exists(DB_PATH):
            print(f"Database file not found: {DB_PATH}")
            print("Creating new database...")

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        if tables:
            print(f"\nFound {len(tables)} tables to clear:")
            for table in tables:
                print(f"  - {table[0]}")

            # Delete all data from each table
            for table in tables:
                table_name = table[0]
                if table_name != 'sqlite_sequence':  # Skip SQLite internal table
                    cursor.execute(f"DELETE FROM {table_name}")
                    print(f"  Cleared: {table_name}")

            # Reset auto-increment counters
            cursor.execute("DELETE FROM sqlite_sequence")
            print("  Reset auto-increment counters")

        conn.commit()
        conn.close()

        # Increment database version to notify users
        increment_database_version()

        print("\n" + "=" * 60)
        print("           DATABASE RESET COMPLETE")
        print("=" * 60)
        print("\nAll data has been deleted.")
        print("The database tables are now empty.")
        print("\nRestart the Flask app to reinitialize the database structure.")

        return True

    except Exception as e:
        print(f"\nError resetting database: {e}")
        return False


def delete_database():
    """Completely delete the database file."""

    print("=" * 60)
    print("        COMPLETE DATABASE DELETION")
    print("=" * 60)
    print()
    print(f"Database: {DB_PATH}")
    print()
    print("This will COMPLETELY DELETE the database file.")
    print("A new database will be created when the app starts.")
    print()

    confirm = input("Type 'DELETE' to confirm complete deletion: ").strip()

    if confirm != 'DELETE':
        print("\nDeletion cancelled. No changes were made.")
        return False

    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(f"\nDeleted: {DB_PATH}")

            # Increment database version to notify users
            increment_database_version()

            print("\nDatabase file has been completely removed.")
            print("Restart the Flask app to create a fresh database.")
            return True
        else:
            print(f"\nDatabase file not found: {DB_PATH}")
            return False

    except Exception as e:
        print(f"\nError deleting database: {e}")
        return False


if __name__ == '__main__':
    print()
    print("Choose an option:")
    print("  1. Reset (clear all data, keep table structure)")
    print("  2. Delete (remove database file, new one created on app start)")
    print("  3. Cancel")
    print()

    choice = input("Enter choice (1/2/3): ").strip()

    if choice == '1':
        reset_database()
    elif choice == '2':
        delete_database()
    else:
        print("\nCancelled. No changes were made.")
