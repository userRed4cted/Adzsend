const { autoUpdater } = require('electron-updater');
const { BrowserWindow } = require('electron');

// Configure auto-updater
autoUpdater.autoDownload = false; // Don't auto-download, let user choose
autoUpdater.autoInstallOnAppQuit = true;

let mainWindow = null;
let updateCheckInProgress = false;

// Set the main window reference
function setMainWindow(window) {
    mainWindow = window;
}

// Send status to renderer
function sendStatusToWindow(status, data = {}) {
    if (mainWindow && mainWindow.webContents) {
        mainWindow.webContents.send('update-status', { status, ...data });
    }
}

// Check for updates
function checkForUpdates(currentVersion) {
    return new Promise((resolve, reject) => {
        if (updateCheckInProgress) {
            resolve({ updateAvailable: false, currentVersion, latestVersion: currentVersion });
            return;
        }

        updateCheckInProgress = true;

        // Set up one-time listeners for this check
        const onUpdateAvailable = (info) => {
            cleanup();
            resolve({
                updateAvailable: true,
                currentVersion,
                latestVersion: info.version,
                releaseNotes: info.releaseNotes
            });
        };

        const onUpdateNotAvailable = (info) => {
            cleanup();
            resolve({
                updateAvailable: false,
                currentVersion,
                latestVersion: info.version
            });
        };

        const onError = (error) => {
            cleanup();
            // Don't reject on error, just return no update available
            // This prevents crashes when offline or GitHub is unreachable
            resolve({
                updateAvailable: false,
                currentVersion,
                latestVersion: currentVersion,
                error: error.message
            });
        };

        const cleanup = () => {
            updateCheckInProgress = false;
            autoUpdater.removeListener('update-available', onUpdateAvailable);
            autoUpdater.removeListener('update-not-available', onUpdateNotAvailable);
            autoUpdater.removeListener('error', onError);
        };

        autoUpdater.once('update-available', onUpdateAvailable);
        autoUpdater.once('update-not-available', onUpdateNotAvailable);
        autoUpdater.once('error', onError);

        // Trigger the check
        autoUpdater.checkForUpdates().catch(onError);
    });
}

// Download update
function downloadUpdate() {
    return new Promise((resolve, reject) => {
        const onDownloadProgress = (progress) => {
            sendStatusToWindow('download-progress', {
                percent: Math.round(progress.percent),
                bytesPerSecond: progress.bytesPerSecond,
                transferred: progress.transferred,
                total: progress.total
            });
        };

        const onUpdateDownloaded = (info) => {
            cleanup();
            sendStatusToWindow('update-downloaded', { version: info.version });
            resolve(info);
        };

        const onError = (error) => {
            cleanup();
            sendStatusToWindow('download-error', { error: error.message });
            reject(error);
        };

        const cleanup = () => {
            autoUpdater.removeListener('download-progress', onDownloadProgress);
            autoUpdater.removeListener('update-downloaded', onUpdateDownloaded);
            autoUpdater.removeListener('error', onError);
        };

        autoUpdater.on('download-progress', onDownloadProgress);
        autoUpdater.once('update-downloaded', onUpdateDownloaded);
        autoUpdater.once('error', onError);

        sendStatusToWindow('downloading');
        autoUpdater.downloadUpdate().catch(onError);
    });
}

// Install update and restart
function installUpdate() {
    autoUpdater.quitAndInstall(false, true);
}

// Compare version strings (returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal)
// Kept for backwards compatibility
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

module.exports = {
    checkForUpdates,
    downloadUpdate,
    installUpdate,
    setMainWindow,
    compareVersions
};
