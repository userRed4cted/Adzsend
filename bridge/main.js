const { app, BrowserWindow, Tray, Menu, ipcMain, nativeImage, dialog, shell } = require('electron');
const path = require('path');
const Store = require('electron-store');
const WebSocketClient = require('./src/websocket');
const { checkForUpdates, downloadUpdate } = require('./src/updater');

// Initialize store for persistent data
// Use machine-specific encryption key derived from app path and user data path
const crypto = require('crypto');
const machineKey = crypto.createHash('sha256')
    .update(app.getPath('userData') + app.getPath('exe'))
    .digest('hex');

const store = new Store({
    name: 'adzsend-bridge-config',
    encryptionKey: machineKey
});

// Constants
const MIN_WIDTH = 380;
const MIN_HEIGHT = 480;
const VERSION = require('./package.json').version;

// Global references
let mainWindow = null;
let tray = null;
let wsClient = null;
let isQuitting = false;
let connectionStatus = 'disconnected'; // disconnected, connecting, connected

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
    app.quit();
} else {
    app.on('second-instance', () => {
        // Someone tried to run a second instance, focus our window
        if (mainWindow) {
            if (mainWindow.isMinimized()) mainWindow.restore();
            mainWindow.show();
            mainWindow.focus();
        }
    });
}

// Create the main window
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 420,
        height: 520,
        minWidth: MIN_WIDTH,
        minHeight: MIN_HEIGHT,
        frame: false, // Custom title bar
        resizable: true,
        maximizable: false,
        backgroundColor: '#121215',
        icon: path.join(__dirname, 'assets', 'favicon.ico'),
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

    // Handle close button - minimize to tray instead of quitting
    mainWindow.on('close', (event) => {
        if (!isQuitting) {
            event.preventDefault();
            mainWindow.hide();
            return false;
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    // Send version to renderer
    mainWindow.webContents.on('did-finish-load', () => {
        mainWindow.webContents.send('version', VERSION);

        // Check for updates on startup
        checkForUpdatesOnStartup();
    });
}

// Create system tray
function createTray() {
    const iconPath = path.join(__dirname, 'assets', 'favicon.ico');
    tray = new Tray(iconPath);

    updateTrayMenu();

    tray.setToolTip('Adzsend Bridge');

    // Double-click to show window
    tray.on('double-click', () => {
        if (mainWindow) {
            mainWindow.show();
            mainWindow.focus();
        }
    });
}

// Update tray menu based on connection status
function updateTrayMenu() {
    const statusText = connectionStatus === 'connected' ? 'Connected' :
                       connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected';

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Adzsend Bridge',
            enabled: false,
            icon: nativeImage.createFromPath(path.join(__dirname, 'assets', 'favicon.ico')).resize({ width: 16, height: 16 })
        },
        { type: 'separator' },
        {
            label: statusText === 'Connected' ? '\u25CF Connected' :
                   statusText === 'Connecting...' ? '\u25CB Connecting...' : '\u25CB Disconnected',
            enabled: false
        },
        { type: 'separator' },
        {
            label: 'Open Window',
            click: () => {
                if (mainWindow) {
                    mainWindow.show();
                    mainWindow.focus();
                }
            }
        },
        {
            label: 'Open Dashboard',
            click: () => {
                shell.openExternal('https://adzsend.com/dashboard');
            }
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => {
                isQuitting = true;
                if (wsClient) {
                    wsClient.disconnect();
                }
                app.quit();
            }
        }
    ]);

    tray.setContextMenu(contextMenu);
}

// Check for updates on startup
async function checkForUpdatesOnStartup() {
    try {
        const updateInfo = await checkForUpdates(VERSION);

        if (updateInfo.updateAvailable) {
            // Send update info to renderer - this will show forced update modal
            if (mainWindow) {
                mainWindow.webContents.send('update-available', updateInfo);
            }
        }
    } catch (error) {
        console.error('Error checking for updates:', error);
        // If we can't check for updates (no internet), show error
        if (mainWindow) {
            mainWindow.webContents.send('update-check-failed', { error: error.message });
        }
    }
}

// IPC Handlers

// Window controls
ipcMain.on('window-minimize', () => {
    if (mainWindow) mainWindow.minimize();
});

ipcMain.on('window-close', () => {
    if (mainWindow) mainWindow.hide();
});

// Get stored secret key
ipcMain.handle('get-secret-key', () => {
    return store.get('secretKey', null);
});

// Save secret key
ipcMain.handle('save-secret-key', (event, secretKey) => {
    store.set('secretKey', secretKey);
    return true;
});

