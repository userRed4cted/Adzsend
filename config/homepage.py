# =============================================================================
# HOMEPAGE CONFIGURATION
# =============================================================================
# This file controls all content displayed on the homepage (home.html).
# Each setting is documented with what it does and which UI element it affects.
# =============================================================================


HOMEPAGE = {

    # =========================================================================
    # HERO SECTION (Main landing area with particle effect)
    # =========================================================================
    # Element: Full-screen section at top of homepage with slideshow text
    # File: templates/home.html - hero section

    'hero': {

        # SLIDESHOW MESSAGES
        # Element: Large rotating text in center of hero section
        # These messages cycle automatically based on interval setting
        # Add/remove as many as you want
        'slideshow_messages': [
            "The first marketing tool to send multiple advertisements all across different discord servers with one click",
            "Tired of expensive and untrustworthy marketing services where you cant monitor, customise, or have control over your marketing?",
            "What used to take hours, now takes seconds with Borz Marketing"
        ],

        # SLIDESHOW TIMING
        # slideshow_interval: Time each message shows (in milliseconds)
        #   - 3000 = 3 seconds
        #   - 5000 = 5 seconds (default)
        #   - 7000 = 7 seconds
        'slideshow_interval': 5000,

        # slideshow_fade_duration: How long the fade animation takes (in milliseconds)
        #   - 300 = fast fade
        #   - 600 = medium fade (default)
        #   - 1000 = slow fade
        'slideshow_fade_duration': 600,

        # CTA BUTTON TEXT
        # Element: The main call-to-action button below the slideshow
        # Links to: Purchase page (/purchase)
        'cta_button_text': "View Pricing",

        # SCROLL INDICATOR TEXT
        # Element: Text with animated chevron at bottom of hero
        # Tells users to scroll down for more content
        'scroll_indicator_text': "Scroll down to view more",
    },


    # =========================================================================
    # GALLERY SECTION (Panel Images showcase)
    # =========================================================================
    # Element: Section with clickable image thumbnails that open in lightbox
    # File: templates/home.html - gallery section

    'gallery': {

        # SECTION TITLE
        # Element: Heading text above the image grid
        'title': "Panel Images",

        # IMAGE LIST
        # Element: Grid of clickable thumbnail images
        # Each image opens in a fullscreen lightbox when clicked
        # Images must be placed in: static/ folder
        # Format: Just the filename (e.g., "image.png")
        'images': [
            "PanelImage1.png",
            "PanelImage2.png",
            "PanelImage3.png"
        ],
    },


    # =========================================================================
    # ABOUT SECTION (Who Are We)
    # =========================================================================
    # Element: Text section describing the service
    # File: templates/home.html - about section

    'about': {

        # SECTION TITLE
        # Element: Heading text for the about section
        'title': "Who are we?",

        # DESCRIPTION TEXT
        # Element: Paragraph text explaining your service
        # Can be as long as needed - will wrap automatically
        'description': "Introducing the first marketing tool that lets you send ads across multiple Discord servers at once, saving time, cutting costs, and giving you total control. No more waiting on marketing teams or wasting money on marketing services. Send ads instantly, track results in real time, and remove underperformers from your workflow. Do it yourself with a single click, or upgrade to our Business Plan to manage a team using our panel, assign ads, and gain detailed insights on each members performance. Marketing, simplified, powerful, and designed to deliver results.",
    },
}
