// =============================================================================
// BRIDGE CONFIGURATION
// =============================================================================
// Centralized config for the bridge app - edit URLs here for production/dev

// Server URLs
const PRODUCTION_WS_URL = 'wss://adzsend.com/bridge/ws';
const DEVELOPMENT_WS_URL = 'ws://127.0.0.1:5000/bridge/ws';

// Detect if running in development
// Only use local server if explicitly set via environment variable
const isDevelopment = process.env.ADZSEND_DEV === 'true';

// Export the appropriate URL based on environment
// Default to production for safety (npm start will use production)
const SERVER_URL = isDevelopment ? DEVELOPMENT_WS_URL : PRODUCTION_WS_URL;

module.exports = {
    SERVER_URL,
    isDevelopment,
    PRODUCTION_WS_URL,
    DEVELOPMENT_WS_URL
};
