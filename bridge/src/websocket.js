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
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
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
                } else {
                    // Normal disconnect or error
                    this.callbacks.onDisconnected(reason.toString() || 'Connection closed');

                    // Attempt reconnect for unexpected disconnects
                    if (code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.attemptReconnect();
                    }
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
                this.reconnectAttempts = 0;
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
                // Add random delay variation
                const baseDelay = task.delay || 0;
                const variation = task.delay_variation || 0;
                const actualDelay = baseDelay + (Math.random() * variation * 2 - variation);

                // Send typing indicator first
                await sendTypingIndicator(task.discord_token, task.channel_id);

                // Wait for typing simulation (0.5 - 1.5 seconds)
                const typingDelay = 500 + Math.random() * 1000;
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

    attemptReconnect() {
        this.reconnectAttempts++;
        const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

        console.log(`Attempting reconnect in ${delay}ms (attempt ${this.reconnectAttempts})`);

        setTimeout(() => {
            if (!this.isConnectedFlag) {
                this.connect();
            }
        }, delay);
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
