/**
 * Version Sync Script
 *
 * This script reads the version from version.json and updates package.json
 * Run this before building to ensure both files have the same version.
 *
 * Usage: node scripts/sync-version.js
 */

const fs = require('fs');
const path = require('path');

const bridgeDir = path.join(__dirname, '..');
const versionJsonPath = path.join(bridgeDir, 'version.json');
const packageJsonPath = path.join(bridgeDir, 'package.json');

try {
    // Read version.json
    const versionData = JSON.parse(fs.readFileSync(versionJsonPath, 'utf8'));
    const version = versionData.version;

    if (!version) {
        console.error('Error: No version found in version.json');
        process.exit(1);
    }

    // Read package.json
    const packageData = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    const oldVersion = packageData.version;

    // Update version in package.json
    packageData.version = version;

    // Write updated package.json (preserve formatting with 2-space indent)
    fs.writeFileSync(packageJsonPath, JSON.stringify(packageData, null, 2) + '\n', 'utf8');

    if (oldVersion !== version) {
        console.log(`Version synced: ${oldVersion} -> ${version}`);
    } else {
        console.log(`Version already in sync: ${version}`);
    }

    process.exit(0);
} catch (error) {
    console.error('Error syncing version:', error.message);
    process.exit(1);
}
