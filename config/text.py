# ==============================================
# TEXT & LABELS CONFIGURATION
# ==============================================
# This file contains various text strings used across pages.
# Edit these to customize messages, labels, and descriptions.
# ==============================================

TEXT = {
    # ==========================================
    # DASHBOARD PAGE
    # ==========================================
    'dashboard': {
        # Panel headers
        'servers_header': 'Your Servers',
        'channels_header': 'Channels',
        'selected_header': 'Selected Channels',
        'message_header': 'Message',

        # Empty states
        'no_servers': 'No servers found',
        'no_channels': 'Select a server to see channels',
        'no_selection': 'No channels selected',

        # Buttons
        'send_button': 'Send Message',
        'clear_all_button': 'Clear All',

        # Placeholders
        'search_servers': 'Search servers...',
        'search_channels': 'Search channels...',
        'message_placeholder': 'Type your advertisement message here...',

        # Status messages
        'sending': 'Sending...',
        'sent_success': 'Message sent successfully!',
        'sent_partial': 'Message sent to {success} channels, {failed} failed',
    },

    # ==========================================
    # SETTINGS PAGE
    # ==========================================
    'settings': {
        # Panel titles
        'usage_panel': 'Usage Statistics',
        'account_panel': 'Account',
        'preferences_panel': 'Preferences',

        # Labels
        'messages_sent': 'Messages Sent',
        'messages_remaining': 'Messages Remaining',
        'plan_type': 'Current Plan',
        'member_since': 'Member Since',

        # Buttons
        'delete_account': 'Delete Account',
        'logout': 'Logout',
        'save_settings': 'Save Settings',

        # Messages
        'support_notice': 'Need help? Contact support in our Discord server.',
        'delete_confirm': 'Are you sure you want to delete your account? This cannot be undone.',
    },

    # ==========================================
    # PURCHASE PAGE
    # ==========================================
    'purchase': {
        # Mode toggle
        'personal_mode': 'Personal',
        'business_mode': 'Business',

        # Billing toggle
        'monthly': 'Monthly',
        'yearly': 'Yearly',
        'save_badge': 'Save 20%',

        # Plan card
        'per_month': '/month',
        'per_year': '/year',
        'purchase_button': 'Get Started',
        'current_plan': 'Current Plan',
    },

    # ==========================================
    # LOGIN/SIGNUP PAGES
    # ==========================================
    'auth': {
        # Page titles
        'login_title': 'Login',
        'signup_title': 'Sign Up',

        # Form labels
        'token_placeholder': 'Enter your Discord token',
        'username_placeholder': 'Username',
        'password_placeholder': 'Password',

        # Buttons
        'login_button': 'Login',
        'signup_button': 'Sign Up',
        'help_button': 'How do I get my token?',

        # Messages
        'security_warning': 'Your token is encrypted and stored securely. We only use it to send messages on your behalf.',
        'invalid_token': 'Invalid token. Please try again.',
        'login_success': 'Login successful!',
    },

    # ==========================================
    # ERROR MESSAGES
    # ==========================================
    'errors': {
        'generic': 'Something went wrong. Please try again.',
        'not_found': 'Page not found.',
        'unauthorized': 'You must be logged in to access this page.',
        'forbidden': 'You do not have permission to access this page.',
        'rate_limited': 'Too many requests. Please wait a moment.',
        'server_error': 'Server error. Please try again later.',
    },

    # ==========================================
    # SUCCESS MESSAGES
    # ==========================================
    'success': {
        'saved': 'Settings saved successfully!',
        'deleted': 'Deleted successfully!',
        'updated': 'Updated successfully!',
    },
}
