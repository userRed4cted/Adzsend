# Discord OAuth2 Permissions Guide

## Current Scopes in Use

The application currently requests the following Discord OAuth2 scopes:

```
identify guilds channels:read messages.read
```

### Scope Breakdown:

| Scope | Purpose | Why Needed |
|-------|---------|-----------|
| `identify` | Read basic user profile info (username, ID, avatar) | Display user info in the navbar |
| `guilds` | Read list of servers the user is in | Show all servers where user is admin/owner |
| `channels:read` | Read channels in servers | List channels for message sending |
| `messages.read` | Read message history | **Currently not needed**, but ready for future features |

## How to Enable These Scopes in Discord Developer Portal

1. **Go to** [Discord Developer Portal](https://discord.com/developers/applications)
2. **Select your application**
3. **Navigate to** OAuth2 → General
4. **In the SCOPES section:**
   - ✅ Check: `identify`
   - ✅ Check: `guilds`
   - ⚠️ Note: `channels:read` and `messages.read` need to be authorized manually during user login (see below)

## Permission for Sending Messages

To actually **send messages** to Discord channels, you'll need:

- **Bot Token Permissions**: `send_messages` (8192)
- **Admin or Bot User**: The application would need to be a Discord bot with proper permissions

**Current Limitation**: The current implementation only reads user data and lists channels. To actually send messages, you would need either:

1. **Option A: Implement a Discord Bot**
   - Create a bot application in Discord Developer Portal
   - Add bot to your servers with `send_messages` permission
   - Use the bot token to send messages on behalf of the bot

2. **Option B: User-Initiated Sends** (Requires browser automation)
   - Would require user's active browser session
   - Not recommended due to security concerns

## Recommended Scopes for Full Message Sending

If you want to enable actual message sending functionality, update scopes in `app.py`:

```python
client_kwargs={'scope': 'identify guilds channels:read'}
```

Then implement a bot user or server-to-server API approach.

## For Future Features

- `messages.read` - Read message history (currently included)
- `channels:manage` - Create/delete channels (admin features)
- `roles:read` - Read server roles (user management)
- `members:read` - Read member information (member lists)

---

**Important**: Users will be prompted to authorize these scopes when they click "Login with Discord"
