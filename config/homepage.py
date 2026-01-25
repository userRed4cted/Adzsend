# =============================================================================
# HOMEPAGE CONFIGURATION
# =============================================================================
# This file controls all content displayed on the homepage (home.html).
# Each setting is documented with what it does and which UI element it affects.
# =============================================================================


HOMEPAGE = {

    # =========================================================================
    # GENERAL SETTINGS
    # =========================================================================

    # DISCORD SERVER URL
    # Element: Link to your Discord server (used on support page, etc.)
    'discord_server_url': "https://discord.gg/KWt6rvCukp",

    # =========================================================================
    # HERO SECTION
    # =========================================================================
    # The main landing area at the top of the homepage

    'hero': {
        # Main title (uses ABC Ginto Nord font, same as support page title)
        'title': "The Ultimate Discord Marketing System",

        # Description text below title (same style as FAQ title in support)
        'description': "Send ads across multiple Discord servers at once. Save time, cut costs, and take total control.",

        # CTA button text
        'cta_text': "Try for free!",

        # Showcase image below the CTA button (place in static folder)
        'showcase_image': "AdzsendShowcaseHomepageImage.png",
    },

    # =========================================================================
    # FEATURE PILLS
    # =========================================================================
    # Pill-shaped feature sections with alternating image/text layout
    # First pill: text left, image right
    # Second pill: image left, text right
    # And so on...

    'feature_pills': [
        {
            # Title (same style as terms subheader)
            'title': "Send Ads Instantly",
            # Description (same style as terms text)
            'description': "No more waiting on marketing teams or wasting money on expensive services. Send ads to multiple servers with a single click.",
            # Video (looped mp4) or image - use 'video' key for mp4, 'image' key for static images
            'video': "6257adef93867e50d84d30e2_6787b62a9742f59453ba8919_Discord_Websote_Refresh_Emojis2_EN-transcode (1).mp4",
            # Background color or gradient
            'gradient': True,  # Set to False for solid color
            'color_start': "rgba(255, 255, 255, 0.1)",  # Start color (or solid color if gradient is False)
            'color_end': "rgba(255, 255, 255, 0.05)",   # End color (ignored if gradient is False)
            'gradient_rotation': 135,  # Gradient angle in degrees (0 = top to bottom, 90 = left to right)
        },
        {
            'title': "Track Performance",
            'description': "Monitor your campaigns in real time. See which servers perform best and remove underperformers from your workflow.",
            'video': "6257adef93867e50d84d30e2_6763b611120b46189e164b4a_Discord_Website_Refresh_EN-transcode.mp4",
            'gradient': True,
            'color_start': "rgba(255, 255, 255, 0.1)",
            'color_end': "rgba(255, 255, 255, 0.05)",
            'gradient_rotation': 135,
        },
        {
            'title': "Manage Your Team",
            'description': "Upgrade to Team Plans to manage a team using our panel. Assign messages, track member performance, and gain detailed insights.",
            'video': "6257adef93867e50d84d30e2_6787b62a9742f59453ba8919_Discord_Websote_Refresh_Emojis2_EN-transcode (1).mp4",
            'gradient': True,
            'color_start': "rgba(255, 255, 255, 0.1)",
            'color_end': "rgba(255, 255, 255, 0.05)",
            'gradient_rotation': 135,
        },
    ],

    # =========================================================================
    # WHY DISCORD SECTION
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
