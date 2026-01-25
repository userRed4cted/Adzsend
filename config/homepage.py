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
