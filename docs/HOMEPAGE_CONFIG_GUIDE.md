# Homepage Configuration Guide

## Config File Location
**File to edit:** `config/homepage.py`

This file controls all text and settings for the homepage.

## Configuration Structure

The homepage config is organized into sections:

```python
HOMEPAGE = {
    'hero': { ... },      # Main landing section
    'gallery': { ... },   # Panel images showcase
    'about': { ... },     # Who are we section
}
```

## Hero Section

The hero section is the first thing visitors see.

```python
'hero': {
    # Slideshow messages that rotate automatically
    'slideshow_messages': [
        "Message 1",
        "Message 2",
        "Message 3"
    ],

    # Time between slides in milliseconds (5000 = 5 seconds)
    'slideshow_interval': 5000,

    # Fade animation duration in milliseconds (600 = 0.6 seconds)
    'slideshow_fade_duration': 600,

    # Call-to-action button text
    'cta_button_text': "View Pricing",

    # Scroll indicator text (shown at bottom of hero)
    'scroll_indicator_text': "Scroll down to view more",
}
```

### Slideshow Settings

| Setting | Description | Recommended |
|---------|-------------|-------------|
| `slideshow_interval` | Time between slides (ms) | 4000-6000 |
| `slideshow_fade_duration` | Fade animation length (ms) | 300-600 |
| `slideshow_messages` | Array of text strings | 2-5 messages |

## Gallery Section

Shows screenshots/images of the panel.

```python
'gallery': {
    'title': "Panel Images",
    'images': [
        "PanelImage1.png",
        "PanelImage2.png",
        "PanelImage3.png"
    ],
}
```

**Note:** Images should be placed in the `static/` folder.

## About Section

Describes your service to visitors.

```python
'about': {
    'title': "Who are we?",
    'description': "Your description text here...",
}
```

## Tips

1. **Slideshow messages**: Keep concise for readability
2. **Timing**: Match interval to message length (longer messages = longer interval)
3. **Images**: Use consistent dimensions for gallery images
4. **Testing**: Refresh the homepage after changes to see updates
