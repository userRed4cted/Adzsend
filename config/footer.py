# Footer Configuration
# Centralized footer settings - sections list from right to left

# Footer logo (relative to static folder)
FOOTER_LOGO = "favicon.ico"

# Footer background gradient (same as view-pricing-btn)
FOOTER_BACKGROUND = "linear-gradient(to bottom, #15d8bc, #006e59)"

# Section title color
FOOTER_SECTION_TITLE_COLOR = "#222225"

# Link text color
FOOTER_LINK_COLOR = "#121215"

# Link hover underline
FOOTER_LINK_HOVER_UNDERLINE = True

# Footer sections - listed from right to left
# Use ~/path for relative links (will use current domain)
# Use full URL for external links
FOOTER_SECTIONS = [
    {
        "title": "Policies",
        "links": [
            {"text": "Terms", "url": "~/terms"},
            {"text": "Guidelines", "url": "~/guidelines"},
            {"text": "Paid Services Terms", "url": "~/terms/paid-services-terms"},
        ]
    },
    {
        "title": "Resources",
        "links": [
            {"text": "How to obtain account Discord token", "url": "#", "lightbox": "TokenTutorial.mp4"},
        ]
    },
]