// Clear secret key
ipcMain.handle('clear-secret-key', () => {
    store.delete('secretKey');
    return true;
});

// Get auto-start setting
ipcMain.handle('get-auto-start', () => {
    return app.getLoginItemSettings().openAtLogin;
});

// Set auto-start
ipcMain.handle('set-auto-start', (event, enabled) => {
    app.setLoginItemSettings({
        openAtLogin: enabled,
        path: app.getPath('exe')
    });
    return true;
});

// Connect to server
ipcMain.handle('connect', async (event, secretKey) => {
    return new Promise((resolve) => {
        if (wsClient && wsClient.isConnected()) {
            resolve({ success: true });
            return;
        }

        connectionStatus = 'connecting';
        updateTrayMenu();

        if (mainWindow) {
            mainWindow.webContents.send('connection-status', 'connecting');
        }

        wsClient = new WebSocketClient(secretKey, {
            onConnected: () => {
                connectionStatus = 'connected';
                updateTrayMenu();
                if (mainWindow) {
                    mainWindow.webContents.send('connection-status', 'connected');
                }
                resolve({ success: true });
            },
            onDisconnected: (reason) => {
                connectionStatus = 'disconnected';
                updateTrayMenu();
                if (mainWindow) {
                    mainWindow.webContents.send('connection-status', 'disconnected', reason);
                }
            },
            onError: (error) => {
                connectionStatus = 'disconnected';
                updateTrayMenu();
                if (mainWindow) {
                    mainWindow.webContents.send('connection-error', error);
                }
                resolve({ success: false, error: error });
            },
            onAuthFailed: (reason) => {
                connectionStatus = 'disconnected';
                updateTrayMenu();
                store.delete('secretKey');
                wsClient = null;
                if (mainWindow) {
                    mainWindow.webContents.send('auth-failed', reason);
                }
                resolve({ success: false, error: reason });
            },
            onLoggedOutElsewhere: () => {
                connectionStatus = 'disconnected';
                updateTrayMenu();
                if (mainWindow) {
                    mainWindow.webContents.send('logged-out-elsewhere');
                }
            },
            onSendCommand: (command) => {
                // Handle send command from server
                if (mainWindow) {
                    mainWindow.webContents.send('send-command', command);
                }
            },
            onMessageSent: () => {
                if (mainWindow) {
                    mainWindow.webContents.send('message-sent');
                }
            }
        });

        wsClient.connect();
    });
});

// Disconnect from server
ipcMain.handle('disconnect', async () => {
    if (wsClient) {
        wsClient.disconnect();
        wsClient = null;
    }
    connectionStatus = 'disconnected';
    updateTrayMenu();
    return true;
});

// Get connection status
ipcMain.handle('get-connection-status', () => {
    return connectionStatus;
});

// Send result back to server
ipcMain.handle('send-result', async (event, result) => {
    if (wsClient && wsClient.isConnected()) {
        wsClient.sendResult(result);
        return true;
    }
    return false;
});

// Open external URL
ipcMain.on('open-external', (event, url) => {
    shell.openExternal(url);
});

// Helper to get dialog parent window (null-safe)
function getDialogParent() {
    return mainWindow && !mainWindow.isDestroyed() ? mainWindow : null;
}

