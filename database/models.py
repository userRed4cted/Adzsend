import sqlite3
import json
import os
import base64
import hashlib
import secrets
import random
from datetime import datetime, timedelta
from cryptography.fernet import Fernet


# Configuration Constants
DEFAULT_MESSAGE_DELAY_MS = 1000  # Default delay between messages in milliseconds
VERIFICATION_CODE_EXPIRY_MINUTES = 10  # How long verification codes are valid
RESEND_COOLDOWN_MINUTES = 1  # Minimum time between resending verification codes
MAX_ID_GENERATION_RETRIES = 5  # Max retries for unique ID generation on collision
ADZSEND_ID_LENGTH = 10  # Length of adzsend_id identifiers


def generate_verification_code():
    """Generate a random 6-digit verification code."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(6)])

def generate_adzsend_id():
    """Generate a unique 18-digit Adzsend ID (like Discord snowflake)."""
    return ''.join([str(secrets.randbelow(10)) for _ in range(18)])

DATABASE = 'marketing_panel.db'

# Token Encryption Functions
def _get_encryption_key():
    """
    Derive a Fernet key from SECRET_KEY.
    SECURITY: SECRET_KEY must be set in environment variables for encryption to work.
    """
    secret_key = os.getenv('SECRET_KEY')

    # CRITICAL SECURITY CHECK: SECRET_KEY must be set
    if not secret_key:
        raise ValueError(
            "CRITICAL SECURITY ERROR: SECRET_KEY environment variable is not set!\n"
            "Token encryption requires a secure SECRET_KEY.\n"
            "Set SECRET_KEY to a random 32+ character string in your environment."
        )

    # Validate minimum key strength
    if len(secret_key) < 32:
        raise ValueError(
            f"CRITICAL SECURITY ERROR: SECRET_KEY is too weak ({len(secret_key)} chars)!\n"
            "SECRET_KEY must be at least 32 characters for secure encryption.\n"
            "Generate a strong key with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )

    # Warn if using default/weak keys
    weak_keys = ['fallback-secret-key', 'your-secret-key-here', 'secret', 'password', 'changeme']
    if secret_key.lower() in weak_keys:
        raise ValueError(
            f"CRITICAL SECURITY ERROR: SECRET_KEY appears to be a default/weak value!\n"
            "Never use default keys in production.\n"
            "Generate a strong key with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )

    # Fernet requires a 32-byte base64-encoded key
    # We use SHA256 to get a consistent 32-byte hash from SECRET_KEY
    key_hash = hashlib.sha256(secret_key.encode()).digest()
    return base64.urlsafe_b64encode(key_hash)

def encrypt_token(plain_token):
    """Encrypt a Discord token for secure storage."""
    if not plain_token:
        return None
    try:
        fernet = Fernet(_get_encryption_key())
        encrypted = fernet.encrypt(plain_token.encode())
        return encrypted.decode()  # Store as string in database
    except Exception as e:
        print(f"[ENCRYPTION ERROR] Failed to encrypt token: {e}")
        return None

def decrypt_token(encrypted_token):
    """Decrypt a Discord token when needed for API calls."""
    if not encrypted_token:
        return None
    try:
        fernet = Fernet(_get_encryption_key())
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"[DECRYPTION ERROR] Failed to decrypt token: {e}")
        return None

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            avatar TEXT,
            discord_token TEXT NOT NULL,
            signup_ip TEXT NOT NULL,
            signup_date TEXT NOT NULL,
            banned INTEGER DEFAULT 0,
            flagged INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Add flagged column if it doesn't exist (migration)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN flagged INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add flag_reason column if it doesn't exist (migration)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN flag_reason TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add flagged_at column if it doesn't exist (migration)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN flagged_at TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add flag_count column if it doesn't exist (migration)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN flag_count INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add total_flags column if it doesn't exist (migration for all-time flag tracking)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN total_flags INTEGER DEFAULT 0')
        # Migrate existing flag_count values to total_flags for users who were flagged before this column existed
        cursor.execute('UPDATE users SET total_flags = flag_count WHERE flag_count > 0 AND total_flags = 0')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add session_id column if it doesn't exist (migration for session management)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN session_id TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add email column if it doesn't exist (migration for email auth)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add Discord OAuth columns (migration for Discord account linking)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN discord_oauth_linked INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN discord_oauth_access_token TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN discord_oauth_refresh_token TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN discord_oauth_expires_at TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN discord_oauth_linked_at TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN discord_oauth_discord_id TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN discord_oauth_username TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN discord_oauth_avatar TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN discord_oauth_avatar_decoration TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add adzsend_id column if it doesn't exist (unique user ID)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN adzsend_id TEXT')
        conn.commit()
        print('[DB MIGRATION] Added adzsend_id column to users table')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add unique index on adzsend_id to prevent race condition duplicates
    try:
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_adzsend_id ON users(adzsend_id) WHERE adzsend_id IS NOT NULL')
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Index already exists

    # Generate adzsend_id for existing users who don't have one
    try:
        cursor.execute('SELECT id FROM users WHERE adzsend_id IS NULL')
        users_without_id = cursor.fetchall()
        if users_without_id:
            for user in users_without_id:
                new_id = generate_adzsend_id()
                # Ensure uniqueness
                while True:
                    cursor.execute('SELECT id FROM users WHERE adzsend_id = ?', (new_id,))
                    if not cursor.fetchone():
                        break
                    new_id = generate_adzsend_id()
                cursor.execute('UPDATE users SET adzsend_id = ? WHERE id = ?', (new_id, user[0]))
            conn.commit()
            print(f'[DB MIGRATION] Generated adzsend_id for {len(users_without_id)} existing users')
    except sqlite3.OperationalError:
        pass  # Column does not exist yet or other error

    # Verification codes table for email authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verification_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            code TEXT NOT NULL,
            purpose TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            resend_count INTEGER DEFAULT 0,
            last_resend_at TEXT,
            wrong_attempts INTEGER DEFAULT 0
        )
    ''')

    # Migration: Add wrong_attempts column to verification_codes if it doesn't exist
    try:
        cursor.execute('ALTER TABLE verification_codes ADD COLUMN wrong_attempts INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Auth rate limiting table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auth_rate_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            purpose TEXT NOT NULL,
            blocked_until TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')

    # Subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            plan_type TEXT NOT NULL,
            plan_id TEXT NOT NULL,
            plan_name TEXT NOT NULL,
            billing_period TEXT,
            message_limit INTEGER,
            usage_type TEXT,
            allowance_period TEXT,
            start_date TEXT NOT NULL,
            end_date TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Usage tracking table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            messages_sent INTEGER DEFAULT 0,
            all_time_sent INTEGER DEFAULT 0,
            last_reset TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # User data table (for selected channels and draft messages)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            selected_channels TEXT,
            draft_message TEXT,
            message_delay INTEGER DEFAULT 1000,
            date_format TEXT DEFAULT 'mm/dd/yy',
            profile_photo TEXT DEFAULT 'Light_Blue.jpg',
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Business teams table (for business plan team management)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS business_teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_user_id INTEGER NOT NULL,
            subscription_id INTEGER NOT NULL,
            team_message TEXT,
            max_members INTEGER DEFAULT 3,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_user_id) REFERENCES users(id),
            FOREIGN KEY (subscription_id) REFERENCES subscriptions(id)
        )
    ''')

    # Business team members table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS business_team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            team_id INTEGER NOT NULL,
            member_discord_id TEXT NOT NULL,
            member_username TEXT,
            member_avatar TEXT,
            invitation_status TEXT DEFAULT 'pending',
            added_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES business_teams(id),
            UNIQUE(team_id, member_discord_id)
        )
    ''')

    # Daily message stats table (for analytics tracking)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_message_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            team_id INTEGER,
            date TEXT NOT NULL,
            messages_sent INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (team_id) REFERENCES business_teams(id),
            UNIQUE(user_id, team_id, date)
        )
    ''')

    # Migration: Fix daily_message_stats table schema
    cursor.execute("PRAGMA table_info(daily_message_stats)")
    daily_stats_columns = [column[1] for column in cursor.fetchall()]

    # Check if we need to recreate the table (wrong columns or wrong constraint)
    needs_recreation = (
        'message_count' in daily_stats_columns or  # Old column name
        'is_team_message' in daily_stats_columns or  # Extra column that shouldn't be there
        'created_at' not in daily_stats_columns  # Missing column
    )

    if needs_recreation:
        # Create new table with correct schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_message_stats_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                team_id INTEGER,
                date TEXT NOT NULL,
                messages_sent INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (team_id) REFERENCES business_teams(id),
                UNIQUE(user_id, team_id, date)
            )
        ''')

        # Copy data from old table, handling different column names
        try:
            if 'message_count' in daily_stats_columns:
                # Old schema with message_count
                cursor.execute('''
                    INSERT OR IGNORE INTO daily_message_stats_new (id, user_id, team_id, date, messages_sent, created_at)
                    SELECT id, user_id, team_id, date, message_count, created_at
                    FROM daily_message_stats
                ''')
            elif 'is_team_message' in daily_stats_columns:
                # Schema with is_team_message - aggregate by user_id, team_id, date
                cursor.execute('''
                    INSERT OR IGNORE INTO daily_message_stats_new (user_id, team_id, date, messages_sent, created_at)
                    SELECT user_id, team_id, date, SUM(messages_sent), MIN(created_at)
                    FROM daily_message_stats
                    GROUP BY user_id, team_id, date
                ''')
            else:
                # Current schema, just copy
                cursor.execute('''
                    INSERT OR IGNORE INTO daily_message_stats_new (id, user_id, team_id, date, messages_sent, created_at)
                    SELECT id, user_id, team_id, date, messages_sent, created_at
                    FROM daily_message_stats
                ''')
        except Exception as e:
            print(f"[WARNING] Error copying data from old daily_message_stats table: {e}")

        # Drop old table and rename new table
        cursor.execute('DROP TABLE daily_message_stats')
        cursor.execute('ALTER TABLE daily_message_stats_new RENAME TO daily_message_stats')

    # Migration: Add message_delay column if it doesn't exist
    cursor.execute("PRAGMA table_info(user_data)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'message_delay' not in columns:
        cursor.execute('ALTER TABLE user_data ADD COLUMN message_delay INTEGER DEFAULT 1000')

    # Migration: Add date_format column if it doesn't exist
    cursor.execute("PRAGMA table_info(user_data)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'date_format' not in columns:
        cursor.execute("ALTER TABLE user_data ADD COLUMN date_format TEXT DEFAULT 'mm/dd/yy'")

    # Migration: Add all_time_sent column if it doesn't exist
    cursor.execute("PRAGMA table_info(usage)")
    usage_columns = [column[1] for column in cursor.fetchall()]
    if 'all_time_sent' not in usage_columns:
        cursor.execute('ALTER TABLE usage ADD COLUMN all_time_sent INTEGER DEFAULT 0')
        # Initialize all_time_sent with current messages_sent values
        cursor.execute('UPDATE usage SET all_time_sent = messages_sent WHERE all_time_sent = 0')

    # Migration: Add business usage tracking columns
    if 'business_messages_sent' not in usage_columns:
        cursor.execute('ALTER TABLE usage ADD COLUMN business_messages_sent INTEGER DEFAULT 0')
    if 'business_all_time_sent' not in usage_columns:
        cursor.execute('ALTER TABLE usage ADD COLUMN business_all_time_sent INTEGER DEFAULT 0')
    if 'business_last_reset' not in usage_columns:
        cursor.execute('ALTER TABLE usage ADD COLUMN business_last_reset TEXT')

    # Migration: Add business_selected_channels to user_data
    cursor.execute("PRAGMA table_info(user_data)")
    user_data_columns = [column[1] for column in cursor.fetchall()]
    if 'business_selected_channels' not in user_data_columns:
        cursor.execute('ALTER TABLE user_data ADD COLUMN business_selected_channels TEXT')

    # Migration: Add profile_photo to user_data
    cursor.execute("PRAGMA table_info(user_data)")
    user_data_columns = [column[1] for column in cursor.fetchall()]
    if 'profile_photo' not in user_data_columns:
        cursor.execute("ALTER TABLE user_data ADD COLUMN profile_photo TEXT DEFAULT 'Light_Blue.jpg'")

    # Migration: Add invitation_status to business_team_members
    cursor.execute("PRAGMA table_info(business_team_members)")
    team_members_columns = [column[1] for column in cursor.fetchall()]
    if 'invitation_status' not in team_members_columns:
        cursor.execute("ALTER TABLE business_team_members ADD COLUMN invitation_status TEXT DEFAULT 'pending'")
        # Set existing members to 'accepted' status
        cursor.execute("UPDATE business_team_members SET invitation_status = 'accepted' WHERE invitation_status IS NULL")

    # Note: max_members is set when business team is created
    # Changing config.py values won't affect existing teams to preserve user data

    # ==========================================
    # DATABASE INDEXES FOR QUERY OPTIMIZATION
    # ==========================================
    # These indexes significantly improve query performance for common lookups

    # Users table indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_discord_id ON users(discord_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_discord_oauth_discord_id ON users(discord_oauth_discord_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_banned ON users(banned)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_flagged ON users(flagged)')

    # Subscriptions table indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_is_active ON subscriptions(is_active)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_id ON subscriptions(plan_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_subscriptions_user_active ON subscriptions(user_id, is_active)')

    # Usage table indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_usage_user_id ON usage(user_id)')

    # Verification codes indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_verification_codes_email ON verification_codes(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_verification_codes_email_purpose ON verification_codes(email, purpose)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_verification_codes_used ON verification_codes(used)')

    # Auth rate limits indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_email ON auth_rate_limits(email)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_auth_rate_limits_email_purpose ON auth_rate_limits(email, purpose)')

    # Business teams indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_business_teams_owner ON business_teams(owner_user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_business_teams_subscription ON business_teams(subscription_id)')

    # Business team members indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_team_members_team_id ON business_team_members(team_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_team_members_discord_id ON business_team_members(member_discord_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_team_members_status ON business_team_members(invitation_status)')

    # User data indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_data_user_id ON user_data(user_id)')

    # Daily message stats indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_stats_user_id ON daily_message_stats(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_stats_team_id ON daily_message_stats(team_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_message_stats(date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_daily_stats_user_team_date ON daily_message_stats(user_id, team_id, date)')

    # Linked Discord accounts table (for sending messages from multiple accounts)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS linked_discord_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            discord_id TEXT NOT NULL,
            username TEXT NOT NULL,
            avatar TEXT,
            avatar_decoration TEXT,
            discord_token TEXT NOT NULL,
            oauth_access_token TEXT,
            oauth_refresh_token TEXT,
            oauth_expires_at TEXT,
            linked_at TEXT NOT NULL,
            last_verified TEXT,
            is_valid INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, discord_id)
        )
    ''')

    # Linked Discord accounts indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_linked_discord_user_id ON linked_discord_accounts(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_linked_discord_discord_id ON linked_discord_accounts(discord_id)')

    conn.commit()
    conn.close()

def create_user(discord_id, username, avatar, discord_token, signup_ip):
    signup_date = datetime.now().isoformat()

    # Encrypt the token before storing
    encrypted_token = encrypt_token(discord_token)
    if not encrypted_token:
        print(f"[ERROR] Failed to encrypt token for user {discord_id}")
        return None

    # Retry loop to handle race conditions on adzsend_id collision
    max_retries = MAX_ID_GENERATION_RETRIES
    for attempt in range(max_retries):
        conn = get_db()
        cursor = conn.cursor()

        # Generate unique adzsend_id
        adzsend_id = generate_adzsend_id()
        while True:
            cursor.execute('SELECT id FROM users WHERE adzsend_id = ?', (adzsend_id,))
            if not cursor.fetchone():
                break
            adzsend_id = generate_adzsend_id()

        try:
            cursor.execute('''
                INSERT INTO users (discord_id, username, avatar, discord_token, signup_ip, signup_date, adzsend_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (discord_id, username, avatar, encrypted_token, signup_ip, signup_date, adzsend_id))

            user_id = cursor.lastrowid

            # Initialize usage tracking
            cursor.execute('''
                INSERT INTO usage (user_id, messages_sent, last_reset)
                VALUES (?, 0, ?)
            ''', (user_id, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            # Auto-activate free plan for new users
            activate_free_plan(user_id)

            return user_id
        except sqlite3.IntegrityError as e:
            conn.close()
            # If it's an adzsend_id collision (race condition), retry with new ID
            if 'adzsend_id' in str(e) or 'idx_users_adzsend_id' in str(e):
                if attempt < max_retries - 1:
                    continue  # Retry with new adzsend_id
            # For other integrity errors (like duplicate discord_id), return None
            return None

    return None  # Max retries exceeded

def get_user_by_discord_id(discord_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE discord_id = ?', (discord_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_adzsend_id(adzsend_id):
    """Get user by their Adzsend ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE adzsend_id = ?', (adzsend_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_decrypted_token(discord_id):
    """Get and decrypt the user's Discord token for API calls.
    This should only be called when actually sending messages."""
    user = get_user_by_discord_id(discord_id)
    if not user:
        return None
    encrypted_token = user.get('discord_token')
    return decrypt_token(encrypted_token)

