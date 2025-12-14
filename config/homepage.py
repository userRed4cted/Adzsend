# ==============================================
# HOMEPAGE CONFIGURATION
# ==============================================
# This file contains all text and settings for the homepage.
# Edit these values to customize what appears on the homepage.
# ==============================================

HOMEPAGE = {
    # ==========================================
    # HERO SECTION (Main landing area)
    # ==========================================
    # The hero section is the first thing visitors see
    'hero': {
        # Slideshow messages that rotate automatically
        # Add or remove messages as needed - they cycle through
        'slideshow_messages': [
            "The first marketing tool to send multiple advertisements all across different discord servers with one click",
            "Tired of expensive and untrustworthy marketing services where you cant monitor, customise, or have control over your marketing?",
            "What used to take hours, now takes seconds with Borz Marketing"
        ],

        # Time between slides in milliseconds (5000 = 5 seconds)
        'slideshow_interval': 5000,

        # Fade animation duration in milliseconds (600 = 0.6 seconds)
        'slideshow_fade_duration': 600,

        # Call-to-action button text
        'cta_button_text': "View Pricing",

        # Scroll indicator text (shown at bottom of hero)
        'scroll_indicator_text': "Scroll down to view more",
    },

    # ==========================================
    # GALLERY SECTION (Panel Images showcase)
    # ==========================================
    # Shows screenshots/images of the panel
    'gallery': {
        # Section title
        'title': "Panel Images",

        # List of image filenames from the static folder
        # Add or remove images - gallery displays all of them
        'images': [
            "PanelImage1.png",
            "PanelImage2.png",
            "PanelImage3.png"
        ],
    },

    # ==========================================
    # ABOUT SECTION (Who Are We)
    # ==========================================
    # Describes your service to visitors
    'about': {
        # Section title
        'title': "Who are we?",

        # Description text - can be as long as needed
        'description': "Introducing the first marketing tool that lets you send ads across multiple Discord servers at once, saving time, cutting costs, and giving you total control. No more waiting on marketing teams or wasting money on marketing services. Send ads instantly, track results in real time, and remove underperformers from your workflow. Do it yourself with a single click, or upgrade to our Business Plan to manage a team using our panel, assign ads, and gain detailed insights on each members performance. Marketing, simplified, powerful, and designed to deliver results.",
    },
}
