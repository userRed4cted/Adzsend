const WebSocket = require('ws');

// Discord Gateway URL
const GATEWAY_URL = 'wss://gateway.discord.gg/?v=10&encoding=json';

// Gateway opcodes
const GatewayOpcodes = {
    DISPATCH: 0,
    HEARTBEAT: 1,
    IDENTIFY: 2,
    PRESENCE_UPDATE: 3,
    VOICE_STATE_UPDATE: 4,
    RESUME: 6,
    RECONNECT: 7,
    REQUEST_GUILD_MEMBERS: 8,
    INVALID_SESSION: 9,
    HELLO: 10,
    HEARTBEAT_ACK: 11
};

// Connection states
const ConnectionState = {
    DISCONNECTED: 'disconnected',
    CONNECTING: 'connecting',
    CONNECTED: 'connected',
    RESUMING: 'resuming'
};

/**
 * Discord Gateway Client
 * Maintains a WebSocket connection to Discord's Gateway for stealth
 */
class DiscordGatewayClient {
    constructor(token) {
        this.token = token;
        this.ws = null;
        this.state = ConnectionState.DISCONNECTED;
        this.heartbeatInterval = null;
        this.heartbeatTimeout = null; // Track initial heartbeat timeout
        this.heartbeatAcked = true;
        this.sequence = null;
        this.sessionId = null;
        this.resumeGatewayUrl = null;
        this.lastHeartbeatSent = null;
        this.latency = 0;
        this.currentStatus = 'online'; // Track current status
    }

    /**
     * Connect to Discord Gateway
     * @param {string} status - Presence status ('online', 'idle', 'dnd', 'invisible', or 'match' to match user's settings)
     */
    connect(status = 'online') {
        return new Promise((resolve, reject) => {
            if (this.state !== ConnectionState.DISCONNECTED) {
                resolve(true);
                return;
            }

            // Store status
            this.currentStatus = status;
            this.state = ConnectionState.CONNECTING;
            const url = this.resumeGatewayUrl || GATEWAY_URL;

            try {
                this.ws = new WebSocket(url);

                const timeout = setTimeout(() => {
                    if (this.state === ConnectionState.CONNECTING) {
                        this.ws.terminate();
                        reject(new Error('Gateway connection timeout'));
                    }
                }, 30000);

                this.ws.on('open', () => {
                    // Connection opened - wait for HELLO
                });

                this.ws.on('message', (data) => {
                    try {
                        const message = JSON.parse(data.toString());
                        this.handleMessage(message, status, resolve, reject, timeout);
                    } catch (error) {
                        // Silent fail on parse errors
                    }
                });

                this.ws.on('close', (code, reason) => {
                    this.handleClose(code);
                });

                this.ws.on('error', (error) => {
                    if (this.state === ConnectionState.CONNECTING) {
                        clearTimeout(timeout);
                        reject(error);
                    }
                });

            } catch (error) {
                this.state = ConnectionState.DISCONNECTED;
                reject(error);
            }
        });
    }

    handleMessage(message, status, resolve, reject, timeout) {
        const { op, d, s, t } = message;

        // Update sequence number
        if (s !== null) {
            this.sequence = s;
        }

        switch (op) {
            case GatewayOpcodes.HELLO:
                // Start heartbeating
                this.startHeartbeat(d.heartbeat_interval);

                // Either identify or resume
                if (this.sessionId && this.sequence !== null) {
                    this.sendResume();
                } else {
                    this.sendIdentify(status);
                }
                break;

            case GatewayOpcodes.HEARTBEAT:
                // Server requested immediate heartbeat
                this.sendHeartbeat();
                break;

            case GatewayOpcodes.HEARTBEAT_ACK:
                this.heartbeatAcked = true;
                if (this.lastHeartbeatSent) {
                    this.latency = Date.now() - this.lastHeartbeatSent;
                }
                break;

            case GatewayOpcodes.DISPATCH:
                this.handleDispatch(t, d, resolve, timeout);
                break;

            case GatewayOpcodes.RECONNECT:
                this.reconnect();
                break;

            case GatewayOpcodes.INVALID_SESSION:
                if (d) {
                    // Can resume
                    setTimeout(() => this.sendResume(), 1000 + Math.random() * 4000);
                } else {
                    // Cannot resume, need fresh identify
                    this.sessionId = null;
                    this.sequence = null;
                    setTimeout(() => this.sendIdentify(status), 1000 + Math.random() * 4000);
                }
                break;

            default:
                // Unknown opcode
                break;
        }
    }

    handleDispatch(eventName, data, resolve, timeout) {
        switch (eventName) {
            case 'READY':
                this.state = ConnectionState.CONNECTED;
                this.sessionId = data.session_id;
                this.resumeGatewayUrl = data.resume_gateway_url;

                // If user's status from settings is available, update presence to match
                // This makes the bridge appear exactly as the user's Discord app would

                clearTimeout(timeout);
                resolve(true);
                break;

            case 'RESUMED':
                this.state = ConnectionState.CONNECTED;
                clearTimeout(timeout);
                resolve(true);
                break;

            case 'SESSIONS_REPLACE':
                // Discord sends this when sessions change
                // Could be used to sync status with other sessions
                break;

            default:
                // Ignore other events - we only need the connection
                break;
        }
    }

    handleClose(code) {
        this.stopHeartbeat();
        this.state = ConnectionState.DISCONNECTED;

        // Handle specific close codes
        const nonRecoverableCodes = [4004, 4010, 4011, 4012, 4013, 4014];
        if (nonRecoverableCodes.includes(code)) {
            this.sessionId = null;
            this.sequence = null;
        }
        // No auto-reconnect - user must manually reactivate bridge
    }