def get_user_by_id(user_id):
    """Get user by internal user ID (for admin panel)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_user_token(discord_id, discord_token):
    conn = get_db()
    cursor = conn.cursor()
    # Encrypt the token before storing
    encrypted_token = encrypt_token(discord_token)
    if not encrypted_token:
        print(f"[ERROR] Failed to encrypt token for user {discord_id}")
        conn.close()
        return False
    cursor.execute('UPDATE users SET discord_token = ? WHERE discord_id = ?', (encrypted_token, discord_id))
    conn.commit()
    conn.close()
    return True

def update_user_session(discord_id, session_id):
    """Update the session ID for a user when they log in."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET session_id = ? WHERE discord_id = ?', (session_id, discord_id))
    conn.commit()
    conn.close()

def validate_user_session(discord_id, session_id):
    """Check if the provided session ID matches the stored session ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT session_id FROM users WHERE discord_id = ?', (discord_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return False

    stored_session_id = user[0] if user[0] else None
    return stored_session_id == session_id

def save_user_data(user_id, selected_channels=None, draft_message=None, message_delay=None, date_format=None, profile_photo=None, business_selected_channels=None):
    """Save or update user's selected channels, draft message, message delay, date format, profile photo, and business selected channels."""
    # Input validation
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("user_id must be a positive integer")

    if message_delay is not None:
        if not isinstance(message_delay, (int, float)) or message_delay < 0 or message_delay > 60000:
            raise ValueError("message_delay must be between 0 and 60000 milliseconds")

    if date_format is not None:
        valid_formats = ['mm/dd/yy', 'dd/mm/yy', 'yy/mm/dd']
        if date_format not in valid_formats:
            raise ValueError("date_format must be one of: mm/dd/yy, dd/mm/yy, yy/mm/dd")

    if profile_photo is not None:
        # Validate profile photo filename (basic security check)
        if not isinstance(profile_photo, str) or '..' in profile_photo or '/' in profile_photo or '\\' in profile_photo:
            raise ValueError("Invalid profile photo filename")

    conn = get_db()
    cursor = conn.cursor()

    # Convert channels list to JSON string
    channels_json = json.dumps(selected_channels) if selected_channels is not None else None
    business_channels_json = json.dumps(business_selected_channels) if business_selected_channels is not None else None

    # Check if user_data exists
    cursor.execute('SELECT id FROM user_data WHERE user_id = ?', (user_id,))
    existing = cursor.fetchone()

    if existing:
        # Update existing record
        update_parts = []
        params = []

        if selected_channels is not None:
            update_parts.append('selected_channels = ?')
            params.append(channels_json)

        if draft_message is not None:
            update_parts.append('draft_message = ?')
            params.append(draft_message)

        if message_delay is not None:
            update_parts.append('message_delay = ?')
            params.append(message_delay)

        if date_format is not None:
            update_parts.append('date_format = ?')
            params.append(date_format)

        if profile_photo is not None:
            update_parts.append('profile_photo = ?')
            params.append(profile_photo)

        if business_selected_channels is not None:
            update_parts.append('business_selected_channels = ?')
            params.append(business_channels_json)

        if update_parts:
            update_parts.append('updated_at = ?')
            params.append(datetime.now().isoformat())
            params.append(user_id)

            # Build query safely - update_parts are hardcoded column names, not user input
            query = f'UPDATE user_data SET {", ".join(update_parts)} WHERE user_id = ?'
            cursor.execute(query, params)
    else:
        # Insert new record
        cursor.execute('''
            INSERT INTO user_data (user_id, selected_channels, draft_message, message_delay, date_format, profile_photo, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, channels_json, draft_message, message_delay if message_delay is not None else DEFAULT_MESSAGE_DELAY_MS, date_format if date_format is not None else 'mm/dd/yy', profile_photo if profile_photo is not None else 'Light_Blue.jpg', datetime.now().isoformat()))

    conn.commit()
    conn.close()

def get_user_data(user_id):
    """Get user's selected channels, draft message, message delay, date format, profile photo, and business selected channels."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT selected_channels, draft_message, message_delay, date_format, profile_photo, business_selected_channels FROM user_data WHERE user_id = ?', (user_id,))
    data = cursor.fetchone()
    conn.close()

    if not data:
        return {'selected_channels': [], 'draft_message': '', 'message_delay': 1000, 'date_format': 'mm/dd/yy', 'profile_photo': 'Light_Blue.jpg', 'business_selected_channels': []}

    # Parse JSON channels
    channels = json.loads(data[0]) if data[0] else []
    message = data[1] if data[1] else ''
    delay = data[2] if data[2] is not None else 1000
    date_fmt = data[3] if data[3] else 'mm/dd/yy'
    profile_photo = data[4] if data[4] else 'Light_Blue.jpg'
    business_channels = json.loads(data[5]) if data[5] else []

    return {
        'selected_channels': channels,
        'draft_message': message,
        'message_delay': delay,
        'date_format': date_fmt,
        'profile_photo': profile_photo,
        'business_selected_channels': business_channels
    }

def delete_user(discord_id):
    """
    Permanently delete a user and ALL their data.
    This ensures complete removal with no recovery possible.
    """
    conn = get_db()
    cursor = conn.cursor()

    # Get user_id and email first
    cursor.execute('SELECT id, email FROM users WHERE discord_id = ?', (discord_id,))
    user = cursor.fetchone()

    if user:
        user_id = user[0]
        user_email = user[1]

        # Delete business team if user owns one
        cursor.execute('SELECT id FROM business_teams WHERE owner_user_id = ?', (user_id,))
        team = cursor.fetchone()
        if team:
            team_id = team[0]
            # Delete all team members first
            cursor.execute('DELETE FROM business_team_members WHERE team_id = ?', (team_id,))
            # Delete the team
            cursor.execute('DELETE FROM business_teams WHERE id = ?', (team_id,))

        # Remove user from any business teams they're a member of
        cursor.execute('DELETE FROM business_team_members WHERE member_discord_id = ?', (discord_id,))

        # Delete all subscriptions
        cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))

        # Delete all usage data
        cursor.execute('DELETE FROM usage WHERE user_id = ?', (user_id,))

        # Delete all user data (saved channels, drafts, etc.)
        cursor.execute('DELETE FROM user_data WHERE user_id = ?', (user_id,))

        # Delete email verification codes (for new login system)
        if user_email:
            cursor.execute('DELETE FROM verification_codes WHERE email = ?', (user_email.lower(),))
            cursor.execute('DELETE FROM auth_rate_limits WHERE email = ?', (user_email.lower(),))

        # Finally delete the user record (includes encrypted token and OAuth data)
        cursor.execute('DELETE FROM users WHERE discord_id = ?', (discord_id,))

        conn.commit()

        # Run VACUUM to permanently remove deleted data from database file
        # This ensures data cannot be recovered from disk
        cursor.execute('VACUUM')

    conn.close()


def delete_user_by_email(email):
    """
    Delete a user by email address. Fallback for when discord_id lookup fails.
    """
    conn = get_db()
    cursor = conn.cursor()

    email_lower = email.lower()

    # Get user by email
    cursor.execute('SELECT id, discord_id FROM users WHERE email = ?', (email_lower,))
    user = cursor.fetchone()

    if user:
        user_id = user[0]
        discord_id = user[1]

        # Delete business team if user owns one
        cursor.execute('SELECT id FROM business_teams WHERE owner_user_id = ?', (user_id,))
        team = cursor.fetchone()
        if team:
            team_id = team[0]
            cursor.execute('DELETE FROM business_team_members WHERE team_id = ?', (team_id,))
            cursor.execute('DELETE FROM business_teams WHERE id = ?', (team_id,))

        # Remove user from any business teams they're a member of
        if discord_id:
            cursor.execute('DELETE FROM business_team_members WHERE member_discord_id = ?', (discord_id,))

        # Delete all subscriptions
        cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))

        # Delete all usage data
        cursor.execute('DELETE FROM usage WHERE user_id = ?', (user_id,))

        # Delete all user data
        cursor.execute('DELETE FROM user_data WHERE user_id = ?', (user_id,))

        # Delete email verification codes
        cursor.execute('DELETE FROM verification_codes WHERE email = ?', (email_lower,))
        cursor.execute('DELETE FROM auth_rate_limits WHERE email = ?', (email_lower,))

        # Delete the user record
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))

        conn.commit()
        cursor.execute('VACUUM')

    conn.close()


def get_active_subscription(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM subscriptions
        WHERE user_id = ? AND is_active = 1
        ORDER BY id DESC LIMIT 1
    ''', (user_id,))
    sub = cursor.fetchone()
    conn.close()
    return dict(sub) if sub else None

