# Adzsend Bridge Release Guide

This guide explains how to build and release new versions of Adzsend Bridge.

---

## Prerequisites

Before building, ensure you have installed:

1. **Node.js** (v18 or later): https://nodejs.org/
2. **npm** (comes with Node.js)

---

## First-Time Setup

1. Open a terminal in the `bridge` folder:
   ```bash
   cd Adzsend/bridge
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

---

## Building the Installer

### Step 1: Update Version Number

Edit `package.json` and update the `"version"` field:
```json
{
  "name": "adzsend-bridge",
  "version": "1.0.1",  // <-- Change this
  ...
}
```

### Step 2: Build the Installer

Run the build command:

**For Windows:**
```bash
npm run build:win
```

**For macOS:**
```bash
npm run build:mac
```

**For Linux:**
```bash
npm run build:linux
```

### Step 3: Find the Built File

After building, the installer will be in the `dist` folder:
- Windows: `dist/AdzsendBridgeSetup.exe`
- macOS: `dist/Adzsend Bridge.dmg`
- Linux: `dist/Adzsend Bridge.AppImage`

---

## Releasing a New Version

### Step 1: Go to GitHub Releases

1. Go to your repository on GitHub
2. Click **"Releases"** (on the right sidebar)
3. Click **"Create a new release"** or **"Draft a new release"**

### Step 2: Create the Release Tag

- **Choose a tag:** Create a new tag
- **Tag name:** `bridge-v1.0.1` (use your new version number)
- **Target:** `main` (or your default branch)

### Step 3: Fill in Release Details

- **Release title:** `Bridge v1.0.1`
- **Description:** (Optional) Add release notes:
  ```
  ## Changes
  - Fixed bug with...
  - Added feature...
  ```

### Step 4: Attach the Installer

1. Drag and drop the built `.exe` file into the "Attach binaries" area
2. Or click "Attach binaries by dropping them here or selecting them"
3. Select `dist/AdzsendBridgeSetup.exe`

### Step 5: Publish the Release

Click **"Publish release"**

### Step 6: Copy the Download URL

1. After publishing, go to the release page
2. Right-click on `AdzsendBridgeSetup.exe`
3. Click **"Copy link address"**

The URL will look like:
```
https://github.com/YOUR_USERNAME/Adzsend/releases/download/bridge-v1.0.1/AdzsendBridgeSetup.exe
```

### Step 7: Update version.json

Edit `bridge/version.json`:
```json
{
    "version": "1.0.1",
    "download_url": "https://github.com/YOUR_USERNAME/Adzsend/releases/download/bridge-v1.0.1/AdzsendBridgeSetup.exe"
}
```

### Step 8: Commit and Push

```bash
git add bridge/version.json bridge/package.json
git commit -m "Release bridge v1.0.1"
git push
```

---

## How Users Receive Updates

1. User opens Adzsend Bridge
2. Bridge fetches `version.json` from GitHub (raw file)
3. Compares local version with remote version
4. If remote is newer, shows forced update modal
5. User clicks "Update Now"
6. Browser opens download URL
7. User runs new installer
8. Old version is replaced

---

## Important Notes

### Version Numbering

Use semantic versioning: `MAJOR.MINOR.PATCH`
- **MAJOR:** Breaking changes (1.0.0 -> 2.0.0)
- **MINOR:** New features (1.0.0 -> 1.1.0)
- **PATCH:** Bug fixes (1.0.0 -> 1.0.1)

### Don't Forget

- [ ] Update version in `package.json`
- [ ] Build the installer
- [ ] Create GitHub release with correct tag
- [ ] Attach the installer file
- [ ] Update `version.json` with new version and URL
- [ ] Commit and push `version.json`

### Testing

Before releasing:
1. Test the build locally by running `npm start`
2. Test the installer on a fresh machine if possible
3. Verify the update flow works correctly

---

## Troubleshooting

### Build fails

- Make sure all dependencies are installed: `npm install`
- Check Node.js version: `node --version` (should be 18+)
- Clear build cache: Delete `dist` folder and rebuild

### Users not seeing updates

- Verify `version.json` is pushed to GitHub
- Check the raw URL is accessible: `https://raw.githubusercontent.com/YOUR_USERNAME/Adzsend/main/bridge/version.json`
- Make sure version number in `version.json` is higher than current

### Download URL not working

- Verify the release is published (not draft)
- Check the file name matches exactly (case-sensitive)
- Wait a few minutes for GitHub CDN to propagate

---

## Quick Reference

| Action | Command/Location |
|--------|------------------|
| Install deps | `npm install` |
| Run locally | `npm start` |
| Build Windows | `npm run build:win` |
| Build macOS | `npm run build:mac` |
| Build Linux | `npm run build:linux` |
| Installer output | `dist/AdzsendBridgeSetup.exe` |
| Version file | `bridge/version.json` |
| Package version | `bridge/package.json` → `"version"` |
