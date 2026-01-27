// DOM Elements
const minimizeBtn = document.getElementById('minimize-btn');
const closeBtn = document.getElementById('close-btn');
const modifyKeyBtn = document.getElementById('modify-key-btn');
const activateBtn = document.getElementById('activate-btn');
const statusValue = document.getElementById('status-value');
const frameStatus = document.getElementById('frame-status');
const openDashboardBtn = document.getElementById('open-dashboard-btn');
const versionDisplay = document.getElementById('version-display');

// State
let isActivated = false;
let secretKey = null;
let isShowingDialog = false; // Prevent popup spam

// Initialize
async function init() {
    // Load stored secret key
    secretKey = await window.bridge.getSecretKey();

    // Set up event listeners
    setupEventListeners();

    // Set up IPC listeners
    setupIPCListeners();

    // Update UI based on state
    updateUI();
}

// Set up DOM event listeners
function setupEventListeners() {
    // Window controls
    minimizeBtn.addEventListener('click', () => window.bridge.minimize());
    closeBtn.addEventListener('click', () => window.bridge.close());

    // Modify key button - use native prompt
    modifyKeyBtn.addEventListener('click', promptForSecretKey);

    // Activate button
    activateBtn.addEventListener('click', handleActivate);

    // Dashboard button - opens ~/dashboard
    openDashboardBtn.addEventListener('click', () => {
        window.bridge.openExternal('https://adzsend.com/dashboard');
    });
}

// Set up IPC event listeners
function setupIPCListeners() {
    window.bridge.onVersion((version) => {
        versionDisplay.textContent = `v${version}`;
    });

    window.bridge.onConnectionStatus((status, reason) => {
        handleConnectionStatus(status, reason);
    });

    window.bridge.onConnectionError((error) => {
        handleConnectionError(error);
    });

    window.bridge.onAuthFailed((reason) => {
        handleAuthFailed(reason);
    });

    window.bridge.onLoggedOutElsewhere(() => {
        handleLoggedOutElsewhere();
    });

    window.bridge.onUpdateAvailable(async (info) => {
        if (info.forceUpdate) {
            // Forced update - unskippable
            const shouldUpdate = await window.bridge.showUpdateDialog(info.currentVersion, info.latestVersion);
            if (shouldUpdate) {
                handleUpdate(info.downloadUrl);
            } else {
                // User closed dialog without updating - quit the app completely
                window.bridge.quitForUpdate();
            }
        } else {
            // Skippable update
            const shouldUpdate = await window.bridge.showSkippableUpdateDialog(info.currentVersion, info.latestVersion);
            if (shouldUpdate) {
                handleUpdate(info.downloadUrl);
            }
            // If not updating, just continue normally
        }
    });

    window.bridge.onUpdateCheckFailed(async (info) => {
        // Show native network error dialog
        const shouldRetry = await window.bridge.showNetworkErrorDialog();
        if (shouldRetry) {
            handleActivate();
        } else {
            window.bridge.close();
        }
    });

}

// Handle activate/deactivate
async function handleActivate() {
    if (isActivated) {
        // Deactivate
        frameStatus.textContent = 'Bridge disconnecting';
        activateBtn.disabled = true;
        try {
            await window.bridge.disconnect();
        } catch (error) {
            console.error('Disconnect error:', error);
        }
        // Reset state regardless of disconnect result
        isActivated = false;
        frameStatus.textContent = 'Bridge offline';
        statusValue.textContent = 'offline';
        statusValue.classList.remove('online');
        activateBtn.textContent = 'Activate';
        activateBtn.disabled = false;
    } else {
        // Check if we have a secret key
        if (!secretKey) {
            // Show error - user must use "Modify Secret Key" to enter key
            isShowingDialog = true;
            await window.bridge.showErrorDialog('No secret key', 'Please click "Modify Secret Key" to enter your secret key.');
            isShowingDialog = false;
            return;
        }

        // Activate - don't change button text yet, wait for connection status
        frameStatus.textContent = 'Bridge connecting';
        activateBtn.disabled = true;

        const result = await window.bridge.connect(secretKey);

        if (!result.success) {
            // Error handled by IPC listeners
            activateBtn.textContent = 'Activate';
            activateBtn.disabled = false;
            frameStatus.textContent = 'Bridge offline';
        }
        // Button text will be set to 'Deactivate' by handleConnectionStatus when connected
    }
}

