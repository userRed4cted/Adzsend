# Adzsend Bridge Release Guide

This guide explains how to build and release new versions of Adzsend Bridge.

---

## Building with GitHub Actions (Recommended)

The easiest way to build the installer is using the GitHub Actions workflow.

### Step 1: Update version.json

Edit `bridge/version.json` with the new version:
```json
{
    "version": "1.0.1",
    "download_url": "https://github.com/YOUR_USERNAME/Adzsend/releases/download/bridge-v1.0.1/AdzsendBridgeSetup.exe"
}
```

### Step 2: Commit and Push

```bash
git add bridge/version.json
git commit -m "Bump version to 1.0.1"
git push
```

### Step 3: Run the Workflow

1. Go to your repository on GitHub
2. Click **"Actions"** tab
3. Select **"Build Bridge Installer"** from the left sidebar
4. Click **"Run workflow"** dropdown (top right)
5. Click the green **"Run workflow"** button

### Step 4: Download the Installer

1. Wait for the workflow to complete (green checkmark)
2. Click on the completed workflow run
3. Scroll down to **"Artifacts"**
4. Download **"AdzsendBridgeSetup"**

### Step 5: Create GitHub Release

1. Go to **"Releases"** on your repository
2. Click **"Create a new release"**
3. **Tag name:** `bridge-v1.0.1` (match your version)
4. **Release title:** `Bridge v1.0.1`
5. Drag and drop the downloaded `.exe` into attachments
6. Click **"Publish release"**

---

## Automatic Release (via Tag)

You can also trigger an automatic build + release by pushing a tag:

```bash
git tag bridge-v1.0.1
git push origin bridge-v1.0.1
```

This will:
1. Trigger the build workflow
2. Build the Windows installer
3. Automatically attach the `.exe` to a GitHub release

---

## Building Locally (Alternative)

If you prefer to build on your machine:

### Prerequisites

1. **Node.js** (v18 or later): https://nodejs.org/
2. **npm** (comes with Node.js)

### Setup

1. Open a terminal in the `bridge` folder
2. Install dependencies: `npm install`

### Build Commands

- Windows: `npm run build:win`
- macOS: `npm run build:mac`
- Linux: `npm run build:linux`

Output: `dist/AdzsendBridgeSetup.exe`

**Note:** The build process automatically syncs version.json → package.json

---

## Resetting to v1.0.0

To reset the version back to 1.0.0 (fresh start):

1. Edit `version.json`:
   ```json
   {
       "version": "1.0.0",
       "download_url": "https://github.com/YOUR_USERNAME/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup.exe"
   }
   ```

2. Run `npm run sync-version` (or build, which syncs automatically)

3. Delete old releases from GitHub if desired

That's it - version numbers are just labels in config files, no history to clear.

---

## How Users Receive Updates

1. User opens Adzsend Bridge
2. Bridge fetches `version.json` from GitHub (raw file)
3. Compares local version with remote version
4. If remote is newer, shows forced update dialog
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

- [ ] Update version in `version.json`
- [ ] Update `download_url` in `version.json` to match the new tag
- [ ] Build the installer
- [ ] Create GitHub release with correct tag
- [ ] Attach the installer file
- [ ] Commit and push changes

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
- Make sure version number in `version.json` is higher than user's current version

### Download URL not working

- Verify the release is published (not draft)
- Check the file name matches exactly (case-sensitive)
- Wait a few minutes for GitHub CDN to propagate

---

## Quick Reference

| Action | Location/Command |
|--------|------------------|
| **Set version** | Edit `version.json` |
| Sync version manually | `npm run sync-version` |
| Run locally | `npm start` |
| Build Windows | `npm run build:win` |
| Build macOS | `npm run build:mac` |
| Build Linux | `npm run build:linux` |
| Installer output | `dist/AdzsendBridgeSetup.exe` |
