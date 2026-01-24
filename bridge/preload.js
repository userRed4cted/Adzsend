const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('bridge', {
    // Window controls
    minimize: () => ipcRenderer.send('window-minimize'),
    close: () => ipcRenderer.send('window-close'),

    // Secret key management
    getSecretKey: () => ipcRenderer.invoke('get-secret-key'),
    saveSecretKey: (key) => ipcRenderer.invoke('save-secret-key', key),
    clearSecretKey: () => ipcRenderer.invoke('clear-secret-key'),

    // Connection
    connect: (secretKey) => ipcRenderer.invoke('connect', secretKey),
    disconnect: () => ipcRenderer.invoke('disconnect'),
    getConnectionStatus: () => ipcRenderer.invoke('get-connection-status'),
    sendResult: (result) => ipcRenderer.invoke('send-result', result),

    // Settings
    getAutoStart: () => ipcRenderer.invoke('get-auto-start'),
    setAutoStart: (enabled) => ipcRenderer.invoke('set-auto-start', enabled),

    // External links
    openExternal: (url) => ipcRenderer.send('open-external', url),

    // Updates
    downloadUpdate: (url) => ipcRenderer.invoke('download-update', url),
    installUpdate: () => ipcRenderer.invoke('install-update'),
    quitForUpdate: () => ipcRenderer.send('quit-for-update'),
    onUpdateStatus: (callback) => ipcRenderer.on('update-status', (event, data) => callback(data)),

    // Custom Styled Dialogs
    showErrorDialog: (title, message) => ipcRenderer.invoke('show-error-dialog', title, message),
    showInfoDialog: (title, message) => ipcRenderer.invoke('show-info-dialog', title, message),
    showConfirmDialog: (title, message, confirmText, cancelText) => ipcRenderer.invoke('show-confirm-dialog', title, message, confirmText, cancelText),
    showInputDialog: (title, message, placeholder, buttonText) => ipcRenderer.invoke('show-input-dialog', title, message, placeholder, buttonText),
    showSecretKeyDialog: () => ipcRenderer.invoke('show-secret-key-dialog'),
    showUpdateDialog: (currentVersion, latestVersion) => ipcRenderer.invoke('show-update-dialog', currentVersion, latestVersion),
    showSkippableUpdateDialog: (currentVersion, latestVersion) => ipcRenderer.invoke('show-skippable-update-dialog', currentVersion, latestVersion),
    showNetworkErrorDialog: () => ipcRenderer.invoke('show-network-error-dialog'),
    showLoggedOutDialog: () => ipcRenderer.invoke('show-logged-out-dialog'),

    // Event listeners
    onVersion: (callback) => ipcRenderer.on('version', (event, version) => callback(version)),
    onConnectionStatus: (callback) => ipcRenderer.on('connection-status', (event, status, reason) => callback(status, reason)),
    onConnectionError: (callback) => ipcRenderer.on('connection-error', (event, error) => callback(error)),
    onAuthFailed: (callback) => ipcRenderer.on('auth-failed', (event, reason) => callback(reason)),
    onLoggedOutElsewhere: (callback) => ipcRenderer.on('logged-out-elsewhere', (event) => callback()),
    onSendCommand: (callback) => ipcRenderer.on('send-command', (event, command) => callback(command)),
    onMessageSent: (callback) => ipcRenderer.on('message-sent', (event) => callback()),
    onUpdateAvailable: (callback) => ipcRenderer.on('update-available', (event, info) => callback(info)),
    onUpdateCheckFailed: (callback) => ipcRenderer.on('update-check-failed', (event, info) => callback(info)),

    // Remove listeners
    removeAllListeners: (channel) => ipcRenderer.removeAllListeners(channel)
});
