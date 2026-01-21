// DOM Elements
const minimizeBtn = document.getElementById('minimize-btn');
const closeBtn = document.getElementById('close-btn');
const modifyKeyBtn = document.getElementById('modify-key-btn');
const activateBtn = document.getElementById('activate-btn');
const statusValue = document.getElementById('status-value');
const frameStatus = document.getElementById('frame-status');
const messagesCounter = document.getElementById('messages-counter');
const messagesCount = document.getElementById('messages-count');
const openDashboardBtn = document.getElementById('open-dashboard-btn');
const settingsBtn = document.getElementById('settings-btn');
const versionDisplay = document.getElementById('version-display');

// Modals
const secretKeyModal = document.getElementById('secret-key-modal');
const errorModal = document.getElementById('error-modal');
const loggedOutModal = document.getElementById('logged-out-modal');
const updateModal = document.getElementById('update-modal');
const networkModal = document.getElementById('network-modal');
const settingsModal = document.getElementById('settings-modal');

// State
let isActivated = false;
let secretKey = null;
let messagesSent = 0;

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

    // Modify key button
    modifyKeyBtn.addEventListener('click', showSecretKeyModal);

    // Activate button
    activateBtn.addEventListener('click', handleActivate);

    // Action buttons
    openDashboardBtn.addEventListener('click', () => {
        window.bridge.openExternal('https://adzsend.com/dashboard');
    });

    settingsBtn.addEventListener('click', showSettingsModal);

    // Secret Key Modal
    document.getElementById('modal-close').addEventListener('click', hideSecretKeyModal);
    document.getElementById('modal-cancel').addEventListener('click', hideSecretKeyModal);
    document.getElementById('modal-add').addEventListener('click', handleAddSecretKey);
    document.getElementById('settings-link').addEventListener('click', (e) => {
        e.preventDefault();
        window.bridge.openExternal('https://adzsend.com/dashboard/settings');
    });

    // Error Modal
    document.getElementById('error-close').addEventListener('click', hideErrorModal);
    document.getElementById('error-cancel').addEventListener('click', hideErrorModal);
    document.getElementById('error-retry').addEventListener('click', () => {
        hideErrorModal();
        handleActivate();
    });

    // Logged Out Modal
    document.getElementById('logged-out-dashboard').addEventListener('click', () => {
        window.bridge.openExternal('https://adzsend.com/dashboard/settings');
        hideLoggedOutModal();
    });
    document.getElementById('logged-out-close').addEventListener('click', hideLoggedOutModal);

    // Update Modal
    document.getElementById('update-btn').addEventListener('click', handleUpdate);

    // Network Modal
    document.getElementById('network-retry').addEventListener('click', () => {
        hideNetworkModal();
        handleActivate();
    });
    document.getElementById('network-close').addEventListener('click', () => {
        hideNetworkModal();
        window.bridge.close();
    });

    // Settings Modal
    document.getElementById('settings-close').addEventListener('click', hideSettingsModal);
    document.getElementById('settings-key-change').addEventListener('click', () => {
        hideSettingsModal();
        showSecretKeyModal();
    });
    document.getElementById('settings-save').addEventListener('click', saveSettings);

    // Enter key in secret key input
    document.getElementById('secret-key-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleAddSecretKey();
        }
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

    window.bridge.onMessageSent(() => {
        messagesSent++;
        messagesCount.textContent = messagesSent;
    });

    window.bridge.onUpdateAvailable((info) => {
        showUpdateModal(info);
    });

    window.bridge.onUpdateCheckFailed((info) => {
        showNetworkModal();
    });
}

