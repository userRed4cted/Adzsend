# Discord OAuth2 Panel

A modern web application to view and manage your Discord servers with OAuth2 authentication.

## Features

✨ **Modern Design** - Beautiful, responsive interface with gradient backgrounds and smooth animations
🔐 **Discord OAuth2** - Secure login with Discord
🖥️ **Server Dashboard** - View all your Discord servers where you have admin or owner permissions
⚡ **Fast & Lightweight** - Built with Flask and vanilla CSS

## Setup Instructions

### 1. Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name and create it
4. Go to "OAuth2" → "General"
5. Copy your **Client ID**
6. Go to "OAuth2" → "Client Secret" and copy it
7. In "OAuth2" → "Redirects", add: `http://localhost:5000/callback`

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env` File

Create a `.env` file in the project root:

```
DISCORD_CLIENT_ID=your_client_id_here
DISCORD_CLIENT_SECRET=your_client_secret_here
SECRET_KEY=your_random_secret_key_here
```

### 4. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

## How to Use

1. Click "Login with Discord" on the home page
2. Authorize the application to access your Discord account
3. View all servers where you have admin or owner permissions
4. Your profile information and avatar are displayed in the top-right corner

## File Structure

```
project/
├── app.py                 # Flask application and routes
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index.html        # Home page with login button
│   └── dashboard.html    # Server list dashboard
├── static/
│   └── styles.css        # Modern styling
└── .env                  # Environment variables (create this)
```

## Technologies Used

- **Backend**: Flask
- **Authentication**: Authlib + Discord OAuth2
- **Frontend**: HTML5, CSS3
- **API**: Discord API v10

## API Permissions

The application requests:
- `identify` - Read your user profile
- `guilds` - Read your server list

## Security Notes

- Keep your `.env` file private (add to `.gitignore`)
- Never commit your Discord credentials
- Use a strong `SECRET_KEY` in production

## Troubleshooting

### "npx: command not found"
Node.js is not installed. This project uses Python/Flask instead.

### Discord login not working
- Verify your Client ID and Secret are correct
- Check that the redirect URL matches exactly (including http/https)
- Ensure the scopes include `identify` and `guilds`

### No servers showing
Only servers where you have admin or owner permissions will appear.

## Future Enhancements

- Server settings management
- Member lists
- Channel information
- Role management
- Audit logs
- Database integration

---

Made with ❤️ for Discord server management
