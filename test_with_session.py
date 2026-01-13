#!/usr/bin/env python
"""Test API with a real logged-in session"""

import requests
from database.models import get_user_by_email
from app import generate_csrf_token

# Create a session
session = requests.Session()

# Step 1: Try to access test page (should redirect to login)
print("=== Step 1: Access /test (not logged in) ===")
response = session.get("http://127.0.0.1:5000/test")
print(f"Status: {response.status_code}")
print(f"Final URL: {response.url}")
print()

# For this test, we need to actually login through the app
# Let's check if we can manually create a session in Flask

print("=== Step 2: Check user in database ===")
user = get_user_by_email("csanjnk@gmail.com")
if user:
    print(f"Found user: ID={user['id']}, Email={user['email']}")
    print()

    # Generate CSRF token
    csrf = generate_csrf_token()
    print(f"Generated CSRF token: {csrf[:20]}... (length: {len(csrf)})")
    print()

    print("=== Step 3: Test API call with CSRF but no session ===")
    headers = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': csrf
    }
    data = {'profile_photo': 'Dark_Purple.jpg'}
    response = session.post("http://127.0.0.1:5000/api/save-user-data",
                           headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print()

    if response.status_code == 401:
        print("✓ Correctly requires login (401)")
    elif response.status_code == 403:
        print("✗ CSRF token issue (403)")
    else:
        print(f"? Unexpected status: {response.status_code}")

else:
    print("User not found!")