// Handle activate/deactivate
async function handleActivate() {
    if (isActivated) {
        // Deactivate
        frameStatus.textContent = 'Bridge disconnecting';
        activateBtn.disabled = true;
        await window.bridge.disconnect();
    } else {
        // Check if we have a secret key
        if (!secretKey) {
            showSecretKeyModal();
            return;
        }

        // Activate
        frameStatus.textContent = 'Bridge connecting';
        activateBtn.textContent = 'Deactivate';
        activateBtn.disabled = true;

        const result = await window.bridge.connect(secretKey);

        if (!result.success) {
            // Error handled by IPC listeners
            activateBtn.textContent = 'Activate';
            activateBtn.disabled = false;
            frameStatus.textContent = 'Bridge offline';
        }
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
            messagesCounter.style.display = 'block';
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
function handleConnectionError(error) {
    isActivated = false;
    activateBtn.textContent = 'Activate';
    activateBtn.disabled = false;
    frameStatus.textContent = 'Bridge offline';
    statusValue.textContent = 'offline';
    statusValue.classList.remove('online');

    if (error.includes('ENOTFOUND') || error.includes('network') || error.includes('internet')) {
        showNetworkModal();
    } else {
        showErrorModal('Connection Error', error);
    }
}

// Handle auth failed
function handleAuthFailed(reason) {
    isActivated = false;
    secretKey = null;
    window.bridge.clearSecretKey();
    activateBtn.textContent = 'Activate';
    activateBtn.disabled = false;
    frameStatus.textContent = 'Bridge offline';
    statusValue.textContent = 'offline';
    statusValue.classList.remove('online');

    showErrorModal('Invalid Secret Key', reason || 'Your secret key is invalid or has been changed. Please enter a new key.');
}

// Handle logged out elsewhere
function handleLoggedOutElsewhere() {
    isActivated = false;
    secretKey = null;
    window.bridge.clearSecretKey();
    activateBtn.textContent = 'Activate';
    activateBtn.disabled = false;
    frameStatus.textContent = 'Bridge offline';
    statusValue.textContent = 'offline';
    statusValue.classList.remove('online');

    showLoggedOutModal();
}

// Update UI based on state
function updateUI() {
    if (secretKey) {
        activateBtn.textContent = 'Activate';
    } else {
        activateBtn.textContent = 'Activate';
    }
}

// Modal functions
function showSecretKeyModal() {
    document.getElementById('secret-key-input').value = '';
    secretKeyModal.style.display = 'flex';
    document.getElementById('secret-key-input').focus();
}

function hideSecretKeyModal() {
    secretKeyModal.style.display = 'none';
}

async function handleAddSecretKey() {
    const input = document.getElementById('secret-key-input');
    const key = input.value.trim();

    if (!key) {
        return;
    }

    secretKey = key;
    await window.bridge.saveSecretKey(key);
    hideSecretKeyModal();

    // Automatically try to connect
    handleActivate();
}

function showErrorModal(title, message) {
    document.getElementById('error-title').textContent = title;
    document.getElementById('error-message').textContent = message;
    errorModal.style.display = 'flex';
}

function hideErrorModal() {
    errorModal.style.display = 'none';
}

function showLoggedOutModal() {
    loggedOutModal.style.display = 'flex';
}

function hideLoggedOutModal() {
    loggedOutModal.style.display = 'none';
}

function showUpdateModal(info) {
    document.getElementById('current-version').textContent = info.currentVersion;
    document.getElementById('latest-version').textContent = info.latestVersion;
    updateModal.style.display = 'flex';
}

async function handleUpdate() {
    const btn = document.getElementById('update-btn');
    btn.textContent = 'Downloading...';
    btn.disabled = true;

    // Open download URL in browser
    const updateInfo = await window.bridge.downloadUpdate();

    // Close app after opening download
    setTimeout(() => {
        window.bridge.quitForUpdate();
    }, 1000);
}

function showNetworkModal() {
    networkModal.style.display = 'flex';
}

function hideNetworkModal() {
    networkModal.style.display = 'none';
}

async function showSettingsModal() {
    // Load current settings
    const autoStart = await window.bridge.getAutoStart();
    document.getElementById('auto-start-checkbox').checked = autoStart;

    // Show current key (masked)
    const keyDisplay = document.getElementById('settings-key-display');
    if (secretKey) {
        keyDisplay.value = secretKey.substring(0, 20) + '...';
    } else {
        keyDisplay.value = 'No key set';
    }

    settingsModal.style.display = 'flex';
}

function hideSettingsModal() {
    settingsModal.style.display = 'none';
}

async function saveSettings() {
    const autoStart = document.getElementById('auto-start-checkbox').checked;
    await window.bridge.setAutoStart(autoStart);
    hideSettingsModal();
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