// Native-style input prompt dialog
// Note: Windows doesn't have a native input prompt dialog, so we use a minimal BrowserWindow
ipcMain.handle('show-input-dialog', async (event, title, message, placeholder = '') => {
    return new Promise((resolve) => {
        const parent = getDialogParent();
        const promptWindow = new BrowserWindow({
            width: 400,
            height: 180,
            parent: parent,
            modal: true,
            show: false,
            resizable: false,
            minimizable: false,
            maximizable: false,
            frame: false,
            backgroundColor: '#2b2b2b',
            webPreferences: {
                nodeIntegration: true,  // Required for IPC in data URL
                contextIsolation: false  // Required for IPC in data URL
            }
        });

        const html = `
<!DOCTYPE html>
<html>
<head>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, sans-serif;
            background: #2b2b2b;
            color: #fff;
            padding: 20px;
            -webkit-app-region: drag;
        }
        .title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .message {
            font-size: 12px;
            color: #aaa;
            margin-bottom: 15px;
        }
        input {
            width: 100%;
            padding: 10px 12px;
            border: 1px solid #444;
            border-radius: 4px;
            background: #1e1e1e;
            color: #fff;
            font-size: 13px;
            outline: none;
            -webkit-app-region: no-drag;
        }
        input:focus { border-color: #15d8bc; }
        input::placeholder { color: #666; }
        .buttons {
            display: flex;
            justify-content: flex-end;
            gap: 10px;
            margin-top: 15px;
            -webkit-app-region: no-drag;
        }
        button {
            padding: 8px 20px;
            border: none;
            border-radius: 4px;
            font-size: 13px;
            cursor: pointer;
        }
        .cancel { background: #444; color: #fff; }
        .cancel:hover { background: #555; }
        .ok { background: #15d8bc; color: #000; font-weight: 600; }
        .ok:hover { background: #12c5ab; }
    </style>
</head>
<body>
    <div class="title">${title.replace(/</g, '&lt;')}</div>
    <div class="message">${message.replace(/</g, '&lt;')}</div>
    <input type="password" id="input" placeholder="${placeholder.replace(/"/g, '&quot;')}" autofocus>
    <div class="buttons">
        <button class="cancel" onclick="cancel()">Cancel</button>
        <button class="ok" onclick="submit()">OK</button>
    </div>
    <script>
        const { ipcRenderer } = require('electron');
        const input = document.getElementById('input');
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') submit();
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') cancel();
        });
        function submit() {
            const val = input.value.trim();
            if (val) {
                ipcRenderer.send('prompt-response', val);
            }
        }
        function cancel() {
            ipcRenderer.send('prompt-response', null);
        }
    </script>
</body>
</html>`;

        promptWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(html)}`);

        promptWindow.once('ready-to-show', () => {
            promptWindow.show();
        });

        const responseHandler = (event, value) => {
            resolve(value);
            promptWindow.close();
        };

        ipcMain.once('prompt-response', responseHandler);

        promptWindow.on('closed', () => {
            ipcMain.removeListener('prompt-response', responseHandler);
            resolve(null);
        });
    });
});

// Native OS dialogs
ipcMain.handle('show-error-dialog', async (event, title, message) => {
    return dialog.showMessageBox(getDialogParent(), {
        type: 'error',
        buttons: ['OK'],
        title: title,
        message: message
    });
});

ipcMain.handle('show-info-dialog', async (event, title, message) => {
    return dialog.showMessageBox(getDialogParent(), {
        type: 'info',
        buttons: ['OK'],
        title: title,
        message: message
    });
});

ipcMain.handle('show-confirm-dialog', async (event, title, message, confirmText = 'Yes', cancelText = 'No') => {
    const result = await dialog.showMessageBox(getDialogParent(), {
        type: 'question',
        buttons: [confirmText, cancelText],
        defaultId: 1,
        cancelId: 1,
        title: title,
        message: message
    });
    return result.response === 0; // true if confirmed
});

ipcMain.handle('show-update-dialog', async (event, currentVersion, latestVersion) => {
    const result = await dialog.showMessageBox(getDialogParent(), {
        type: 'info',
        buttons: ['Update Now'],
        defaultId: 0,
        title: 'Update Required',
        message: 'A new version is available',
        detail: `Current: v${currentVersion}\nLatest: v${latestVersion}\n\nYou must update to continue using Adzsend Bridge.`,
        noLink: true
    });
    return result.response === 0;
});

ipcMain.handle('show-network-error-dialog', async () => {
    const result = await dialog.showMessageBox(getDialogParent(), {
        type: 'error',
        buttons: ['Retry', 'Quit'],
        defaultId: 0,
        title: 'No Internet Connection',
        message: 'Unable to connect',
        detail: 'Please check your internet connection and try again.'
    });
    return result.response === 0; // true if retry
});

ipcMain.handle('show-logged-out-dialog', async () => {
    const result = await dialog.showMessageBox(getDialogParent(), {
        type: 'warning',
        buttons: ['Open Dashboard', 'Close'],
        defaultId: 0,
        title: 'Logged Out',
        message: 'You have been logged out',
        detail: 'If this wasn\'t you, don\'t worry, your Adzsend account is safe. Regenerate your secret key to use Adzsend Bridge.'
    });
    return result.response === 0; // true if open dashboard
});

// Download and install update
ipcMain.handle('download-update', async (event, downloadUrl) => {
    try {
        await downloadUpdate(downloadUrl);
        return { success: true };
    } catch (error) {
        return { success: false, error: error.message };
    }
});

// Quit app for update
ipcMain.on('quit-for-update', () => {
    isQuitting = true;
    app.quit();
});

// App lifecycle
app.whenReady().then(() => {
    createWindow();
    createTray();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    // Don't quit on macOS when all windows are closed
    if (process.platform !== 'darwin') {
        // On Windows/Linux, keep running in tray
        // App will quit when user clicks Quit in tray
    }
});

app.on('before-quit', () => {
    isQuitting = true;
});
