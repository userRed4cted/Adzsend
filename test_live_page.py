#!/usr/bin/env python
"""Test what the actual rendered HTML looks like"""

# Check database and what template should show
print("=== Check database and what template should show ===")
from database.models import get_user_data, get_user_by_id

user = get_user_by_id(2)
user_data = get_user_data(2)

print(f"User 2:")
print(f"  Email: {user.get('email')}")
print(f"  Profile photo in DB: {user_data.get('profile_photo')}")
print(f"  Date format in DB: {user_data.get('date_format')}")
print()

print("The template should render with:")
print(f"  <img src=\"/static/profile_photos/{user_data.get('profile_photo')}\" ... >")
print(f"  window.userDateFormat = '{user_data.get('date_format') or 'mm/dd/yy'}';")
print()

print("=== What to check in browser ===")
print("1. Login at http://127.0.0.1:5000/test")
print("2. Do a HARD refresh (Ctrl+Shift+F5 or Ctrl+Shift+R)")
print("3. Right-click on page > View Page Source")
print("4. Search for 'window.userDateFormat' - it should show:", user_data.get('date_format'))
print("5. Search for 'profile_photos' - it should show:", user_data.get('profile_photo'))
print("6. Open DevTools > Network tab > Check response headers for 'Cache-Control'")
print("7. It should have: 'no-cache, no-store, must-revalidate'")
