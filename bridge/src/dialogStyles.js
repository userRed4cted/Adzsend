// =============================================================================
// CENTRALIZED DIALOG STYLES FOR BRIDGE
// =============================================================================
// Common styles shared across all Electron dialog windows
// Matches the main website style exactly

const baseStyles = `
    @font-face {
        font-family: 'gg sans';
        src: local('Segoe UI'), local('Arial');
    }
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body {
        background: transparent !important;
        height: 100%;
        overflow: hidden;
    }
    body {
        font-family: 'gg sans', 'Segoe UI', sans-serif;
        color: #fff;
        padding: 1px;
    }
    .dialog-container {
        background: #1A1A1E;
        padding: 1.25rem 1.5rem 1.5rem 1.5rem;
        border: 1px solid #222225;
        border-radius: 8px;
        height: calc(100% - 2px);
        display: flex;
        flex-direction: column;
        position: relative;
        overflow: hidden;
    }
    .close-btn {
        position: absolute;
        top: 0.75rem;
        right: 0.75rem;
        background: transparent;
        border: 1px solid transparent;
        color: #81828A;
        font-size: 1.5rem;
        cursor: pointer;
        padding: 0;
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 300;
        line-height: 1;
        border-radius: 4px;
        transition: all 0.2s ease;
    }
    .close-btn:hover {
        background: #1A1A1E;
        border-color: #222225;
        color: white;
    }
    .close-btn:active, .close-btn:focus {
        background: #1A1A1E;
        border-color: #222225;
        color: white;
        outline: none;
    }
    .title {
        font-size: 1.125rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #ffffff;
        padding-right: 2rem;
    }
    .message {
        font-size: 0.8925rem;
        color: #81828A;
        line-height: 1.4;
        white-space: pre-wrap;
    }
    .buttons {
        margin-top: auto;
        padding-top: 1rem;
    }
    button.ok {
        width: 100%;
        background: linear-gradient(to bottom, #15d8bc, #006e59);
        color: #121215;
        border: none;
        border-radius: 4px;
        padding: 0.65rem 1.25rem;
        font-size: 0.875rem;
        font-weight: 600;
        font-family: 'gg sans', 'Segoe UI', sans-serif;
        cursor: pointer;
        transition: filter 0.2s ease;
        min-height: 38px;
    }
    button.ok:hover:not(:disabled) { filter: brightness(1.1); }
    button.ok:active:not(:disabled) { filter: brightness(0.9); }
    button.ok:disabled { cursor: not-allowed; opacity: 0.8; }
`;

const inputStyles = `
    input {
        width: 100%;
        padding: 0.6rem 0.75rem;
        border: 1px solid #222225;
        border-radius: 6px;
        background: #121215;
        color: #dcddde;
        font-size: 0.875rem;
        font-family: 'gg sans', 'Segoe UI', sans-serif;
        outline: none;
    }
    input:focus { border-color: #222225; }
    input::placeholder { color: #81828A; }
    input:disabled { opacity: 0.6; }
`;

const loadingDotsStyles = `
    .loading-dots {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
    }
    .loading-dots .dot {
        width: 8px;
        height: 8px;
        background-color: #121215;
        border-radius: 50%;
        animation: dot-pulse 1.4s infinite ease-in-out both;
        will-change: opacity, transform;
    }
    .loading-dots .dot:nth-child(1) { animation-delay: 0s; }
    .loading-dots .dot:nth-child(2) { animation-delay: 0.16s; }
    .loading-dots .dot:nth-child(3) { animation-delay: 0.32s; }
    @keyframes dot-pulse {
        0%, 80%, 100% { opacity: 0.4; transform: scale(0.8); }
        40% { opacity: 1; transform: scale(1); }
    }
`;

// Loading dots HTML
const loadingDotsHTML = '<div class="loading-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Get combined styles for different dialog types
function getDialogStyles(options = {}) {
    let styles = baseStyles;
    if (options.hasInput) {
        styles += inputStyles;
    }
    if (options.hasLoading) {
        styles += loadingDotsStyles;
    }
    return styles;
}

// Get standard dialog window options
function getDialogWindowOptions(parent, customOptions = {}) {
    const options = {
        width: customOptions.width || 440,
        height: customOptions.height || 180,
        show: false,
        resizable: false,
        minimizable: false,
        maximizable: false,
        frame: false,
        transparent: true,
        backgroundColor: '#00000000',
        hasShadow: false,
        skipTaskbar: true,
        alwaysOnTop: false, // Don't show on top of other apps
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        },
        ...customOptions
    };

    // Set parent to keep dialog with main window when switching apps
    if (parent && !parent.isDestroyed()) {
        options.parent = parent;
        const parentBounds = parent.getBounds();
        options.x = Math.round(parentBounds.x + (parentBounds.width - options.width) / 2);
        options.y = Math.round(parentBounds.y + (parentBounds.height - options.height) / 2);
    }

    return options;
}

// Safely close a dialog window (hide first to prevent visual glitches)
function closeDialog(window) {
    if (!window || window.isDestroyed()) return;
    window.hide();
    setImmediate(() => {
        if (!window.isDestroyed()) {
            window.close();
        }
    });
}

module.exports = {
    baseStyles,
    inputStyles,
    loadingDotsStyles,
    loadingDotsHTML,
    escapeHtml,
    getDialogStyles,
    getDialogWindowOptions,
    closeDialog
};
