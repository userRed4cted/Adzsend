const https = require('https');

// Discord API base URL
const DISCORD_API_BASE = 'discord.com';
const API_VERSION = 'v10';

// Generate realistic browser headers
function getHeaders(token) {
    return {
        'Authorization': token,
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Origin': 'https://discord.com',
        'Referer': 'https://discord.com/channels/@me',
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'X-Discord-Locale': 'en-US',
        'X-Discord-Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
        'X-Debug-Options': 'bugReporterEnabled'
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

// Send typing indicator
async function sendTypingIndicator(token, channelId) {
    try {
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

module.exports = {
    sendDiscordMessage,
    sendTypingIndicator,
    fetchUserInfo
};
