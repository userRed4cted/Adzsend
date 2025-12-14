# =============================================================================
# MAIN SITE CONFIGURATION
# =============================================================================
# This file contains global settings that affect the entire website.
# These settings are applied site-wide and cannot be overridden per-page.
# =============================================================================


# -----------------------------------------------------------------------------
# TYPOGRAPHY
# -----------------------------------------------------------------------------
# Font settings for the entire site

# Primary font family - used for all text on the site
# You can use:
#   - System fonts: 'Arial', 'Helvetica', 'Georgia', etc.
#   - Google Fonts: 'Inter', 'Roboto', 'Open Sans', etc. (must be imported in CSS)
#   - Font stacks: "'Inter', 'Segoe UI', sans-serif"
SITE_FONT = "'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif"

# Heading font family - used for h1, h2, h3, etc.
# Set to None to use SITE_FONT for headings too
HEADING_FONT = None

# Code/monospace font - used for code blocks and technical text
CODE_FONT = "'Fira Code', 'Consolas', 'Monaco', monospace"

# Base font size (in pixels) - other sizes scale from this
BASE_FONT_SIZE = 16

# Line height multiplier - affects readability
LINE_HEIGHT = 1.5


# -----------------------------------------------------------------------------
# SITE METADATA
# -----------------------------------------------------------------------------
# Basic site information used in various places

# Site name - used in page titles, emails, etc.
SITE_NAME = 'Borz Marketing Panel'

# Site description - used for SEO meta tags
SITE_DESCRIPTION = 'Discord marketing automation panel'

# Copyright text - shown in footer
COPYRIGHT_TEXT = '2024 Borz Marketing Panel'


# -----------------------------------------------------------------------------
# LAYOUT
# -----------------------------------------------------------------------------
# Global layout settings

# Maximum content width (in pixels)
MAX_CONTENT_WIDTH = 1400

# Default border radius for cards, buttons, inputs (in pixels)
BORDER_RADIUS = 8

# Default spacing unit (in pixels) - used for margins/padding
SPACING_UNIT = 16


# -----------------------------------------------------------------------------
# ANIMATION
# -----------------------------------------------------------------------------
# Global animation settings

# Enable/disable animations site-wide
ANIMATIONS_ENABLED = True

# Default transition duration (in milliseconds)
TRANSITION_DURATION = 300

# Default easing function
TRANSITION_EASING = 'ease-in-out'
