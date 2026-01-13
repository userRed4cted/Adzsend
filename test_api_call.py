#!/usr/bin/env python
"""Test the actual API endpoint with a real HTTP call"""

import requests
import json

# First, let's check what the actual issue is by looking at the response
def test_api_without_session():
    """Test API call without session (should fail with 401)"""
    print("=== Test 1: API call without session ===")
    url = "http://127.0.0.1:5000/api/save-user-data"
    headers = {
        'Content-Type': 'application/json',
        'X-CSRF-Token': 'test-token'
    }
    data = {
        'profile_photo': 'Dark_Green.jpg'
    }

    response = requests.post(url, headers=headers, json=data)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    print()

def test_get_user_data():
    """Test getting user data without session"""
    print("=== Test 2: Get user data without session ===")
    url = "http://127.0.0.1:5000/api/get-user-data"
    response = requests.get(url)
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    print()

if __name__ == '__main__':
    test_api_without_session()
    test_get_user_data()

    print("\n=== Analysis ===")
    print("Both should return 401 (Not logged in)")
    print("The real issue is that the browser isn't sending proper session cookies")
    print("Or the CSRF token is invalid/missing in the template")
