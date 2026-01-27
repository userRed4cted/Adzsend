# ==============================================
# EMAIL SERVICE - Resend Integration
# ==============================================
# Handles sending verification emails via Resend API
# ==============================================

import os
import urllib.request
import urllib.error
import json

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
    print(f"[EMAIL] API key set: {bool(RESEND_API_KEY)}, from: {FROM_EMAIL}", flush=True)

    if not RESEND_API_KEY:
        # Development mode - skip sending
        print("[EMAIL] No API key, skipping (dev mode)", flush=True)
        return True, None

    subject = f'Adzsend Verification Code: {code}'
    text_content = f'''Enter this code:

{code}

Don't share this code or email with anyone. If you didn't request verification, you can safely ignore this.'''

    try:
        # Use urllib instead of requests to avoid recursion issues on Render
        payload = json.dumps({
            'from': FROM_EMAIL,
            'to': [to_email],
            'subject': subject,
            'text': text_content
        }).encode('utf-8')

        print(f"[EMAIL] Sending to {to_email}", flush=True)

        req = urllib.request.Request(
            'https://api.resend.com/emails',
            data=payload,
            headers={
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json',
                'User-Agent': 'Adzsend/1.0'
            },
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"[EMAIL] Response status: {response.status}", flush=True)
            if response.status == 200:
                return True, None
            else:
                error_data = json.loads(response.read().decode('utf-8'))
                error_msg = error_data.get('message', f'HTTP {response.status}')
                print(f"[EMAIL] Error: {error_msg}", flush=True)
                return False, error_msg

    except urllib.error.HTTPError as e:
        try:
            raw_response = e.read().decode('utf-8')
            print(f"[EMAIL] HTTPError raw response: {raw_response}", flush=True)
            error_data = json.loads(raw_response)
            error_msg = error_data.get('message', f'HTTP {e.code}')
        except Exception as parse_err:
            print(f"[EMAIL] Parse error: {parse_err}", flush=True)
            error_msg = f'HTTP {e.code}'
        print(f"[EMAIL] HTTPError: {error_msg}", flush=True)
        return False, error_msg
    except urllib.error.URLError as e:
        print(f"[EMAIL] URLError: {e.reason}", flush=True)
        if 'timed out' in str(e.reason).lower():
            return False, "Email service timeout"
        return False, str(e.reason)
    except Exception as e:
        print(f"[EMAIL] Exception: {e}", flush=True)
        return False, str(e)
