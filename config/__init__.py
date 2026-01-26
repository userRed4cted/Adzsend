# =============================================================================
# CONFIG PACKAGE
# =============================================================================
# Import all configs from this folder for easy access.
# Usage: from config import BUTTONS, HOMEPAGE, SITE, etc.
# =============================================================================

from .buttons import BUTTONS
from .homepage import HOMEPAGE
from .navbar import NAVBAR
from .colors import COLORS
from .pages import PAGES, get_page_title, get_page_subtitle, get_page_description, get_page_embed
from .plans import SUBSCRIPTION_PLANS, BUSINESS_PLANS
from .admin import ADMIN_EMAILS, is_admin
from .email import BLACKLISTED_EMAIL_DOMAINS, ALLOWED_EMAIL_TLDS
from .discord_accounts import (
    DEFAULT_ACCOUNT_LIMIT, ACCOUNT_LIMIT_OVERRIDES,
    get_account_limit, can_link_more_accounts
)
from .support import SUPPORT_HERO_TITLE, SUPPORT_FAQ_TITLE, SUPPORT_CONTACT_TEXT, FAQ_ITEMS
from .terms import TERMS_SECTIONS
from .guidelines import GUIDELINES_SECTIONS
from .paid_services_terms import PAID_SERVICES_TERMS_SECTIONS
from .bridge import BRIDGE_TITLE, BRIDGE_DESCRIPTION, BRIDGE_DOWNLOAD_URLS, BRIDGE_FEATURE_PILLS

# Import site-wide settings
from .site import SITE_FONT, SITE


def get_all_config():
    """Return all configuration as a single dictionary for template injection."""
    return {
        'buttons': BUTTONS,
        'homepage': HOMEPAGE,
        'navbar': NAVBAR,
        'colors': COLORS,
        'pages': PAGES,
        # Backwards compatibility aliases
        'page_titles': PAGES['titles'],
    }
