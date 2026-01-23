const https = require('https');
const { shell } = require('electron');

// Version file URL
const VERSION_URL = 'https://raw.githubusercontent.com/userRed4cted/Adzsend/main/bridge/version.json';

// Check for updates
function checkForUpdates(currentVersion) {
    return new Promise((resolve, reject) => {
        const makeRequest = (url) => {
            const req = https.get(url, (res) => {
                // Handle redirects (301, 302, 307, 308)
                if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
                    makeRequest(res.headers.location);
                    return;
                }

                if (res.statusCode !== 200) {
                    reject(new Error(`Server returned ${res.statusCode}`));
                    return;
                }

                let data = '';

                res.on('data', (chunk) => {
                    data += chunk;
                });

                res.on('end', () => {
                    try {
                        const versionInfo = JSON.parse(data);
                        const updateAvailable = compareVersions(versionInfo.version, currentVersion) > 0;

                        resolve({
                            updateAvailable,
                            currentVersion,
                            latestVersion: versionInfo.version,
                            downloadUrl: versionInfo.download_url,
                            forceUpdate: versionInfo.force_update || false
                        });
                    } catch (error) {
                        reject(new Error('Failed to parse version info'));
                    }
                });
            });

            // Set 10 second timeout
            req.setTimeout(10000, () => {
                req.destroy();
                reject(new Error('Connection timeout'));
            });

            req.on('error', (error) => {
                reject(new Error('No internet connection'));
            });
        };

        makeRequest(VERSION_URL);
    });
}

// Compare version strings (returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal)
function compareVersions(v1, v2) {
    const parts1 = v1.split('.').map(Number);
    const parts2 = v2.split('.').map(Number);

    for (let i = 0; i < Math.max(parts1.length, parts2.length); i++) {
        const p1 = parts1[i] || 0;
        const p2 = parts2[i] || 0;

        if (p1 > p2) return 1;
        if (p1 < p2) return -1;
    }

    return 0;
}

// Download update - opens the download URL in browser
// User will download and run the installer manually
async function downloadUpdate(downloadUrl) {
    return new Promise((resolve, reject) => {
        try {
            // Open the download URL in the default browser
            shell.openExternal(downloadUrl);
            resolve();
        } catch (error) {
            reject(error);
        }
    });
}

module.exports = {
    checkForUpdates,
    downloadUpdate
};
