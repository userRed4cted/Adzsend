# Admin Configuration
# Add Discord User IDs of administrators here

ADMIN_USER_IDS = [
    '1042840778990440580'
    # Add admin Discord IDs here
    # Example: '123456789012345678',
]

def is_admin(discord_id):
    """Check if a Discord ID belongs to an admin."""
    return str(discord_id) in ADMIN_USER_IDS
