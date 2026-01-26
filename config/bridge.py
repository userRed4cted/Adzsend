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

# Download URLs for the bridge application (per OS and architecture)
BRIDGE_DOWNLOAD_URLS = {
    'windows_x64': "https://github.com/userRed4cted/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup-x64.exe",
    'windows_arm64': "https://github.com/userRed4cted/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup-arm64.exe",
    'macos': "https://github.com/userRed4cted/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup.dmg",  # Universal (Intel + Apple Silicon)
    'linux_x64': "https://github.com/userRed4cted/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup-x64.deb",
    'linux_arm64': "https://github.com/userRed4cted/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup-arm64.deb",
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
        'description': "Send messages all across Discord without interruption, from anywhere, at any time. We're new in town so please forgive us for any bugs you may encounter, placeholders, etc!",
        'image': "DiscordDesktopRandomimage.png",
        # Image offset in pixels from center (positive = right/down, negative = left/up)
        'image_offset_x': 90,  # Horizontal offset (px)
        'image_offset_y': 90,  # Vertical offset (px)
        # Gradient background behind the image (same options as homepage pills)
        'bg_gradient_start': "#38EE81",
        'bg_gradient_end': "#BAFDE5",
        'gradient_rotation': 180,  # Angle in degrees (0 = top to bottom, 90 = left to right)
        # Buttons under description
        # Each button has: text, icon (image filename in static folder), url (use ~/path for internal links), and optional 'download': True
        'buttons': [
             {'text': "MacOS", 'icon': "AppleLogo.png", 'url': "https://github.com/userRed4cted/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup.dmg", 'download': True},
            {'text': "Windows (x64)", 'icon': "WindowsLogo.png", 'url': "https://github.com/userRed4cted/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup-x64.exe", 'download': True},
            {'text': "Windows (ARM64)", 'icon': "WindowsLogo.png", 'url': "https://github.com/userRed4cted/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup-arm64.exe", 'download': True},
            {'text': "Linux (.deb)", 'icon': "LinuxLogo.png", 'url': "https://github.com/userRed4cted/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup.deb", 'download': True},
            {'text': "Linux (.tar.gz)", 'icon': "LinuxLogo.png", 'url': "https://github.com/userRed4cted/Adzsend/releases/download/bridge-v1.0.0/AdzsendBridgeSetup.tar.gz", 'download': True},
        ],
    },
    {
        'title': "COMPATIBILITY",
        'description': "Download the bridge on any compatible device. No need for anything else or even Discord installed, just a device with a stable internet connection. Time to make use of your old laptop!",
        'image': "placeholderimagething.png",
        # Image offset in pixels from center (positive = right/down, negative = left/up)
        'image_offset_x': 0,  # Horizontal offset (px)
        'image_offset_y': 0,  # Vertical offset (px)
        'bg_gradient_start': "#5865F2",
        'bg_gradient_end': "#DADDF8",
        'gradient_rotation': 135,
    },
    {
        'title': "SIMPLE SETUP",
        'description': "Just download and activate Adzsend Bridge, and you're all set to start sending! No complicated setups or difficult configurations.",
        'image': "placeholderimagething.png",
        # Image offset in pixels from center (positive = right/down, negative = left/up)
        'image_offset_x': 0,  # Horizontal offset (px)
        'image_offset_y': 0,  # Vertical offset (px)
        'bg_gradient_start': "#ff6bda",
        'bg_gradient_end': "#ffb8ec",
        'gradient_rotation': 135,
    },
]