// Handle connection status changes
function handleConnectionStatus(status, reason) {
    switch (status) {
        case 'connecting':
            frameStatus.textContent = 'Bridge connecting';
            activateBtn.textContent = 'Deactivate';
            activateBtn.disabled = false;
            break;

        case 'connected':
            isActivated = true;
            frameStatus.textContent = 'Bridge online';
            statusValue.textContent = 'online';
            statusValue.classList.add('online');
            activateBtn.textContent = 'Deactivate';
            activateBtn.disabled = false;
            break;

        case 'disconnected':
            isActivated = false;
            frameStatus.textContent = 'Bridge offline';
            statusValue.textContent = 'offline';
            statusValue.classList.remove('online');
            activateBtn.textContent = 'Activate';
            activateBtn.disabled = false;
            break;
    }
}

// Handle connection errors
async function handleConnectionError(error) {
    if (isShowingDialog) return; // Prevent popup spam

    isActivated = false;
    activateBtn.textContent = 'Activate';
    activateBtn.disabled = false;
    frameStatus.textContent = 'Bridge offline';
    statusValue.textContent = 'offline';
    statusValue.classList.remove('online');

    isShowingDialog = true;
    if (error.includes('ENOTFOUND') || error.includes('network') || error.includes('internet')) {
        // Show network error dialog
        const shouldRetry = await window.bridge.showNetworkErrorDialog();
        isShowingDialog = false;
        if (shouldRetry) {
            handleActivate();
        }
    } else {
        // Show error dialog
        await window.bridge.showErrorDialog('Connection error', error + '.');
        isShowingDialog = false;
    }
}

// Handle auth failed
async function handleAuthFailed(reason) {
    if (isShowingDialog) return; // Prevent popup spam

    isActivated = false;
    secretKey = null;
    window.bridge.clearSecretKey();
    activateBtn.textContent = 'Activate';
    activateBtn.disabled = false;
    frameStatus.textContent = 'Bridge offline';
    statusValue.textContent = 'offline';
    statusValue.classList.remove('online');

    // Show error dialog
    isShowingDialog = true;
    await window.bridge.showErrorDialog('Invalid secret key', reason || 'Your secret key is invalid or has been changed.');
    isShowingDialog = false;
}

// Handle logged out elsewhere
async function handleLoggedOutElsewhere() {
    if (isShowingDialog) return; // Prevent popup spam

    isActivated = false;
    secretKey = null;
    window.bridge.clearSecretKey();
    activateBtn.textContent = 'Activate';
    activateBtn.disabled = false;
    frameStatus.textContent = 'Bridge offline';
    statusValue.textContent = 'offline';
    statusValue.classList.remove('online');

    // Show logged out dialog
    isShowingDialog = true;
    await window.bridge.showLoggedOutDialog();
    isShowingDialog = false;
}

// Update UI based on initial state
function updateUI() {
    activateBtn.textContent = 'Activate';
}

// Prompt for secret key using styled dialog with validation
async function promptForSecretKey() {
    if (isShowingDialog) return; // Prevent popup spam

    isShowingDialog = true;
    const result = await window.bridge.showSecretKeyDialog();
    isShowingDialog = false;

    if (result.success && result.key) {
        // Key was validated by server - save it (user must manually activate)
        secretKey = result.key;
        await window.bridge.saveSecretKey(result.key);
    }
}

// Handle update download
async function handleUpdate(downloadUrl) {
    // Download the update
    const result = await window.bridge.downloadUpdate(downloadUrl);

    if (result.success) {
        // Close app after download starts
        setTimeout(() => {
            window.bridge.quitForUpdate();
        }, 1000);
    } else {
        await window.bridge.showErrorDialog('Update failed', result.error || 'Failed to download update.');
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
