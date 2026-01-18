from flask import Flask, render_template, redirect, url_for, session, request, jsonify
import os
import secrets
from dotenv import load_dotenv
import requests
import uuid
import sqlite3
from datetime import timedelta, datetime
from urllib.parse import urlencode

# Database imports
from database import (
    init_db, create_user, get_user_by_discord_id, get_user_by_id, update_user_token,
    set_subscription, get_active_subscription, can_send_message,
    record_successful_send, get_plan_status, update_user_session,
    validate_user_session, save_user_data, get_user_data,
    get_all_users_for_admin, get_user_admin_details, ban_user, unban_user,
    flag_user, unflag_user, delete_user_account_admin,
    get_decrypted_token,
    # Email authentication functions
    get_user_by_email, create_user_with_email, create_verification_code,
    verify_code, get_resend_status, resend_verification_code, clear_rate_limit,
    is_code_rate_limited,
    # Discord OAuth account linking functions
    save_discord_oauth, get_discord_oauth_status, get_discord_oauth_info,
    complete_discord_link, unlink_discord_oauth, is_discord_linked,
    get_user_by_internal_id, full_unlink_discord_account, update_discord_profile
)

# Config imports
from config import (
    BUTTONS, HOMEPAGE, NAVBAR, COLORS, PAGES, TEXT, get_all_config, is_admin,
    DATABASE_VERSION, DATABASE_WIPE_MESSAGE, SITE,
    get_page_description, get_page_embed,
    SUPPORT_HERO_TITLE, SUPPORT_FAQ_TITLE, SUPPORT_CONTACT_TEXT, FAQ_ITEMS
)

# Security imports
from security import (
    rate_limit, rate_limiter,
    validate_discord_id, validate_discord_token, validate_message_content, validate_plan_data,
    validate_channel_id,
    generate_csrf_token, validate_csrf_token, add_security_headers,
    secure_session_config, get_client_ip as security_get_client_ip,
    is_ip_blocked, check_message_content, BLACKLISTED_WORDS, PHRASE_EXCEPTIONS
)

load_dotenv()

app = Flask(__name__)

# Apply secure session configuration
secure_session_config(app)

# Session security configuration
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'  # Secure cookies in production
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)  # 30 days session
app.config['SESSION_PERMANENT'] = True

# Make CSRF token available to all templates
@app.context_processor
def inject_csrf_token():
    return {'csrf_token': generate_csrf_token()}

# Make user_data available to all templates (for navbar profile photo, settings popup, etc)
@app.context_processor
def inject_user_data():
    if 'user' in session:
        user = get_user_by_id(session.get('user_id'))
        if user:
            # Inject both user_data and db_user (full database user with banned/flagged status)
            return {
                'user_data': get_user_data(user['id']),
                'db_user': user  # Full user object from database with banned, flagged, flag_count, etc
            }
    return {'user_data': None, 'db_user': None}

# Make site config available in all templates
@app.context_processor
def inject_site_config():
    return {
        'site_config': get_all_config(),
        'welcome_slideshow': NAVBAR['welcome_slideshow'],
        'button_styles': BUTTONS,
        'colors': COLORS,
        'pages': PAGES,
        'text': TEXT,
        'db_version': DATABASE_VERSION,
        'db_wipe_message': DATABASE_WIPE_MESSAGE,
        # Site-wide settings (font, layout, etc.)
        'site': SITE,
        # Page metadata helper functions
        'get_page_embed': get_page_embed,
        'get_page_description': get_page_description,
    }

# Custom Jinja filter for formatting dates
@app.template_filter('format_date')
def format_date_filter(date_str):
    """Format ISO date string to readable format like 'January 3, 2026'"""
    if not date_str:
        return '-'
    try:
        # Parse the ISO date string (handles both full datetime and date-only)
        if 'T' in str(date_str):
            dt = datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
        else:
            dt = datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
        return dt.strftime('%B %d, %Y')  # e.g., "January 03, 2026"
    except (ValueError, TypeError):
        return str(date_str)[:10] if date_str else '-'

# Discord API configuration (for fetching user info)
DISCORD_API_BASE = 'https://discord.com/api/v10'

