# Config Package
# Import all configs from this folder for easy access

from .buttons import BUTTONS
from .homepage import HOMEPAGE
from .navbar import NAVBAR
from .colors import COLORS
from .pages import PAGES
from .text import TEXT
from .plans import SUBSCRIPTION_PLANS, ONE_TIME_PLANS, BUSINESS_PLANS, YEARLY_DISCOUNT_PERCENT
from .admin import ADMIN_USER_IDS, is_admin


def get_all_config():
    """Return all configuration as a single dictionary for template injection."""
    return {
        'buttons': BUTTONS,
        'homepage': HOMEPAGE,
        'navbar': NAVBAR,
        'colors': COLORS,
        'pages': PAGES,
        'text': TEXT,
        # Backwards compatibility aliases
        'page_titles': PAGES['titles'],
    }
