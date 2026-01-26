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
        'title': "THE ULTIMATE DISCORD MARKETING SYSTEM",

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
            'title': "SEND MESSAGES INSTANTLY",
            # Description (same style as terms text)
            'description': "No more hours of copy and pasting, do it all with one button press. Send messages all across discord with a button press. No more wasting time.",
            # Video (looped mp4) or image - use 'video' key for mp4, 'image' key for static images
            'video': "placeholderimagething2.mp4",
            # Background color or gradient
            'gradient': True,  # Set to False for solid color
            'color_start': "rgba(255, 255, 255, 0.1)",  # Start color (or solid color if gradient is False)
            'color_end': "rgba(255, 255, 255, 0.02)",   # End color (ignored if gradient is False)
            'gradient_rotation': 135,  # Gradient angle in degrees (0 = top to bottom, 90 = left to right)
        },
        {
            'title': "CONTROL & POWER",
            'description': "Everyone desires power, start controlling your marketing campaigns, instead of letting people control them for you. Overpaying marketing services that take long and result in minimal results, NO MORE!: with Adzsend.",
            'video': "placeholderimagething2.mp4",
            'gradient': True,
            'color_start': "rgba(255, 255, 255, 0.02)",
            'color_end': "rgba(255, 255, 255, 0.1)",
            'gradient_rotation': 135,
        },
        {
            'title': "SPEED",
            'description': "Connect multiple Discord accounts, and send at the same time. No more long waits.",
            'video': "placeholderimagething2.mp4",
            'gradient': True,
            'color_start': "rgba(255, 255, 255, 0.1)",
            'color_end': "rgba(255, 255, 255, 0.02)",
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
