# ==============================================
# NAVBAR CONFIGURATION
# ==============================================
# This file contains settings for the navigation bar.
# ==============================================

NAVBAR = {
    # ==========================================
    # WELCOME TEXT SLIDESHOW
    # ==========================================
    # Rotating welcome messages shown next to profile photo (logged in users only)
    'welcome_slideshow': {
        # Messages to rotate through - add/remove as many as you want
        'messages': [
            "Hello.",
            "Welcome!",
            "Greetings.",
            "Hi :D"
        ],

        # Time each message shows (in milliseconds)
        # 5000 = 5 seconds (default)
        'interval': 7000,

        # How long the fade animation takes (in milliseconds)
        # 300 = fast fade, 500 = medium fade, 800 = slow fade
        'fade_duration': 700,
    },
}
