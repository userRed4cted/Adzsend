const { app, BrowserWindow, Tray, Menu, ipcMain, nativeImage, dialog, shell } = require('electron');
const path = require('path');
const Store = require('electron-store');
const WebSocketClient = require('./src/websocket');
const { checkForUpdates, downloadUpdate } = require('./src/updater');

// Initialize store for persistent data
const store = new Store({
    name: 'adzsend-bridge-config',
    encryptionKey: 'adzsend-bridge-local-encryption-key'
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
        icon: path.join(__dirname, 'assets', 'icon.png'),
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
    const iconPath = path.join(__dirname, 'assets', 'icon.png');
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
            icon: nativeImage.createFromPath(path.join(__dirname, 'assets', 'icon.png')).resize({ width: 16, height: 16 })
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

// Show OS dialog for secret key input
ipcMain.handle('show-secret-key-dialog', async () => {
    const result = await dialog.showMessageBox(mainWindow, {
        type: 'question',
        buttons: ['Add', 'Cancel'],
        defaultId: 0,
        title: 'Modify Secret Key',
        message: 'Enter your secret key:',
        detail: 'Get your secret key from adzsend.com/dashboard/settings',
        inputType: 'text'
    });

    return result;
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