def set_subscription(user_id, plan_type, plan_id, plan_config, billing_period=None):
    """
    Activate a subscription or one-time plan for a user.

    Args:
        user_id: User's database ID
        plan_type: 'subscription' or 'one-time'
        plan_id: Plan identifier from config
        plan_config: Plan configuration dict from config.py
        billing_period: 'monthly' or 'yearly' (for subscriptions only)
    """
    conn = get_db()
    cursor = conn.cursor()

    # Deactivate old subscriptions
    cursor.execute('UPDATE subscriptions SET is_active = 0 WHERE user_id = ?', (user_id,))

    # Calculate end date
    start_date = datetime.now()
    end_date = None

    if plan_type == 'subscription':
        # Subscriptions run until cancelled
        if billing_period == 'yearly':
            end_date = (start_date + timedelta(days=365)).isoformat()
        else:  # monthly
            end_date = (start_date + timedelta(days=30)).isoformat()
    else:  # one-time
        # One-time plans have specific duration
        duration_days = plan_config.get('duration_days', 1)
        end_date = (start_date + timedelta(days=duration_days)).isoformat()

    # Add new subscription
    cursor.execute('''
        INSERT INTO subscriptions (
            user_id, plan_type, plan_id, plan_name, billing_period,
            message_limit, usage_type, allowance_period,
            start_date, end_date, is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    ''', (
        user_id,
        plan_type,
        plan_id,
        plan_config.get('name'),
        billing_period,
        plan_config.get('message_limit'),
        plan_config.get('usage_type'),
        plan_config.get('allowance_period'),
        start_date.isoformat(),
        end_date
    ))

    # Update last_reset timestamp and reset messages_sent for new plans
    # For business/team plans, also reset business usage counters
    if plan_id.startswith('team_plan_'):
        # Reset both personal and business usage for the owner
        cursor.execute('''
            UPDATE usage SET messages_sent = 0, last_reset = ?,
            business_messages_sent = 0, business_last_reset = ?
            WHERE user_id = ?
        ''', (start_date.isoformat(), start_date.isoformat(), user_id))

        # Also reset business usage for all team members
        cursor.execute('SELECT discord_id FROM users WHERE id = ?', (user_id,))
        owner_discord = cursor.fetchone()
        if owner_discord:
            # Get team ID for this owner
            cursor.execute('SELECT id FROM business_teams WHERE owner_user_id = ?', (user_id,))
            team_row = cursor.fetchone()
            if team_row:
                team_id = team_row[0]
                # Get all team members
                cursor.execute('''
                    SELECT btm.member_discord_id FROM business_team_members btm
                    WHERE btm.team_id = ? AND btm.invitation_status = 'accepted'
                ''', (team_id,))
                member_discord_ids = [row[0] for row in cursor.fetchall()]

                # Reset business usage for all team members
                for discord_id in member_discord_ids:
                    cursor.execute('SELECT id FROM users WHERE discord_id = ?', (discord_id,))
                    member_row = cursor.fetchone()
                    if member_row:
                        member_user_id = member_row[0]
                        cursor.execute('''
                            UPDATE usage SET business_messages_sent = 0, business_last_reset = ?
                            WHERE user_id = ?
                        ''', (start_date.isoformat(), member_user_id))
    else:
        # For non-team plans, reset personal usage
        cursor.execute('''
            UPDATE usage SET messages_sent = 0, last_reset = ? WHERE user_id = ?
        ''', (start_date.isoformat(), user_id))

    conn.commit()
    conn.close()

