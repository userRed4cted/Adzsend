# ==============================================
# BRIDGE PAGE CONFIGURATION
# ==============================================
# This file controls the content on the bridge page.
# ==============================================

# ==========================================
# HERO SECTION
# ==========================================
# Title (same style as homepage hero title)
BRIDGE_TITLE = "ADZSEND BRIDGE"

# Description (same style as homepage hero description)
BRIDGE_DESCRIPTION = "Use Adzsend Bridge to start messaging with Discord effectively, without interruptions. Use on any device, from anywhere in the world!"

# Download URLs for the bridge application (per OS)
BRIDGE_DOWNLOAD_URLS = {
    'windows': "",  # Windows x64
    'macos': "",    # macOS (universal - Intel + Apple Silicon)
    'linux': "",    # Linux x64
}

# ==========================================
# FEATURE PILLS
# ==========================================
# Similar to homepage pills but with modified styling:
# - No background
# - Media at 70% width, 30% taller
# - Media positioned at outer edge (not centered)

BRIDGE_FEATURE_PILLS = [
    {
        'title': "DOWNLOAD FOR DESKTOP",
        'description': "Bridge connects your Discord accounts effortlessly. Send messages across multiple servers without interruption or switching between accounts.",
        'image': "DiscordPcImageThing.png",
        # Image position offset in pixels (positive = right/down, negative = left/up)
        'image_offset_x': 0,  # Horizontal offset in pixels
        'image_offset_y': 0,  # Vertical offset in pixels
        # Gradient background behind the image (same options as homepage pills)
        'bg_gradient_start': "#38EE81",
        'bg_gradient_end': "#BAFDE5",
        'gradient_rotation': 0,  # Angle in degrees (0 = top to bottom, 90 = left to right)
        # Buttons under description
        # Each button has: text, icon (image filename in static folder), url (use ~/path for internal links), and optional 'download': True
        'buttons': [
            {'text': "Download for Windows", 'icon': "AppleLogo.png", 'url': "", 'download': True},
            {'text': "Download for MacOS", 'icon': "WindowsLogo.png", 'url': "", 'download': True},
            {'text': "Download for Linux (.deb)", 'icon': "LinuxLogo.png", 'url': "", 'download': True},
            {'text': "Download for Linux (.tar.gz)", 'icon': "LinuxLogo.png", 'url': "", 'download': True},
        ],
    },
    {
        'title': "COMPATIBILITY",
        'description': "Download the bridge on any compatable device system. No need for anything else or Discord installed, just a device with a stable internet connection. Time to make use of your old laptop!",
        'image': "DiscordPcImageThing.png",
        'image_offset_x': 0,
        'image_offset_y': 0,
        'bg_gradient_start': "#ff6bda",
        'bg_gradient_end': "#ffb8ec",
        'gradient_rotation': 135,
    },
    {
        'title': "CROSS-DEVICE SUPPORT",
        'description': "Access Bridge from any device, anywhere in the world. Your marketing campaigns continue running regardless of where you are.",
        'image': "DiscordPcImageThing.png",
        'image_offset_x': 0,
        'image_offset_y': 0,
        'bg_gradient_start': "#ff6bda",
        'bg_gradient_end': "#ffb8ec",
        'gradient_rotation': 135,
    },
]
