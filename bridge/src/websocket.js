const WebSocket = require('ws');
const { sendDiscordMessage, sendTypingIndicator } = require('./discord');

// Server URL - update this for production
const SERVER_URL = 'wss://adzsend.com/bridge/ws';
// For development:
// const SERVER_URL = 'ws://localhost:5000/bridge/ws';

class WebSocketClient {
    constructor(secretKey, callbacks) {
        this.secretKey = secretKey;
        this.callbacks = callbacks;
        this.ws = null;
        this.isConnectedFlag = false;
        this.heartbeatInterval = null;
        this.connectionTimeout = null;
        this.messagesSentThisSession = 0;
    }

    connect() {
        try {
            this.ws = new WebSocket(SERVER_URL);

            // Set connection timeout (15 seconds)
            this.connectionTimeout = setTimeout(() => {
                if (!this.isConnectedFlag && this.ws) {
                    console.log('Connection timeout');
                    this.ws.terminate();
                    this.callbacks.onError('Connection timeout - server not responding');
                }
            }, 15000);

            this.ws.on('open', () => {
                console.log('WebSocket connection opened');
                // Send authentication
                this.send({
                    type: 'auth',
                    secret_key: this.secretKey
                });
            });

            this.ws.on('message', (data) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.handleMessage(message);
                } catch (error) {
                    console.error('Error parsing message:', error);
                }
            });

            this.ws.on('close', (code, reason) => {
                console.log('WebSocket closed:', code, reason.toString());
                this.isConnectedFlag = false;
                this.stopHeartbeat();

                // Handle different close codes
                if (code === 4001) {
                    // Invalid secret key
                    this.callbacks.onAuthFailed('Invalid secret key');
                } else if (code === 4002) {
                    // Logged in elsewhere
                    this.callbacks.onLoggedOutElsewhere();
                } else if (code === 4003) {
                    // Key changed/revoked
                    this.callbacks.onAuthFailed('Secret key has been changed or revoked');
                } else if (code === 1000) {
                    // Normal disconnect (user initiated)
                    this.callbacks.onDisconnected(reason.toString() || 'Disconnected');
                } else {
                    // Unexpected disconnect - don't auto-reconnect, let user decide
                    this.callbacks.onDisconnected(reason.toString() || 'Connection lost');
                }
            });

            this.ws.on('error', (error) => {
                console.error('WebSocket error:', error);
                this.callbacks.onError(error.message || 'Connection error');
            });

        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.callbacks.onError(error.message || 'Failed to connect');
        }
    }

    handleMessage(message) {
        switch (message.type) {
            case 'auth_success':
                console.log('Authentication successful');
                this.isConnectedFlag = true;
                this.clearConnectionTimeout();
                this.startHeartbeat();
                this.callbacks.onConnected();
                break;

            case 'auth_failed':
                console.log('Authentication failed:', message.reason);
                this.callbacks.onAuthFailed(message.reason || 'Authentication failed');
                break;

            case 'pong':
                // Heartbeat acknowledged
                break;

            case 'send':
                // Server wants us to send messages
                this.handleSendCommand(message);
                break;

            case 'logged_out':
                // Logged in from another device
                this.callbacks.onLoggedOutElsewhere();
                break;

            default:
                console.log('Unknown message type:', message.type);
        }
    }

    async handleSendCommand(command) {
        const results = [];

        // Validate command structure
        if (!command || !Array.isArray(command.tasks) || command.tasks.length === 0) {
            console.error('Invalid command structure received');
            this.send({
                type: 'send_result',
                id: command?.id || 'unknown',
                results: [{ success: false, error: 'Invalid command structure' }]
            });
            return;
        }

        const tasks = command.tasks;
        for (let i = 0; i < tasks.length; i++) {
            const task = tasks[i];
            // Validate task has required fields
            if (!task.discord_token || !task.channel_id || !task.message) {
                results.push({
                    channel_id: task?.channel_id || 'unknown',
                    success: false,
                    error: 'Missing required task fields'
                });
                continue;
            }
            try {
                // Add random delay variation of ±0.5 seconds (±500ms)
                // This makes timing more human-like and less detectable
                const baseDelay = task.delay || 0;
                const fixedVariation = 500; // ±0.5 seconds
                const randomOffset = (Math.random() * fixedVariation * 2) - fixedVariation;
                const actualDelay = Math.max(0, baseDelay + randomOffset);

                // Send typing indicator first
                await sendTypingIndicator(task.discord_token, task.channel_id);

                // Wait for typing simulation (0.5 - 0.8 seconds, randomized)
                const typingDelay = 500 + Math.random() * 300;
                await this.sleep(typingDelay);

                // Send the message
                const result = await sendDiscordMessage(
                    task.discord_token,
                    task.channel_id,
                    task.message
                );

                results.push({
                    channel_id: task.channel_id,
                    success: result.success,
                    message_id: result.message_id,
                    error: result.error
                });

                if (result.success) {
                    this.messagesSentThisSession++;
                    this.callbacks.onMessageSent();
                } else if (result.error === 'token_invalid') {
                    // Token is invalid - stop sending, mark remaining as failed
                    // No popup - user will see invalid status in dashboard

                    // Mark remaining tasks as failed (don't waste API calls)
                    for (let j = i + 1; j < tasks.length; j++) {
                        results.push({
                            channel_id: tasks[j].channel_id || 'unknown',
                            success: false,
                            error: 'token_invalid'
                        });
                    }
                    break; // Stop the loop
                }

                // Wait before next message (if there is one)
                if (i < tasks.length - 1 && actualDelay > 0) {
                    await this.sleep(actualDelay);
                }

            } catch (error) {
                results.push({
                    channel_id: task.channel_id,
                    success: false,
                    error: error.message
                });
            }
        }

        // Send results back to server
        this.send({
            type: 'send_result',
            id: command.id,
            results: results
        });
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnectedFlag) {
                this.send({ type: 'ping' });
            }
        }, 30000); // Every 30 seconds
    }

    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }

    clearConnectionTimeout() {
        if (this.connectionTimeout) {
            clearTimeout(this.connectionTimeout);
            this.connectionTimeout = null;
        }
    }


    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    sendResult(result) {
        this.send({
            type: 'send_result',
            ...result
        });
    }

    disconnect() {
        this.clearConnectionTimeout();
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close(1000, 'User disconnected');
            this.ws = null;
        }
        this.isConnectedFlag = false;
    }

    isConnected() {
        return this.isConnectedFlag;
    }

    getMessagesSentThisSession() {
        return this.messagesSentThisSession;
    }
}

module.exports = WebSocketClient;