def cancel_subscription(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE subscriptions SET is_active = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    # Auto-activate free plan after cancelling
    activate_free_plan(user_id)

def activate_free_plan(user_id):
    """Activate the free plan for a user (used when no plan or after cancellation)."""
    from config import SUBSCRIPTION_PLANS

    free_plan_config = SUBSCRIPTION_PLANS.get('plan_free')
    if not free_plan_config:
        return  # Free plan not configured

    conn = get_db()
    cursor = conn.cursor()

    # Check if user already has an active free plan
    cursor.execute('''
        SELECT id FROM subscriptions
        WHERE user_id = ? AND plan_id = 'plan_free' AND is_active = 1
    ''', (user_id,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return  # Already on free plan

    # Deactivate any other plans (shouldn't be any, but just in case)
    cursor.execute('UPDATE subscriptions SET is_active = 0 WHERE user_id = ?', (user_id,))

    # Create free plan subscription (no end date - runs indefinitely)
    start_date = datetime.now()
    cursor.execute('''
        INSERT INTO subscriptions (
            user_id, plan_type, plan_id, plan_name, billing_period,
            message_limit, usage_type, allowance_period,
            start_date, end_date, is_active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    ''', (
        user_id,
        'subscription',
        'plan_free',
        free_plan_config.get('name'),
        'monthly',  # Free plan is perpetual
        free_plan_config.get('message_limit'),
        free_plan_config.get('usage_type'),
        free_plan_config.get('allowance_period'),
        start_date.isoformat(),
        None  # No end date for free plan
    ))

    conn.commit()
    conn.close()

def get_usage(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usage WHERE user_id = ?', (user_id,))
    usage = cursor.fetchone()
    conn.close()
    return dict(usage) if usage else None

def increment_usage(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE usage SET messages_sent = messages_sent + 1, all_time_sent = all_time_sent + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    # Also record daily stats for personal analytics (team_id=0 for personal)
    record_daily_stat(user_id, 0)

def increment_business_usage(user_id, team_id=None):
    """Increment the business usage counters for a team member."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE usage
        SET business_messages_sent = business_messages_sent + 1,
            business_all_time_sent = business_all_time_sent + 1
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

    # Also record daily stats for analytics
    # Use NULL for personal stats, actual team_id for team sends
    # This ensures personal analytics can properly filter team messages
    record_daily_stat(user_id, team_id)


def record_daily_stat(user_id, team_id):
    """Record a message send in the daily stats table for analytics."""
    conn = get_db()
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')

    # Try to update existing record, or insert new one
    cursor.execute('''
        INSERT INTO daily_message_stats (user_id, team_id, date, messages_sent)
        VALUES (?, ?, ?, 1)
        ON CONFLICT(user_id, team_id, date) DO UPDATE SET messages_sent = messages_sent + 1
    ''', (user_id, team_id, today))

    conn.commit()
    conn.close()

def reset_usage(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE usage SET messages_sent = 0, last_reset = ? WHERE user_id = ?
    ''', (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def check_and_reset_allowance(user_id, subscription):
    """
    Check if allowance should be reset based on the plan's allowance_period.
    Returns True if reset was performed, False otherwise.
    """
    if not subscription or subscription['usage_type'] != 'allowance':
        return False

    usage = get_usage(user_id)
    if not usage or not usage['last_reset']:
        return False

    last_reset = datetime.fromisoformat(usage['last_reset'])
    now = datetime.now()
    allowance_period = subscription['allowance_period']

    should_reset = False

    if allowance_period == 'daily':
        # Reset if it's a new day
        should_reset = last_reset.date() < now.date()
    elif allowance_period == 'weekly':
        # Reset if it's a new week (Monday)
        last_week = last_reset.isocalendar()[1]
        current_week = now.isocalendar()[1]
        should_reset = last_week != current_week or last_reset.year != now.year
    elif allowance_period == 'monthly':
        # Reset if it's a new month
        should_reset = last_reset.month != now.month or last_reset.year != now.year

    if should_reset:
        reset_usage(user_id)
        return True

    return False

def can_send_message(user_id):
    """
    Check if user can send a message based on their plan and usage.
    Returns (can_send: bool, reason: str, remaining: int)
    """
    subscription = get_active_subscription(user_id)

    # No active subscription
    if not subscription:
        return False, "No active plan", 0

    # Check if plan has expired
    if subscription['end_date']:
        end_date = datetime.fromisoformat(subscription['end_date'])
        if datetime.now() > end_date:
            # Deactivate expired plan
            cancel_subscription(user_id)
            return False, "Plan expired", 0

    # Check and reset allowance if needed
    check_and_reset_allowance(user_id, subscription)

    # Unlimited messages
    if subscription['message_limit'] == -1:
        return True, "Unlimited", -1

    # Get current usage
    usage = get_usage(user_id)
    messages_sent = usage['messages_sent'] if usage else 0

    # Check if limit reached
    remaining = subscription['message_limit'] - messages_sent
    if remaining <= 0:
        return False, "Message limit reached", 0

    return True, "OK", remaining

def record_successful_send(user_id):
    """
    Record a successful message send. Only call this after a message is successfully sent.
    """
    increment_usage(user_id)

def get_plan_status(user_id):
    """
    Get comprehensive plan status for a user.
    Returns dict with plan info, usage, and limits.
    """
    subscription = get_active_subscription(user_id)

    if not subscription:
        # Auto-activate free plan for users without a subscription
        activate_free_plan(user_id)
        subscription = get_active_subscription(user_id)

        # If still no subscription (free plan not configured), return fallback
        if not subscription:
            usage = get_usage(user_id)
            all_time_sent = usage['all_time_sent'] if usage else 0
            return {
                'has_plan': False,
                'plan_name': 'No Plan',
                'message_limit': 0,
                'messages_sent': 0,
                'all_time_sent': all_time_sent,
                'messages_remaining': 0,
                'is_unlimited': False,
                'expires_at': None,
                'next_reset': None,
                'max_channels_per_server': 2  # Default limit
            }

    # Check if expired (skip for free plan which is perpetual)
    if subscription['end_date'] and subscription['plan_id'] != 'plan_free':
        end_date = datetime.fromisoformat(subscription['end_date'])
        if datetime.now() > end_date:
            cancel_subscription(user_id)
            # Activate free plan immediately instead of returning "Expired"
            activate_free_plan(user_id)
            subscription = get_active_subscription(user_id)
            if not subscription:
                usage = get_usage(user_id)
                all_time_sent = usage['all_time_sent'] if usage else 0
                return {
                    'has_plan': False,
                    'plan_name': 'No Plan',
                    'message_limit': 0,
                    'messages_sent': 0,
                    'all_time_sent': all_time_sent,
                    'messages_remaining': 0,
                    'is_unlimited': False,
                    'expires_at': None,
                    'next_reset': None,
                    'max_channels_per_server': 2  # Default limit
                }

    # Check and reset allowance if needed
    check_and_reset_allowance(user_id, subscription)

    usage = get_usage(user_id)
    messages_sent = usage['messages_sent'] if usage else 0
    all_time_sent = usage['all_time_sent'] if usage else 0

    is_unlimited = subscription['message_limit'] == -1
    remaining = -1 if is_unlimited else max(0, subscription['message_limit'] - messages_sent)

    # Calculate next reset time for allowance-based plans
    next_reset = None
    if subscription['usage_type'] == 'allowance' and usage and usage['last_reset']:
        last_reset = datetime.fromisoformat(usage['last_reset'])
        now = datetime.now()
        allowance_period = subscription['allowance_period']

        if allowance_period == 'daily':
            # Next reset is 24 hours after last reset
            next_reset = (last_reset + timedelta(days=1)).isoformat()
        elif allowance_period == 'weekly':
            # Next reset is 7 days after last reset
            next_reset = (last_reset + timedelta(weeks=1)).isoformat()
        elif allowance_period == 'monthly':
            # Next reset is 30 days after last reset
            next_reset = (last_reset + timedelta(days=30)).isoformat()

    # Get max_channels_per_server from plan config
    from config import SUBSCRIPTION_PLANS, BUSINESS_PLANS
    plan_id = subscription['plan_id']
    max_channels_per_server = 2  # Default

    # Look up in appropriate plan dictionary
    if plan_id in SUBSCRIPTION_PLANS:
        max_channels_per_server = SUBSCRIPTION_PLANS[plan_id].get('max_channels_per_server', -1)
    elif plan_id in BUSINESS_PLANS:
        max_channels_per_server = BUSINESS_PLANS[plan_id].get('max_channels_per_server', -1)

    return {
        'has_plan': True,
        'plan_type': subscription['plan_type'],
        'plan_id': subscription['plan_id'],
        'plan_name': subscription['plan_name'],
        'billing_period': subscription.get('billing_period'),
        'message_limit': subscription['message_limit'],
        'messages_sent': messages_sent,
        'all_time_sent': all_time_sent,
        'messages_remaining': remaining,
        'is_unlimited': is_unlimited,
        'usage_type': subscription['usage_type'],
        'allowance_period': subscription['allowance_period'],
        'expires_at': subscription['end_date'],
        'started_at': subscription['start_date'],
        'next_reset': next_reset,
        'max_channels_per_server': max_channels_per_server
    }

def get_business_plan_status(team_id, owner_user_id):
    """
    Get business plan status with aggregated team member usage.
    Shows total usage across all team members for business plans.
    """
    # Get the base plan status from the owner
    plan_status = get_plan_status(owner_user_id)

    if not plan_status['has_plan']:
        return plan_status

    # Get all team member stats
    conn = get_db()
    cursor = conn.cursor()

    # Get owner's user_id for the team query
    cursor.execute('''
        SELECT btm.member_discord_id
        FROM business_team_members btm
        WHERE btm.team_id = ? AND btm.invitation_status = 'accepted'
    ''', (team_id,))
    member_discord_ids = [row[0] for row in cursor.fetchall()]

    # Also include the owner's Discord ID
    cursor.execute('SELECT discord_id FROM users WHERE id = ?', (owner_user_id,))
    owner_row = cursor.fetchone()
    if owner_row:
        member_discord_ids.append(owner_row[0])

    # Get total business usage across all team members
    total_business_all_time = 0
    total_business_messages_sent = 0

    for discord_id in member_discord_ids:
        cursor.execute('SELECT id FROM users WHERE discord_id = ?', (discord_id,))
        user_row = cursor.fetchone()
        if user_row:
            user_id = user_row[0]
            cursor.execute('''
                SELECT business_all_time_sent, business_messages_sent
                FROM usage
                WHERE user_id = ?
            ''', (user_id,))
            usage_row = cursor.fetchone()
            if usage_row:
                total_business_all_time += usage_row[0] or 0
                total_business_messages_sent += usage_row[1] or 0

    conn.close()

    # Update plan status with aggregated business usage
    plan_status['all_time_sent'] = total_business_all_time
    plan_status['messages_sent'] = total_business_messages_sent

    # Recalculate remaining messages
    if plan_status['is_unlimited']:
        plan_status['messages_remaining'] = -1
    else:
        plan_status['messages_remaining'] = max(0, plan_status['message_limit'] - total_business_messages_sent)

    return plan_status

# Business team management functions

def create_business_team(owner_user_id, subscription_id, max_members=3):
    """Create a new business team for a business plan holder."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if team already exists for this subscription
    cursor.execute('SELECT id FROM business_teams WHERE subscription_id = ?', (subscription_id,))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        return existing[0]

    cursor.execute('''
        INSERT INTO business_teams (owner_user_id, subscription_id, max_members, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (owner_user_id, subscription_id, max_members, datetime.now().isoformat(), datetime.now().isoformat()))

    team_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return team_id

def get_business_team_by_owner(user_id):
    """Get business team where user is the owner."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bt.* FROM business_teams bt
        JOIN subscriptions s ON bt.subscription_id = s.id
        WHERE bt.owner_user_id = ? AND s.is_active = 1
        ORDER BY bt.id DESC LIMIT 1
    ''', (user_id,))
    team = cursor.fetchone()
    conn.close()
    return dict(team) if team else None

def get_business_team_by_member(discord_id):
    """Get business team where user is an accepted member."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bt.* FROM business_teams bt
        JOIN business_team_members btm ON bt.id = btm.team_id
        WHERE btm.member_discord_id = ? AND btm.invitation_status = 'accepted'
        ORDER BY bt.id DESC LIMIT 1
    ''', (discord_id,))
    team = cursor.fetchone()
    conn.close()
    return dict(team) if team else None

def add_team_member(team_id, discord_id, username, avatar):
    """Add a member to a business team with pending invitation status."""
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO business_team_members (team_id, member_discord_id, member_username, member_avatar, invitation_status, added_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
        ''', (team_id, discord_id, username, avatar, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False  # Member already exists

def remove_team_member(team_id, discord_id):
    """Remove a member from a business team."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM business_team_members WHERE team_id = ? AND member_discord_id = ?', (team_id, discord_id))
    conn.commit()
    conn.close()

def remove_team_member_by_adzsend_id(team_id, adzsend_id):
    """Remove a member from a business team by their Adzsend ID."""
    conn = get_db()
    cursor = conn.cursor()
    # First get the user's discord_id from their adzsend_id
    cursor.execute('SELECT discord_id FROM users WHERE adzsend_id = ?', (adzsend_id,))
    result = cursor.fetchone()
    if result:
        member_discord_id = result[0]
        cursor.execute('DELETE FROM business_team_members WHERE team_id = ? AND member_discord_id = ?', (team_id, member_discord_id))
        conn.commit()
    conn.close()

def update_team_member_info(team_id, discord_id, username, avatar):
    """Update username and avatar for a team member."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE business_team_members
        SET member_username = ?, member_avatar = ?
        WHERE team_id = ? AND member_discord_id = ?
    ''', (username, avatar, team_id, discord_id))
    conn.commit()
    conn.close()

def update_user_profile(user_id, username, avatar):
    """Update username and avatar for a user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users
        SET username = ?, avatar = ?
        WHERE id = ?
    ''', (username, avatar, user_id))
    conn.commit()
    conn.close()

def get_team_members(team_id, include_all=False):
    """Get members of a business team.

    Args:
        team_id: The ID of the business team
        include_all: If True, include all members (pending, denied, left, etc).
                    If False (default), only return accepted members.
    """
    conn = get_db()
    cursor = conn.cursor()
    if include_all:
        cursor.execute('''
            SELECT btm.*, u.id as user_id, u.email as member_email, u.adzsend_id as member_adzsend_id
            FROM business_team_members btm
            LEFT JOIN users u ON u.discord_id = btm.member_discord_id
            WHERE btm.team_id = ?
            ORDER BY btm.added_at
        ''', (team_id,))
    else:
        cursor.execute('''
            SELECT btm.*, u.id as user_id, u.email as member_email, u.adzsend_id as member_adzsend_id
            FROM business_team_members btm
            LEFT JOIN users u ON u.discord_id = btm.member_discord_id
            WHERE btm.team_id = ? AND btm.invitation_status = 'accepted'
            ORDER BY btm.added_at
        ''', (team_id,))
    members = cursor.fetchall()
    conn.close()
    return [dict(member) for member in members]

def get_team_member_count(team_id):
    """Get the count of active team members (accepted invitations only)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM business_team_members
        WHERE team_id = ? AND invitation_status = 'accepted'
    ''', (team_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def update_team_message(team_id, message):
    """Update the team message for a business team."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE business_teams SET team_message = ?, updated_at = ? WHERE id = ?
    ''', (message, datetime.now().isoformat(), team_id))
    conn.commit()
    conn.close()

def is_business_plan_owner(user_id):
    """Check if user is a business plan owner."""
    team = get_business_team_by_owner(user_id)
    return team is not None

def is_business_team_member(discord_id):
    """Check if user is a business team member."""
    team = get_business_team_by_member(discord_id)
    return team is not None

def get_team_member_stats(team_id):
    """Get statistics for all team members including their business usage, with owner first."""
    conn = get_db()
    cursor = conn.cursor()

    # First get the team owner
    cursor.execute('''
        SELECT bt.owner_user_id, u.discord_id, u.username, u.avatar, u.email, u.adzsend_id
        FROM business_teams bt
        JOIN users u ON u.id = bt.owner_user_id
        WHERE bt.id = ?
    ''', (team_id,))
    owner_row = cursor.fetchone()

    stats = []

    # Add owner first with is_owner flag
    if owner_row:
        owner_dict = {
            'member_discord_id': owner_row['discord_id'],
            'member_username': owner_row['username'],
            'member_avatar': owner_row['avatar'],
            'member_email': owner_row['email'],
            'member_adzsend_id': owner_row['adzsend_id'],
            'added_at': None,
            'user_id': owner_row['owner_user_id'],
            'is_owner': True
        }
        # Get owner's business usage
        cursor.execute('''
            SELECT business_messages_sent
            FROM usage WHERE user_id = ?
        ''', (owner_row['owner_user_id'],))
        owner_usage = cursor.fetchone()
        owner_dict['business_messages_sent'] = owner_usage[0] if owner_usage else 0

        # Get owner's all-time sent for THIS TEAM ONLY from daily_message_stats
        cursor.execute('''
            SELECT SUM(messages_sent)
            FROM daily_message_stats
            WHERE user_id = ? AND team_id = ?
        ''', (owner_row['owner_user_id'], team_id))
        all_time_row = cursor.fetchone()
        owner_dict['business_all_time_sent'] = all_time_row[0] if all_time_row and all_time_row[0] else 0

        stats.append(owner_dict)

    # Then get team members
    cursor.execute('''
        SELECT
            btm.member_discord_id,
            btm.member_username,
            btm.member_avatar,
            btm.added_at,
            u.id as user_id,
            u.email as member_email,
            u.adzsend_id as member_adzsend_id
        FROM business_team_members btm
        LEFT JOIN users u ON u.discord_id = btm.member_discord_id
        WHERE btm.team_id = ? AND btm.invitation_status = 'accepted'
        ORDER BY btm.added_at
    ''', (team_id,))
    members = cursor.fetchall()

    for member in members:
        member_dict = dict(member)
        member_dict['is_owner'] = False

        # Get business usage for this member if they have a user account
        if member_dict['user_id']:
            cursor.execute('''
                SELECT business_messages_sent
                FROM usage
                WHERE user_id = ?
            ''', (member_dict['user_id'],))
            usage = cursor.fetchone()
            member_dict['business_messages_sent'] = usage[0] if usage else 0

            # Get all-time sent for THIS TEAM ONLY from daily_message_stats
            cursor.execute('''
                SELECT SUM(messages_sent)
                FROM daily_message_stats
                WHERE user_id = ? AND team_id = ?
            ''', (member_dict['user_id'], team_id))
            all_time_row = cursor.fetchone()
            member_dict['business_all_time_sent'] = all_time_row[0] if all_time_row and all_time_row[0] else 0
        else:
            member_dict['business_messages_sent'] = 0
            member_dict['business_all_time_sent'] = 0

        stats.append(member_dict)

    conn.close()
    return stats


# Team invitation management functions

def get_team_invitations(discord_id):
    """Get all pending team invitations for a user."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT btm.*, bt.owner_user_id, u.username as owner_username, u.avatar as owner_avatar, u.discord_id as owner_discord_id, u.adzsend_id as owner_adzsend_id
        FROM business_team_members btm
        JOIN business_teams bt ON btm.team_id = bt.id
        JOIN users u ON bt.owner_user_id = u.id
        WHERE btm.member_discord_id = ? AND btm.invitation_status = 'pending'
        ORDER BY btm.added_at DESC
    ''', (discord_id,))
    invitations = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return invitations


def accept_team_invitation(member_id):
    """Accept a team invitation and reset business usage counters."""
    conn = get_db()
    cursor = conn.cursor()

    # Get the member's discord_id to find their user_id
    cursor.execute('SELECT member_discord_id FROM business_team_members WHERE id = ?', (member_id,))
    member_row = cursor.fetchone()

    cursor.execute('''
        UPDATE business_team_members
        SET invitation_status = 'accepted'
        WHERE id = ?
    ''', (member_id,))

    # Reset business usage for this member when they join a team
    if member_row:
        discord_id = member_row[0]
        cursor.execute('SELECT id FROM users WHERE discord_id = ?', (discord_id,))
        user_row = cursor.fetchone()
        if user_row:
            cursor.execute('''
                UPDATE usage SET business_messages_sent = 0, business_last_reset = ?
                WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_row[0]))

    conn.commit()
    conn.close()


def deny_team_invitation(member_id):
    """Deny a team invitation."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE business_team_members
        SET invitation_status = 'denied'
        WHERE id = ?
    ''', (member_id,))
    conn.commit()
    conn.close()


def clear_all_invitations(discord_id):
    """Clear all pending invitations for a user by marking them as denied."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE business_team_members
        SET invitation_status = 'denied'
        WHERE member_discord_id = ? AND invitation_status = 'pending'
    ''', (discord_id,))
    conn.commit()
    conn.close()


def leave_team(discord_id):
    """Leave a team by updating status to 'left'."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE business_team_members
        SET invitation_status = 'left'
        WHERE member_discord_id = ? AND invitation_status = 'accepted'
    ''', (discord_id,))
    conn.commit()
    conn.close()


def remove_team_member_from_list(member_id):
    """Remove a team member from the list (for denied/left/banned members)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM business_team_members
        WHERE id = ? AND invitation_status IN ('denied', 'left', 'banned')
    ''', (member_id,))
    conn.commit()
    conn.close()


def get_current_team_for_member(discord_id):
    """Get the current team a member is part of (accepted status)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT bt.*,
               u.username as owner_username,
               u.discord_id as owner_discord_id,
               u.avatar as owner_avatar,
               u.adzsend_id as owner_adzsend_id,
               ud.profile_photo as owner_profile_photo
        FROM business_team_members btm
        JOIN business_teams bt ON btm.team_id = bt.id
        JOIN users u ON bt.owner_user_id = u.id
        LEFT JOIN user_data ud ON u.id = ud.user_id
        WHERE btm.member_discord_id = ? AND btm.invitation_status = 'accepted'
        ORDER BY btm.added_at DESC LIMIT 1
    ''', (discord_id,))
    team = cursor.fetchone()
    conn.close()
    return dict(team) if team else None


# Admin Functions

def get_all_users_for_admin(filters=None):
    """Get all users with optional filters for admin panel."""
    conn = get_db()
    cursor = conn.cursor()

    query = '''
        SELECT u.*,
               (SELECT COUNT(*) FROM subscriptions WHERE user_id = u.id AND is_active = 1 AND plan_id != 'plan_free') as has_paid_plan
        FROM users u
        WHERE 1=1
    '''

    params = []

    if filters:
        conditions = []
        if 'non_plan' in filters:
            # Free plan = user only has plan_free subscription (no paid plans)
            conditions.append('(SELECT COUNT(*) FROM subscriptions WHERE user_id = u.id AND is_active = 1 AND plan_id != \'plan_free\') = 0')
        if 'plan' in filters:
            # Paid plan = user has at least one active subscription that is NOT plan_free
            conditions.append('(SELECT COUNT(*) FROM subscriptions WHERE user_id = u.id AND is_active = 1 AND plan_id != \'plan_free\') > 0')
        if 'banned' in filters:
            conditions.append('u.banned = 1')
        if 'flagged' in filters:
            conditions.append('u.flagged = 1')
        if 'no_discord' in filters:
            # Users with no linked Discord (discord_oauth_discord_id is NULL or empty)
            conditions.append('(u.discord_oauth_discord_id IS NULL OR u.discord_oauth_discord_id = \'\')')

        if conditions:
            query += ' AND (' + ' OR '.join(conditions) + ')'

    query += ' ORDER BY u.created_at DESC'

    cursor.execute(query, params)
    users = [dict(row) for row in cursor.fetchall()]

    # Add is_admin flag for each user
    from config import is_admin
    for user in users:
        user['is_admin'] = is_admin(user.get('email'))

    conn.close()
    return users


def get_user_admin_details(user_id):
    """Get detailed user information for admin panel."""
    conn = get_db()
    cursor = conn.cursor()

    # Get user basic info
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return None

    user = dict(result)

    # Check if user is admin
    from config import is_admin
    user['is_admin'] = is_admin(user.get('email'))

    # Get active subscriptions
    cursor.execute('''
        SELECT * FROM subscriptions
        WHERE user_id = ? AND is_active = 1
    ''', (user_id,))
    user['subscriptions'] = [dict(row) for row in cursor.fetchall()]

    # Check if user is business team owner (with active subscription)
    cursor.execute('''
        SELECT bt.* FROM business_teams bt
        JOIN subscriptions s ON bt.subscription_id = s.id
        WHERE bt.owner_user_id = ? AND s.is_active = 1
    ''', (user_id,))
    team = cursor.fetchone()
    user['is_business_owner'] = team is not None
    if team:
        user['business_team'] = dict(team)

    # Check if user is business team member (with owner's active subscription)
    cursor.execute('''
        SELECT bt.*, btm.member_discord_id
        FROM business_team_members btm
        JOIN business_teams bt ON btm.team_id = bt.id
        JOIN subscriptions s ON bt.subscription_id = s.id
        WHERE btm.member_discord_id = ? AND btm.invitation_status = 'accepted' AND s.is_active = 1
    ''', (user['discord_id'],))
    team_member = cursor.fetchone()
    user['is_business_member'] = team_member is not None
    if team_member:
        user['business_team_member_of'] = dict(team_member)
        # Get team owner info
        cursor.execute('SELECT * FROM users WHERE id = ?', (dict(team_member)['owner_user_id'],))
        owner = cursor.fetchone()
        if owner:
            user['business_team_owner'] = dict(owner)

    conn.close()
    return user


def ban_user(user_id):
    """Ban a user and remove them from teams/invitations."""
    conn = get_db()
    cursor = conn.cursor()

    # Get user's discord_id
    cursor.execute('SELECT discord_id FROM users WHERE id = ?', (user_id,))
    user_row = cursor.fetchone()

    if user_row:
        discord_id = user_row[0]

        # Mark accepted team memberships as 'banned' (similar to 'left')
        cursor.execute('''
            UPDATE business_team_members
            SET invitation_status = 'banned'
            WHERE member_discord_id = ? AND invitation_status = 'accepted'
        ''', (discord_id,))

        # Delete all pending invitations for this user
        cursor.execute('''
            DELETE FROM business_team_members
            WHERE member_discord_id = ? AND invitation_status = 'pending'
        ''', (discord_id,))

    # Update user's banned status
    cursor.execute('UPDATE users SET banned = 1 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def unban_user(user_id):
    """Unban a user and reset flag count."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET banned = 0, flag_count = 0 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def flag_user(user_id, reason=None):
    """Flag a user for inappropriate content. Auto-bans on 3rd flag. Returns (new_count, was_banned)."""
    conn = get_db()
    cursor = conn.cursor()
    flagged_at = datetime.now().isoformat()

    # Get current flag count and total flags
    cursor.execute('SELECT flag_count, total_flags, flagged FROM users WHERE id = ?', (user_id,))
    row = cursor.fetchone()
    current_count = row[0] if row and row[0] is not None else 0
    total_flags = row[1] if row and row[1] is not None else 0
    currently_flagged = row[2] if row and row[2] is not None else 0

    # If user is not currently flagged, this is a new flag streak - start from 1
    # If they are currently flagged, increment their existing count
    if currently_flagged == 0:
        new_count = 1  # Fresh start
    else:
        new_count = current_count + 1  # Continue streak

    new_total = total_flags + 1

    # Increment both flag_count (for auto-ban) and total_flags (all-time tracking)
    cursor.execute('''
        UPDATE users
        SET flagged = 1, flag_reason = ?, flagged_at = ?, flag_count = ?, total_flags = ?
        WHERE id = ?
    ''', (reason, flagged_at, new_count, new_total, user_id))

    was_banned = False
    # Auto-ban if this is the 3rd flag
    if new_count >= 3:
        cursor.execute('UPDATE users SET banned = 1 WHERE id = ?', (user_id,))
        was_banned = True

        # Get user's discord_id and remove from teams
        cursor.execute('SELECT discord_id FROM users WHERE id = ?', (user_id,))
        user_row = cursor.fetchone()
        if user_row:
            discord_id = user_row[0]
            # Mark accepted team memberships as 'banned'
            cursor.execute('''
                UPDATE business_team_members
                SET invitation_status = 'banned'
                WHERE member_discord_id = ? AND invitation_status = 'accepted'
            ''', (discord_id,))
            # Delete pending invitations
            cursor.execute('''
                DELETE FROM business_team_members
                WHERE member_discord_id = ? AND invitation_status = 'pending'
            ''', (discord_id,))

    conn.commit()
    conn.close()

    return new_count, was_banned


def unflag_user(user_id):
    """Remove flag from a user and reset flag count (but keep total_flags for historical record)."""
    conn = get_db()
    cursor = conn.cursor()
    # Only reset current flag status and flag_count, keep total_flags intact
    cursor.execute('UPDATE users SET flagged = 0, flag_reason = NULL, flagged_at = NULL, flag_count = 0 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()


def delete_user_account_admin(user_id):
    """Delete a user account (admin function)."""
    conn = get_db()
    cursor = conn.cursor()

    # Get user's email and discord_id first
    cursor.execute('SELECT discord_id, email FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    user_discord_id = user_data[0] if user_data else None
    user_email = user_data[1] if user_data else None

    # Delete user's subscriptions
    cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))

    # Delete user's business team if they own one
    cursor.execute('SELECT id FROM business_teams WHERE owner_user_id = ?', (user_id,))
    team = cursor.fetchone()
    if team:
        team_id = team[0]
        cursor.execute('DELETE FROM business_team_members WHERE team_id = ?', (team_id,))
        cursor.execute('DELETE FROM business_teams WHERE id = ?', (team_id,))

    # Remove from business teams they're a member of
    if user_discord_id:
        cursor.execute('DELETE FROM business_team_members WHERE member_discord_id = ?', (user_discord_id,))

    # Delete user's saved data
    cursor.execute('DELETE FROM user_data WHERE user_id = ?', (user_id,))

    # Delete usage tracking
    cursor.execute('DELETE FROM usage WHERE user_id = ?', (user_id,))

    # Delete email verification codes (for new login system)
    if user_email:
        cursor.execute('DELETE FROM verification_codes WHERE email = ?', (user_email.lower(),))
        cursor.execute('DELETE FROM auth_rate_limits WHERE email = ?', (user_email.lower(),))

    # Finally delete the user (includes encrypted token and OAuth data)
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))

    conn.commit()

    # Run VACUUM to permanently remove deleted data from database file
    cursor.execute('VACUUM')

    conn.close()


def get_purchase_history(user_id):
    """Get all purchase history for a user (paid plans only, excluding free plan)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM subscriptions
        WHERE user_id = ? AND plan_id != 'plan_free'
        ORDER BY start_date DESC
    ''', (user_id,))
    history = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return history


def auto_deny_pending_invitations(discord_id):
    """Auto-deny all pending team invitations for a user who becomes a business owner."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE business_team_members
        SET invitation_status = 'owns_team'
        WHERE member_discord_id = ? AND invitation_status = 'pending'
    ''', (discord_id,))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count


# =============================================================================
# EMAIL AUTHENTICATION FUNCTIONS
# =============================================================================

def get_user_by_email(email):
    """Get user by email address."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_email(user_id, new_email):
    """Update user's email address."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET email = ? WHERE id = ?', (new_email.lower(), user_id))
    conn.commit()
    conn.close()


def create_user_with_email(email, signup_ip):
    """Create a new user with email (no Discord connection yet)."""
    import hashlib

    signup_date = datetime.now().isoformat()
    email_lower = email.lower()

    # Generate a unique placeholder discord_id based on email hash
    # This ensures each email-only user has a unique identifier
    email_hash = hashlib.sha256(email_lower.encode()).hexdigest()[:16]
    placeholder_discord_id = f'email_{email_hash}'

    # Retry loop to handle race conditions on adzsend_id collision
    max_retries = MAX_ID_GENERATION_RETRIES
    for attempt in range(max_retries):
        conn = get_db()
        cursor = conn.cursor()

        # Generate unique adzsend_id
        adzsend_id = generate_adzsend_id()
        while True:
            cursor.execute('SELECT id FROM users WHERE adzsend_id = ?', (adzsend_id,))
            if not cursor.fetchone():
                break
            adzsend_id = generate_adzsend_id()

        try:
            cursor.execute('''
                INSERT INTO users (discord_id, username, avatar, discord_token, signup_ip, signup_date, email, adzsend_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                placeholder_discord_id,  # Unique placeholder until they connect Discord
                email_lower.split('@')[0],  # Use email prefix as temporary username
                None,
                'pending',  # Placeholder token
                signup_ip,
                signup_date,
                email_lower,
                adzsend_id
            ))

            user_id = cursor.lastrowid

            # Initialize user_data with random profile photo
            profile_photos = ['Dark_Green.jpg', 'Dark_Purple.jpg', 'Dark_Rose.jpg', 'Light_Blue.jpg', 'Light_Green.jpg', 'Light_Orange.jpg', 'Light_Pink.jpg', 'Light_Yellow.jpg']
            random_photo = random.choice(profile_photos)
            cursor.execute('''
                INSERT INTO user_data (user_id, profile_photo, updated_at)
                VALUES (?, ?, ?)
            ''', (user_id, random_photo, datetime.now().isoformat()))

            # Initialize usage tracking
            cursor.execute('''
                INSERT INTO usage (user_id, messages_sent, last_reset)
                VALUES (?, 0, ?)
            ''', (user_id, datetime.now().isoformat()))

            conn.commit()
            conn.close()

            # Auto-activate free plan for new users
            activate_free_plan(user_id)

            return user_id
        except sqlite3.IntegrityError as e:
            conn.close()
            # If it's an adzsend_id collision (race condition), retry with new ID
            if 'adzsend_id' in str(e) or 'idx_users_adzsend_id' in str(e):
                if attempt < max_retries - 1:
                    continue  # Retry with new adzsend_id
            # For other integrity errors (like duplicate email), return None
            return None

    return None  # Max retries exceeded


def has_active_verification_code(email, purpose='login'):
    """Check if there's already an active (unexpired, unused) verification code.
    Returns (has_active, is_rate_limited) tuple."""
    conn = get_db()
    cursor = conn.cursor()

    email_lower = email.lower()
    now = datetime.now()

    # First check if rate limited from wrong attempts
    five_min_ago = (now - timedelta(minutes=5)).isoformat()
    cursor.execute('''
        SELECT wrong_attempts FROM verification_codes
        WHERE email = ? AND purpose = ? AND wrong_attempts >= 3 AND created_at > ?
        ORDER BY created_at DESC LIMIT 1
    ''', (email_lower, purpose, five_min_ago))

    if cursor.fetchone():
        conn.close()
        return False, True  # No active code usable, is rate limited

    # Check for active unexpired code
    cursor.execute('''
        SELECT id FROM verification_codes
        WHERE email = ? AND purpose = ? AND used = 0 AND expires_at > ?
        ORDER BY created_at DESC LIMIT 1
    ''', (email_lower, purpose, now.isoformat()))

    active_code = cursor.fetchone()
    conn.close()

    return active_code is not None, False


def create_verification_code(email, purpose='login'):
    """Create a verification code for email auth. Returns the code or None if rate limited."""
    conn = get_db()
    cursor = conn.cursor()

    email_lower = email.lower()
    now = datetime.now()

    # Check if currently rate limited from wrong attempts on ANY recent code (used or unused)
    # This prevents bypass by going back and requesting a new code
    five_min_ago = (now - timedelta(minutes=5)).isoformat()
    cursor.execute('''
        SELECT wrong_attempts, created_at FROM verification_codes
        WHERE email = ? AND purpose = ? AND wrong_attempts >= 3 AND created_at > ?
        ORDER BY created_at DESC LIMIT 1
    ''', (email_lower, purpose, five_min_ago))

    rate_limited_code = cursor.fetchone()
    if rate_limited_code:
        # There's a recent code with 3+ wrong attempts - still rate limited
        conn.close()
        return None

    code = generate_verification_code()
    created_at = now
    expires_at = created_at + timedelta(minutes=VERIFICATION_CODE_EXPIRY_MINUTES)

    # Invalidate any existing unused codes for this email/purpose
    cursor.execute('''
        UPDATE verification_codes
        SET used = 1
        WHERE email = ? AND purpose = ? AND used = 0
    ''', (email_lower, purpose))

    # Create new code
    cursor.execute('''
        INSERT INTO verification_codes (email, code, purpose, created_at, expires_at, resend_count)
        VALUES (?, ?, ?, ?, ?, 0)
    ''', (email_lower, code, purpose, created_at.isoformat(), expires_at.isoformat()))

    conn.commit()
    conn.close()

    return code


def verify_code(email, code, purpose='login'):
    """Verify a code. Returns (success, error_message, code_rate_limited)."""
    conn = get_db()
    cursor = conn.cursor()

    email_lower = email.lower()
    now = datetime.now()

    # First, get the active verification code record for this email
    cursor.execute('''
        SELECT * FROM verification_codes
        WHERE email = ? AND purpose = ? AND used = 0
        ORDER BY created_at DESC LIMIT 1
    ''', (email_lower, purpose))

    active_record = cursor.fetchone()

    if not active_record:
        conn.close()
        return False, "No active verification code. Please request a new one.", False

    active_record = dict(active_record)

    # Check if already rate limited (3+ wrong attempts)
    wrong_attempts = active_record.get('wrong_attempts', 0) or 0
    if wrong_attempts >= 3:
        conn.close()
        return False, "Too many incorrect attempts. Please try again later.", True

    # Check if expired
    expires_at = datetime.fromisoformat(active_record['expires_at'])
    if now > expires_at:
        conn.close()
        return False, "Verification code has expired. Please request a new one.", False

    # DEV ONLY: Bypass code - always accept 000001
    if code == '000001':
        cursor.execute('UPDATE verification_codes SET used = 1 WHERE id = ?', (active_record['id'],))
        conn.commit()
        conn.close()
        return True, None, False

    # Check if the code matches
    if active_record['code'] != code:
        # Increment wrong attempts
        new_wrong_attempts = wrong_attempts + 1
        cursor.execute('UPDATE verification_codes SET wrong_attempts = ? WHERE id = ?',
                      (new_wrong_attempts, active_record['id']))
        conn.commit()
        conn.close()

        if new_wrong_attempts >= 3:
            return False, "Too many incorrect attempts. Please try again later.", True
        else:
            remaining = 3 - new_wrong_attempts
            return False, f"Invalid verification code. {remaining} attempt{'s' if remaining > 1 else ''} remaining.", False

    # Code is correct - mark as used
    cursor.execute('UPDATE verification_codes SET used = 1 WHERE id = ?', (active_record['id'],))
    conn.commit()
    conn.close()

    return True, None, False


def get_resend_status(email, purpose='login'):
    """Get resend status for an email. Returns (can_resend, seconds_until_resend, attempts_remaining)."""
    conn = get_db()
    cursor = conn.cursor()

    email_lower = email.lower()

    # Check if rate limited
    cursor.execute('''
        SELECT blocked_until FROM auth_rate_limits
        WHERE email = ? AND purpose = ?
        ORDER BY created_at DESC LIMIT 1
    ''', (email_lower, purpose))

    rate_limit = cursor.fetchone()
    if rate_limit:
        blocked_until = datetime.fromisoformat(rate_limit[0])
        if datetime.now() < blocked_until:
            seconds_remaining = int((blocked_until - datetime.now()).total_seconds())
            conn.close()
            return False, seconds_remaining, 0

    # Get current verification code record
    cursor.execute('''
        SELECT resend_count, last_resend_at FROM verification_codes
        WHERE email = ? AND purpose = ? AND used = 0
        ORDER BY created_at DESC LIMIT 1
    ''', (email_lower, purpose))

    record = cursor.fetchone()
    conn.close()

    if not record:
        return True, 0, 3  # No active code, can send first one

    resend_count = record[0] or 0
    last_resend_at = record[1]

    # Check cooldown between resends
    if last_resend_at:
        last_resend = datetime.fromisoformat(last_resend_at)
        cooldown_end = last_resend + timedelta(minutes=RESEND_COOLDOWN_MINUTES)
        if datetime.now() < cooldown_end:
            seconds_remaining = int((cooldown_end - datetime.now()).total_seconds())
            return False, seconds_remaining, 3 - resend_count

    attempts_remaining = 3 - resend_count
    return attempts_remaining > 0, 0, attempts_remaining


def resend_verification_code(email, purpose='login'):
    """Resend verification code. Returns (success, code_or_error, seconds_blocked)."""
    conn = get_db()
    cursor = conn.cursor()

    email_lower = email.lower()

    # Get current code record
    cursor.execute('''
        SELECT id, resend_count FROM verification_codes
        WHERE email = ? AND purpose = ? AND used = 0
        ORDER BY created_at DESC LIMIT 1
    ''', (email_lower, purpose))

    record = cursor.fetchone()

    if not record:
        conn.close()
        # No existing code, create new one
        code = create_verification_code(email, purpose)
        return True, code, 0

    record_id = record[0]
    resend_count = record[1] or 0

    # Check if max resends reached
    if resend_count >= 3:
        # Rate limit for 5 minutes
        blocked_until = datetime.now() + timedelta(minutes=5)
        cursor.execute('''
            INSERT INTO auth_rate_limits (email, purpose, blocked_until, created_at)
            VALUES (?, ?, ?, ?)
        ''', (email_lower, purpose, blocked_until.isoformat(), datetime.now().isoformat()))
        conn.commit()
        conn.close()
        return False, "Too many attempts. Please try again in 5 minutes.", 300

    # Update resend count and generate new code
    new_code = generate_verification_code()
    expires_at = datetime.now() + timedelta(minutes=10)

    cursor.execute('''
        UPDATE verification_codes
        SET code = ?, resend_count = resend_count + 1, last_resend_at = ?, expires_at = ?
        WHERE id = ?
    ''', (new_code, datetime.now().isoformat(), expires_at.isoformat(), record_id))

    conn.commit()
    conn.close()

    return True, new_code, 0


def clear_rate_limit(email, purpose='login'):
    """Clear rate limit for an email (called after successful verification)."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM auth_rate_limits WHERE email = ? AND purpose = ?', (email.lower(), purpose))
    conn.commit()
    conn.close()


def is_code_rate_limited(email, purpose='login'):
    """Check if code verification is rate limited (3+ wrong attempts within 5 min cooldown)."""
    conn = get_db()
    cursor = conn.cursor()

    now = datetime.now()

    # Check for ANY code with 3+ wrong attempts created in the last 5 minutes
    # This prevents bypass by creating a new code after being rate limited
    five_min_ago = (now - timedelta(minutes=5)).isoformat()
    cursor.execute('''
        SELECT wrong_attempts, created_at FROM verification_codes
        WHERE email = ? AND purpose = ? AND wrong_attempts >= 3 AND created_at > ?
        ORDER BY created_at DESC LIMIT 1
    ''', (email.lower(), purpose, five_min_ago))

    rate_limited_record = cursor.fetchone()
    conn.close()

    return rate_limited_record is not None


# =============================================================================
# DISCORD OAUTH ACCOUNT LINKING FUNCTIONS
# =============================================================================

def save_discord_oauth(user_id, discord_id, username, avatar, access_token, refresh_token, expires_at, avatar_decoration=None):
    """Save Discord OAuth tokens after successful authorization."""
    conn = get_db()
    cursor = conn.cursor()

    # Encrypt the tokens
    encrypted_access = encrypt_token(access_token) if access_token else None
    encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

    cursor.execute('''
        UPDATE users SET
            discord_oauth_discord_id = ?,
            discord_oauth_username = ?,
            discord_oauth_avatar = ?,
            discord_oauth_avatar_decoration = ?,
            discord_oauth_access_token = ?,
            discord_oauth_refresh_token = ?,
            discord_oauth_expires_at = ?
        WHERE id = ?
    ''', (discord_id, username, avatar, avatar_decoration, encrypted_access, encrypted_refresh, expires_at, user_id))

    conn.commit()
    conn.close()


def get_discord_oauth_status(user_id):
    """Get Discord OAuth linking status for a user."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT discord_oauth_linked, discord_oauth_discord_id, discord_oauth_username,
               discord_oauth_avatar, discord_oauth_linked_at
        FROM users WHERE id = ?
    ''', (user_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return None

    return {
        'is_linked': bool(result[0]),
        'discord_id': result[1],
        'username': result[2],
        'avatar': result[3],
        'linked_at': result[4]
    }


def get_discord_oauth_info(user_id):
    """Get full Discord OAuth info including whether OAuth was completed (but not token linked yet)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT discord_oauth_linked, discord_oauth_discord_id, discord_oauth_username,
               discord_oauth_avatar, discord_oauth_linked_at, discord_id, username, avatar,
               discord_oauth_avatar_decoration
        FROM users WHERE id = ?
    ''', (user_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return None

    return {
        'is_fully_linked': bool(result[0]),
        'oauth_discord_id': result[1],
        'oauth_username': result[2],
        'oauth_avatar': result[3],
        'linked_at': result[4],
        'has_oauth': result[1] is not None,  # True if OAuth was completed
        # Current linked account info (after full linking)
        'linked_discord_id': result[5],
        'linked_username': result[6],
        'linked_avatar': result[7],
        'oauth_avatar_decoration': result[8]
    }


def complete_discord_link(user_id, discord_token):
    """Complete Discord account linking after token is verified.
    Updates the main discord_id, username, avatar, and token fields."""
    conn = get_db()
    cursor = conn.cursor()

    # Get the OAuth info
    cursor.execute('''
        SELECT discord_oauth_discord_id, discord_oauth_username, discord_oauth_avatar
        FROM users WHERE id = ?
    ''', (user_id,))

    result = cursor.fetchone()
    if not result or not result[0]:
        conn.close()
        return False, "No Discord OAuth data found"

    oauth_discord_id = result[0]
    oauth_username = result[1]
    oauth_avatar = result[2]

    # Encrypt the Discord token
    encrypted_token = encrypt_token(discord_token)

    # Update the user with the linked Discord account
    cursor.execute('''
        UPDATE users SET
            discord_id = ?,
            username = ?,
            avatar = ?,
            discord_token = ?,
            discord_oauth_linked = 1,
            discord_oauth_linked_at = ?
        WHERE id = ?
    ''', (oauth_discord_id, oauth_username, oauth_avatar, encrypted_token, datetime.now().isoformat(), user_id))

    conn.commit()
    conn.close()

    return True, None


def unlink_discord_oauth(user_id):
    """Clear Discord OAuth data (allows user to re-link a different account)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE users SET
            discord_oauth_discord_id = NULL,
            discord_oauth_username = NULL,
            discord_oauth_avatar = NULL,
            discord_oauth_access_token = NULL,
            discord_oauth_refresh_token = NULL,
            discord_oauth_expires_at = NULL
        WHERE id = ?
    ''', (user_id,))

    conn.commit()
    conn.close()


def full_unlink_discord_account(user_id):
    """Fully unlink Discord account - clears both OAuth data and linked status.
    Called when token becomes invalid to reset the account to unlinked state."""
    conn = get_db()
    cursor = conn.cursor()

    # Get user's email to preserve it
    cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    email = result[0] if result else None

    # Reset all Discord-related fields while preserving email and account
    cursor.execute('''
        UPDATE users SET
            discord_id = ?,
            username = ?,
            avatar = NULL,
            discord_token = 'pending',
            discord_oauth_linked = 0,
            discord_oauth_linked_at = NULL,
            discord_oauth_discord_id = NULL,
            discord_oauth_username = NULL,
            discord_oauth_avatar = NULL,
            discord_oauth_access_token = NULL,
            discord_oauth_refresh_token = NULL,
            discord_oauth_expires_at = NULL
        WHERE id = ?
    ''', (f'pending_{email}' if email else f'pending_{user_id}',
          email.split('@')[0] if email else 'User',
          user_id))

    conn.commit()
    conn.close()


def is_discord_linked(user_id):
    """Quick check if user has fully linked their Discord account."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT discord_oauth_linked FROM users WHERE id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()

    return bool(result and result[0])


def update_discord_profile(user_id, username, avatar, avatar_decoration=None):
    """Update Discord profile info (username, avatar, decoration) from fresh API data."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE users SET
            discord_oauth_username = ?,
            discord_oauth_avatar = ?,
            discord_oauth_avatar_decoration = ?
        WHERE id = ?
    ''', (username, avatar, avatar_decoration, user_id))

    conn.commit()
    conn.close()


def get_user_by_internal_id(user_id):
    """Get user by their internal database ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


# =============================================================================
# TEAM MEMBER ANALYTICS FUNCTIONS
# =============================================================================

def get_member_analytics(member_user_id, team_id):
    """Get analytics data for a team member - ONLY for current team."""
    conn = get_db()
    cursor = conn.cursor()

    # Get member's last reset date to calculate current cycle for THIS TEAM
    cursor.execute('''
        SELECT business_last_reset
        FROM usage WHERE user_id = ?
    ''', (member_user_id,))
    usage = cursor.fetchone()
    last_reset = usage[0] if usage and usage[0] else None

    # Calculate current cycle from daily_message_stats since last reset for THIS TEAM
    if last_reset:
        cursor.execute('''
            SELECT SUM(messages_sent)
            FROM daily_message_stats
            WHERE user_id = ? AND team_id = ? AND date >= ?
        ''', (member_user_id, team_id, last_reset))
    else:
        # No reset date, count all messages for this team
        cursor.execute('''
            SELECT SUM(messages_sent)
            FROM daily_message_stats
            WHERE user_id = ? AND team_id = ?
        ''', (member_user_id, team_id))
    current_cycle_row = cursor.fetchone()
    current_cycle = current_cycle_row[0] if current_cycle_row and current_cycle_row[0] else 0

    # Calculate all-time stats from daily_message_stats for THIS TEAM ONLY
    cursor.execute('''
        SELECT SUM(messages_sent)
        FROM daily_message_stats
        WHERE user_id = ? AND team_id = ?
    ''', (member_user_id, team_id))
    all_time_row = cursor.fetchone()
    all_time = all_time_row[0] if all_time_row and all_time_row[0] else 0

    # Get when member joined the team
    cursor.execute('''
        SELECT added_at FROM business_team_members
        WHERE team_id = ? AND member_discord_id = (SELECT discord_id FROM users WHERE id = ?)
    ''', (team_id, member_user_id))
    member_row = cursor.fetchone()
    joined_at = member_row[0] if member_row else None

    # If no join date found, check if user is the team owner and use team creation date
    if not joined_at:
        cursor.execute('''
            SELECT created_at FROM business_teams
            WHERE id = ? AND owner_user_id = ?
        ''', (team_id, member_user_id))
        owner_row = cursor.fetchone()
        if owner_row:
            joined_at = owner_row[0]

    # Get team's total usage for percentage calculation (from daily_message_stats for THIS TEAM)
    cursor.execute('''
        SELECT SUM(dms.messages_sent)
        FROM daily_message_stats dms
        JOIN business_team_members btm ON btm.member_discord_id = (SELECT discord_id FROM users WHERE id = dms.user_id)
        WHERE btm.team_id = ? AND dms.team_id = ? AND btm.invitation_status = 'accepted'
    ''', (team_id, team_id))
    total_row = cursor.fetchone()
    team_total = total_row[0] if total_row and total_row[0] else 0

    # Also add owner's usage to total (from daily_message_stats)
    cursor.execute('''
        SELECT bt.owner_user_id FROM business_teams bt WHERE bt.id = ?
    ''', (team_id,))
    owner_row = cursor.fetchone()
    if owner_row:
        cursor.execute('''
            SELECT SUM(messages_sent) FROM daily_message_stats
            WHERE user_id = ? AND team_id = ?
        ''', (owner_row[0], team_id))
        owner_usage = cursor.fetchone()
        if owner_usage and owner_usage[0]:
            team_total += owner_usage[0]

    conn.close()

    percentage = (all_time / team_total * 100) if team_total > 0 else 0

    return {
        'current_cycle': current_cycle,
        'all_time': all_time,
        'joined_at': joined_at,
        'team_total': team_total,
        'percentage': round(percentage, 1)
    }


def get_member_daily_stats(member_user_id, team_id, start_date=None, end_date=None):
    """Get daily message stats for a team member within a date range."""
    conn = get_db()
    cursor = conn.cursor()

    # Default to last 30 days if no dates specified
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    cursor.execute('''
        SELECT date, messages_sent
        FROM daily_message_stats
        WHERE user_id = ? AND team_id = ? AND date >= ? AND date <= ?
        ORDER BY date ASC
    ''', (member_user_id, team_id, start_date, end_date))

    rows = cursor.fetchall()
    conn.close()

    # Create a dict of existing data
    data_by_date = {row[0]: row[1] for row in rows}

    # Fill in all dates in range with 0 for missing days
    stats = []
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        stats.append({'date': date_str, 'count': data_by_date.get(date_str, 0)})
        current += timedelta(days=1)

    # Calculate summary stats
    total = sum(s['count'] for s in stats)
    days = len(stats) if stats else 1
    avg = total / days if days > 0 else 0
    peak = max((s['count'] for s in stats), default=0)
    peak_date = next((s['date'] for s in stats if s['count'] == peak), None) if peak > 0 else None

    return {
        'stats': stats,
        'total': total,
        'average': round(avg, 1),
        'peak': peak,
        'peak_date': peak_date,
        'start_date': start_date,
        'end_date': end_date
    }


def get_member_join_date(member_user_id, team_id):
    """Get when a member joined a specific team."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT added_at FROM business_team_members
        WHERE team_id = ? AND member_discord_id = (SELECT discord_id FROM users WHERE id = ?)
    ''', (team_id, member_user_id))

    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None


