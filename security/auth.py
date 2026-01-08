"""
Security module for Borz Marketing Panel
Provides: Rate limiting, input validation, CSRF protection, security headers
"""

import time
import re
import os
import hashlib
import secrets
from functools import wraps
from flask import request, session, abort, g
from collections import defaultdict
import threading

# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """Thread-safe rate limiter using sliding window algorithm."""

    def __init__(self):
        self.requests = defaultdict(list)  # IP -> list of timestamps
        self.lock = threading.Lock()

    def is_rate_limited(self, identifier, max_requests, window_seconds):
        """
        Check if identifier (IP) is rate limited.
        Returns (is_limited, remaining, reset_time)
        """
        now = time.time()
        window_start = now - window_seconds

        with self.lock:
            # Clean old requests
            self.requests[identifier] = [
                ts for ts in self.requests[identifier]
                if ts > window_start
            ]

            current_count = len(self.requests[identifier])

            if current_count >= max_requests:
                # Calculate reset time
                oldest_in_window = min(self.requests[identifier]) if self.requests[identifier] else now
                reset_time = oldest_in_window + window_seconds
                return True, 0, reset_time

            # Record this request
            self.requests[identifier].append(now)
            remaining = max_requests - current_count - 1

            return False, remaining, now + window_seconds

    def cleanup(self):
        """Remove old entries to prevent memory bloat."""
        now = time.time()
        max_age = 3600  # 1 hour

        with self.lock:
            keys_to_remove = []
            for key, timestamps in self.requests.items():
                self.requests[key] = [ts for ts in timestamps if now - ts < max_age]
                if not self.requests[key]:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()

# Rate limit configurations (requests per window)
RATE_LIMITS = {
    'login': (5, 60),         # 5 attempts per minute
    'signup': (3, 60),        # 3 attempts per minute
    'api': (60, 60),          # 60 requests per minute for API
    'send_message': (30, 60), # 30 messages per minute
    'token_update': (3, 300), # 3 token updates per 5 minutes
    'general': (100, 60),     # 100 requests per minute general
}


def get_client_ip():
    """Get real client IP, handling proxies."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP').strip()
    return request.remote_addr


def rate_limit(limit_type='general'):
    """
    Decorator for rate limiting endpoints.
    Usage: @rate_limit('login')

    NOTE: Rate limiting is DISABLED for general endpoints.
    Only auth endpoints (login/signup/verify) have their own separate rate limiting.
    The hosting provider handles DDoS/DoS protection.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Rate limiting disabled - pass through all requests
            # Auth endpoints (login/signup/verify) have their own rate limiting
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# INPUT VALIDATION & SANITIZATION
# =============================================================================

def sanitize_string(value, max_length=1000, allow_html=False):
    """
    Sanitize string input.
    - Strips whitespace
    - Limits length
    - Optionally removes HTML tags
    """
    if not isinstance(value, str):
        return ''

    value = value.strip()

    if len(value) > max_length:
        value = value[:max_length]

    if not allow_html:
        # Remove potential script tags and other dangerous HTML
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'<[^>]+>', '', value)
        # Escape remaining special chars
        value = value.replace('<', '&lt;').replace('>', '&gt;')

    return value


def validate_discord_id(discord_id):
    """
    Validate Discord ID format.
    Discord IDs are 17-19 digit snowflakes.
    """
    if not discord_id:
        return False

    if not isinstance(discord_id, str):
        discord_id = str(discord_id)

    # Discord snowflake: 17-19 digits
    if not re.match(r'^\d{17,19}$', discord_id):
        return False

    return True


def validate_channel_id(channel_id):
    """Validate Discord channel ID format."""
    return validate_discord_id(channel_id)


def validate_guild_id(guild_id):
    """Validate Discord guild/server ID format."""
    return validate_discord_id(guild_id)


def validate_discord_token(token):
    """
    Basic Discord token format validation.
    Discord tokens have a specific format: base64.timestamp.hmac
    """
    if not token:
        return False

    if not isinstance(token, str):
        return False

    # Token should have reasonable length (50-100 chars typically)
    if len(token) < 50 or len(token) > 150:
        return False

    # Basic format check - should contain dots
    parts = token.split('.')
    if len(parts) != 3:
        return False

    return True


def validate_message_content(content):
    """
    Validate message content for sending.
    Returns (is_valid, error_message)
    """
    if not content:
        return False, "Message cannot be empty"

    if not isinstance(content, str):
        return False, "Invalid message format"

    content = content.strip()

    if len(content) == 0:
        return False, "Message cannot be empty"

    if len(content) > 2000:  # Discord's message limit
        return False, "Message exceeds 2000 character limit"

    return True, None


