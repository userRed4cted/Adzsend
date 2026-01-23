const https = require('https');
const { gatewayManager } = require('./discordGateway');

// Discord API base URL
const DISCORD_API_BASE = 'discord.com';
const API_VERSION = 'v10';

// Whether to use Gateway for stealth (enabled by default)
let useGateway = true;

// X-Super-Properties payload (base64 encoded client properties)
// This is what real Discord web clients send with every request
const superPropertiesData = {
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
};
const superProperties = Buffer.from(JSON.stringify(superPropertiesData)).toString('base64');

// Generate realistic browser headers
function getHeaders(token) {
    return {
        'Authorization': token,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://discord.com',
        'Referer': 'https://discord.com/channels/@me',
        'Sec-Ch-Ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'X-Discord-Locale': 'en-US',
        'X-Discord-Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
        'X-Debug-Options': 'bugReporterEnabled',
        'X-Super-Properties': superProperties
    };
}

// Make HTTP request to Discord API
function makeRequest(method, path, token, body = null) {
    return new Promise((resolve, reject) => {
        const options = {
            hostname: DISCORD_API_BASE,
            port: 443,
            path: `/api/${API_VERSION}${path}`,
            method: method,
            headers: getHeaders(token),
            timeout: 15000
        };

        const req = https.request(options, (res) => {
            let data = '';

            res.on('data', (chunk) => {
                data += chunk;
            });

            res.on('end', () => {
                try {
                    const parsed = data ? JSON.parse(data) : {};
                    resolve({
                        status: res.statusCode,
                        data: parsed
                    });
                } catch (error) {
                    resolve({
                        status: res.statusCode,
                        data: data
                    });
                }
            });
        });

        req.setTimeout(15000, () => {
            req.destroy();
            reject(new Error('Request timeout'));
        });

        req.on('error', (error) => {
            reject(error);
        });

        if (body) {
            req.write(JSON.stringify(body));
        }

        req.end();
    });
}

/**
 * Ensure Gateway connection exists for token (for stealth)
 * This makes REST API calls appear to come from a real Discord client
 * @param {string} token - Discord token
 */
async function ensureGatewayConnection(token) {
    if (!useGateway) return;

    try {
        // Connect with 'online' status - more natural than invisible when sending messages
        await gatewayManager.ensureConnection(token, 'online');
    } catch (error) {
        // Gateway connection failed, but we can still use REST API
        console.warn('[Discord] Gateway connection failed, using REST only:', error.message);
    }
}

// Send typing indicator
async function sendTypingIndicator(token, channelId) {
    try {
        // Ensure Gateway connection first (for stealth)
        await ensureGatewayConnection(token);

        const response = await makeRequest('POST', `/channels/${channelId}/typing`, token);
        return response.status === 204 || response.status === 200;
    } catch (error) {
        console.error('Error sending typing indicator:', error);
        return false;
    }
}

// Send a message to a Discord channel
async function sendDiscordMessage(token, channelId, content) {
    try {
        // Ensure Gateway connection first (for stealth)
        await ensureGatewayConnection(token);

        const response = await makeRequest(
            'POST',
            `/channels/${channelId}/messages`,
            token,
            { content: content }
        );

        if (response.status === 200 || response.status === 201) {
            return {
                success: true,
                message_id: response.data.id
            };
        } else if (response.status === 401) {
            return {
                success: false,
                error: 'token_invalid',
                message: 'Discord token is invalid or expired'
            };
        } else if (response.status === 403) {
            return {
                success: false,
                error: 'forbidden',
                message: response.data.message || 'Missing permissions to send in this channel'
            };
        } else if (response.status === 429) {
            // Rate limited
            const retryAfter = response.data.retry_after || 5;
            return {
                success: false,
                error: 'rate_limited',
                retry_after: retryAfter,
                message: `Rate limited. Retry after ${retryAfter} seconds`
            };
        } else {
            return {
                success: false,
                error: 'unknown',
                message: response.data.message || `Error ${response.status}`
            };
        }
    } catch (error) {
        return {
            success: false,
            error: 'network_error',
            message: error.message
        };
    }
}

// Fetch user info (for verification)
async function fetchUserInfo(token) {
    try {
        const response = await makeRequest('GET', '/users/@me', token);

        if (response.status === 200) {
            return {
                success: true,
                user: response.data
            };
        } else {
            return {
                success: false,
                error: response.data.message || 'Failed to fetch user info'
            };
        }
    } catch (error) {
        return {
            success: false,
            error: error.message
        };
    }
}

// Enable/disable Gateway mode
function setGatewayMode(enabled) {
    useGateway = enabled;
    if (!enabled) {
        gatewayManager.disconnectAll();
    }
}

// Check if Gateway mode is enabled
function isGatewayEnabled() {
    return useGateway;
}

// Get Gateway connection count
function getGatewayConnectionCount() {
    return gatewayManager.getConnectionCount();
}

// Cleanup all Gateway connections
function cleanupGateway() {
    gatewayManager.disconnectAll();
}

module.exports = {
    sendDiscordMessage,
    sendTypingIndicator,
    fetchUserInfo,
    setGatewayMode,
    isGatewayEnabled,
    getGatewayConnectionCount,
    cleanupGateway,
    ensureGatewayConnection
};