def get_personal_daily_stats(user_id, start_date=None, end_date=None):
    """Get daily message stats for a user's personal usage (non-team messages)."""
    conn = get_db()
    cursor = conn.cursor()

    # Default to last 30 days if no dates specified
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    # Get personal stats (where team_id is NULL or 0, excluding team messages)
    cursor.execute('''
        SELECT date, messages_sent
        FROM daily_message_stats
        WHERE user_id = ? AND (team_id IS NULL OR team_id = 0) AND date >= ? AND date <= ?
        ORDER BY date ASC
    ''', (user_id, start_date, end_date))

    rows = cursor.fetchall()
    conn.close()

    # Create a dict of existing data
    data_by_date = {row[0]: row[1] for row in rows}

    # Fill in all dates in range with 0 for missing days
    stats = []
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    while current <= end:
        date_str = current.strftime('%Y-%m-%d')
        stats.append({'date': date_str, 'count': data_by_date.get(date_str, 0)})
        current += timedelta(days=1)

    # Calculate summary stats
    total = sum(s['count'] for s in stats)
    days = len(stats) if stats else 1
    avg = total / days if days > 0 else 0
    peak = max((s['count'] for s in stats), default=0)
    peak_date = next((s['date'] for s in stats if s['count'] == peak), None) if peak > 0 else None

    return {
        'stats': stats,
        'total': total,
        'average': round(avg, 1),
        'peak': peak,
        'peak_date': peak_date,
        'start_date': start_date,
        'end_date': end_date
    }


