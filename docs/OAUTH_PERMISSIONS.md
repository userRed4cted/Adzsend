# Discord OAuth2 Permissions Guide

## Current Scopes in Use

The application requests the following Discord OAuth2 scopes:

```
identify guilds
```

### Scope Breakdown

| Scope | Purpose |
|-------|---------|
| `identify` | Read basic user profile info (username, ID, avatar) |
| `guilds` | Read list of servers the user is in |

## How to Enable These Scopes

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Select your application
3. Navigate to OAuth2 > General
4. In the SCOPES section, check: `identify` and `guilds`
5. Add your redirect URL: `http://localhost:5000/callback`

## Message Sending

The application uses the user's Discord token (stored encrypted) to send messages on their behalf. This requires the user to have appropriate permissions in the target servers/channels.

## Security Notes

- User tokens are encrypted before storage
- Tokens are only used for sending messages
- Users must have permission in target channels
