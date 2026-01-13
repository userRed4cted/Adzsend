#!/usr/bin/env python
"""Verify the current state of profile photo and date format saving"""

import sqlite3
from database.models import get_user_data

def check_database():
    """Check what's currently in the database for user 2"""
    print("=== Current Database State for User 2 ===\n")

    # Check using models.py
    user_data = get_user_data(2)
    print(f"Profile photo: {user_data.get('profile_photo', 'NOT SET')}")
    print(f"Date format: {user_data.get('date_format', 'NOT SET')}")

    # Check database directly
    print("\n=== Direct Database Check ===")
    conn = sqlite3.connect('marketing_panel.db')
    cursor = conn.cursor()

    # Check if columns exist
    cursor.execute("PRAGMA table_info(user_data)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"Columns in user_data: {columns}")

    # Check user 2's data
    cursor.execute('SELECT user_id, profile_photo, date_format FROM user_data WHERE user_id = 2')
    row = cursor.fetchone()
    if row:
        print(f"\nUser 2 data:")
        print(f"  user_id: {row[0]}")
        print(f"  profile_photo: {row[1]}")
        print(f"  date_format: {row[2]}")
    else:
        print("\nNo user_data record found for user 2!")

    conn.close()

    print("\n=== Instructions ===")
    print("1. Open browser and login to http://127.0.0.1:5000/test")
    print("2. Open browser console (F12)")
    print("3. Hard refresh (Ctrl+Shift+R)")
    print("4. Open Settings and try to change profile photo")
    print("5. Check console for errors and look for:")
    print("   - '[SETTINGS POPUP] CSRF Token: ...' (should show a long token)")
    print("   - 'Response status: 200' (should be 200, not 403 or 401)")
    print("   - 'Raw response: {\"success\":true}' (should show success)")
    print("6. Run this script again to verify database was updated")

if __name__ == '__main__':
    check_database()
