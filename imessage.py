"""
iMessage sender using AppleScript with proper injection protection.
"""
import subprocess
import re


def escape_applescript_string(text: str) -> str:
    """
    Safely escape a string for use in AppleScript.

    AppleScript strings use backslash escapes:
    - \\ for literal backslash
    - \" for literal quote
    - \r for carriage return
    - \n for newline (in some contexts)
    """
    if not text:
        return ""

    # First escape backslashes, then quotes
    escaped = text.replace('\\', '\\\\')
    escaped = escaped.replace('"', '\\"')
    # Escape carriage returns and newlines
    escaped = escaped.replace('\r', '\\r')
    escaped = escaped.replace('\n', '\\n')
    # Remove any other control characters that could cause issues
    escaped = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', escaped)

    return escaped


def validate_phone_for_applescript(phone: str) -> tuple[bool, str]:
    """
    Validate and sanitize phone number for AppleScript.
    Only allows digits, +, -, spaces, parentheses.
    """
    if not phone:
        return False, "Phone number required"

    # Only allow safe characters
    if not re.match(r'^[\d\+\-\s\(\)\.]+$', phone):
        return False, "Invalid phone number characters"

    # Remove formatting, keep only digits and +
    cleaned = re.sub(r'[^\d\+]', '', phone)

    if len(cleaned) < 10 or len(cleaned) > 16:
        return False, "Phone number must be 10-16 digits"

    return True, cleaned


def send_imessage(phone: str, message: str) -> dict:
    """
    Send an iMessage to a phone number.

    Args:
        phone: Phone number (e.g., "+1234567890")
        message: Message text to send

    Returns:
        dict with 'success' bool and 'error' string if failed
    """
    # Validate phone
    valid, phone_result = validate_phone_for_applescript(phone)
    if not valid:
        return {'success': False, 'error': phone_result}

    # Validate message
    if not message or not message.strip():
        return {'success': False, 'error': 'Message cannot be empty'}

    if len(message) > 10000:
        return {'success': False, 'error': 'Message too long (max 10000 characters)'}

    # Escape message content for AppleScript
    escaped_message = escape_applescript_string(message)
    escaped_phone = escape_applescript_string(phone_result)

    # Build AppleScript with properly escaped strings
    applescript = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{escaped_phone}" of targetService
        send "{escaped_message}" to targetBuddy
    end tell
    '''

    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() or 'AppleScript failed'
            # Don't expose internal errors to users
            if 'execution error' in error_msg.lower():
                return {'success': False, 'error': 'Failed to send message. Check Messages app is running.'}
            return {'success': False, 'error': error_msg}

        return {'success': True}

    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Timeout - Messages app may not be responding'}
    except FileNotFoundError:
        return {'success': False, 'error': 'osascript not found - macOS required'}
    except Exception as e:
        # Log the actual error internally, return generic message
        print(f"iMessage send error: {e}")
        return {'success': False, 'error': 'Failed to send message'}


def check_messages_app() -> bool:
    """Check if Messages app is available and running."""
    applescript = '''
    tell application "System Events"
        return exists (application process "Messages")
    end tell
    '''
    try:
        result = subprocess.run(
            ['osascript', '-e', applescript],
            capture_output=True,
            text=True,
            timeout=5
        )
        return 'true' in result.stdout.lower()
    except Exception:
        return False


def get_imessage_status() -> dict:
    """Get iMessage service status."""
    try:
        # Check if Messages app exists
        app_check = subprocess.run(
            ['osascript', '-e', 'tell application "System Events" to return exists (application process "Messages")'],
            capture_output=True,
            text=True,
            timeout=5
        )
        app_running = 'true' in app_check.stdout.lower()

        return {
            'available': True,
            'app_running': app_running,
            'error': None
        }
    except FileNotFoundError:
        return {
            'available': False,
            'app_running': False,
            'error': 'macOS required for iMessage'
        }
    except Exception as e:
        return {
            'available': False,
            'app_running': False,
            'error': str(e)
        }
