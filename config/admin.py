# =============================================================================
# ADMIN CONFIGURATION
# =============================================================================
# Add admin email addresses here to grant administrator access.
# Users with these emails will have access to the admin panel.
# =============================================================================

ADMIN_EMAILS = [
    'artiomroveo@gmail.com',
    # Add admin email addresses here
    # Example: 'admin@yourdomain.com',
]


def is_admin(email):
    """Check if an email address belongs to an admin."""
    if not email:
        return False
    return email.lower() in [e.lower() for e in ADMIN_EMAILS]