# Discord OAuth2 configuration (for account linking)
DISCORD_CLIENT_ID = os.getenv('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.getenv('DISCORD_CLIENT_SECRET')
DISCORD_OAUTH_REDIRECT_URI = os.getenv('DISCORD_OAUTH_REDIRECT_URI', 'http://127.0.0.1:5000/discord/callback')

# Initialize database
init_db()

# Use the security module's get_client_ip function
get_client_ip = security_get_client_ip

# CSRF validation helper for API endpoints
def check_csrf():
    """Check CSRF token from request headers or JSON body. Returns error response if invalid."""
    # Check both header formats for compatibility
    token = request.headers.get('X-CSRF-Token') or request.headers.get('X-CSRFToken')
    if not token and request.is_json:
        data = request.get_json(silent=True)
        if data:
            token = data.get('csrf_token')
    if not validate_csrf_token(token):
        return {'error': 'Invalid or missing CSRF token'}, 403
    return None

# Helper function to check business access
def has_business_access(user_id, discord_id):
    """Check if user has access to business features (owner or member)."""
    from database import get_business_team_by_owner, get_business_team_by_member, get_discord_oauth_info, get_active_subscription

    # Check if user owns a business team
    team = get_business_team_by_owner(user_id)
    if team:
        return True

    # Check if user has a business subscription but no team yet (team creation failed previously)
    subscription = get_active_subscription(user_id)
    if subscription and subscription.get('plan_id', '').startswith('team_plan_'):
        return True

    # Check if user is a member of a business team using their main discord_id
    team = get_business_team_by_member(discord_id)
    if team:
        return True

    # Also check using OAuth-linked Discord ID (for email users who linked Discord later)
    oauth_info = get_discord_oauth_info(user_id)
    if oauth_info and oauth_info.get('oauth_discord_id'):
        team = get_business_team_by_member(oauth_info['oauth_discord_id'])
        if team:
            return True

    return False

def is_business_owner(user_id):
    """Check if user is specifically a business team owner (or has a business subscription)."""
    from database import get_business_team_by_owner, get_active_subscription
    team = get_business_team_by_owner(user_id)
    if team:
        return True
    # Also check for business subscription without team (team creation may have failed)
    subscription = get_active_subscription(user_id)
    if subscription and subscription.get('plan_id', '').startswith('team_plan_'):
        return True
    return False

def fetch_discord_user_info(discord_id):
    """Fetch user information from Discord API using bot token."""
    bot_token = os.getenv('DISCORD_BOT_TOKEN')

    if not bot_token:
        return None, None

    try:
        headers = {'Authorization': f'Bot {bot_token}'}
        response = requests.get(f'{DISCORD_API_BASE}/users/{discord_id}', headers=headers, timeout=5)

        if response.status_code == 200:
            discord_user = response.json()
            username = discord_user.get('username', 'Unknown User')
            avatar = discord_user.get('avatar', '')
            print(f"[DISCORD API] Successfully fetched user info for {discord_id}: {username}")
            return username, avatar
        else:
            print(f"[DISCORD API] Failed to fetch user {discord_id}: Status {response.status_code}, Response: {response.text}")
            return None, None
    except requests.exceptions.Timeout:
        print(f"[DISCORD API] Timeout fetching user {discord_id}")
        return None, None
    except Exception as e:
        print(f"[DISCORD API] Error fetching user {discord_id}: {str(e)}")
        return None, None

# Session validation before each request
@app.before_request
def validate_session():
    """Validate user session before each request (single session enforcement)."""
    # Skip validation for static files, login, signup, verify, discord callback, and home page
    if request.endpoint in ['static', 'login_page', 'signup_page', 'verify_page', 'discord_oauth_callback', 'home', 'root']:
        return

    # Check if user is logged in
    if 'user' in session and 'session_id' in session:
        discord_id = session['user']['id']
        session_id = session['session_id']

        # Validate session ID against database
        if not validate_user_session(discord_id, session_id):
            # Session invalid - clear session and redirect to home
            session.clear()
            return redirect(url_for('home'))

# Add security headers to all responses
@app.after_request
def apply_security_headers(response):
    return add_security_headers(response)

# Check for blocked IPs
@app.before_request
def check_blocked_ip():
    if is_ip_blocked(get_client_ip()):
        return {'error': 'Your IP has been temporarily blocked due to abuse.'}, 403

@app.route('/')
def root():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    # Get plan status if user is logged in
    plan_status = None
    has_business = False
    is_admin_user = False
    is_owner = False
    user = None
    if 'user' in session:
        user = get_user_by_id(session.get('user_id'))
        if user:
            plan_status = get_plan_status(user['id'])
            # Check if user has business access (owner or member)
            from database import is_business_plan_owner, is_business_team_member
            has_business = is_business_plan_owner(user['id']) or is_business_team_member(session['user']['id'])
            is_owner = is_business_owner(user['id'])
            # Check if user is admin (use email from database)
            is_admin_user = is_admin(user.get('email'))

    return render_template('home.html',
                         slideshow_messages=HOMEPAGE['hero']['slideshow_messages'],
                         slideshow_interval=HOMEPAGE['hero']['slideshow_interval'],
                         slideshow_fade_duration=HOMEPAGE['hero']['slideshow_fade_duration'],
                         hero_image=HOMEPAGE['hero']['hero_image'],
                         hero_panel_images=HOMEPAGE['hero']['panel_images'],
                         about_title=HOMEPAGE['about']['title'],
                         about_description=HOMEPAGE['about']['description'],
                         hero_cta_button_text=HOMEPAGE['hero']['cta_button_text'],
                         scroll_indicator_text=HOMEPAGE['hero']['scroll_indicator_text'],
                         why_discord_title=HOMEPAGE['why_discord']['title'],
                         why_discord_stats=HOMEPAGE['why_discord']['stats'],
                         why_discord_benefits=HOMEPAGE['why_discord']['benefits'],
                         plan_status=plan_status,
                         has_business=has_business,
                         is_owner=is_owner,
                         is_admin_user=is_admin_user,
                         user=user)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if 'authenticated' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        error = session.pop('login_error', None)
        csrf_token = generate_csrf_token()
        session['csrf_token'] = csrf_token

        # Store referrer if it's a valid page to return to after login
        # Only store on first visit (not when redirected from verify)
        referrer = request.referrer
        if referrer and not any(path in referrer for path in ['/login', '/signup', '/verify', '/logout']):
            if 'login_referrer' not in session:
                session['login_referrer'] = referrer
                session.modified = True  # Force session save
                print(f"[LOGIN] Stored referrer: {referrer}")

        response = app.make_response(render_template('login.html', error=error, csrf_token=csrf_token))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # POST request handling - email-based login
    email = request.form.get('email', '').strip().lower()

    if not email:
        csrf_token = generate_csrf_token()
        session['csrf_token'] = csrf_token
        return render_template('login.html', error='Email is required', csrf_token=csrf_token), 400

    # Check if email exists
    user = get_user_by_email(email)
    if not user:
        csrf_token = generate_csrf_token()
        session['csrf_token'] = csrf_token
        return render_template('login.html', error='No account found with this email. Please sign up first.', csrf_token=csrf_token), 400

    # Check if there's already an active verification code (prevents bypass by re-submitting login)
    from database import has_active_verification_code
    has_active, is_rate_limited = has_active_verification_code(email, 'login')

    if is_rate_limited:
        csrf_token = generate_csrf_token()
        session['csrf_token'] = csrf_token
        return render_template('login.html', error='Too many incorrect attempts. Please wait 5 minutes before trying again.', csrf_token=csrf_token), 429

    # Store email in session for login verification
    session['pending_login_email'] = email

    # Only create a new code if there isn't an active one
    if not has_active:
        # Check resend rate limiting (prevents spam)
        can_send, cooldown_seconds, attempts_remaining = get_resend_status(email, 'login')
        if not can_send and cooldown_seconds > 0:
            csrf_token = generate_csrf_token()
            session['csrf_token'] = csrf_token
            return render_template('login.html', error=f'Too many attempts. Please wait {cooldown_seconds} seconds.', csrf_token=csrf_token), 429

        # Create verification code and send email
        code = create_verification_code(email, 'login')

        # Check if rate limited from too many wrong attempts
        if code is None:
            csrf_token = generate_csrf_token()
            session['csrf_token'] = csrf_token
            return render_template('login.html', error='Too many incorrect attempts. Please wait 5 minutes before trying again.', csrf_token=csrf_token), 429

        # TODO: Send email via Resend API

    # Redirect to verification page (code already exists or was just created)
    return redirect(url_for('verify_code_page', purpose='login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if 'authenticated' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'GET':
        error = session.pop('signup_error', None)
        csrf_token = generate_csrf_token()
        session['csrf_token'] = csrf_token

        response = app.make_response(render_template('signup.html', error=error, csrf_token=csrf_token))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    # POST request handling - email-based signup
    email = request.form.get('email', '').strip().lower()

    if not email:
        csrf_token = generate_csrf_token()
        session['csrf_token'] = csrf_token
        return render_template('signup.html', error='Email is required', csrf_token=csrf_token), 400

    # Validate email format and domain
    import re
    if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        csrf_token = generate_csrf_token()
        session['csrf_token'] = csrf_token
        return render_template('signup.html', error='Invalid email format', csrf_token=csrf_token), 400

    # Check against blacklisted domains
    from config import BLACKLISTED_EMAIL_DOMAINS, ALLOWED_EMAIL_TLDS
    for blacklisted in BLACKLISTED_EMAIL_DOMAINS:
        if email.endswith(blacklisted):
            csrf_token = generate_csrf_token()
            session['csrf_token'] = csrf_token
            return render_template('signup.html', error=f'Email domain {blacklisted} is not allowed', csrf_token=csrf_token), 400

    # Check if email ends with an allowed TLD
    if ALLOWED_EMAIL_TLDS:
        is_allowed = any(email.endswith(tld) for tld in ALLOWED_EMAIL_TLDS)
        if not is_allowed:
            csrf_token = generate_csrf_token()
            session['csrf_token'] = csrf_token
            return render_template('signup.html', error='Email domain is not supported', csrf_token=csrf_token), 400

    # Check if email already exists
    existing_user = get_user_by_email(email)
    if existing_user:
        csrf_token = generate_csrf_token()
        session['csrf_token'] = csrf_token
        return render_template('signup.html', error='An account with this email already exists. Please login instead.', csrf_token=csrf_token), 400

    # Check if there's already an active verification code (prevents bypass by re-submitting signup)
    from database import has_active_verification_code
    has_active, is_rate_limited = has_active_verification_code(email, 'signup')

    if is_rate_limited:
        csrf_token = generate_csrf_token()
        session['csrf_token'] = csrf_token
        return render_template('signup.html', error='Too many incorrect attempts. Please wait 5 minutes before trying again.', csrf_token=csrf_token), 429

    # Store email in session for signup completion
    session['pending_signup_email'] = email

    # Only create a new code if there isn't an active one
    if not has_active:
        # Check resend rate limiting (prevents spam)
        can_send, cooldown_seconds, attempts_remaining = get_resend_status(email, 'signup')
        if not can_send and cooldown_seconds > 0:
            csrf_token = generate_csrf_token()
            session['csrf_token'] = csrf_token
            return render_template('signup.html', error=f'Too many attempts. Please wait {cooldown_seconds} seconds.', csrf_token=csrf_token), 429

        # Create verification code and send email
        code = create_verification_code(email, 'signup')

        # Check if rate limited from too many wrong attempts
        if code is None:
            csrf_token = generate_csrf_token()
            session['csrf_token'] = csrf_token
            return render_template('signup.html', error='Too many incorrect attempts. Please wait 5 minutes before trying again.', csrf_token=csrf_token), 429

        # TODO: Send email via Resend API

    # Redirect to verification page (code already exists or was just created)
    return redirect(url_for('verify_code_page', purpose='signup'))

@app.route('/verify', methods=['GET', 'POST'])
def verify_code_page():
    purpose = request.args.get('purpose') or request.form.get('purpose', 'login')

    # SECURITY: Get email from session only - never from client input
    # This prevents attackers from verifying arbitrary emails via inspect element
    if purpose == 'signup':
        email = session.get('pending_signup_email')
    elif purpose == 'login':
        email = session.get('pending_login_email')
    elif purpose == 'email_change':
        email = session.get('pending_email_change')
    else:
        email = None

    if not email:
        # No pending verification - redirect to appropriate page
        if purpose == 'signup':
            return redirect(url_for('signup_page'))
        return redirect(url_for('login_page'))

    csrf_token = generate_csrf_token()
    session['csrf_token'] = csrf_token

    # Get resend status
    can_resend, cooldown_seconds, attempts_remaining = get_resend_status(email, purpose)

    # Check if code verification is rate limited
    code_rate_limited = is_code_rate_limited(email, purpose)

    if request.method == 'GET':
        return render_template('verify.html',
                             email=email,
                             purpose=purpose,
                             csrf_token=csrf_token,
                             cooldown_seconds=cooldown_seconds,
                             code_rate_limited=code_rate_limited)

    # POST - verify the code
    code = request.form.get('code', '').strip()

    if not code or len(code) != 6:
        return render_template('verify.html',
                             email=email,
                             purpose=purpose,
                             csrf_token=csrf_token,
                             cooldown_seconds=cooldown_seconds,
                             code_rate_limited=code_rate_limited,
                             error='Please enter a valid 6-digit code')

    # Verify the code
    success, error_msg, code_rate_limited = verify_code(email, code, purpose)

    if not success:
        return render_template('verify.html',
                             email=email,
                             purpose=purpose,
                             csrf_token=csrf_token,
                             cooldown_seconds=cooldown_seconds,
                             code_rate_limited=code_rate_limited,
                             error=error_msg)

    # Clear rate limits on successful verification
    clear_rate_limit(email, purpose)

    # Clear pending email from session
    session.pop('pending_signup_email', None)
    session.pop('pending_login_email', None)

    # Handle based on purpose
    if purpose == 'signup':
        # Create the user account
        client_ip = security_get_client_ip()
        user_id = create_user_with_email(email, client_ip)

        if not user_id:
            return render_template('verify.html',
                                 email=email,
                                 purpose=purpose,
                                 csrf_token=csrf_token,
                                 cooldown_seconds=0,
                                 code_rate_limited=False,
                                 error='Failed to create account. Email may already be registered.')

        # Get the user
        user = get_user_by_email(email)
    else:
        # Login - get existing user
        user = get_user_by_email(email)
        if not user:
            return render_template('verify.html',
                                 email=email,
                                 purpose=purpose,
                                 csrf_token=csrf_token,
                                 cooldown_seconds=0,
                                 code_rate_limited=False,
                                 error='Account not found')

    # Banned users can still log in - they just can't access panels (handled in dashboard)

    # Create session
    session_id = str(uuid.uuid4())
    update_user_session(user['discord_id'], session_id)

    session['user'] = {
        'id': user['discord_id'],
        'username': user['username'],
        'avatar': user.get('avatar'),
        'email': user.get('email')
    }
    session['user_id'] = user['id']  # Database user ID for OAuth endpoints
    session['authenticated'] = True
    session['user_session_id'] = session_id
    session.permanent = True

    # Redirect - signup goes to purchase, login goes to settings
    if purpose == 'signup':
        return redirect(url_for('purchase'))
    return redirect(url_for('settings'))

@app.route('/discover')
def discover():
    user = None
    user_data = None
    if 'user' in session:
        user = session.get('user')
        user_data = get_user_data(session.get('user_id'))

    return render_template('discover.html',
                         user=user,
                         user_data=user_data)

@app.route('/support')
def support():
    user = None
    user_data = None
    if 'user' in session:
        user = session.get('user')
        user_data = get_user_data(session.get('user_id'))

    return render_template('support.html',
                         user=user,
                         user_data=user_data,
                         support_hero_title=SUPPORT_HERO_TITLE,
                         support_faq_title=SUPPORT_FAQ_TITLE,
                         support_contact_text=SUPPORT_CONTACT_TEXT,
                         faq_items=FAQ_ITEMS,
                         discord_server_url=HOMEPAGE['hero']['discord_server_url'])

@app.route('/purchase')
def purchase():
    from config import SUBSCRIPTION_PLANS, BUSINESS_PLANS

    # Get plan status if user is logged in
    plan_status = None
    has_business = False
    is_admin_user = False
    is_owner = False
    user_data = None
    if 'user' in session:
        user = get_user_by_id(session.get('user_id'))
        if user:
            plan_status = get_plan_status(user['id'])
            has_business = has_business_access(user['id'], session['user']['id'])
            is_owner = is_business_owner(user['id'])
            is_admin_user = is_admin(user.get('email'))
            user_data = get_user_data(user['id'])

    return render_template('purchase.html',
                         subscription_plans=SUBSCRIPTION_PLANS,
                         business_plans=BUSINESS_PLANS,
                         plan_status=plan_status,
                         has_business=has_business,
                         is_owner=is_owner,
                         is_admin_user=is_admin_user,
                         user=session.get('user'),
                         user_data=user_data)

@app.route('/api/resend-code', methods=['POST'])
@rate_limit('api')
def resend_code_api():
    """API endpoint to resend verification code."""
    from flask import jsonify

    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return jsonify({'success': False, 'error': 'CSRF token invalid'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    purpose = data.get('purpose', 'login')

    if purpose not in ['login', 'signup', 'email_change']:
        return jsonify({'success': False, 'error': 'Invalid purpose'}), 400

    # SECURITY: Get email from session only - never from client input
    if purpose == 'signup':
        email = session.get('pending_signup_email')
    elif purpose == 'login':
        email = session.get('pending_login_email')
    elif purpose == 'email_change':
        email = session.get('pending_email_change')
    else:
        email = None

    if not email:
        return jsonify({'success': False, 'error': 'No pending verification. Please start over.'}), 400

    # Check if code verification is rate limited (3+ wrong attempts)
    if is_code_rate_limited(email, purpose):
        return jsonify({
            'success': False,
            'error': 'Too many incorrect attempts. Please wait before trying again.',
            'rate_limited': True
        }), 429

    # Check resend status
    can_resend, cooldown_seconds, attempts_remaining = get_resend_status(email, purpose)

    if not can_resend:
        # Check if rate limited (no attempts remaining)
        if attempts_remaining <= 0:
            return jsonify({
                'success': False,
                'error': 'Rate limit reached',
                'rate_limited': True
            }), 429
        return jsonify({
            'success': False,
            'error': f'Please wait {cooldown_seconds} seconds before resending',
            'blocked_seconds': cooldown_seconds
        }), 429

    # Resend the code
    success, code_or_error, blocked_seconds = resend_verification_code(email, purpose)

    if not success:
        # Check if it's a rate limit error
        if 'limit' in code_or_error.lower() or attempts_remaining <= 0:
            return jsonify({
                'success': False,
                'error': 'Rate limit reached',
                'rate_limited': True
            }), 429
        return jsonify({
            'success': False,
            'error': code_or_error,
            'blocked_seconds': blocked_seconds
        }), 429

    # TODO: Send email via Resend API

    return jsonify({'success': True, 'message': 'Verification code sent'})

@app.route('/api/verify-code', methods=['POST'])
@rate_limit('api')
def verify_code_api():
    """API endpoint to verify code without page refresh."""
    from flask import jsonify

    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return jsonify({'success': False, 'error': 'CSRF token invalid'}), 403

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request'}), 400

    code = data.get('code', '').strip()
    purpose = data.get('purpose', 'login')

    if purpose not in ['login', 'signup', 'email_change']:
        return jsonify({'success': False, 'error': 'Invalid purpose'}), 400

    # SECURITY: Get email from session only - never from client input
    # This prevents attackers from verifying arbitrary emails via inspect element
    if purpose == 'signup':
        email = session.get('pending_signup_email')
    elif purpose == 'login':
        email = session.get('pending_login_email')
    elif purpose == 'email_change':
        email = session.get('pending_email_change')
    else:
        email = None

    if not email:
        return jsonify({'success': False, 'error': 'No pending verification. Please start over.'}), 400

    if not code:
        return jsonify({'success': False, 'error': 'Code is required'}), 400

    if len(code) != 6:
        return jsonify({'success': False, 'error': 'Please enter a valid 6-digit code'}), 400

    # Verify the code
    success, error_msg, code_rate_limited = verify_code(email, code, purpose)

    if not success:
        return jsonify({
            'success': False,
            'error': error_msg,
            'code_rate_limited': code_rate_limited
        }), 429 if code_rate_limited else 400

    # Clear rate limits on successful verification
    clear_rate_limit(email, purpose)

    # Clear pending email from session
    session.pop('pending_signup_email', None)
    session.pop('pending_login_email', None)

    # Handle email change purpose
    if purpose == 'email_change':
        from database import update_user_email

        # Get user
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Update the email
        update_user_email(user['id'], email)

        # Update session
        session['user']['email'] = email

        # Clear pending email change
        session.pop('pending_email_change', None)
        session.pop('email_change_user_id', None)

        print(f"[EMAIL CHANGE] Email changed for user {user['id']} to {email}")

        return jsonify({'success': True, 'redirect': url_for('settings')})

    # Handle based on purpose
    if purpose == 'signup':
        # Create the user account
        client_ip = security_get_client_ip()
        user_id = create_user_with_email(email, client_ip)

        if not user_id:
            return jsonify({'success': False, 'error': 'Failed to create account. Email may already be registered.'}), 400

        # Get the user
        user = get_user_by_email(email)
    else:
        # Login - get existing user
        user = get_user_by_email(email)
        if not user:
            return jsonify({'success': False, 'error': 'Account not found'}), 400

    # Banned users can still log in - they just can't access panels (handled in dashboard)

    # Create session
    session_id = str(uuid.uuid4())
    update_user_session(user['discord_id'], session_id)

    session['user'] = {
        'id': user['discord_id'],
        'username': user['username'],
        'avatar': user.get('avatar'),
        'email': user.get('email')
    }
    session['user_id'] = user['id']  # Database user ID for OAuth endpoints
    session['authenticated'] = True
    session['user_session_id'] = session_id
    session.permanent = True

    # Return success with redirect URL
    # Signup goes to purchase page, login redirects back to the referring page
    if purpose == 'signup':
        redirect_url = url_for('purchase')
        return jsonify({'success': True, 'redirect': redirect_url})
    else:
        # Login - get the page they were on before login (stored in session)
        redirect_url = session.pop('login_referrer', None)
        print(f"[LOGIN SUCCESS] Retrieved referrer from session: {redirect_url}")
        if not redirect_url:
            redirect_url = url_for('dashboard')
            print(f"[LOGIN SUCCESS] No referrer, defaulting to dashboard")
        else:
            print(f"[LOGIN SUCCESS] Redirecting to: {redirect_url}")
        return jsonify({'success': True, 'redirect': redirect_url})

@app.route('/api/set-plan', methods=['POST'])
@rate_limit('api')
def set_plan():
    """API endpoint to activate a plan for a user."""
    from config import SUBSCRIPTION_PLANS, BUSINESS_PLANS
    from flask import jsonify

    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Invalid request data'}), 400

    plan_type = data.get('plan_type')  # 'subscription' or 'business'
    plan_id = data.get('plan_id')
    billing_period = data.get('billing_period')  # 'monthly' or 'yearly'

    # Validate plan data
    is_valid, error_msg = validate_plan_data(plan_type, plan_id, billing_period)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400

    # Get plan configuration
    if plan_type == 'subscription':
        if plan_id not in SUBSCRIPTION_PLANS:
            return jsonify({'success': False, 'error': 'Invalid subscription plan'}), 400
        if billing_period not in ['monthly', 'yearly']:
            return jsonify({'success': False, 'error': 'Invalid billing period'}), 400
        plan_config = SUBSCRIPTION_PLANS[plan_id]
    elif plan_type == 'business':
        if plan_id not in BUSINESS_PLANS:
            return jsonify({'success': False, 'error': 'Invalid business plan'}), 400
        if billing_period not in ['monthly', 'yearly']:
            return jsonify({'success': False, 'error': 'Invalid billing period'}), 400
        plan_config = BUSINESS_PLANS[plan_id]
    else:
        return jsonify({'success': False, 'error': 'Invalid plan type'}), 400

    # Get user from database
    user = get_user_by_id(session.get('user_id'))
    if not user:
        return jsonify({'success': False, 'error': 'User not found in database'}), 404

    try:
        # Activate the plan
        set_subscription(user['id'], plan_type, plan_id, plan_config, billing_period)
        print(f"[PLAN] Plan activated for {session['user']['username']}: {plan_config['name']} ({plan_type})")

        # If it's a business plan, create a business team
        redirect_url = '/dashboard'
        if plan_type == 'business':
            from database import create_business_team, get_active_subscription, auto_deny_pending_invitations
            subscription = get_active_subscription(user['id'])
            print(f"[PLAN] Business plan - subscription lookup for user {user['id']}: {subscription}")
            if subscription:
                max_members = plan_config.get('max_members', 3)
                team_id = create_business_team(user['id'], subscription['id'], max_members)
                print(f"[PLAN] Business team created: team_id={team_id}, max_members={max_members}")
                redirect_url = '/team-management'

                # Auto-deny any pending team invitations since user is now a business owner
                auto_deny_pending_invitations(session['user']['id'])
            else:
                print(f"[ERROR] No subscription found after activation for user {user['id']}")

        return jsonify({
            'success': True,
            'message': f"{plan_config['name']} plan activated!",
            'redirect_url': redirect_url
        }), 200
    except Exception as e:
        print(f"[ERROR] Plan activation error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to activate plan'}), 500

@app.route('/api/update-token', methods=['POST'])
@rate_limit('token_update')
def update_token():
    """Update user's Discord token securely."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'authenticated' not in session:
        return {'error': 'Unauthorized'}, 401

    user = get_user_by_id(session.get('user_id'))
    if not user:
        return {'error': 'User not found'}, 404

    data = request.json
    if not data:
        return {'error': 'Invalid request data'}, 400

    new_token = data.get('token', '').strip()

    # Validate token format
    if not new_token:
        return {'error': 'Token is required'}, 400

    if not validate_discord_token(new_token):
        return {'error': 'Invalid token format'}, 400

    # Verify the token by making an API call to Discord
    test_headers = {'Authorization': new_token}
    try:
        test_response = requests.get(f'{DISCORD_API_BASE}/users/@me', headers=test_headers, timeout=10)

        if test_response.status_code != 200:
            return {'error': 'Invalid Discord token. Please check your token and try again.'}, 400

        test_user_data = test_response.json()
        test_discord_id = test_user_data.get('id')

        # Verify the token belongs to the same user
        if test_discord_id != session['user']['id']:
            return {'error': 'Token does not match your Discord account. Please use your own token.'}, 400

        # Update the token in database (encrypted)
        update_user_token(session['user']['id'], new_token)

        # Update session with any new user info
        session['user']['username'] = test_user_data.get('username')
        session['user']['avatar'] = test_user_data.get('avatar')
        session.modified = True

        print(f"[TOKEN UPDATE] User {session['user']['id']} updated their token | IP: {get_client_ip()}")

        return {'success': True, 'message': 'Token updated successfully'}, 200

    except requests.exceptions.Timeout:
        return {'error': 'Discord API timeout. Please try again.'}, 500
    except Exception as e:
        print(f"[ERROR] Token update error: {str(e)}")
        return {'error': 'Failed to verify token'}, 500

@app.route('/old_personal_panel')
def old_personal_panel():
    # Old personal panel - kept for backwards compatibility
    if 'authenticated' not in session:
        return redirect(url_for('login_page'))

    # Get user info
    user = get_user_by_id(session.get('user_id'))
    if not user:
        session.clear()
        return redirect(url_for('login_page'))

    # Redirect to new dashboard
    return redirect(url_for('dashboard'))

@app.route('/debug-guilds')
def debug_guilds():
    if 'authenticated' not in session:
        return "Not logged in", 401

    user = get_user_by_id(session.get('user_id'))
    if not user:
        return "User not found", 404

    from database import get_linked_discord_accounts, get_linked_discord_account_by_id
    linked_accounts = get_linked_discord_accounts(user['id'])

    debug_info = {
        'user_id': user['id'],
        'linked_accounts_count': len(linked_accounts),
        'accounts': []
    }

    for acc in linked_accounts:
        account_details = get_linked_discord_account_by_id(acc['id'])
        acc_info = {
            'id': acc['id'],
            'username': acc['username'],
            'discord_id': acc['discord_id'],
            'has_discord_token': account_details.get('discord_token') is not None if account_details else False
        }

        if account_details and account_details.get('discord_token'):
            from database.models import decrypt_token
            try:
                decrypted_token = decrypt_token(account_details['discord_token'])
                acc_info['token_decrypted'] = decrypted_token is not None

                if decrypted_token:
                    headers = {'Authorization': decrypted_token}
                    guilds_resp = requests.get('https://discord.com/api/v10/users/@me/guilds', headers=headers, timeout=5)
                    acc_info['api_status'] = guilds_resp.status_code

                    if guilds_resp.status_code == 200:
                        guilds = guilds_resp.json()
                        acc_info['guilds_count'] = len(guilds)
                        acc_info['guilds'] = [{'name': g['name'], 'id': g['id']} for g in guilds[:5]]
                    else:
                        acc_info['api_error'] = guilds_resp.text[:200]
            except Exception as e:
                acc_info['error'] = str(e)

        debug_info['accounts'].append(acc_info)

    import json
    return f"<pre>{json.dumps(debug_info, indent=2)}</pre>"

@app.route('/dashboard')
def dashboard():
    if 'authenticated' not in session:
        return redirect(url_for('login_page'))

    # Get user info
    user = get_user_by_id(session.get('user_id'))
    if not user:
        session.clear()
        return redirect(url_for('login_page'))

    # Get linked Discord accounts using new system
    from database import get_linked_discord_accounts, get_linked_discord_account_by_id
    linked_accounts = get_linked_discord_accounts(user['id'])

    # Check if any Discord account is linked
    discord_linked = len(linked_accounts) > 0
    discord_info = None
    guilds = []
    primary_account = None

    print(f"[DASHBOARD] User {user['id']} - Linked accounts: {len(linked_accounts)}")

    # Fetch guilds from ALL linked accounts and merge them
    all_guilds = []
    guild_to_account = {}  # Map guild_id -> account_id for token lookup
    suspended_accounts = []  # Track suspended/deleted accounts for popup

    if discord_linked:
        # Use the first account as primary for discord_info (don't filter by is_valid)
        primary_account = linked_accounts[0] if linked_accounts else None

        print(f"[DASHBOARD] Primary account: {primary_account['id'] if primary_account else None}")

        if primary_account:
            # Get full account details with token for discord_info
            account_details = get_linked_discord_account_by_id(primary_account['id'])
            print(f"[DASHBOARD] Account details retrieved: {account_details is not None}")
            if account_details:
                # Create discord_info from primary account
                discord_info = {
                    'id': account_details['discord_id'],
                    'username': account_details['username'],
                    'avatar': account_details['avatar'],
                    'avatar_decoration_data': {
                        'asset': account_details['avatar_decoration']
                    } if account_details.get('avatar_decoration') else None
                }

        # Fetch guilds from ALL linked accounts
        for acc in linked_accounts:
            print(f"[DASHBOARD] Checking account {acc['id']}, is_valid: {acc.get('is_valid')}")

            # Don't skip based on is_valid - try all accounts
            # The is_valid field might be NULL/None for newly linked accounts
            # if not acc.get('is_valid', True):
            #     print(f"[DASHBOARD] Skipping invalid account {acc['id']}")
            #     continue

            account_details = get_linked_discord_account_by_id(acc['id'])
            if not account_details:
                print(f"[DASHBOARD] No details found for account {acc['id']}")
                continue

            if not account_details.get('discord_token'):
                print(f"[DASHBOARD] No token found for account {acc['id']}")
                continue

            print(f"[DASHBOARD] Account {acc['id']} has valid token, fetching guilds...")

            try:
                token = account_details['discord_token']
                headers = {'Authorization': token}
                guilds_resp = requests.get('https://discord.com/api/v10/users/@me/guilds', headers=headers, timeout=5)
                print(f"[DASHBOARD] Account {acc['id']} guilds API response: {guilds_resp.status_code}")

                if guilds_resp.status_code == 200:
                    account_guilds = guilds_resp.json()
                    print(f"[DASHBOARD] Account {acc['id']} guilds fetched: {len(account_guilds)} servers")

                    # Add account_id to each guild and track mapping
                    for guild in account_guilds:
                        guild['_account_id'] = acc['id']  # Store which account this guild belongs to
                        guild_to_account[guild['id']] = acc['id']
                        all_guilds.append(guild)
                elif guilds_resp.status_code == 401:
                    # Token is invalid - mark account as needing token update
                    print(f"[DASHBOARD] Account {acc['id']} has invalid token (401)")
                    # Set is_valid to 0 so frontend shows update popup
                    from database import get_db
                    conn = get_db()
                    cursor = conn.cursor()
                    cursor.execute('UPDATE linked_discord_accounts SET is_valid = 0 WHERE id = ?', (acc['id'],))
                    conn.commit()
                    conn.close()
                elif guilds_resp.status_code == 403:
                    # Check if account is suspended/deleted
                    try:
                        error_data = guilds_resp.json()
                        error_code = error_data.get('code', 0)
                        if error_code in [40001, 40002]:
                            print(f"[DASHBOARD] Account {acc['id']} is suspended/disabled (code {error_code})")
                            # Unlink the account and store info for popup
                            from database.models import unlink_discord_account
                            suspended_accounts.append({
                                'username': acc.get('username', 'Unknown'),
                                'discord_id': acc.get('discord_id', 'Unknown')
                            })
                            unlink_discord_account(user['id'], acc['id'])
                    except Exception as e:
                        print(f"[DASHBOARD] Error parsing 403 response: {e}")
                else:
                    print(f"[DASHBOARD] Account {acc['id']} failed to fetch guilds: {guilds_resp.status_code}")
            except Exception as e:
                print(f"[DASHBOARD] Error fetching guilds for account {acc['id']}: {e}")

    guilds = all_guilds
    print(f"[DASHBOARD] Final guilds count from all accounts: {len(guilds)}")

    # Fallback to old single-account system if new system found nothing
    if len(guilds) == 0 and user.get('discord_token'):
        print(f"[DASHBOARD] No guilds from new system, trying legacy token")
        try:
            legacy_token = get_decrypted_token(user['discord_id'])
            if legacy_token:
                headers = {'Authorization': legacy_token}
                guilds_resp = requests.get('https://discord.com/api/v10/users/@me/guilds', headers=headers, timeout=5)
                print(f"[DASHBOARD] Legacy token guilds API response: {guilds_resp.status_code}")
                if guilds_resp.status_code == 200:
                    guilds = guilds_resp.json()
                    print(f"[DASHBOARD] Legacy token guilds fetched: {len(guilds)} servers")
        except Exception as e:
            print(f"[DASHBOARD] Error with legacy token: {e}")

    # Get plan status and user data
    plan_status = get_plan_status(user['id'])
    user_data = get_user_data(user['id'])

    # Check if user has team access (owner or member)
    from database import get_business_team_by_owner, get_business_team_by_member, get_discord_oauth_info, get_active_subscription, create_business_team
    from config import BUSINESS_PLANS
    team = get_business_team_by_owner(user['id'])

    if not team:
        # Check if user has an active business subscription but no team
        subscription = get_active_subscription(user['id'])
        if subscription and subscription.get('plan_id', '').startswith('team_plan_'):
            plan_config = BUSINESS_PLANS.get(subscription['plan_id'], {})
            max_members = plan_config.get('max_members', 3)
            team_id = create_business_team(user['id'], subscription['id'], max_members)
            team = get_business_team_by_owner(user['id'])

    if not team:
        # Check by main discord_id
        team = get_business_team_by_member(user['discord_id'])

    if not team:
        # Also check by OAuth-linked Discord ID
        oauth_info = get_discord_oauth_info(user['id'])
        if oauth_info and oauth_info.get('oauth_discord_id'):
            team = get_business_team_by_member(oauth_info['oauth_discord_id'])

    has_team = team is not None
    is_owner = is_business_owner(user['id']) if has_team else False

    # Get business plan status for usage tracking
    business_plan_status = None
    if has_team:
        from database import get_business_plan_status
        if is_owner:
            business_plan_status = get_business_plan_status(team['id'], user['id'])
        else:
            business_plan_status = get_business_plan_status(team['id'], team['owner_user_id'])

    # Get team management data if user is team owner
    members = []
    member_stats = []
    active_member_count = 0
    if is_owner and team:
        from database import get_team_members, get_team_member_stats, get_team_member_count
        members = get_team_members(team['id'], include_all=True)
        member_stats = get_team_member_stats(team['id'])
        active_member_count = get_team_member_count(team['id'])

    # Get purchase history for billing invoices
    from database import get_purchase_history
    purchase_history = get_purchase_history(user['id'])

    csrf_token = generate_csrf_token()
    response = app.make_response(render_template('dashboard.html',
        discord_info=discord_info,
        discord_linked=discord_linked,
        linked_accounts=linked_accounts,
        primary_account=primary_account,
        guilds=guilds,
        plan_status=plan_status,
        business_plan_status=business_plan_status,
        user_data=user_data,
        user=user,
        team=team,
        has_team=has_team,
        is_team_owner=is_owner,
        members=members,
        member_stats=member_stats,
        active_member_count=active_member_count,
        purchase_history=purchase_history,
        BLACKLISTED_WORDS=BLACKLISTED_WORDS,
        PHRASE_EXCEPTIONS=PHRASE_EXCEPTIONS,
        csrf_token=csrf_token,
        suspended_accounts=suspended_accounts
    ))
    # Prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/bridge')
def bridge():
    if 'authenticated' not in session:
        return redirect(url_for('login_page'))

    user = get_user_by_id(session.get('user_id'))
    if not user:
        session.clear()
        return redirect(url_for('login_page'))

    # Get user data
    user_data = get_user_data(user['id'])

    csrf_token = generate_csrf_token()
    response = app.make_response(render_template('bridge.html',
        user=session.get('user'),
        user_data=user_data,
        csrf_token=csrf_token
    ))
    # Prevent caching
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/guild/<guild_id>/channels')
@rate_limit('api')
def get_guild_channels(guild_id):
    if 'authenticated' not in session:
        return {'error': 'Unauthorized'}, 401

    user = get_user_by_id(session.get('user_id'))
    if not user:
        return {'error': 'User not found'}, 404

    # Validate guild ID
    if not validate_discord_id(guild_id):
        return {'error': 'Invalid guild ID'}, 400

    # Get token from linked Discord accounts (new system)
    from database import get_linked_discord_accounts, get_linked_discord_account_by_id
    linked_accounts = get_linked_discord_accounts(user['id'])

    user_token = None
    if linked_accounts:
        primary_account = linked_accounts[0]
        account_details = get_linked_discord_account_by_id(primary_account['id'])
        if account_details:
            user_token = account_details.get('discord_token')

    if not user_token:
        return {'error': 'No linked Discord account'}, 401
    headers = {'Authorization': user_token}

    try:
        # Fetch channels for this guild
        resp = requests.get(
            f'https://discord.com/api/v10/guilds/{guild_id}/channels',
            headers=headers,
            timeout=10
        )

        if resp.status_code == 200:
            channels = resp.json()
            # Filter and return only text channels
            text_channels = [ch for ch in channels if ch.get('type') == 0]
            return {'channels': text_channels}, 200
        elif resp.status_code == 401:
            # Token is invalid/expired - return account info for token update popup
            # Don't unlink immediately, let user update the token
            return {
                'error': 'Token invalid',
                'token_invalid': True,
                'account_info': {
                    'account_id': primary_account['id'],
                    'username': primary_account.get('username', 'Unknown'),
                    'discord_id': primary_account.get('discord_id', 'Unknown')
                }
            }, 401
        else:
            return {'error': 'Failed to fetch channels'}, resp.status_code
    except requests.exceptions.Timeout:
        return {'error': 'Request timeout'}, 500
    except Exception as e:
        return {'error': str(e)}, 500

@app.route('/api/send-message-single', methods=['POST'])
@rate_limit('send_message')
def send_message_single():
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'authenticated' not in session:
        return {'error': 'Unauthorized'}, 401

    # Get user
    user = get_user_by_id(session.get('user_id'))
    if not user:
        return {'error': 'User not found'}, 404

    data = request.json
    if not data:
        return {'error': 'Invalid request data'}, 400

    is_business = data.get('is_business', False)
    owner_user_id = None  # Will be set if business send

    if is_business:
        # For business sends, check owner's usage limits
        from database import get_business_team_by_owner, get_business_team_by_member
        team = get_business_team_by_owner(user['id'])
        if team:
            # User is owner
            owner_user_id = user['id']
        else:
            # User is member - get owner (use discord_id from user object)
            team = get_business_team_by_member(user['discord_id'])
            if team:
                owner_user_id = team['owner_user_id']

        if not owner_user_id:
            return {'error': 'No business team found'}, 404

        # Check owner's usage limits for business sends
        can_send, reason, remaining = can_send_message(owner_user_id)
    else:
        # For personal sends, check user's own limits
        can_send, reason, remaining = can_send_message(user['id'])

    if not can_send:
        return {'error': f'Cannot send message: {reason}', 'limit_reached': True}, 403

    channel = data.get('channel', {})
    guild_id = channel.get('guildId')

    print(f"[SEND] Attempting to send to guild {guild_id}, channel {channel.get('id')}, channel name: {channel.get('name')}")

    # Get token from linked Discord accounts based on which account has this guild
    from database import get_linked_discord_accounts, get_linked_discord_account_by_id
    linked_accounts = get_linked_discord_accounts(user['id'])

    print(f"[SEND] Found {len(linked_accounts)} linked accounts")

    if not linked_accounts:
        return {'error': 'No Discord account linked'}, 401

    # Find which account has access to this guild
    user_token = None
    account_used = None

    for acc in linked_accounts:
        print(f"[SEND] Checking account {acc['id']}, is_valid: {acc.get('is_valid')}")

        # Don't skip based on is_valid - try all accounts
        # if not acc.get('is_valid', True):
        #     print(f"[SEND] Skipping invalid account {acc['id']}")
        #     continue

        account_details = get_linked_discord_account_by_id(acc['id'])
        if not account_details or not account_details.get('discord_token'):
            print(f"[SEND] Account {acc['id']} has no token")
            continue

        print(f"[SEND] Account {acc['id']} has token, checking guilds...")

        # Fetch guilds for this account to check if it has the target guild
        try:
            token = account_details['discord_token']
            headers_check = {'Authorization': token}
            guilds_resp = requests.get('https://discord.com/api/v10/users/@me/guilds', headers=headers_check, timeout=5)

            if guilds_resp.status_code == 200:
                account_guilds = guilds_resp.json()
                guild_ids = [g['id'] for g in account_guilds]

                print(f"[SEND] Account {acc['id']} has {len(account_guilds)} guilds")
                print(f"[SEND] Looking for guild {guild_id} in account {acc['id']}")

                if guild_id in guild_ids:
                    user_token = token
                    account_used = acc
                    print(f"[SEND] ✓ MATCH! Using account {acc['id']} for guild {guild_id}")
                    break
                else:
                    print(f"[SEND] Guild {guild_id} NOT found in account {acc['id']}")
            else:
                print(f"[SEND] Failed to fetch guilds for account {acc['id']}: HTTP {guilds_resp.status_code}")
        except Exception as e:
            print(f"[SEND] Error checking account {acc['id']}: {e}")
            continue

    if not user_token:
        # Fallback to first account if guild not found
        print(f"[SEND] Guild {guild_id} not found in any account, using first account")
        primary_account = linked_accounts[0] if linked_accounts else None
        if primary_account:
            account_details = get_linked_discord_account_by_id(primary_account['id'])
            if account_details and account_details.get('discord_token'):
                user_token = account_details['discord_token']

    if not user_token:
        return {'error': 'Discord account token not found'}, 401

    headers = {'Authorization': user_token, 'Content-Type': 'application/json'}
    message_content = data.get('message', '').strip()

    # Validate channel ID
    if channel and not validate_channel_id(channel.get('id', '')):
        return {'error': 'Invalid channel ID'}, 400

    # Validate message content
    is_valid, error_msg = validate_message_content(message_content)
    if not is_valid:
        return {'error': error_msg}, 400

    # Check content filter and flag user if needed
    is_valid, filter_reason = check_message_content(message_content, user['id'])
    if not is_valid:
        # Get updated user status after flagging to check if they were auto-banned
        user = get_user_by_id(user['id'])
        user_banned = user.get('banned', 0) == 1
        # Return error with flags to trigger UI update
        return {'error': filter_reason, 'user_flagged': True, 'user_banned': user_banned}, 400

    if not channel:
        return {'error': 'No channel provided'}, 400

    channel_id = channel.get('id')
    channel_name = channel.get('name')

    try:
        resp = requests.post(
            f'https://discord.com/api/v10/channels/{channel_id}/messages',
            headers=headers,
            json={'content': message_content},
            timeout=10
        )

        if resp.status_code == 200 or resp.status_code == 201:
            try:
                if is_business and owner_user_id:
                    # For business sends: update owner's and member's business stats
                    from database import increment_business_usage
                    team_id = team['id'] if team else None
                    increment_business_usage(owner_user_id, team_id)  # Owner's business usage
                    if user['id'] != owner_user_id:  # Only increment member if not owner
                        increment_business_usage(user['id'], team_id)  # Member's business stats
                else:
                    # For personal sends: update user's own usage
                    record_successful_send(user['id'])
                # Also update session for backward compatibility
                if 'sent_count' not in session:
                    session['sent_count'] = 0
                session['sent_count'] += 1
                session.modified = True
            except Exception as db_error:
                print(f"[ERROR] Database error after successful send: {str(db_error)}")
                import traceback
                traceback.print_exc()
                # Message was sent successfully, return success anyway
            return {'success': True, 'channel': channel_name}, 200
        elif resp.status_code == 401:
            # Token is invalid/expired - mark account as needing token update
            account_info = None
            if account_used:
                from database import get_db
                conn = get_db()
                cursor = conn.cursor()
                cursor.execute('UPDATE linked_discord_accounts SET is_valid = 0 WHERE id = ?', (account_used['id'],))
                conn.commit()
                conn.close()
                account_info = {
                    'account_id': account_used['id'],
                    'username': account_used.get('username', 'Unknown'),
                    'discord_id': account_used.get('discord_id', 'Unknown')
                }
            return {'success': False, 'error': 'Token invalid', 'token_invalid': True, 'account_info': account_info}, 401
        elif resp.status_code == 403:
            # Check if account is suspended/deleted/disabled
            try:
                error_data = resp.json()
                error_code = error_data.get('code', 0)
                # Discord error codes for account issues:
                # 40001 = Unauthorized (account disabled)
                # 40002 = You need to verify your account
                # 40007 = User is banned from this guild
                # 50001 = Missing Access
                if error_code in [40001, 40002] and account_used:
                    # Account is suspended/disabled - unlink it
                    from database.models import unlink_discord_account
                    unlink_discord_account(user['id'], account_used['id'])
                    return {
                        'success': False,
                        'error': 'Account unavailable',
                        'account_suspended': True,
                        'account_info': {
                            'account_id': account_used['id'],
                            'username': account_used.get('username', 'Unknown'),
                            'discord_id': account_used.get('discord_id', 'Unknown')
                        }
                    }, 403
            except:
                pass
            return {'success': False, 'error': 'Access denied'}, 403
        elif resp.status_code == 429:
            # Extract retry_after from Discord's response
            try:
                rate_limit_data = resp.json()
                retry_after = rate_limit_data.get('retry_after', 1.0)  # Discord returns seconds as float
                # Convert to milliseconds for JavaScript
                retry_after_ms = int(retry_after * 1000)
            except:
                retry_after_ms = 1000  # Default to 1 second
            return {'success': False, 'error': 'Rate limited', 'retry_after': retry_after_ms}, 429
        else:
            try:
                error_msg = resp.json().get('message', 'Unknown error')
            except:
                error_msg = f'HTTP {resp.status_code}'
            return {'success': False, 'error': error_msg}, resp.status_code
    except requests.exceptions.Timeout:
        return {'success': False, 'error': 'Request timeout'}, 500
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/send-message', methods=['POST'])
@rate_limit('send_message')
def send_message():
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'authenticated' not in session:
        return {'error': 'Unauthorized'}, 401

    user = get_user_by_id(session.get('user_id'))
    if not user:
        return {'error': 'User not found'}, 404

    # Get token from linked Discord accounts (new multi-account system)
    from database import get_linked_discord_accounts, get_linked_discord_account_by_id
    linked_accounts = get_linked_discord_accounts(user['id'])
    if not linked_accounts:
        return {'error': 'No Discord account linked'}, 401

    # Use the first valid account as primary
    primary_account = next((acc for acc in linked_accounts if acc.get('is_valid', True)), linked_accounts[0])
    account_details = get_linked_discord_account_by_id(primary_account['id'])

    if not account_details or not account_details.get('discord_token'):
        return {'error': 'Discord account token not found'}, 401

    user_token = account_details['discord_token']
    headers = {'Authorization': user_token, 'Content-Type': 'application/json'}

    data = request.json
    if not data:
        return {'error': 'Invalid request data'}, 400

    is_business = data.get('is_business', False)
    owner_user_id = None  # Will be set if business send
    team = None  # Will store team info if business send

    if is_business:
        # For business sends, check owner's usage limits
        from database import get_business_team_by_owner, get_business_team_by_member
        team = get_business_team_by_owner(user['id'])
        if team:
            # User is owner
            owner_user_id = user['id']
        else:
            # User is member - get owner (use discord_id from user object)
            team = get_business_team_by_member(user['discord_id'])
            if team:
                owner_user_id = team['owner_user_id']

        if not owner_user_id:
            return {'error': 'No business team found'}, 404

    channels = data.get('channels', [])
    message_content = data.get('message', '').strip()

    # Validate message content
    is_valid_msg, error_msg = validate_message_content(message_content)
    if not is_valid_msg:
        return {'error': error_msg}, 400

    # Validate all channel IDs
    for ch in channels:
        if not validate_channel_id(ch.get('id', '')):
            return {'error': f"Invalid channel ID: {ch.get('name', 'unknown')}"}, 400

    # Get user for limit checking and flagging
    user = get_user_by_id(session.get('user_id'))
    if not user:
        return {'error': 'User not found'}, 404

    # Check content filter and flag user if needed
    is_valid, filter_reason = check_message_content(message_content, user['id'])
    if not is_valid:
        # Get updated user status after flagging to check if they were auto-banned
        user = get_user_by_id(user['id'])
        user_banned = user.get('banned', 0) == 1
        # Return error with flags to trigger UI update
        return {'error': filter_reason, 'user_flagged': True, 'user_banned': user_banned}, 400

    if not channels:
        return {'error': 'No channels selected'}, 400

    results = {'success': [], 'failed': []}

    for channel in channels:
        # Check if user can still send before each message
        # For business sends, check owner's limits; for personal sends, check user's limits
        check_user_id = owner_user_id if is_business else user['id']
        can_send, reason, remaining = can_send_message(check_user_id)
        if not can_send:
            results['failed'].append(f'{channel.get("name")} (Limit reached: {reason})')
            continue

        channel_id = channel.get('id')
        channel_name = channel.get('name')

        try:
            resp = requests.post(
                f'https://discord.com/api/v10/channels/{channel_id}/messages',
                headers=headers,
                json={'content': message_content},
                timeout=10
            )

            print(f"[SEND] Channel: {channel_name}, Status: {resp.status_code}")
            if resp.status_code == 200 or resp.status_code == 201:
                results['success'].append(channel_name)
                # Track successful send in database
                if is_business and owner_user_id:
                    # For business sends: update owner's and member's business stats
                    from database import increment_business_usage
                    team_id = team['id'] if team else None
                    increment_business_usage(owner_user_id, team_id)  # Owner's business usage
                    if user['id'] != owner_user_id:  # Only increment member if not owner
                        increment_business_usage(user['id'], team_id)  # Member's business stats
                else:
                    # For personal sends: update user's own usage
                    record_successful_send(user['id'])
                # Also update session for backward compatibility
                if 'sent_count' not in session:
                    session['sent_count'] = 0
                session['sent_count'] += 1
                session.modified = True
            elif resp.status_code == 429:
                results['failed'].append(f'{channel_name} (Rate limited)')
            else:
                try:
                    error_data = resp.json()
                    error_msg = error_data.get('message', 'Unknown error')
                    print(f"[SEND ERROR] Channel: {channel_name}, Status: {resp.status_code}, Response: {error_data}")
                except:
                    error_msg = f'HTTP {resp.status_code}'
                    print(f"[SEND ERROR] Channel: {channel_name}, Status: {resp.status_code}, Could not parse response")
                results['failed'].append(f'{channel_name} ({error_msg})')
        except requests.exceptions.Timeout:
            results['failed'].append(f'{channel_name} (Request timeout)')
        except Exception as e:
            results['failed'].append(f'{channel_name} ({str(e)})')

    return results, 200

@app.route('/team-management')
def team_management():
    """Team plan management page for team owners - ARCHIVED, redirects to dashboard."""
    return redirect(url_for('dashboard'))

    client_ip = get_client_ip()
    if 'login_ip' in session and session['login_ip'] != client_ip:
        session.clear()
        return redirect(url_for('login_page'))

    user = get_user_by_id(session.get('user_id'))
    if not user:
        session.clear()
        return redirect(url_for('login_page'))

    # Check if user is banned - pass to template instead of redirecting
    is_banned = user.get('banned', 0) == 1

    # Check if user owns a business plan
    from database import get_business_team_by_owner, get_team_members, get_team_member_stats, update_team_member_info, get_team_member_count, get_active_subscription, create_business_team
    from config import BUSINESS_PLANS
    team = get_business_team_by_owner(user['id'])

    if not team:
        # Check if user has an active business subscription but no team (could happen if team creation failed)
        subscription = get_active_subscription(user['id'])
        if subscription and subscription.get('plan_id', '').startswith('team_plan_'):
            # Create the business team now
            plan_config = BUSINESS_PLANS.get(subscription['plan_id'], {})
            max_members = plan_config.get('max_members', 3)
            team_id = create_business_team(user['id'], subscription['id'], max_members)
            print(f"[BUSINESS] Late team creation for user {user['id']}: team_id={team_id}")
            # Refetch the team
            team = get_business_team_by_owner(user['id'])

    if not team:
        return redirect(url_for('purchase'))

    # Get team members (include all statuses for management view)
    members = get_team_members(team['id'], include_all=True)

    # Refresh Discord info for members who show as "Unknown User"
    for member in members:
        if member['member_username'] == 'Unknown User' or not member['member_username']:
            username, avatar = fetch_discord_user_info(member['member_discord_id'])
            if username:
                update_team_member_info(team['id'], member['member_discord_id'], username, avatar)
                print(f"[BUSINESS] Updated member info for {member['member_discord_id']}: {username}")

    # Get member stats including usage (refetch after potential updates)
    member_stats = get_team_member_stats(team['id'])
    plan_status = get_plan_status(user['id'])

    # Get active member count (only accepted members)
    active_member_count = get_team_member_count(team['id'])

    # User has business access (they're on this page)
    has_business = True

    # Check if user is admin (use email from database)
    is_admin_user = is_admin(user.get('email'))

    return render_template('team-management.html',
                         user=session['user'],
                         team=team,
                         members=members,
                         member_stats=member_stats,
                         plan_status=plan_status,
                         has_business=has_business,
                         is_owner=True,
                         is_admin_user=is_admin_user,
                         active_member_count=active_member_count,
                         BLACKLISTED_WORDS=BLACKLISTED_WORDS,
                         PHRASE_EXCEPTIONS=PHRASE_EXCEPTIONS,
                         is_banned=is_banned)

@app.route('/team-panel')
def team_panel():
    """Team panel for team members to send messages."""
    if 'authenticated' not in session:
        return redirect(url_for('login_page'))

    client_ip = get_client_ip()
    if 'login_ip' in session and session['login_ip'] != client_ip:
        session.clear()
        return redirect(url_for('login_page'))

    user = get_user_by_id(session.get('user_id'))
    if not user:
        session.clear()
        return redirect(url_for('login_page'))

    # Check if Discord account is linked
    discord_linked = is_discord_linked(user['id'])

    # Check if user is banned - pass to template instead of redirecting
    is_banned = user.get('banned', 0) == 1

    # Check if user is team owner or member
    from database import get_business_team_by_owner, get_business_team_by_member, get_discord_oauth_info, get_active_subscription, create_business_team
    from config import BUSINESS_PLANS
    team = get_business_team_by_owner(user['id'])

    if not team:
        # Check if user has an active business subscription but no team (could happen if team creation failed)
        subscription = get_active_subscription(user['id'])
        if subscription and subscription.get('plan_id', '').startswith('team_plan_'):
            # Create the business team now
            plan_config = BUSINESS_PLANS.get(subscription['plan_id'], {})
            max_members = plan_config.get('max_members', 3)
            team_id = create_business_team(user['id'], subscription['id'], max_members)
            print(f"[TEAM] Late team creation for user {user['id']}: team_id={team_id}")
            # Refetch the team
            team = get_business_team_by_owner(user['id'])

    if not team:
        # Check by main discord_id
        team = get_business_team_by_member(session['user']['id'])

    if not team:
        # Also check by OAuth-linked Discord ID (for email users who linked Discord)
        oauth_info = get_discord_oauth_info(user['id'])
        if oauth_info and oauth_info.get('oauth_discord_id'):
            team = get_business_team_by_member(oauth_info['oauth_discord_id'])

    if not team:
        return redirect(url_for('purchase'))

    plan_status = get_plan_status(user['id'])

    # If Discord not linked, show panel but with modal
    guilds = []
    if discord_linked:
        # Decrypt token only when needed for API call
        user_token = get_decrypted_token(user['discord_id'])
        if user_token:
            headers = {'Authorization': user_token}
            resp = requests.get('https://discord.com/api/v10/users/@me/guilds', headers=headers)

            if resp.status_code == 200:
                guilds = resp.json()

    # Get user data
    user_data = get_user_data(user['id'])

    # User has business access (they're on this page)
    has_business = True

    # Check if user is admin (use email from database)
    is_admin_user = is_admin(user.get('email'))

    response = app.make_response(render_template('team-panel.html',
                                                user=session['user'],
                                                guilds=guilds,
                                                team=team,
                                                plan_status=plan_status,
                                                user_data=user_data,
                                                has_business=has_business,
                                                is_owner=is_business_owner(user['id']),
                                                is_admin_user=is_admin_user,
                                                BLACKLISTED_WORDS=BLACKLISTED_WORDS,
                                                PHRASE_EXCEPTIONS=PHRASE_EXCEPTIONS,
                                                is_banned=is_banned,
                                                discord_linked=discord_linked))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/settings')
def settings():
    # Settings are now a popup in the panel, so redirect to panel
    return redirect(url_for('dashboard'))

@app.route('/api/change-email', methods=['POST'])
@rate_limit('api')
def api_change_email():
    """Initiate email change process - sends verification code to new email."""
    from flask import jsonify
    from database import get_user_by_email, create_verification_code

    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        data = request.get_json()
        new_email = data.get('new_email', '').strip().lower()

        if not new_email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400

        # Basic email validation
        import re
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', new_email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400

        # Check against blacklisted domains
        from config import BLACKLISTED_EMAIL_DOMAINS, ALLOWED_EMAIL_TLDS
        email_lower = new_email.lower()
        for blacklisted in BLACKLISTED_EMAIL_DOMAINS:
            if email_lower.endswith(blacklisted):
                return jsonify({'success': False, 'error': f'Email domain {blacklisted} is not allowed'}), 400

        # Check if email ends with an allowed TLD
        if ALLOWED_EMAIL_TLDS:
            is_allowed = any(email_lower.endswith(tld) for tld in ALLOWED_EMAIL_TLDS)
            if not is_allowed:
                return jsonify({'success': False, 'error': 'Email domain is not supported'}), 400

        # Check if email is already in use
        existing_user = get_user_by_email(new_email)
        if existing_user:
            return jsonify({'success': False, 'error': 'Email already in use'}), 400

        # Get current user
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Check if same as current email
        if user.get('email', '').lower() == new_email:
            return jsonify({'success': False, 'error': 'This is already your email'}), 400

        # Store the new email in session for verification
        session['pending_email_change'] = new_email
        session['email_change_user_id'] = user['id']

        # Create verification code for the new email
        code = create_verification_code(new_email, 'email_change')

        # Return redirect URL to verification page
        return jsonify({
            'success': True,
            'redirect_url': url_for('verify_email_change', email=new_email)
        }), 200

    except Exception as e:
        print(f"[ERROR] Email change error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to initiate email change'}), 500

@app.route('/verify-email-change')
def verify_email_change():
    """Verification page for email change."""
    if 'authenticated' not in session:
        return redirect(url_for('login_page'))

    email = request.args.get('email', '')
    if not email or 'pending_email_change' not in session:
        return redirect(url_for('settings'))

    # Get resend status for rate limiting display
    can_resend, cooldown_seconds, attempts_remaining = get_resend_status(email, 'email_change')
    code_rate_limited = is_code_rate_limited(email, 'email_change')

    # Get user info for dropdown menu (user is still logged in with their current email)
    user = get_user_by_id(session.get('user_id'))
    is_admin_user = is_admin(user.get('email')) if user else False
    has_business = has_business_access(user['id'], session['user']['id']) if user else False
    is_owner = is_business_owner(user['id']) if user else False
    plan_status = get_plan_status(user['id']) if user else {}

    return render_template('verify.html',
                          email=email,
                          purpose='email_change',
                          csrf_token=generate_csrf_token(),
                          cooldown_seconds=cooldown_seconds,
                          code_rate_limited=code_rate_limited,
                          is_admin_user=is_admin_user,
                          has_business=has_business,
                          is_owner=is_owner,
                          plan_status=plan_status)

@app.route('/api/verify-email-change', methods=['POST'])
@rate_limit('api')
def api_verify_email_change():
    """Verify email change code and update email."""
    from flask import jsonify
    from database import verify_code, update_user_email

    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        data = request.get_json()
        code = data.get('code', '').strip()

        if not code:
            return jsonify({'success': False, 'error': 'Code is required'}), 400

        # SECURITY: Get email from session only - never from client input
        email = session.get('pending_email_change')
        if not email:
            return jsonify({'success': False, 'error': 'No pending email change request'}), 400

        # Verify the code
        success, error_msg, code_rate_limited = verify_code(email, code, 'email_change')
        if not success:
            return jsonify({'success': False, 'error': error_msg or 'Invalid or expired code'}), 400

        # Get user
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Update the email
        update_user_email(user['id'], email)

        # Update session
        session['user']['email'] = email

        # Clear pending email change
        session.pop('pending_email_change', None)
        session.pop('email_change_user_id', None)

        print(f"[EMAIL CHANGE] Email changed for user {user['id']} to {email}")

        return jsonify({
            'success': True,
            'redirect': url_for('settings')
        }), 200

    except Exception as e:
        print(f"[ERROR] Email change verification error: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to change email'}), 500

@app.route('/api/cancel-plan', methods=['POST'])
@rate_limit('api')
def cancel_plan():
    from flask import jsonify
    from database import cancel_subscription

    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Cancel the subscription
        cancel_subscription(user['id'])
        print(f"[PLAN] Plan cancelled for {session['user']['username']}")

        return jsonify({'success': True}), 200

    except Exception as e:
        print(f"[ERROR] Cancel plan error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/cancel')
def dev_cancel_plan():
    """DEV ONLY: Quick route to reset subscription to free plan."""
    from database import cancel_subscription

    if 'user' not in session:
        return redirect(url_for('home'))

    try:
        user = get_user_by_id(session.get('user_id'))
        if user:
            cancel_subscription(user['id'])
            print(f"[DEV] Plan reset to free for {session['user']['username']}")
        return redirect(url_for('dashboard'))
    except Exception as e:
        print(f"[DEV ERROR] Cancel error: {str(e)}")
        return redirect(url_for('dashboard'))

@app.route('/api/flag-self', methods=['POST'])
@rate_limit('api')
def api_flag_self():
    """Flag the current user for using banned words."""
    from flask import jsonify

    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        data = request.get_json()
        words = data.get('words', [])

        # Flag the user with the banned words as reason
        reason = f"Used banned words: {', '.join(words)}"
        flag_user(user['id'], reason)

        return jsonify({'success': True}), 200

    except Exception as e:
        print(f"[ERROR] Flag self error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save-user-data', methods=['POST'])
@rate_limit('api')
def api_save_user_data():
    """Save user's selected channels, draft message, and/or message delay."""
    from flask import jsonify

    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        data = request.get_json()
        selected_channels = data.get('selected_channels')
        business_selected_channels = data.get('business_selected_channels')
        draft_message = data.get('draft_message')
        message_delay = data.get('message_delay')
        date_format = data.get('date_format')
        profile_photo = data.get('profile_photo')

        # Check content filter for draft message and flag user if needed
        if draft_message and draft_message.strip():
            is_valid, filter_reason = check_message_content(draft_message, user['id'])
            if not is_valid:
                return jsonify({'success': False, 'error': filter_reason}), 400

        # Save to database
        save_user_data(user['id'], selected_channels, draft_message, message_delay, date_format, profile_photo, business_selected_channels)

        return jsonify({'success': True}), 200

    except Exception as e:
        print(f"[ERROR] Save user data error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/get-user-data', methods=['GET'])
def api_get_user_data():
    """Get user's selected channels and draft message."""
    from flask import jsonify

    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404

        # Get from database
        user_data = get_user_data(user['id'])

        return jsonify({
            'success': True,
            'data': user_data
        }), 200

    except Exception as e:
        print(f"[ERROR] Get user data error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/status-check', methods=['GET'])
def status_check():
    """Real-time status check for user status changes (ban, team, etc.)."""
    from flask import jsonify

    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return jsonify({'success': False, 'redirect': '/home'}), 401

        # Check ban status
        is_banned = user.get('is_banned', False)

        # Check team membership status
        from database import get_business_team_by_member, is_business_plan_owner
        team = get_business_team_by_member(session['user']['id'])
        is_team_member = team is not None
        is_owner = is_business_plan_owner(user['id'])

        # Check if user has any active plan
        plan_status = get_plan_status(user['id'])
        has_plan = plan_status.get('has_plan', False) if plan_status else False

        return jsonify({
            'success': True,
            'is_banned': is_banned,
            'is_team_member': is_team_member,
            'is_owner': is_owner,
            'has_plan': has_plan
        }), 200

    except Exception as e:
        print(f"[ERROR] Status check error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/delete-account', methods=['POST'])
@rate_limit('api')
def delete_account():
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        user_data = session.get('user')
        user_id = session.get('user_id')
        user_email = user_data.get('email')

        # Get the actual user from database to ensure we have correct ID
        from database import delete_user, delete_user_by_email
        user = get_user_by_id(user_id)

        if user:
            # Delete user from database (this will cascade delete subscriptions and usage)
            delete_user(user['discord_id'])
            print(f"[DELETE] Account deleted: {user_data.get('username')} (ID: {user_id})")
        elif user_email:
            # Fallback: delete by email if discord_id lookup fails
            delete_user_by_email(user_email)
            print(f"[DELETE] Account deleted by email: {user_data.get('username')} ({user_email})")
        else:
            return {'success': False, 'error': 'User not found'}, 404

        # Clear session
        session.clear()

        return {'success': True}, 200

    except Exception as e:
        print(f"[ERROR] Delete account error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/team/add-member', methods=['POST'])
@rate_limit('api')
def add_team_member_api():
    """Add a member to the team by Adzsend ID."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        # Check if user owns a business team
        from database import get_business_team_by_owner, get_team_member_count, add_team_member, get_user_by_adzsend_id
        team = get_business_team_by_owner(user['id'])

        if not team:
            return {'success': False, 'error': 'No business team found'}, 404

        data = request.get_json()
        if not data:
            return {'success': False, 'error': 'Invalid request data'}, 400

        adzsend_id = data.get('adzsend_id', '').strip()

        if not adzsend_id:
            return {'success': False, 'error': 'Adzsend ID required'}, 400

        # Validate Adzsend ID format (18 digits)
        import re
        if not re.match(r'^\d{18}$', adzsend_id):
            return {'success': False, 'error': 'Invalid Adzsend ID format'}, 400

        # Look up the user by Adzsend ID - they must have an account
        member_user = get_user_by_adzsend_id(adzsend_id)
        if not member_user:
            return {'success': False, 'error': 'No account found with this Adzsend ID'}, 404

        # Get the member's discord_id (could be OAuth or email placeholder)
        member_discord_id = member_user.get('discord_id')
        if not member_discord_id:
            return {'success': False, 'error': 'User account is incomplete'}, 400

        # Check if trying to add yourself
        if member_user['id'] == user['id']:
            return {'success': False, 'error': 'Cannot add yourself as a team member'}, 400

        # Check if the user being added is banned
        if member_user.get('banned', 0) == 1:
            return {'success': False, 'error': 'This user is banned and cannot be added to teams'}, 403

        # Check if the user being added is a business plan owner themselves
        if is_business_owner(member_user['id']):
            return {'success': False, 'error': 'This user is a team plan owner and cannot be added to other teams'}, 400

        # Check if team is full
        current_count = get_team_member_count(team['id'])
        if current_count >= team['max_members']:
            return {'success': False, 'error': f"Team is full (max {team['max_members']} members)"}, 400

        # Get username and avatar from the user's account or Discord
        username = member_user.get('username') or member_user.get('email', '').split('@')[0]
        avatar = member_user.get('avatar', '')

        # If user has linked Discord OAuth, try to get their Discord info
        oauth_discord_id = member_user.get('discord_oauth_discord_id')
        if oauth_discord_id:
            discord_username, discord_avatar = fetch_discord_user_info(oauth_discord_id)
            if discord_username:
                username = discord_username
                avatar = discord_avatar or avatar

        # Add member with their info
        success = add_team_member(team['id'], member_discord_id, username, avatar)

        if success:
            return {'success': True, 'message': 'Member added successfully', 'discord_id': member_discord_id}, 200
        else:
            return {'success': False, 'error': 'Member already exists in the team'}, 400

    except Exception as e:
        print(f"[ERROR] Add member error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/team/remove-member', methods=['POST'])
@rate_limit('api')
def remove_team_member_api():
    """Remove a member from the team by Adzsend ID."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        # Check if user owns a business team
        from database import get_business_team_by_owner, remove_team_member_by_adzsend_id
        team = get_business_team_by_owner(user['id'])

        if not team:
            return {'success': False, 'error': 'No business team found'}, 404

        data = request.get_json()
        adzsend_id = data.get('adzsend_id')

        if not adzsend_id:
            return {'success': False, 'error': 'Adzsend ID required'}, 400

        remove_team_member_by_adzsend_id(team['id'], adzsend_id)
        return {'success': True, 'message': 'Member removed successfully'}, 200

    except Exception as e:
        print(f"[ERROR] Remove member error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/team/set-team-message', methods=['POST'])
def set_team_message():
    """Set the team message for team panel."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        # Check if user owns a business team
        from database import get_business_team_by_owner, update_team_message
        team = get_business_team_by_owner(user['id'])

        if not team:
            return {'success': False, 'error': 'No business team found'}, 404

        data = request.get_json()
        message = data.get('message', '')

        # Check content filter and flag user if needed (only if message is not empty)
        if message and message.strip():
            is_valid, filter_reason = check_message_content(message, user['id'])
            if not is_valid:
                return {'success': False, 'error': filter_reason}, 400

        update_team_message(team['id'], message)
        return {'success': True, 'message': 'Team message updated successfully'}, 200

    except Exception as e:
        print(f"[ERROR] Set team message error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


# Team member analytics API endpoints

@app.route('/api/team/member/<member_adzsend_id>/analytics', methods=['GET'])
@rate_limit('api')
def get_team_member_analytics(member_adzsend_id):
    """Get analytics data for a specific team member by their adzsend_id."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        # Check if user owns a business team
        from database import get_business_team_by_owner, get_member_analytics, get_user_by_adzsend_id
        team = get_business_team_by_owner(user['id'])

        if not team:
            return {'success': False, 'error': 'You must be a team owner'}, 403

        # Look up member by adzsend_id
        member = get_user_by_adzsend_id(member_adzsend_id)
        if not member:
            return {'success': False, 'error': 'Member not found'}, 404

        analytics = get_member_analytics(member['id'], team['id'])
        # Add server date for calendar restrictions
        analytics['server_date'] = datetime.now().strftime('%Y-%m-%d')
        return {'success': True, 'analytics': analytics}, 200

    except Exception as e:
        print(f"[ERROR] Get member analytics error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@app.route('/api/team/member/<member_adzsend_id>/daily-stats', methods=['GET'])
@rate_limit('api')
def get_team_member_daily_stats(member_adzsend_id):
    """Get daily message stats for a specific team member by their adzsend_id."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        # Check if user owns a business team
        from database import get_business_team_by_owner, get_member_daily_stats, get_user_by_adzsend_id
        team = get_business_team_by_owner(user['id'])

        if not team:
            return {'success': False, 'error': 'You must be a team owner'}, 403

        # Look up member by adzsend_id
        member = get_user_by_adzsend_id(member_adzsend_id)
        if not member:
            return {'success': False, 'error': 'Member not found'}, 404

        # Get date range from query params
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        stats = get_member_daily_stats(member['id'], team['id'], start_date, end_date)
        return {'success': True, 'data': stats}, 200

    except Exception as e:
        import traceback
        print(f"[ERROR] Get member daily stats error: {str(e)}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}, 500


# Personal analytics API endpoints

@app.route('/api/personal/analytics', methods=['GET'])
@rate_limit('api')
def get_personal_analytics():
    """Get personal analytics data for the current user."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        # Get account creation date (stored as signup_date in database)
        account_created = user.get('signup_date', None)
        server_date = datetime.now().strftime('%Y-%m-%d')

        return {
            'success': True,
            'account_created': account_created,
            'server_date': server_date
        }, 200

    except Exception as e:
        print(f"[ERROR] Get personal analytics error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@app.route('/api/personal/daily-stats', methods=['GET'])
@rate_limit('api')
def get_personal_daily_stats():
    """Get daily message stats for the current user's personal usage."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        from database import get_personal_daily_stats
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        stats = get_personal_daily_stats(user['id'], start_date, end_date)
        return {'success': True, 'data': stats}, 200

    except Exception as e:
        import traceback
        print(f"[ERROR] Get personal daily stats error: {str(e)}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}, 500


@app.route('/api/personal/analytics-summary', methods=['GET'])
@rate_limit('api')
def get_personal_analytics_summary_endpoint():
    """Get summary analytics for the current user: all-time counts and peak dates."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        from database import get_personal_analytics_summary
        summary = get_personal_analytics_summary(user['id'])
        return {'success': True, 'data': summary}, 200

    except Exception as e:
        import traceback
        print(f"[ERROR] Get personal analytics summary error: {str(e)}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}, 500


# Team invitation API endpoints

@app.route('/api/team/invitations', methods=['GET'])
def get_invitations():
    """Get pending team invitations for the current user."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        from database import get_team_invitations
        invitations = get_team_invitations(session['user']['id'])
        return {'success': True, 'invitations': invitations}, 200

    except Exception as e:
        print(f"[ERROR] Get invitations error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@app.route('/api/team/invitation/accept/<int:member_id>', methods=['POST'])
def accept_invitation(member_id):
    """Accept a team invitation."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        from database import accept_team_invitation, get_team_invitations, deny_team_invitation

        # Get all invitations for this user
        invitations = get_team_invitations(session['user']['id'])

        # Check if this invitation belongs to the user
        invitation = next((inv for inv in invitations if inv['id'] == member_id), None)
        if not invitation:
            return {'success': False, 'error': 'Invitation not found'}, 404

        # Accept this invitation
        accept_team_invitation(member_id)

        # Deny all other pending invitations for this user
        for inv in invitations:
            if inv['id'] != member_id:
                deny_team_invitation(inv['id'])

        return {'success': True, 'message': 'Invitation accepted'}, 200

    except Exception as e:
        print(f"[ERROR] Accept invitation error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@app.route('/api/team/invitation/deny/<int:member_id>', methods=['POST'])
def deny_invitation(member_id):
    """Deny a team invitation."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        from database import deny_team_invitation, get_team_invitations

        # Verify this invitation belongs to the user
        invitations = get_team_invitations(session['user']['id'])
        invitation = next((inv for inv in invitations if inv['id'] == member_id), None)
        if not invitation:
            return {'success': False, 'error': 'Invitation not found'}, 404

        deny_team_invitation(member_id)
        return {'success': True, 'message': 'Invitation denied'}, 200

    except Exception as e:
        print(f"[ERROR] Deny invitation error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@app.route('/api/team/invitations/clear', methods=['POST'])
def clear_invitations():
    """Clear all pending invitations for the current user."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        from database import clear_all_invitations
        clear_all_invitations(session['user']['id'])
        return {'success': True, 'message': 'All invitations cleared'}, 200

    except Exception as e:
        print(f"[ERROR] Clear invitations error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@app.route('/api/team/current', methods=['GET'])
def get_current_team():
    """Get the current team info for the logged in user."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        from database import get_current_team_for_member, get_business_team_by_owner, get_team_members

        user = get_user_by_id(session.get('user_id'))
        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        # Check if user is a business plan owner
        owner_team = get_business_team_by_owner(user['id'])
        if owner_team:
            # Get team members (only accepted ones)
            members = get_team_members(owner_team['id'])
            accepted_members = [m for m in members if m.get('status') == 'accepted']

            # Get user data for profile photo
            user_data = get_user_data(user['id'])

            return {
                'success': True,
                'is_owner': True,
                'in_team': False,
                'owner_info': {
                    'username': user.get('username'),
                    'discord_id': user.get('discord_id'),
                    'avatar': user.get('avatar'),
                    'adzsend_id': user.get('adzsend_id'),
                    'profile_photo': user_data.get('profile_photo') if user_data else 'Light_Blue.jpg'
                },
                'team_members': [{
                    'username': m.get('member_username'),
                    'discord_id': m.get('member_discord_id'),
                    'avatar': m.get('member_avatar'),
                    'adzsend_id': m.get('member_adzsend_id')
                } for m in accepted_members]
            }, 200

        # Check if user is a team member
        team = get_current_team_for_member(session['user']['id'])
        if not team:
            return {'success': True, 'in_team': False, 'is_owner': False}, 200

        return {
            'success': True,
            'in_team': True,
            'is_owner': False,
            'team': {
                'owner_username': team.get('owner_username'),
                'owner_discord_id': team.get('owner_discord_id'),
                'owner_avatar': team.get('owner_avatar'),
                'owner_adzsend_id': team.get('owner_adzsend_id')
            }
        }, 200

    except Exception as e:
        print(f"[ERROR] Get current team error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@app.route('/api/team/leave', methods=['POST'])
def leave_team_route():
    """Leave the current team."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        from database import leave_team, get_current_team_for_member

        # Check if user is in a team
        team = get_current_team_for_member(session['user']['id'])
        if not team:
            return {'success': False, 'error': 'Not in any team'}, 404

        leave_team(session['user']['id'])
        return {'success': True, 'message': 'Left team successfully'}, 200

    except Exception as e:
        print(f"[ERROR] Leave team error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@app.route('/api/team/member/remove/<int:member_id>', methods=['POST'])
def remove_member_from_list(member_id):
    """Remove a team member from the list (owner only, for denied/left members)."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    try:
        user = get_user_by_id(session.get('user_id'))
        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        from database import get_business_team_by_owner, remove_team_member_from_list, get_team_members

        # Check if user owns a business team
        team = get_business_team_by_owner(user['id'])
        if not team:
            return {'success': False, 'error': 'No business team found'}, 404

        # Verify this member belongs to this team
        members = get_team_members(team['id'])
        member = next((m for m in members if m['id'] == member_id), None)
        if not member:
            return {'success': False, 'error': 'Member not found'}, 404

        # Can only remove denied or left members
        if member['invitation_status'] not in ['denied', 'left']:
            return {'success': False, 'error': 'Can only remove denied or left members'}, 400

        remove_team_member_from_list(member_id)
        return {'success': True, 'message': 'Member removed from list'}, 200

    except Exception as e:
        print(f"[ERROR] Remove member from list error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500


@app.route('/admin')
def admin_panel():
    """Admin panel page."""
    if 'user' not in session:
        return redirect(url_for('login_page'))

    # Check if IP has changed
    client_ip = get_client_ip()
    if 'login_ip' in session and session['login_ip'] != client_ip:
        session.clear()
        return redirect(url_for('login_page'))

    # Get user from database first
    user = get_user_by_id(session.get('user_id'))
    if not user:
        session.clear()
        return redirect(url_for('login_page'))

    # Check if user is admin using database email (not session email which may be stale)
    if not is_admin(user.get('email')):
        return redirect(url_for('home'))

    plan_status = get_plan_status(user['id'])
    has_business = has_business_access(user['id'], session['user']['id'])
    is_admin_user = True  # They're already on the admin page

    response = app.make_response(render_template('admin.html',
                                                user=session['user'],
                                                plan_status=plan_status,
                                                has_business=has_business,
                                                is_owner=is_business_owner(user['id']),
                                                is_admin_user=is_admin_user,
                                                db_version=DATABASE_VERSION,
                                                db_wipe_message=DATABASE_WIPE_MESSAGE))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    """Get all users with optional filters."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    user = get_user_by_id(session.get('user_id'))
    if not user or not is_admin(user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        # Get filters from query params
        filters = []
        if request.args.get('non_plan') == 'true':
            filters.append('non_plan')
        if request.args.get('plan') == 'true':
            filters.append('plan')
        if request.args.get('banned') == 'true':
            filters.append('banned')
        if request.args.get('flagged') == 'true':
            filters.append('flagged')
        if request.args.get('no_discord') == 'true':
            filters.append('no_discord')

        users = get_all_users_for_admin(filters if filters else None)
        return {'success': True, 'users': users}, 200

    except Exception as e:
        import traceback
        print(f"[ERROR] Admin get users error: {str(e)}")
        traceback.print_exc()
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/search-user', methods=['GET'])
@rate_limit('api')
def admin_search_user():
    """Search for a user by email, Adzsend ID, or Discord ID."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        from database import get_user_by_email, get_user_by_adzsend_id

        email = request.args.get('email')
        adzsend_id = request.args.get('adzsend_id')
        discord_id = request.args.get('discord_id')

        user = None

        if email:
            user = get_user_by_email(email.strip().lower())
        elif adzsend_id:
            # Validate Adzsend ID format (18 digits)
            import re
            if not re.match(r'^\d{18}$', adzsend_id):
                return {'success': False, 'error': 'Invalid Adzsend ID format'}, 400
            user = get_user_by_adzsend_id(adzsend_id)
        elif discord_id:
            # Validate Discord ID format
            if not validate_discord_id(discord_id):
                return {'success': False, 'error': 'Invalid Discord ID format'}, 400
            user = get_user_by_discord_id(discord_id)
        else:
            return {'success': False, 'error': 'Search term required'}, 400

        if not user:
            return {'success': False, 'error': 'User not found'}, 404

        # Get has_plan status
        from database import get_active_subscription
        subscription = get_active_subscription(user['id'])
        user['has_plan'] = 1 if subscription else 0

        # Check if user is admin
        user['is_admin'] = is_admin(user.get('email'))

        # Fetch fresh Discord profile info
        username, avatar = fetch_discord_user_info(discord_id)
        if username:
            # Update user info in database
            from database import update_user_profile
            update_user_profile(user['id'], username, avatar)
            user['username'] = username
            user['avatar'] = avatar

        return {'success': True, 'user': user}, 200

    except Exception as e:
        print(f"[ERROR] Admin search user error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/user/<int:user_id>', methods=['GET'])
def admin_get_user_details(user_id):
    """Get detailed user information."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        user_details = get_user_admin_details(user_id)
        if not user_details:
            return {'success': False, 'error': 'User not found'}, 404

        # Fetch fresh Discord profile info
        username, avatar = fetch_discord_user_info(user_details['discord_id'])
        if username:
            # Update user info in database
            from database import update_user_profile
            update_user_profile(user_id, username, avatar)
            user_details['username'] = username
            user_details['avatar'] = avatar

        return {'success': True, 'user': user_details}, 200

    except Exception as e:
        print(f"[ERROR] Admin get user details error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/ban/<int:user_id>', methods=['POST'])
@rate_limit('api')
def admin_ban_user(user_id):
    """Ban a user."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        # Prevent banning admin users (server-side protection)
        target_user = get_user_by_id(user_id)
        if target_user and is_admin(target_user.get('email')):
            return {'success': False, 'error': 'Cannot ban admin users'}, 403

        ban_user(user_id)
        return {'success': True, 'message': 'User banned successfully'}, 200

    except Exception as e:
        print(f"[ERROR] Admin ban user error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/unban/<int:user_id>', methods=['POST'])
@rate_limit('api')
def admin_unban_user(user_id):
    """Unban a user."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        unban_user(user_id)
        return {'success': True, 'message': 'User unbanned successfully'}, 200

    except Exception as e:
        print(f"[ERROR] Admin unban user error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/flag/<int:user_id>', methods=['POST'])
@rate_limit('api')
def admin_flag_user(user_id):
    """Flag a user."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        flag_user(user_id)
        return {'success': True, 'message': 'User flagged successfully'}, 200

    except Exception as e:
        print(f"[ERROR] Admin flag user error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/unflag/<int:user_id>', methods=['POST'])
@rate_limit('api')
def admin_unflag_user(user_id):
    """Unflag a user."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        unflag_user(user_id)
        return {'success': True, 'message': 'User unflagged successfully'}, 200

    except Exception as e:
        print(f"[ERROR] Admin unflag user error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/delete/<int:user_id>', methods=['POST'])
@rate_limit('api')
def admin_delete_user(user_id):
    """Delete a user account."""
    # CSRF protection
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        # Prevent deleting admin users (server-side protection)
        target_user = get_user_by_id(user_id)
        if target_user and is_admin(target_user.get('email')):
            return {'success': False, 'error': 'Cannot delete admin users'}, 403

        delete_user_account_admin(user_id)
        return {'success': True, 'message': 'User deleted successfully'}, 200

    except Exception as e:
        print(f"[ERROR] Admin delete user error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/user/<int:user_id>/message', methods=['GET'])
def admin_get_user_message(user_id):
    """Get user's saved draft message from their panel."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        # Get user_data which contains draft_message
        user_data = get_user_data(user_id)
        if not user_data:
            return {'success': True, 'message': '', 'has_message': False}, 200

        draft_message = user_data.get('draft_message', '')
        return {'success': True, 'message': draft_message or '', 'has_message': bool(draft_message)}, 200

    except Exception as e:
        print(f"[ERROR] Admin get user message error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/user/<int:user_id>/team-message', methods=['GET'])
def admin_get_team_message(user_id):
    """Get business team message if user is owner or member."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        from database import get_business_team_by_owner, get_user_by_id
        user_data = get_user_by_id(user_id)
        if not user_data:
            return {'success': False, 'error': 'User not found'}, 404

        # Check if user owns a business team
        team = get_business_team_by_owner(user_id)
        if not team:
            # Check if user is a member
            from database import get_business_team_by_member
            team = get_business_team_by_member(user_data['discord_id'])

        if not team:
            return {'success': False, 'error': 'User is not part of any business team'}, 404

        team_message = team.get('team_message', '')
        return {'success': True, 'message': team_message or '', 'has_message': bool(team_message)}, 200

    except Exception as e:
        print(f"[ERROR] Admin get team message error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/user/<int:user_id>/billing-history', methods=['GET'])
def admin_get_billing_history(user_id):
    """Get user's complete billing/subscription history."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        from database import get_purchase_history
        history = get_purchase_history(user_id)
        return {'success': True, 'history': history, 'has_history': len(history) > 0}, 200

    except Exception as e:
        print(f"[ERROR] Admin get billing history error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/admin/user/<int:user_id>/plan-status', methods=['GET'])
def admin_get_user_plan_status(user_id):
    """Get user's plan status including usage and reset info."""
    if 'user' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401

    # Get user from database and check if admin using database email
    admin_user = get_user_by_id(session.get('user_id'))
    if not admin_user or not is_admin(admin_user.get('email')):
        return {'success': False, 'error': 'Unauthorized'}, 403

    try:
        from database import get_plan_status
        plan_status = get_plan_status(user_id)
        return {'success': True, 'plan_status': plan_status}, 200

    except Exception as e:
        print(f"[ERROR] Admin get plan status error: {str(e)}")
        return {'success': False, 'error': str(e)}, 500

# =============================================================================
# DISCORD OAUTH ACCOUNT LINKING ROUTES
# =============================================================================

def get_session_user_id():
    """Get user_id from session, with fallback lookup if missing."""
    if 'user_id' in session:
        return session['user_id']

    # Fallback: look up user_id from session['user']['id'] (discord_id)
    if 'user' in session and 'id' in session['user']:
        discord_id = session['user']['id']
        user = get_user_by_discord_id(discord_id)
        if user:
            session['user_id'] = user['id']  # Cache it for future requests
            return user['id']

    return None

@app.route('/api/discord/auth-url')
def discord_auth_url():
    """Generate Discord OAuth2 authorization URL."""
    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    if not DISCORD_CLIENT_ID:
        return {'error': 'Discord OAuth not configured'}, 500

    # Generate a random state parameter for CSRF protection
    state = secrets.token_urlsafe(32)
    session['discord_oauth_state'] = state

    # Build OAuth2 authorization URL
    params = {
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': DISCORD_OAUTH_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify',
        'state': state
    }

    auth_url = f'https://discord.com/api/oauth2/authorize?{urlencode(params)}'
    return {'success': True, 'auth_url': auth_url}


def handle_link_account_callback(user_id, state):
    """Handle Discord OAuth2 callback for linking a new account."""
    # Clear the state from session
    session.pop('discord_link_account_state', None)

    # Check for error response
    error = request.args.get('error')
    if error:
        return render_template('oauth_callback.html', success=False, error='Authorization cancelled')

    # Get authorization code
    code = request.args.get('code')
    if not code:
        return render_template('oauth_callback.html', success=False, error='No authorization code')

    # Exchange code for access token
    token_url = f'{DISCORD_API_BASE}/oauth2/token'
    token_data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_OAUTH_REDIRECT_URI
    }

    try:
        token_response = requests.post(token_url, data=token_data, timeout=10)

        if token_response.status_code != 200:
            print(f"[LINK ACCOUNT] Token exchange failed: {token_response.text}")
            return render_template('oauth_callback.html', success=False, error='Failed to get access token')

        token_json = token_response.json()
        access_token = token_json.get('access_token')
        refresh_token = token_json.get('refresh_token')
        expires_in = token_json.get('expires_in', 604800)  # Default 7 days
        expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

        # Get user info from Discord
        user_response = requests.get(
            f'{DISCORD_API_BASE}/users/@me',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )

        if user_response.status_code != 200:
            print(f"[LINK ACCOUNT] Failed to get user info: {user_response.text}")
            return render_template('oauth_callback.html', success=False, error='Failed to get user info')

        discord_user = user_response.json()
        discord_id = discord_user.get('id')
        username = discord_user.get('username')
        avatar = discord_user.get('avatar')

        # Get avatar decoration asset if present
        avatar_decoration = None
        avatar_decoration_data = discord_user.get('avatar_decoration_data')
        if avatar_decoration_data and avatar_decoration_data.get('asset'):
            avatar_decoration = avatar_decoration_data.get('asset')

        # Store OAuth info in session for token verification step
        session['pending_link_account'] = {
            'discord_id': discord_id,
            'username': username,
            'avatar': avatar,
            'avatar_decoration': avatar_decoration,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at
        }

        # Return a page that closes the popup and notifies the parent window
        return render_template('oauth_callback.html', success=True)

    except requests.exceptions.Timeout:
        return render_template('oauth_callback.html', success=False, error='Connection timeout')
    except Exception as e:
        print(f"[LINK ACCOUNT] Error: {str(e)}")
        return render_template('oauth_callback.html', success=False, error='An error occurred')


@app.route('/discord/callback')
def discord_oauth_callback():
    """Handle Discord OAuth2 callback."""
    user_id = get_session_user_id()
    if not user_id:
        return redirect(url_for('login_page'))

    # Check if this is a link-account callback
    state = request.args.get('state')
    link_account_state = session.get('discord_link_account_state')

    if link_account_state and state == link_account_state:
        # This is a link-account callback, handle it separately
        return handle_link_account_callback(user_id, state)

    # Regular OAuth callback - verify state parameter
    stored_state = session.pop('discord_oauth_state', None)

    if not state or state != stored_state:
        return render_template('settings.html', error='Invalid OAuth state. Please try again.')

    # Check for error response
    error = request.args.get('error')
    if error:
        return redirect(url_for('settings') + '?discord_error=Authorization%20cancelled')

    # Get authorization code
    code = request.args.get('code')
    if not code:
        return redirect(url_for('settings') + '?discord_error=No%20authorization%20code')

    # Exchange code for access token
    token_url = f'{DISCORD_API_BASE}/oauth2/token'
    token_data = {
        'client_id': DISCORD_CLIENT_ID,
        'client_secret': DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': DISCORD_OAUTH_REDIRECT_URI
    }

    try:
        token_response = requests.post(token_url, data=token_data, timeout=10)

        if token_response.status_code != 200:
            print(f"[DISCORD OAUTH] Token exchange failed: {token_response.text}")
            return redirect(url_for('settings') + '?discord_error=Failed%20to%20get%20access%20token')

        token_json = token_response.json()
        access_token = token_json.get('access_token')
        refresh_token = token_json.get('refresh_token')
        expires_in = token_json.get('expires_in', 604800)  # Default 7 days
        expires_at = (datetime.now() + timedelta(seconds=expires_in)).isoformat()

        # Get user info from Discord
        user_response = requests.get(
            f'{DISCORD_API_BASE}/users/@me',
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )

        if user_response.status_code != 200:
            print(f"[DISCORD OAUTH] Failed to get user info: {user_response.text}")
            return redirect(url_for('settings') + '?discord_error=Failed%20to%20get%20user%20info')

        discord_user = user_response.json()
        discord_id = discord_user.get('id')
        username = discord_user.get('username')
        avatar = discord_user.get('avatar')

        # Get avatar decoration asset if present
        avatar_decoration = None
        avatar_decoration_data = discord_user.get('avatar_decoration_data')
        if avatar_decoration_data and avatar_decoration_data.get('asset'):
            avatar_decoration = avatar_decoration_data.get('asset')

        # Save OAuth data to database (user_id already retrieved at top of function)
        save_discord_oauth(user_id, discord_id, username, avatar, access_token, refresh_token, expires_at, avatar_decoration)

        # Redirect back to settings with success message
        return redirect(url_for('settings') + '?discord_success=1')

    except requests.exceptions.Timeout:
        return redirect(url_for('settings') + '?discord_error=Connection%20timeout')
    except Exception as e:
        print(f"[DISCORD OAUTH] Error: {str(e)}")
        return redirect(url_for('settings') + '?discord_error=An%20error%20occurred')


@app.route('/api/discord/status')
def discord_status():
    """Get Discord OAuth linking status."""
    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    oauth_info = get_discord_oauth_info(user_id)

    if not oauth_info:
        return {'error': 'User not found'}, 404

    return {
        'success': True,
        'is_fully_linked': oauth_info['is_fully_linked'],
        'has_oauth': oauth_info['has_oauth'],
        'oauth_discord_id': oauth_info['oauth_discord_id'],
        'oauth_username': oauth_info['oauth_username'],
        'oauth_avatar': oauth_info['oauth_avatar'],
        'linked_discord_id': oauth_info['linked_discord_id'],
        'linked_username': oauth_info['linked_username'],
        'linked_avatar': oauth_info['linked_avatar']
    }


@app.route('/api/discord/verify-token', methods=['POST'])
@rate_limit('discord_token_verify')
def discord_verify_token():
    """Verify that provided token matches the OAuth account."""
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    data = request.get_json()
    if not data:
        return {'error': 'No data provided'}, 400

    token = data.get('token', '').strip()
    if not token:
        return {'error': 'Token is required'}, 400

    # Validate token format
    if not validate_discord_token(token):
        return {'error': 'Token must match the Discord account you authorized above'}, 400

    # Get OAuth info to compare Discord IDs
    oauth_info = get_discord_oauth_info(user_id)
    if not oauth_info or not oauth_info['has_oauth']:
        return {'error': 'Please complete Discord authorization first'}, 400

    expected_discord_id = oauth_info['oauth_discord_id']

    # Verify token against Discord API
    try:
        headers = {'Authorization': token}
        response = requests.get(f'{DISCORD_API_BASE}/users/@me', headers=headers, timeout=10)

        if response.status_code == 401:
            return {'error': 'Invalid token'}, 400

        if response.status_code != 200:
            return {'error': 'Failed to verify token'}, 400

        user_data = response.json()
        token_discord_id = user_data.get('id')

        # Check if token's Discord ID matches OAuth Discord ID
        if token_discord_id != expected_discord_id:
            return {
                'error': f'Token does not match authorized account. Expected account: {oauth_info["oauth_username"]}',
                'mismatch': True
            }, 400

        return {'success': True, 'message': 'Token verified successfully'}

    except requests.exceptions.Timeout:
        return {'error': 'Connection timeout'}, 500
    except Exception as e:
        print(f"[DISCORD TOKEN VERIFY] Error: {str(e)}")
        return {'error': 'An error occurred'}, 500


@app.route('/api/discord/link', methods=['POST'])
@rate_limit('discord_link')
def discord_link():
    """Complete Discord account linking with verified token."""
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    data = request.get_json()
    if not data:
        return {'error': 'No data provided'}, 400

    token = data.get('token', '').strip()
    if not token:
        return {'error': 'Token is required'}, 400

    # Get OAuth info
    oauth_info = get_discord_oauth_info(user_id)
    if not oauth_info or not oauth_info['has_oauth']:
        return {'error': 'Please complete Discord authorization first'}, 400

    expected_discord_id = oauth_info['oauth_discord_id']

    # Verify token one more time before linking
    try:
        headers = {'Authorization': token}
        response = requests.get(f'{DISCORD_API_BASE}/users/@me', headers=headers, timeout=10)

        if response.status_code != 200:
            return {'error': 'Token verification failed'}, 400

        user_data = response.json()
        token_discord_id = user_data.get('id')

        if token_discord_id != expected_discord_id:
            return {'error': 'Token does not match authorized account'}, 400

        # Complete the linking
        success, error = complete_discord_link(user_id, token)
        if not success:
            return {'error': error or 'Failed to link account'}, 500

        # Update session with new Discord info
        session['user'] = {
            'id': oauth_info['oauth_discord_id'],
            'username': oauth_info['oauth_username'],
            'avatar': oauth_info['oauth_avatar']
        }
        session.modified = True

        return {'success': True, 'message': 'Discord account linked successfully'}

    except requests.exceptions.Timeout:
        return {'error': 'Connection timeout'}, 500
    except Exception as e:
        print(f"[DISCORD LINK] Error: {str(e)}")
        return {'error': 'An error occurred'}, 500


@app.route('/api/discord/unlink', methods=['POST'])
def discord_unlink():
    """Fully unlink Discord account."""
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    # Get user's email before unlinking (for session update)
    user = get_user_by_internal_id(user_id)
    if not user:
        return {'error': 'User not found'}, 404

    email = user.get('email')

    full_unlink_discord_account(user_id)

    # Update session to reflect the new discord_id (pending_email)
    # This prevents issues when the page reloads and tries to look up user
    if 'user' in session and email:
        session['user']['id'] = f'pending_{email}'
        session['user']['username'] = email.split('@')[0]
        session['user']['avatar'] = None

    return {'success': True, 'message': 'Discord account unlinked successfully.'}


# =============================================================================
# LINKED DISCORD ACCOUNTS API (Multiple accounts for sending messages)
# =============================================================================

@app.route('/api/linked-accounts')
def get_linked_accounts():
    """Get all linked Discord accounts for the current user."""
    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    from database import get_linked_discord_accounts, get_linked_discord_account_count
    from config import get_account_limit, can_link_more_accounts, is_admin

    user = get_user_by_internal_id(user_id)
    if not user:
        return {'error': 'User not found'}, 404

    user_is_admin = is_admin(user.get('email'))
    accounts = get_linked_discord_accounts(user_id)
    count = get_linked_discord_account_count(user_id)
    can_link, limit, remaining = can_link_more_accounts(user.get('email'), count, user_is_admin)

    return {
        'success': True,
        'accounts': accounts,
        'count': count,
        'limit': limit,
        'remaining': remaining,
        'can_link': can_link
    }


@app.route('/api/linked-accounts/search')
def search_linked_accounts_api():
    """Search linked Discord accounts."""
    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    query = request.args.get('q', '')
    if not query:
        return {'error': 'No search query provided'}, 400

    from database import search_linked_discord_accounts
    accounts = search_linked_discord_accounts(user_id, query)

    return {
        'success': True,
        'accounts': accounts
    }


@app.route('/api/linked-accounts/pending')
def get_pending_link_account():
    """Get pending link account data from session."""
    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    pending_data = session.get('pending_link_account')
    if not pending_data:
        return {'success': True, 'pending': None}

    return {
        'success': True,
        'pending': {
            'discord_id': pending_data.get('discord_id'),
            'username': pending_data.get('username'),
            'avatar': pending_data.get('avatar'),
            'avatar_decoration': pending_data.get('avatar_decoration')
        }
    }


@app.route('/discord/link-account')
def discord_link_account():
    """Initiate Discord OAuth2 for linking a new account."""
    user_id = get_session_user_id()
    if not user_id:
        return redirect(url_for('login_page'))

    # Check if user can link more accounts
    from database import get_linked_discord_account_count
    from config import can_link_more_accounts, is_admin

    user = get_user_by_internal_id(user_id)
    if not user:
        return redirect(url_for('settings') + '?error=User%20not%20found')

    user_is_admin = is_admin(user.get('email'))
    count = get_linked_discord_account_count(user_id)
    can_link, limit, remaining = can_link_more_accounts(user.get('email'), count, user_is_admin)

    if not can_link:
        return redirect(url_for('settings') + '?error=Account%20limit%20reached')

    # Generate OAuth2 state
    state = secrets.token_urlsafe(32)
    session['discord_link_account_state'] = state

    # Build OAuth2 authorization URL
    # Use the base callback URL with link_account flag
    params = urlencode({
        'client_id': DISCORD_CLIENT_ID,
        'redirect_uri': DISCORD_OAUTH_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify',
        'state': state
    })

    auth_url = f'{DISCORD_API_BASE}/oauth2/authorize?{params}'
    return redirect(auth_url)


@app.route('/api/linked-accounts/verify-token', methods=['POST'])
def verify_link_account_token():
    """Verify the Discord token and complete account linking."""
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    # Get pending link data from session
    pending_data = session.get('pending_link_account')
    if not pending_data:
        return {'error': 'No pending account link'}, 400

    # Get token from request
    data = request.get_json()
    discord_token = data.get('token', '').strip()

    if not discord_token:
        return {'error': 'Token is required'}, 400

    # Verify token by making a request to Discord API
    try:
        user_response = requests.get(
            f'{DISCORD_API_BASE}/users/@me',
            headers={'Authorization': discord_token},
            timeout=10
        )

        if user_response.status_code != 200:
            return {'error': 'Incorrect account token', 'valid': False}, 200

        # Verify that the token belongs to the OAuth-authorized account
        token_user = user_response.json()
        if token_user.get('id') != pending_data['discord_id']:
            return {'error': 'Incorrect account token', 'valid': False}, 200

        # Token is valid, add the account
        from database import add_linked_discord_account

        success, result = add_linked_discord_account(
            user_id=user_id,
            discord_id=pending_data['discord_id'],
            username=pending_data['username'],
            avatar=pending_data['avatar'],
            avatar_decoration=pending_data.get('avatar_decoration'),
            discord_token=discord_token,
            oauth_access_token=pending_data['access_token'],
            oauth_refresh_token=pending_data['refresh_token'],
            oauth_expires_at=pending_data['expires_at']
        )

        if not success:
            return {'error': result, 'valid': False}, 200

        # Clear pending data
        session.pop('pending_link_account', None)

        return {
            'success': True,
            'valid': True,
            'message': 'Account linked successfully',
            'account_id': result
        }

    except requests.exceptions.Timeout:
        return {'error': 'Connection timeout', 'valid': False}, 200
    except Exception as e:
        print(f"[VERIFY TOKEN] Error: {str(e)}")
        return {'error': 'Verification failed', 'valid': False}, 200


@app.route('/api/linked-accounts/<int:account_id>/unlink', methods=['POST'])
def unlink_account(account_id):
    """Unlink a Discord account."""
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    from database import unlink_discord_account
    success = unlink_discord_account(user_id, account_id)

    if not success:
        return {'error': 'Account not found or already unlinked'}, 404

    return {'success': True, 'message': 'Account unlinked successfully'}


@app.route('/api/linked-accounts/update-token', methods=['POST'])
def update_account_token():
    """Update the token for a linked Discord account."""
    csrf_error = check_csrf()
    if csrf_error:
        return csrf_error

    user_id = get_session_user_id()
    if not user_id:
        return {'error': 'Not logged in'}, 401

    data = request.json
    if not data:
        return {'error': 'Invalid request'}, 400

    account_id = data.get('account_id')
    new_token = data.get('token', '').strip()

    if not account_id or not new_token:
        return {'error': 'Missing account_id or token'}, 400

    # Basic token format validation
    if len(new_token) < 50 or '.' not in new_token:
        return {'error': 'Invalid token format'}, 400

    # Verify the account belongs to this user
    from database import get_linked_discord_account_by_id, get_linked_discord_accounts
    linked_accounts = get_linked_discord_accounts(user_id)
    account_ids = [acc['id'] for acc in linked_accounts]

    if account_id not in account_ids:
        return {'error': 'Account not found'}, 404

    # Verify the token is valid by making a Discord API call
    headers = {'Authorization': new_token}
    try:
        resp = requests.get('https://discord.com/api/v10/users/@me', headers=headers, timeout=10)

        if resp.status_code != 200:
            return {'error': 'Invalid Discord token'}, 400

        user_data = resp.json()
        token_discord_id = user_data.get('id')

        # Get the account to verify the token matches the same Discord user
        account = get_linked_discord_account_by_id(account_id)
        if not account:
            return {'error': 'Account not found'}, 404

        if token_discord_id != account['discord_id']:
            return {'error': 'Token does not match this Discord account'}, 400

        # Update the token in database
        from database.models import encrypt_token, get_db
        encrypted_token = encrypt_token(new_token)
        if not encrypted_token:
            return {'error': 'Failed to encrypt token'}, 500

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE linked_discord_accounts
            SET discord_token = ?, is_valid = 1, last_verified = CURRENT_TIMESTAMP,
                username = ?, avatar = ?, avatar_decoration = ?
            WHERE id = ? AND user_id = ?
        ''', (
            encrypted_token,
            user_data.get('username'),
            user_data.get('avatar'),
            user_data.get('avatar_decoration_data', {}).get('asset') if user_data.get('avatar_decoration_data') else None,
            account_id,
            user_id
        ))
        conn.commit()
        conn.close()

        return {'success': True, 'message': 'Token updated successfully'}

    except requests.exceptions.Timeout:
        return {'error': 'Discord API timeout'}, 500
    except Exception as e:
        print(f"[TOKEN UPDATE] Error: {e}")
        return {'error': 'Failed to verify token'}, 500


@app.route('/logout')
def logout():
    session.clear()
    response = app.make_response(render_template('logout.html'))
    # Prevent caching to avoid going back to personal panel after logout
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Global error handler for API routes - return JSON instead of HTML
@app.errorhandler(Exception)
def handle_error(e):
    import traceback
    traceback.print_exc()
    # For API routes, return JSON
    if request.path.startswith('/api/'):
        return jsonify({'error': f'Server error: {str(e)}'}), 500
    # For regular routes, let Flask handle it normally
    raise e

if __name__ == '__main__':
    # Use environment variable for debug mode (default: False for production safety)
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(debug=debug_mode)
