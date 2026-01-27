# ==============================================
# EMAIL SERVICE - Resend Integration
# ==============================================
# Handles sending verification emails via Resend API
# ==============================================

import os
import requests

# Resend configuration
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
FROM_EMAIL = os.getenv('FROM_EMAIL', 'Adzsend <noreply@adzsend.com>')


def send_verification_email(to_email, code, purpose='login'):
    """Send verification code email via Resend.

    Args:
        to_email: Recipient email address
        code: 6-digit verification code
        purpose: 'login', 'signup', or 'email_change'

    Returns:
        (success: bool, error_message: str or None)
    """
    if not RESEND_API_KEY:
        # Development mode - skip sending
        return True, None

    subject = f'Adzsend Verification Code: {code}'
    text_content = f'''Enter this code:

{code}

Don't share this code or email with anyone. If you didn't request verification, you can safely ignore this.'''

    try:
        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'from': FROM_EMAIL,
                'to': [to_email],
                'subject': subject,
                'text': text_content
            },
            timeout=10
        )

        if response.status_code == 200:
            return True, None
        else:
            error_data = response.json()
            error_msg = error_data.get('message', f'HTTP {response.status_code}')
            return False, error_msg

    except requests.exceptions.Timeout:
        return False, "Email service timeout"
    except Exception as e:
        return False, str(e)
