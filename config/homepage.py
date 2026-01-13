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

        # HERO IMAGE
        # Element: Image displayed at the top (e.g., favicon or logo)
        # Image must be placed in: static/ folder
        # Format: Just the filename (e.g., "favicon.png")
        'hero_image': "favicon.png",

        # SLIDESHOW MESSAGES
        # Element: Large rotating text in center of hero section
        # These messages cycle automatically based on interval setting
        # Add/remove as many as you want
        'slideshow_messages': [
            "Stop wasting time copy and pasting messages, time is money",
            "Tired of expensive marketing services where you cant monitor, customise, or have control over your marketing?",
            "Lazy? Not a problem",
            "What used to take hours, now takes seconds with Adzsend"
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

        # DISCORD SERVER URL
        # Element: Link for "Our Discord server" button
        # Opens in a new tab when clicked
        'discord_server_url': "https://discord.gg/KWt6rvCukp",

        # PANEL IMAGES
        # Element: 3 images displayed below the CTA button with rotation effect
        # Images must be placed in: static/ folder
        # Format: Just the filename (e.g., "PanelImage1.png")
        # Order: [left_image, center_image, right_image]
        'panel_images': [
            "PanelImage1.png",
            "PanelImage2.png",
            "PanelImage1.png"
        ],

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
           # "PanelImage3.png"
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
        'description': "Introducing the only marketing system you will ever need, allowing you send ads across multiple Discord servers at once, saving time, cutting costs, and giving you total control. No more waiting on marketing teams or wasting money on marketing services. Send ads instantly, track results in real time, and remove underperformers from your workflow. Do it yourself with a single click, or upgrade to our Team Plans to manage a team using our panel, assign messages, and gain detailed insights on each members performance. Marketing, simplified, powerful, and designed to deliver results.",
    },


    # =========================================================================
    # WHY DISCORD SECTION (Why use Discord to market?)
    # =========================================================================
    # Element: Section explaining benefits of Discord marketing with stats
    # File: templates/home.html - why discord section

    'why_discord': {

        # SECTION TITLE
        # Element: Heading text for the section
        'title': "Why use Discord for marketing?",

        # DISCORD STATISTICS
        # Element: Stats displayed in a row showing Discord's reach
        'stats': [
            {
                'value': "250M+",
                'label': "Monthly Active Users",
            },
            {
                'value': "21M+",
                'label': "Active Servers",
            },
            {
                'value': "650M+",
                'label': "Registered Accounts",
            },
        ],

        # BENEFITS LIST
        # Element: List of key benefits displayed as cards/points
        # Each item has a title and description
        'benefits': [
            {
                'title': "Engaged Communities",
                'description': "Discord servers are highly engaged communities where members actively participate in discussions."
            },
            {
                'title': "Targeted Audiences",
                'description': "Reach specific niches and demographics through specialized servers related to your product or service."
            },
            {
                'title': "Direct Communication",
                'description': "Connect directly with potential customers without algorithmic barriers or paid promotion requirements."
            },
            {
                'title': "Growing Platform",
                'description': "Discord continues to grow rapidly, expanding beyond gaming into business, education, and social communities."
            }
        ],
    },
}