def get_personal_analytics_summary(user_id):
    """Get summary analytics for a user: all-time counts and peak dates."""
    conn = get_db()
    cursor = conn.cursor()

    # Get all-time personal and team messages from usage table
    cursor.execute('''
        SELECT all_time_sent, business_all_time_sent
        FROM usage WHERE user_id = ?
    ''', (user_id,))
    usage_row = cursor.fetchone()

    personal_all_time = usage_row[0] if usage_row and usage_row[0] else 0
    team_all_time = usage_row[1] if usage_row and usage_row[1] else 0
    total_all_time = personal_all_time + team_all_time

    # Get peak date for personal panel (team_id = 0 or NULL)
    cursor.execute('''
        SELECT date, SUM(messages_sent) as total
        FROM daily_message_stats
        WHERE user_id = ? AND (team_id IS NULL OR team_id = 0)
        GROUP BY date
        ORDER BY total DESC
        LIMIT 1
    ''', (user_id,))
    personal_peak_row = cursor.fetchone()
    personal_peak_date = personal_peak_row[0] if personal_peak_row else None

    # Get peak date across all panels (personal + team)
    cursor.execute('''
        SELECT date, SUM(messages_sent) as total
        FROM daily_message_stats
        WHERE user_id = ?
        GROUP BY date
        ORDER BY total DESC
        LIMIT 1
    ''', (user_id,))
    all_peak_row = cursor.fetchone()
    all_peak_date = all_peak_row[0] if all_peak_row else None

    conn.close()

    return {
        'personal_all_time': personal_all_time,
        'team_all_time': team_all_time,
        'total_all_time': total_all_time,
        'personal_peak_date': personal_peak_date,
        'all_peak_date': all_peak_date
    }


