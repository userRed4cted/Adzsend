# Testing Instructions

## What Was Fixed

1. **Added `profile_photo` and `date_format` columns** to the database
2. **Added CSRF token** to the test.html template
3. **Added cache-busting headers** to prevent browser caching
4. **Added comprehensive logging** to debug API calls
5. **Archived old templates** (dashboard.html, settings.html, team-management.html, team-panel.html)

## Testing Steps

### Test Profile Photo Saving

1. **Hard refresh browser** (Ctrl+Shift+R)
2. **Open Settings** (gear icon in navbar)
3. **Click on "My account"** in the left menu
4. **Click on your profile photo** (circular image)
5. **Select a different photo** from the popup
6. **Check console** - Should see:
   - `[SETTINGS POPUP] CSRF Token: [long token]`
   - `Response status: 200`
   - `Raw response: {"success":true}`
   - `Total profile images updated: 1`
7. **Refresh the page** (Ctrl+R)
8. **Verify the photo persists** - Your new photo should still be showing

### Test Date Format Saving

1. **Open Settings** → **Date format** page
2. **Select a different format** (dd/mm/yy or yy/mm/dd)
3. **Check console** - Should see:
   - `[DATE FORMAT] Saving: dd/mm/yy`
   - `[DATE FORMAT] Response status: 200`
   - `[DATE FORMAT] Saved successfully`
4. **Refresh the page**
5. **Check My Account** - Signup date should show in the new format

## Verify Database

Run this to check the database has the saved values:

```bash
cd "c:\Users\Artio\Desktop\visualStudio\BorzMarketing"
python -c "from database.models import get_user_data; data = get_user_data(2); print(f'Profile: {data[\"profile_photo\"]}'); print(f'Date format: {data[\"date_format\"]}')"
```

## If Still Not Working

1. Check Flask is running: `curl http://127.0.0.1:5000/`
2. Clear browser cache completely
3. Try in incognito/private browsing mode
4. Check browser console for any errors
5. Check Flask logs for API call logs

## Root Causes Found

1. **CSRF token was missing** - Not passed to template
2. **Browser was caching** - Old user_data was cached
3. **Database migration didn't run** - Columns didn't exist
4. **User 2 had no user_data record** - Needed to create it
