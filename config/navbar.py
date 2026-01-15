# ==============================================
# NAVBAR CONFIGURATION
# ==============================================
# This file contains all settings for the navigation bar.
# Edit these values to customize navigation text and links.
# ==============================================

NAVBAR = {
    # ==========================================
    # BRANDING (Logo area)
    # ==========================================
    # Shown in the top-left of the navbar
    'branding': {
        'title': "Ad Z send",
        'subtitle': "Welcome to your marketing automation hub",
    },

    # ==========================================
    # NAVIGATION MENU LABELS
    # ==========================================
    # Text shown in the dropdown menu
    'menu': {
        'home': 'Home',
        'purchase': 'Purchase',
        'panel': 'Personal Panel',
        'settings': 'Settings',
        'admin': 'Admin',
        'team_management': 'Team Management',
        'team_panel': 'Team Panel',
        'discord': 'Discord Server',
        'logout': 'Logout',
    },

    # ==========================================
    # AUTHENTICATION BUTTONS
    # ==========================================
    # Login/Signup buttons shown when user is not logged in
    'auth_buttons': {
        'login': 'Login',
        'signup': 'Sign Up',
    },

    # ==========================================
    # EXTERNAL LINKS
    # ==========================================
    'links': {
        # Discord server invite link
        'discord_invite': "https://discord.gg/KWt6rvCukp",
    },

    # ==========================================
    # WELCOME TEXT SLIDESHOW
    # ==========================================
    # Rotating welcome messages shown next to profile photo (logged in users only)
    'welcome_slideshow': {
        # Messages to rotate through - add/remove as many as you want
        'messages': [
            "Hello.",
            "Welcome!",
            "Hi :D"
        ],

        # Time each message shows (in milliseconds)
        # 5000 = 5 seconds (default)
        'interval': 5000,

        # How long the fade animation takes (in milliseconds)
        # 300 = fast fade, 500 = medium fade, 800 = slow fade
        'fade_duration': 400,
    },
}