# =============================================================================
# LINKED DISCORD ACCOUNTS FUNCTIONS (for sending messages)
# =============================================================================

def add_linked_discord_account(user_id, discord_id, username, avatar, avatar_decoration, discord_token,
                                oauth_access_token=None, oauth_refresh_token=None, oauth_expires_at=None):
    """Add a new linked Discord account for the user."""
    conn = get_db()
    cursor = conn.cursor()

    # Encrypt tokens
    encrypted_token = encrypt_token(discord_token)
    encrypted_oauth_access = encrypt_token(oauth_access_token) if oauth_access_token else None
    encrypted_oauth_refresh = encrypt_token(oauth_refresh_token) if oauth_refresh_token else None

    try:
        cursor.execute('''
            INSERT INTO linked_discord_accounts
            (user_id, discord_id, username, avatar, avatar_decoration, discord_token,
             oauth_access_token, oauth_refresh_token, oauth_expires_at, linked_at, last_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, discord_id, username, avatar, avatar_decoration, encrypted_token,
              encrypted_oauth_access, encrypted_oauth_refresh, oauth_expires_at,
              datetime.now().isoformat(), datetime.now().isoformat()))

        conn.commit()
        account_id = cursor.lastrowid
        conn.close()
        return True, account_id
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Account already linked"


def get_linked_discord_accounts(user_id):
    """Get all linked Discord accounts for a user."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, discord_id, username, avatar, avatar_decoration, linked_at, last_verified, is_valid
        FROM linked_discord_accounts
        WHERE user_id = ?
        ORDER BY linked_at DESC
    ''', (user_id,))

    accounts = cursor.fetchall()
    conn.close()

    return [dict(account) for account in accounts]


