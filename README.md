# Adzsend Marketing Panel

A Discord marketing automation web application with email-based authentication.

## Features

- Email-based login with 6-digit verification codes (randomly generated)
- Multi-server message broadcasting
- Subscription and one-time purchase plans (including free plan)
- Team plan management with invitation system
  - Team owners can invite members by email address (must have account)
  - Members can accept/deny invitations
  - Team membership statuses: pending, accepted, denied, left, banned, owns_team
  - Team plan owners cannot join other teams
  - Pending invitations auto-denied when user becomes team owner
- Discord OAuth2 account linking
- Real-time status updates (polling every 5 seconds for ban/team changes)
- Settings page with organized panels: Display, Discord, Teams, Usage, Billing, General
- Adjust Plan dialog for subscription management
- Purchase history / invoices view
- Personal Panel access for personal plan users
- Team Panel access for team plan members
- Admin panel for user management (ban, flag, delete users, filter by Discord link status)
- Mobile-responsive design
- Token encryption for secure storage using Fernet

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create `.env` File

Create a `.env` file in the project root:

```env
SECRET_KEY=your_random_secret_key_here
DISCORD_BOT_TOKEN=your_bot_token_here
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_OAUTH_REDIRECT_URI=http://127.0.0.1:5000/discord/callback
FLASK_DEBUG=false
```

### 3. Configure Admin Users

Edit `config/admin.py` to add admin email addresses:

```python
ADMIN_EMAILS = [
    'your-admin@email.com',
]
```

### 4. Run the Application

```bash
python app.py
```

The application will be available at `http://localhost:5000`

For development with debug mode:
```bash
FLASK_DEBUG=true python app.py
```

## Project Structure

```
BorzMarketing/
├── app.py                    # Flask application
├── requirements.txt          # Python dependencies
├── config/                   # Configuration files
│   ├── __init__.py          # Config exports
│   ├── admin.py             # Admin email addresses
│   ├── buttons.py           # Button text config
│   ├── colors.py            # Color theme config
│   ├── database_version.py  # DB version for wipe notices
│   ├── email.py             # Email validation settings
│   ├── homepage.py          # Homepage content config
│   ├── navbar.py            # Navigation config
│   ├── pages.py             # Page titles config
│   ├── plans.py             # Pricing plans config
│   ├── site.py              # Site-wide settings (fonts, etc.)
│   └── text.py              # UI text/labels config
├── database/                 # Database utilities
│   └── models.py            # Database models and operations
├── security/                 # Security utilities
│   ├── auth.py              # Authentication & validation
│   └── content_filter.py    # Message content filtering
├── templates/                # Jinja2 HTML templates
├── static/                   # CSS, JS files
└── RESET_DATABASE.py         # Database reset script
```

## Configuration

All configuration is in the `config/` folder:

- **plans.py** - Pricing plans and features
- **homepage.py** - Homepage slideshow and content
- **navbar.py** - Navigation menu labels
- **text.py** - UI text and labels
- **site.py** - Site-wide settings (fonts, layout, animations)
- **admin.py** - Admin email addresses
- **email.py** - Email validation (blacklisted domains, allowed TLDs)
- **database_version.py** - Database wipe notification version

See the individual config files for detailed settings.

## Authentication

The application uses email-based authentication with 6-digit verification codes:

1. User enters their email on login/signup page
2. A randomly generated 6-digit verification code is created and stored server-side
3. User enters the code to complete authentication
4. Rate limiting:
   - 3 wrong code attempts triggers 5-minute lockout
   - Resend has 60-second cooldown between sends
   - Lockout persists even if user navigates away and returns
   - Existing valid codes are reused (no new code on revisit)

**Security Features:**
- Email is stored in server-side session only (not in hidden form fields)
- Prevents email tampering via browser developer tools
- CSRF protection on all verification endpoints
- IP-based rate limiting on API endpoints

**Note:** Email sending integration requires additional setup with an email service provider (e.g., Resend API). Without email integration, codes are generated but must be retrieved from the database for testing.

## Discord Account Linking

Users can link their Discord account via OAuth2:

1. Navigate to Settings > Discord
2. Click "Link Account" to authorize with Discord
3. Enter your Discord token for verification
4. Token must match the authorized Discord account

## Database Management

### Reset Database
Run `python RESET_DATABASE.py` to:
1. **Reset** - Clear all data but keep table structure
2. **Delete** - Remove database file entirely

Both options increment the database version, which triggers a notification for all users.

## Security Notes

- Keep your `.env` file private (add to `.gitignore`)
- Never commit Discord credentials
- User Discord tokens are encrypted using Fernet symmetric encryption before storage
- Encryption key is derived from SECRET_KEY using SHA256
- CSRF protection enabled on all POST endpoints with token validation
- Session cookies configured with HttpOnly and SameSite flags
- Email verification is entirely server-side (no client-side email values)
- Rate limiting on sensitive endpoints (verification, resend, account changes)
- Admin actions validate admin status from database (not session)
- Set `FLASK_DEBUG=false` in production
- Debug mode is disabled by default for production safety

### Rate Limiting

API endpoints are protected with the following limits:
- Login: 5 attempts per minute
- Signup: 3 attempts per minute
- General API: 60 requests per minute
- Token update: 3 updates per 5 minutes
- Message sending: 30 per minute

### Token Encryption

Discord tokens are encrypted at rest using:
- Fernet symmetric encryption (AES-128-CBC with HMAC)
- Key derived from SECRET_KEY via SHA256 hash
- Encrypted tokens stored as base64 strings in SQLite database
