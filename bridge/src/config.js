// =============================================================================
// BRIDGE CONFIGURATION
// =============================================================================

// =====================
// EDIT THIS LINE ONLY:
// =====================
// Set to true for local Flask testing, false for production (adzsend.com)
const USE_LOCAL_SERVER = true;

// Server URLs (don't edit these)
const PRODUCTION_WS_URL = 'wss://adzsend.com/bridge/ws';
const DEVELOPMENT_WS_URL = 'ws://127.0.0.1:5000/bridge/ws';

// Uses the setting above
const isDevelopment = USE_LOCAL_SERVER || process.env.ADZSEND_DEV === 'true';
const SERVER_URL = isDevelopment ? DEVELOPMENT_WS_URL : PRODUCTION_WS_URL;

module.exports = {
    SERVER_URL,
    isDevelopment,
    PRODUCTION_WS_URL,
    DEVELOPMENT_WS_URL
};