def get_linked_discord_account_count(user_id):
    """Get the number of linked Discord accounts for a user."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM linked_discord_accounts WHERE user_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()

    return count


def get_linked_discord_account_by_id(account_id):
    """Get a specific linked Discord account by its ID."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, user_id, discord_id, username, avatar, avatar_decoration,
               discord_token, linked_at, last_verified, is_valid
        FROM linked_discord_accounts
        WHERE id = ?
    ''', (account_id,))

    account = cursor.fetchone()
    conn.close()

    if not account:
        return None

    account_dict = dict(account)
    # Decrypt token if needed
    if account_dict.get('discord_token'):
        account_dict['discord_token'] = decrypt_token(account_dict['discord_token'])

    return account_dict


def unlink_discord_account(user_id, account_id):
    """Unlink a Discord account."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        DELETE FROM linked_discord_accounts
        WHERE id = ? AND user_id = ?
    ''', (account_id, user_id))

    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()

    return deleted


def update_linked_discord_account_profile(account_id, username, avatar, avatar_decoration):
    """Update the profile info of a linked Discord account."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE linked_discord_accounts
        SET username = ?, avatar = ?, avatar_decoration = ?, last_verified = ?
        WHERE id = ?
    ''', (username, avatar, avatar_decoration, datetime.now().isoformat(), account_id))

    conn.commit()
    conn.close()


def mark_linked_account_invalid(account_id):
    """Mark a linked Discord account as invalid (bad token)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE linked_discord_accounts
        SET is_valid = 0, last_verified = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), account_id))

    conn.commit()
    conn.close()


def mark_linked_account_valid(account_id):
    """Mark a linked Discord account as valid (good token)."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE linked_discord_accounts
        SET is_valid = 1, last_verified = ?
        WHERE id = ?
    ''', (datetime.now().isoformat(), account_id))

    conn.commit()
    conn.close()


def search_linked_discord_accounts(user_id, query):
    """Search linked Discord accounts by username or Discord ID."""
    conn = get_db()
    cursor = conn.cursor()

    search_query = f'%{query}%'
    cursor.execute('''
        SELECT id, discord_id, username, avatar, avatar_decoration, linked_at, last_verified, is_valid
        FROM linked_discord_accounts
        WHERE user_id = ? AND (username LIKE ? OR discord_id LIKE ?)
        ORDER BY linked_at DESC
    ''', (user_id, search_query, search_query))

    accounts = cursor.fetchall()
    conn.close()

    return [dict(account) for account in accounts]


# Initialize database on import
init_db()
