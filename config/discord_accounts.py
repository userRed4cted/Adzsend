# =============================================================================
# DISCORD LINKED ACCOUNTS CONFIGURATION
# =============================================================================
# This file controls the limits and permissions for linking multiple Discord
# accounts that can be used to send messages from the panel.
# =============================================================================

# Default maximum number of linked Discord accounts per user
DEFAULT_ACCOUNT_LIMIT = 3

# =============================================================================
# ADMIN LIMIT CONFIGURATION
# =============================================================================
# Enable or disable special account limits for admin users
ADMIN_HIGHER_LIMIT_ENABLED = True  # Set to False to treat admins like regular users

# Maximum accounts for admin users (only applies if ADMIN_HIGHER_LIMIT_ENABLED = True)
ADMIN_ACCOUNT_LIMIT = 10

# =============================================================================
# EMAIL-BASED OVERRIDES
# =============================================================================
# Email-based account limit overrides (takes precedence over admin limits)
# Users with these emails can link more accounts than the default
# Format: { 'email@example.com': limit_number }
ACCOUNT_LIMIT_OVERRIDES = {
    # Example: Specific user gets 15 accounts
    # 'specific_user@example.com': 15,

    # Add your email overrides here
}


def get_account_limit(user_email, is_admin=False):
    """
    Get the account link limit for a specific user.

    Args:
        user_email: The user's email address
        is_admin: Whether the user is an admin

    Returns:
        int: The maximum number of Discord accounts this user can link
    """
    if not user_email:
        return DEFAULT_ACCOUNT_LIMIT

    # Check for email-specific override first (highest priority)
    override = ACCOUNT_LIMIT_OVERRIDES.get(user_email.lower())
    if override:
        return override

    # Check if user is admin and admin higher limits are enabled
    if is_admin and ADMIN_HIGHER_LIMIT_ENABLED:
        return ADMIN_ACCOUNT_LIMIT

    # Return default limit
    return DEFAULT_ACCOUNT_LIMIT


def can_link_more_accounts(user_email, current_count, is_admin=False):
    """
    Check if a user can link more Discord accounts.

    Args:
        user_email: The user's email address
        current_count: Current number of linked accounts
        is_admin: Whether the user is an admin

    Returns:
        tuple: (can_link: bool, limit: int, remaining: int)
    """
    limit = get_account_limit(user_email, is_admin)
    remaining = max(0, limit - current_count)
    can_link = current_count < limit

    return can_link, limit, remaining