def validate_plan_data(plan_type, plan_id, billing_period=None):
    """Validate plan selection data."""
    valid_plan_types = ['subscription', 'one-time', 'business']
    valid_billing_periods = ['monthly', 'yearly', None]

    if plan_type not in valid_plan_types:
        return False, "Invalid plan type"

    if not plan_id or not isinstance(plan_id, str):
        return False, "Invalid plan ID"

    # Sanitize plan_id to prevent injection
    if not re.match(r'^[a-zA-Z0-9_-]+$', plan_id):
        return False, "Invalid plan ID format"

    if plan_type in ['subscription', 'business'] and billing_period not in ['monthly', 'yearly']:
        return False, "Invalid billing period"

    return True, None


# =============================================================================
# CSRF PROTECTION
# =============================================================================

def generate_csrf_token():
    """Generate a secure CSRF token."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token(token):
    """Validate CSRF token."""
    stored_token = session.get('_csrf_token')
    if not stored_token or not token:
        return False
    # Use constant-time comparison to prevent timing attacks
    return secrets.compare_digest(stored_token, token)


def csrf_protect(f):
    """
    Decorator to enforce CSRF protection on POST/PUT/DELETE requests.
    Token can be in form data as 'csrf_token' or header as 'X-CSRF-Token'.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method in ['POST', 'PUT', 'DELETE']:
            token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')

            # For JSON requests, also check body
            if not token and request.is_json:
                data = request.get_json(silent=True)
                if data:
                    token = data.get('csrf_token')

            if not validate_csrf_token(token):
                return {'error': 'Invalid or missing CSRF token'}, 403

        return f(*args, **kwargs)
    return decorated_function


# =============================================================================
# SECURITY HEADERS
# =============================================================================

def add_security_headers(response):
    """Add security headers to response."""
    # HTTP Strict Transport Security (HSTS) - only in production with HTTPS
    if os.getenv('FLASK_ENV') == 'production':
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'

    # XSS Protection (legacy, but still useful)
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Prevent MIME sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Referrer Policy
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

    # Permissions Policy (disable sensitive features)
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'

    # Content Security Policy - allows inline scripts for your existing JS
    # Note: In production, move inline scripts to files and use nonces
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' https://cdn.discordapp.com data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'self';"
    )

    return response


# =============================================================================
# SESSION SECURITY
# =============================================================================

def secure_session_config(app):
    """Apply secure session configuration to Flask app."""
    # Session cookie settings
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'  # HTTPS only in production
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JS access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

    # Use a strong secret key
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key or secret_key == 'your-secret-key-here':
        print("[SECURITY WARNING] Using a weak or default SECRET_KEY! Set a strong SECRET_KEY environment variable.")
        # Generate a random one for this session (tokens will be invalid on restart)
        app.secret_key = secrets.token_hex(32)
    else:
        app.secret_key = secret_key


def check_session_integrity(discord_id, session_id):
    """
    Verify session integrity.
    Returns True if session is valid, False otherwise.
    """
    from database import validate_user_session
    return validate_user_session(discord_id, session_id)


# =============================================================================
# PASSWORD/TOKEN SECURITY
# =============================================================================

def hash_for_logging(value):
    """
    Create a hash of a value for safe logging (never log actual tokens).
    """
    if not value:
        return 'none'
    return hashlib.sha256(value.encode()).hexdigest()[:16]


# =============================================================================
# REQUEST VALIDATION MIDDLEWARE
# =============================================================================

def validate_json_request():
    """
    Validate incoming JSON requests.
    Call this at the start of API endpoints.
    Returns (is_valid, error_response)
    """
    if not request.is_json:
        return False, ({'error': 'Content-Type must be application/json'}, 400)

    try:
        data = request.get_json()
        if data is None:
            return False, ({'error': 'Invalid JSON body'}, 400)
    except Exception:
        return False, ({'error': 'Failed to parse JSON'}, 400)

    return True, None


# =============================================================================
# IP BLOCKING (Optional - for abuse prevention)
# =============================================================================

# In-memory blocklist (use Redis in production)
blocked_ips = set()
blocked_ips_lock = threading.Lock()


def block_ip(ip, duration_seconds=3600):
    """Block an IP address temporarily."""
    with blocked_ips_lock:
        blocked_ips.add((ip, time.time() + duration_seconds))


def is_ip_blocked(ip):
    """Check if IP is blocked."""
    now = time.time()
    with blocked_ips_lock:
        # Clean expired blocks
        expired = [item for item in blocked_ips if item[1] < now]
        for item in expired:
            blocked_ips.discard(item)

        # Check if blocked
        for blocked_ip, expiry in blocked_ips:
            if blocked_ip == ip and expiry > now:
                return True
    return False


def ip_block_check(f):
    """Decorator to check if IP is blocked."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = get_client_ip()
        if is_ip_blocked(ip):
            return {'error': 'Your IP has been temporarily blocked due to abuse.'}, 403
        return f(*args, **kwargs)
    return decorated_function
