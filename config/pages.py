# ==============================================
# PAGE CONFIGURATION
# ==============================================
# This file controls page titles, subtitles, descriptions, and embeds.
# ==============================================

PAGES = {
    # ==========================================
    # BROWSER TAB TITLES
    # ==========================================
    # The text shown in the browser tab for each page
    'titles': {
        'home': 'Home',
        'purchase': 'Purchase',
        'settings': 'Settings',
        'signup': 'Signup',
        'login': 'Login',
        'verify': 'Verify',
        'personal_panel': 'Personal Panel',
        'team_management': 'Team Management',
        'team_panel': 'Team Panel',
        'admin': 'Admin',
        'logout': 'Logout',
    },

    # ==========================================
    # NAVBAR SUBTITLES
    # ==========================================
    # The small text shown below the main title in the navbar for each page
    'subtitles': {
        'home': 'Welcome to your AdzSend',
        'purchase': 'Choose your plan and start sending',
        'settings': 'Manage your account settings and preferences',
        'signup': 'Sign up to get started',
        'login': 'Login to your account',
        'verify': 'Verify your email',
        'personal_panel': 'Select servers and channels to send messages',
        'team_management': 'Manage your team and shared message',
        'team_panel': 'Send team messages',
        'admin': 'Manage users and monitor platform activity',
    },

    # ==========================================
    # PAGE DESCRIPTIONS (SEO)
    # ==========================================
    # Used for meta description tags - appears in search results
    'descriptions': {
        'home': 'Adzsend Home',
        'purchase': 'Adzsend Purchase',
        'settings': 'Adzsend Settings',
        'signup': 'Adzsend Signup',
        'login': 'Adzsend Login',
        'verify': 'Adzsend Verify',
        'personal_panel': 'Adzsend Personal Panel',
        'team_management': 'Adzsend Team Management',
        'team_panel': 'Adzsend Team Panel',
        'admin': 'Adzsend Admin',
    },

    # ==========================================
    # SOCIAL MEDIA EMBEDS (Open Graph / Twitter Cards)
    # ==========================================
    # Controls how links appear when shared on Discord, Twitter, Facebook, etc.
    # - title: The title shown in the embed
    # - description: The description shown in the embed
    # - image: Image filename in static folder (e.g., 'embed_preview.png')
    # - color: Theme color for the embed (hex format)
    'embeds': {
        'home': {
            'title': 'Adzsend',
            'description': 'Stop wasting time copy and pasting messages, time is money.',
            'image': None,  # Add image filename here, e.g., 'embed_preview.png'
            'color': '#15d8bc',
        },
        'purchase': {
            'title': 'Adzsend',
            'description': 'Choose your plan and start automating your Discord marketing.',
            'image': None,
            'color': None,
        },
        'signup': {
            'title': 'Adzsend',
            'description': 'Create your account and start marketing on Discord.',
            'image': None,
            'color': None,
        },
        'login': {
            'title': 'Adzsend',
            'description': 'Login to your Adzsend account.',
            'image': None,
            'color': None,
        },
    },
}


# ==========================================
# HELPER FUNCTIONS
# ==========================================
# These functions are used by templates to get page configuration

def get_page_title(page):
    """Get the browser tab title for a page."""
    return PAGES.get('titles', {}).get(page, 'Adzsend')


def get_page_subtitle(page):
    """Get the navbar subtitle for a page."""
    return PAGES.get('subtitles', {}).get(page, '')


def get_page_description(page):
    """Get the SEO meta description for a page."""
    return PAGES.get('descriptions', {}).get(page, 'Discord marketing automation panel')


def get_page_embed(page):
    """Get the social media embed configuration for a page."""
    default = {
        'title': 'Adzsend',
        'description': 'Discord marketing automation panel',
        'image': None,
        'color': '#15d8bc',
    }
    return PAGES.get('embeds', {}).get(page, default)
