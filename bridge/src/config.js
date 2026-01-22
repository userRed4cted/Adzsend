// =============================================================================
// BRIDGE CONFIGURATION
// =============================================================================
// Centralized config for the bridge app - edit URLs here for production/dev

// Detect if running in development (packaged apps won't have this)
const isDevelopment = !process.resourcesPath || process.env.NODE_ENV === 'development';

// Server URLs
const PRODUCTION_WS_URL = 'wss://adzsend.com/bridge/ws';
const DEVELOPMENT_WS_URL = 'ws://127.0.0.1:5000/bridge/ws';

// Export the appropriate URL based on environment
const SERVER_URL = isDevelopment ? DEVELOPMENT_WS_URL : PRODUCTION_WS_URL;

module.exports = {
    SERVER_URL,
    isDevelopment,
    PRODUCTION_WS_URL,
    DEVELOPMENT_WS_URL
};
