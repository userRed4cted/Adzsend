# =============================================================================
# DISCORD LINKED ACCOUNTS CONFIGURATION
# =============================================================================
# This file controls the limits and permissions for linking multiple Discord
# accounts that can be used to send messages from the panel.
# =============================================================================

# Default maximum number of linked Discord accounts per user
DEFAULT_ACCOUNT_LIMIT = 4

# Email-based account limit overrides
# Users with these emails can link more accounts than the default
# Format: { 'email@example.com': limit_number }
ACCOUNT_LIMIT_OVERRIDES = {
    # Example: Owner gets 10 accounts
    # 'owner@example.com': 10,

    # Add your email overrides here
}


def get_account_limit(user_email):
    """
    Get the account link limit for a specific user.

    Args:
        user_email: The user's email address

    Returns:
        int: The maximum number of Discord accounts this user can link
    """
    if not user_email:
        return DEFAULT_ACCOUNT_LIMIT

    # Check for override
    override = ACCOUNT_LIMIT_OVERRIDES.get(user_email.lower())
    if override:
        return override

    return DEFAULT_ACCOUNT_LIMIT


def can_link_more_accounts(user_email, current_count):
    """
    Check if a user can link more Discord accounts.

    Args:
        user_email: The user's email address
        current_count: Current number of linked accounts

    Returns:
        tuple: (can_link: bool, limit: int, remaining: int)
    """
    limit = get_account_limit(user_email)
    remaining = max(0, limit - current_count)
    can_link = current_count < limit

    return can_link, limit, remaining
