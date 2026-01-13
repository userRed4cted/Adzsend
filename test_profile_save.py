#!/usr/bin/env python
"""Test script to verify profile photo saving works"""

import sys
import sqlite3
from database.models import save_user_data, get_user_data

def test_profile_save():
    """Test saving and retrieving profile photo"""

    print("=== Testing Profile Photo Save ===\n")

    # Test for user 1
    print("Testing User 1:")
    print("Before save:")
    user1_data = get_user_data(1)
    print(f"  Profile photo: {user1_data['profile_photo']}")

    # Save new photo
    save_user_data(1, None, None, None, None, 'Light_Orange.jpg')
    print("\nAfter saving 'Light_Orange.jpg':")
    user1_data = get_user_data(1)
    print(f"  Profile photo: {user1_data['profile_photo']}")

    # Test for user 2
    print("\n\nTesting User 2:")
    print("Before save:")
    user2_data = get_user_data(2)
    print(f"  Profile photo: {user2_data['profile_photo']}")

    # Save new photo
    save_user_data(2, None, None, None, None, 'Light_Green.jpg')
    print("\nAfter saving 'Light_Green.jpg':")
    user2_data = get_user_data(2)
    print(f"  Profile photo: {user2_data['profile_photo']}")

    # Verify it persists by checking database directly
    print("\n\n=== Verifying in database directly ===")
    conn = sqlite3.connect('marketing_panel.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, profile_photo FROM user_data')
    rows = cursor.fetchall()
    for row in rows:
        print(f"User {row[0]}: {row[1]}")
    conn.close()

    print("\n=== Test Complete ===")
    print("If you see the saved photos above, the database is working correctly.")
    print("The issue is likely with the Flask API or frontend JavaScript.")

if __name__ == '__main__':
    test_profile_save()