    sendIdentify(status = 'online') {
        // Validate status - default to 'online' if invalid
        const validStatuses = ['online', 'idle', 'dnd', 'invisible'];
        const presenceStatus = validStatuses.includes(status) ? status : 'online';

        // Use properties that match a real Discord web client
        const payload = {
            op: GatewayOpcodes.IDENTIFY,
            d: {
                token: this.token,
                intents: 0, // No intents needed - we just want the session
                properties: {
                    os: 'Windows',
                    browser: 'Chrome',
                    device: '',
                    system_locale: 'en-US',
                    browser_user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                    browser_version: '131.0.0.0',
                    os_version: '10',
                    referrer: '',
                    referring_domain: '',
                    referrer_current: '',
                    referring_domain_current: '',
                    release_channel: 'stable',
                    client_build_number: 307749,
                    client_event_source: null
                },
                presence: {
                    status: presenceStatus,
                    since: null,
                    activities: [],
                    afk: false
                },
                compress: false,
                client_state: {
                    guild_versions: {},
                    highest_last_message_id: '0',
                    read_state_version: 0,
                    user_guild_settings_version: -1,
                    user_settings_version: -1,
                    private_channels_version: '0',
                    api_code_version: 0
                }
            }
        };
        this.send(payload);
    }

    sendResume() {
        this.state = ConnectionState.RESUMING;
        const payload = {
            op: GatewayOpcodes.RESUME,
            d: {
                token: this.token,
                session_id: this.sessionId,
                seq: this.sequence
            }
        };
        this.send(payload);
    }

    startHeartbeat(interval) {
        this.stopHeartbeat();

        // Send first heartbeat after jitter
        const jitter = Math.random() * interval;
        this.heartbeatTimeout = setTimeout(() => {
            this.heartbeatTimeout = null;
            this.sendHeartbeat();
            // Then send heartbeats at regular interval
            this.heartbeatInterval = setInterval(() => {
                if (!this.heartbeatAcked) {
                    this.ws.terminate();
                    return;
                }
                this.sendHeartbeat();
            }, interval);
        }, jitter);
    }

    stopHeartbeat() {
        if (this.heartbeatTimeout) {
            clearTimeout(this.heartbeatTimeout);
            this.heartbeatTimeout = null;
        }
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    sendHeartbeat() {
        this.heartbeatAcked = false;
        this.lastHeartbeatSent = Date.now();
        this.send({
            op: GatewayOpcodes.HEARTBEAT,
            d: this.sequence
        });
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    reconnect() {
        const status = this.currentStatus;
        this.disconnect();
        setTimeout(() => this.connect(status), 1000);
    }

    disconnect() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close(1000);
            this.ws = null;
        }
        this.state = ConnectionState.DISCONNECTED;
    }

    isConnected() {
        return this.state === ConnectionState.CONNECTED;
    }

    getLatency() {
        return this.latency;
    }
}

/**
 * Gateway Connection Manager
 * Manages multiple Gateway connections for different Discord tokens
 */
class GatewayManager {
    constructor() {
        this.connections = new Map(); // token -> DiscordGatewayClient
        this.cleanupTimeouts = new Map(); // token -> cleanup timeout
    }

    /**
     * Get random idle timeout between 3-6 minutes (looks more natural)
     */
    getRandomIdleTimeout() {
        const minMs = 3 * 60 * 1000; // 3 minutes
        const maxMs = 6 * 60 * 1000; // 6 minutes
        return minMs + Math.random() * (maxMs - minMs);
    }

    /**
     * Schedule cleanup for a specific token
     */
    scheduleCleanup(token) {
        // Clear existing timeout for this token
        if (this.cleanupTimeouts.has(token)) {
            clearTimeout(this.cleanupTimeouts.get(token));
        }

        // Schedule new cleanup with random delay
        const delay = this.getRandomIdleTimeout();
        const timeout = setTimeout(() => {
            this.disconnect(token);
        }, delay);

        this.cleanupTimeouts.set(token, timeout);
    }

    /**
     * Ensure a Gateway connection exists for a token
     * @param {string} token - Discord token
     * @param {string} status - Presence status ('online', 'idle', 'dnd', 'invisible')
     */
    async ensureConnection(token, status = 'online') {
        // Reset cleanup timer (message was sent, so keep connection alive)
        this.scheduleCleanup(token);

        // Check if already connected
        if (this.connections.has(token)) {
            const client = this.connections.get(token);
            if (client.isConnected()) {
                return client;
            }
            // Exists but not connected, remove it
            client.disconnect();
            this.connections.delete(token);
        }

        // Create new connection
        const client = new DiscordGatewayClient(token);
        try {
            await client.connect(status);
            this.connections.set(token, client);
            return client;
        } catch (error) {
            throw error;
        }
    }

    /**
     * Disconnect a specific token
     */
    disconnect(token) {
        // Clear cleanup timeout
        if (this.cleanupTimeouts.has(token)) {
            clearTimeout(this.cleanupTimeouts.get(token));
            this.cleanupTimeouts.delete(token);
        }

        // Disconnect and remove connection
        if (this.connections.has(token)) {
            this.connections.get(token).disconnect();
            this.connections.delete(token);
        }
    }

    /**
     * Disconnect all tokens
     */
    disconnectAll() {
        // Clear all cleanup timeouts
        for (const timeout of this.cleanupTimeouts.values()) {
            clearTimeout(timeout);
        }
        this.cleanupTimeouts.clear();

        // Disconnect all connections
        for (const client of this.connections.values()) {
            client.disconnect();
        }
        this.connections.clear();
    }

    /**
     * Get connection count
     */
    getConnectionCount() {
        return this.connections.size;
    }
}

// Singleton instance
const gatewayManager = new GatewayManager();

module.exports = {
    DiscordGatewayClient,
    GatewayManager,
    gatewayManager
};
