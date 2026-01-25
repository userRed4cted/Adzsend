# ==============================================
# SUPPORT PAGE CONFIGURATION
# ==============================================
# This file controls the FAQ section on the support page.
# ==============================================

# ==========================================
# SUPPORT PAGE TEXT
# ==========================================
SUPPORT_HERO_TITLE = "Need help?\nWe've got your back."
SUPPORT_FAQ_TITLE = "Frequent topics:"
SUPPORT_CONTACT_TEXT = "Still cant find answers for your problem? Contact our support team."

# ==========================================
# FAQ ITEMS
# ==========================================
# Each FAQ item has a question, answer, and optional gradient styling
# Gradient options (same as homepage pills):
#   - gradient: True/False (default: False uses solid color_start)
#   - color_start: Start color or solid color
#   - color_end: End color (ignored if gradient is False)
#   - gradient_rotation: Angle in degrees (default: 135)
FAQ_ITEMS = [
    {
        'question': 'Encounter a bug, glitch, or something happened which wasent supposed to happen?',
        'answer': 'Please contact our support team so we can adress the issue. We thank all users who take their time to report issues, so we can improve everyones experience.',
        'gradient': True,
        'color_start': 'rgba(255, 255, 255, 0.1)',
        'color_end': 'rgba(255, 255, 255, 0.02)',
        'gradient_rotation': 135,
    },
    {
        'question': 'How to adjust your subscriptions?',
        'answer': 'Go to settings, billing, and press Adjust plan.',
        'gradient': True,
        'color_start': 'rgba(255, 255, 255, 0.02)',
        'color_end': 'rgba(255, 255, 255, 0.1)',
        'gradient_rotation': 135,
    },
    {
        'question': 'Account mistakenly flagged or suspended?',
        'answer': 'If the system detects content in violation of the Community Guidelines multiple times then your account will be automatically suspended, to appeal contact our support team. Account standing can be found in settings.',
        'gradient': True,
        'color_start': 'rgba(255, 255, 255, 0.1)',
        'color_end': 'rgba(255, 255, 255, 0.02)',
        'gradient_rotation': 135,
    },
    {
        'question': 'Want to report someone?',
        'answer': 'Only report if the user is violating our [Community Guidelines](~/guidelines), and [other policies](~/terms). Before reporting make sure, with evidence that the user is using our services. You may use the Discord mesage link search bar above to see if messages were sent via Adzsend.',
        'gradient': True,
        'color_start': 'rgba(255, 255, 255, 0.02)',
        'color_end': 'rgba(255, 255, 255, 0.1)',
        'gradient_rotation': 135,
    },
]
