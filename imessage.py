"""
iMessage sender using AppleScript.
"""
import subprocess


def send_imessage(phone: str, message: str) -> dict:
    """
    Send an iMessage to a phone number.

    Args:
        phone: Phone number (e.g., "+1234567890")
        message: Message text to send

    Returns:
        dict with 'success' bool and 'error' string if failed
    """
    # Escape double quotes and backslashes in message
    escaped_message = message.replace('\\', '\\\\').replace('"', '\\"')

    applescript = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{phone}" of targetService
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
            return {
                'success': False,
                'error': result.stderr.strip() or 'AppleScript failed'
            }

        return {'success': True}

    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Timeout - Messages app may not be responding'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def check_messages_app() -> bool:
    """Check if Messages app is available."""
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
    except:
        return False
