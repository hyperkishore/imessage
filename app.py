"""
iMessage Auto-Sender Webapp
Send iMessages from Google Sheet data with template support.
"""
import csv
import io
import os
import re
import sys
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from markupsafe import escape

from imessage import send_imessage
from database import (
    get_sender, save_sender,
    register_agent, get_agent_by_token, get_all_agents,
    update_agent_heartbeat, get_pending_messages, update_message_status,
    queue_message
)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# === CORS Configuration (for React dev server) ===
CORS(app, supports_credentials=True, origins=[
    'http://localhost:5173',
    'http://127.0.0.1:5173'
])

# === Security Configuration ===

# Session secret - MUST be persistent (not random on each restart)
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    print("ERROR: SECRET_KEY environment variable is required!")
    print("Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\"")
    print("Add it to your .env file: SECRET_KEY=your-generated-key")
    sys.exit(1)

app.secret_key = SECRET_KEY

# CSRF Protection
csrf = CSRFProtect(app)

# Rate Limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Password configuration
APP_PASSWORD = os.environ.get('IMESSAGE_PASSWORD', '').strip()
if not APP_PASSWORD:
    print("WARNING: No IMESSAGE_PASSWORD set. Please set a strong password in .env")
    print("Using temporary password: 'changeme' (CHANGE THIS!)")
    APP_PASSWORD = 'changeme'
elif len(APP_PASSWORD) < 8:
    print("WARNING: Password should be at least 8 characters for security")

# Debug mode
DEBUG_MODE = os.environ.get('FLASK_ENV', 'development') == 'development'


# === Input Validation ===

def validate_phone(phone: str) -> tuple[bool, str]:
    """Validate phone number format."""
    if not phone:
        return False, "Phone number is required"
    # Remove common formatting
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    # Must start with + or digit, be 10-15 chars
    if not re.match(r'^[\+]?[0-9]{10,15}$', cleaned):
        return False, "Invalid phone format. Use: +1234567890 or 1234567890"
    return True, cleaned


def validate_message(message: str, max_length: int = 5000) -> tuple[bool, str]:
    """Validate message content."""
    if not message:
        return False, "Message is required"
    if len(message) > max_length:
        return False, f"Message too long (max {max_length} characters)"
    return True, message.strip()


def validate_sheet_url(url: str) -> tuple[bool, str]:
    """Validate Google Sheets URL."""
    if not url:
        return False, "Sheet URL is required"
    if not re.match(r'^https://docs\.google\.com/spreadsheets/d/[a-zA-Z0-9_-]+', url):
        return False, "Invalid Google Sheets URL"
    return True, url


# === Decorators ===

def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            if request.is_json:
                return jsonify({'error': 'Not authenticated'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def sender_required(f):
    """Decorator to require sender profile setup."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not get_sender():
            return redirect(url_for('setup'))
        return f(*args, **kwargs)
    return decorated_function


# === Helper Functions ===

def sheet_url_to_csv(url: str) -> str:
    """Convert Google Sheet URL to CSV export URL."""
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not match:
        raise ValueError('Invalid Google Sheet URL')

    sheet_id = match.group(1)
    gid_match = re.search(r'gid=(\d+)', url)
    gid = gid_match.group(1) if gid_match else '0'

    return f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'


def fetch_sheet_data(url: str, max_rows: int = 1000) -> tuple[list[str], list[dict]]:
    """Fetch and parse Google Sheet as CSV with row limit."""
    csv_url = sheet_url_to_csv(url)
    response = requests.get(csv_url, timeout=30)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text))
    headers = reader.fieldnames or []
    rows = []
    for i, row in enumerate(reader):
        if i >= max_rows:
            break
        rows.append(row)

    return headers, rows


def render_template_message(template: str, row: dict) -> str:
    """Replace {variable} placeholders with row values (case-insensitive)."""
    row_lower = {k.lower(): v for k, v in row.items()}

    def replace_var(match):
        var_name = match.group(1).lower()
        return str(row_lower.get(var_name, match.group(0)) or '')

    return re.sub(r'\{(\w+)\}', replace_var, template)


# === Make CSRF token available to templates ===
@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=generate_csrf)


# === Routes ===

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """Login page with rate limiting."""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == APP_PASSWORD:
            session['authenticated'] = True
            session.permanent = True
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid password')
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect(url_for('login'))


# === SPA-friendly JSON API endpoints ===

@app.route('/api/csrf-token')
def api_csrf_token():
    """Get CSRF token for SPA usage."""
    return jsonify({'csrf_token': generate_csrf()})


@app.route('/api/login', methods=['POST'])
@limiter.limit("10 per minute")
@csrf.exempt  # Exempt from CSRF for SPA - relies on password auth
def api_login():
    """JSON login endpoint for SPA."""
    data = request.json or {}
    password = data.get('password', '')

    if password == APP_PASSWORD:
        session['authenticated'] = True
        session.permanent = True
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Invalid password'}), 401


@app.route('/api/setup', methods=['POST'])
@login_required
@csrf.exempt  # Exempt from CSRF for SPA - session auth required
def api_setup():
    """JSON setup endpoint for SPA."""
    data = request.json or {}
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()

    # Validate name
    if not name or len(name) < 2:
        return jsonify({'success': False, 'error': 'Name must be at least 2 characters'}), 400
    if len(name) > 100:
        return jsonify({'success': False, 'error': 'Name too long (max 100 characters)'}), 400

    # Validate phone
    valid, result = validate_phone(phone)
    if not valid:
        return jsonify({'success': False, 'error': result}), 400

    save_sender(name, result)
    return jsonify({'success': True})


@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """Sender profile setup page."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()

        # Validate name
        if not name or len(name) < 2:
            return render_template('setup.html', error='Name must be at least 2 characters')
        if len(name) > 100:
            return render_template('setup.html', error='Name too long (max 100 characters)')

        # Validate phone
        valid, result = validate_phone(phone)
        if not valid:
            return render_template('setup.html', error=result)

        save_sender(name, result)
        return redirect(url_for('index'))

    sender = get_sender()
    return render_template('setup.html', sender=sender)


@app.route('/')
@login_required
@sender_required
def index():
    sender = get_sender()
    return render_template('index.html', sender=sender)


@app.route('/api/sender')
@login_required
def api_sender():
    """Get current sender info."""
    sender = get_sender()
    if not sender:
        return jsonify({'error': 'No sender configured'}), 404
    return jsonify(sender)


@app.route('/preview', methods=['POST'])
@login_required
@limiter.limit("20 per minute")
@csrf.exempt  # SPA uses session auth
def preview():
    """Fetch sheet and preview messages."""
    data = request.json or {}
    sheet_url = data.get('sheet_url', '').strip()
    template = data.get('template', '').strip()

    # Validate inputs
    valid, result = validate_sheet_url(sheet_url)
    if not valid:
        return jsonify({'error': result}), 400

    valid, result = validate_message(template, max_length=2000)
    if not valid:
        return jsonify({'error': result}), 400

    try:
        headers, rows = fetch_sheet_data(sheet_url)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except requests.RequestException as e:
        return jsonify({'error': f'Failed to fetch sheet: {e}'}), 400

    headers_lower = [h.lower() for h in headers]
    if 'phone' not in headers_lower:
        return jsonify({'error': 'Sheet must have a "phone" column'}), 400

    previews = []
    for idx, row in enumerate(rows):
        row_lower = {k.lower(): v for k, v in row.items()}
        phone = row_lower.get('phone', '').strip()
        if not phone:
            continue

        # Validate each phone number
        valid, cleaned_phone = validate_phone(phone)
        if not valid:
            continue

        message = render_template_message(template, row)
        previews.append({
            'id': idx,
            'phone': cleaned_phone,
            'name': escape(row_lower.get('name', '')),  # XSS protection
            'message': message,
            'row': {k: escape(v) for k, v in row.items()}  # XSS protection
        })

    return jsonify({
        'headers': [escape(h) for h in headers],
        'previews': previews,
        'count': len(previews)
    })


@app.route('/send-one', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
@csrf.exempt  # SPA uses session auth
def send_one():
    """Send a single message."""
    data = request.json or {}
    phone = data.get('phone', '').strip()
    message = data.get('message', '').strip()

    # Validate inputs
    valid, result = validate_phone(phone)
    if not valid:
        return jsonify({'success': False, 'error': result}), 400

    valid, msg_result = validate_message(message)
    if not valid:
        return jsonify({'success': False, 'error': msg_result}), 400

    result = send_imessage(result, msg_result)
    return jsonify(result)


@app.route('/send-bulk', methods=['POST'])
@login_required
@limiter.limit("5 per minute")
@csrf.exempt  # SPA uses session auth
def send_bulk():
    """Send multiple messages."""
    data = request.json or {}
    messages = data.get('messages', [])

    if not messages:
        return jsonify({'error': 'No messages to send'}), 400

    if len(messages) > 100:
        return jsonify({'error': 'Too many messages (max 100)'}), 400

    results = []
    for msg in messages:
        phone = msg.get('phone', '').strip()
        message = msg.get('message', '').strip()

        # Validate each message
        valid_phone, cleaned_phone = validate_phone(phone)
        valid_msg, cleaned_msg = validate_message(message)

        if not valid_phone or not valid_msg:
            results.append({
                'phone': phone,
                'success': False,
                'error': 'Invalid phone or message'
            })
            continue

        result = send_imessage(cleaned_phone, cleaned_msg)
        results.append({
            'phone': cleaned_phone,
            'success': result['success'],
            'error': result.get('error')
        })

    success_count = sum(1 for r in results if r['success'])
    return jsonify({
        'results': results,
        'success_count': success_count,
        'total': len(results)
    })


# === Phase 2: Agent API endpoints ===

@app.route('/api/agents/register', methods=['POST'])
@limiter.limit("5 per hour")
@csrf.exempt  # Allow external agents to register
def api_register_agent():
    """Register a new agent with rate limiting."""
    data = request.json or {}
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()

    # Validate inputs
    if not name or len(name) < 2:
        return jsonify({'error': 'Name required (min 2 characters)'}), 400
    if len(name) > 100:
        return jsonify({'error': 'Name too long (max 100 characters)'}), 400

    valid, result = validate_phone(phone)
    if not valid:
        return jsonify({'error': result}), 400

    agent_data = register_agent(name, result)
    return jsonify(agent_data)


@app.route('/api/agents/poll', methods=['POST'])
@limiter.limit("60 per minute")
@csrf.exempt  # Allow external agents to poll
def api_agent_poll():
    """Agent heartbeat - returns pending messages."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'error': 'Invalid authorization'}), 401

    token = auth[7:]
    if not token or len(token) < 20:
        return jsonify({'error': 'Invalid token'}), 401

    agent = get_agent_by_token(token)
    if not agent:
        return jsonify({'error': 'Invalid token'}), 401

    update_agent_heartbeat(agent['id'])
    messages = get_pending_messages(agent['id'])

    return jsonify({
        'agent_id': agent['id'],
        'messages': messages
    })


@app.route('/api/agents/report', methods=['POST'])
@limiter.limit("60 per minute")
@csrf.exempt  # Allow external agents to report
def api_agent_report():
    """Agent reports message send status."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'error': 'Invalid authorization'}), 401

    token = auth[7:]
    agent = get_agent_by_token(token)
    if not agent:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.json or {}
    message_id = data.get('message_id')
    status = data.get('status')
    error = data.get('error')

    if not message_id or status not in ('sent', 'failed'):
        return jsonify({'error': 'Invalid request'}), 400

    update_message_status(message_id, status, error)
    return jsonify({'success': True})


@app.route('/api/agents', methods=['GET'])
@login_required
def api_list_agents():
    """List all registered agents."""
    agents = get_all_agents()
    return jsonify(agents)


@app.route('/api/queue', methods=['POST'])
@login_required
@limiter.limit("30 per minute")
@csrf.exempt  # SPA uses session auth
def api_queue_message():
    """Queue a message to be sent by a specific agent."""
    data = request.json or {}
    agent_id = data.get('agent_id')
    recipient_phone = data.get('phone', '').strip()
    message_text = data.get('message', '').strip()

    # Validate agent_id
    if not agent_id or not isinstance(agent_id, int):
        return jsonify({'error': 'Valid agent_id required'}), 400

    # Validate phone
    valid, cleaned_phone = validate_phone(recipient_phone)
    if not valid:
        return jsonify({'error': cleaned_phone}), 400

    # Validate message
    valid, cleaned_msg = validate_message(message_text)
    if not valid:
        return jsonify({'error': cleaned_msg}), 400

    message_id = queue_message(agent_id, cleaned_phone, cleaned_msg)
    return jsonify({'success': True, 'message_id': message_id})


@app.route('/api/queue/bulk', methods=['POST'])
@login_required
@limiter.limit("10 per minute")
@csrf.exempt  # SPA uses session auth
def api_queue_bulk():
    """Queue multiple messages for a specific agent."""
    data = request.json or {}
    agent_id = data.get('agent_id')
    messages = data.get('messages', [])

    if not agent_id or not isinstance(agent_id, int):
        return jsonify({'error': 'Valid agent_id required'}), 400

    if not messages:
        return jsonify({'error': 'Messages required'}), 400

    if len(messages) > 100:
        return jsonify({'error': 'Too many messages (max 100)'}), 400

    queued = []
    for msg in messages:
        phone = msg.get('phone', '').strip()
        text = msg.get('message', '').strip()

        valid_phone, cleaned_phone = validate_phone(phone)
        valid_msg, cleaned_msg = validate_message(text)

        if valid_phone and valid_msg:
            message_id = queue_message(agent_id, cleaned_phone, cleaned_msg)
            queued.append({'phone': cleaned_phone, 'message_id': message_id})

    return jsonify({'success': True, 'queued': len(queued), 'messages': queued})


# === Health Check ===

@app.route('/health')
@csrf.exempt
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({'status': 'ok', 'version': '0.5.02'})


if __name__ == '__main__':
    print('Starting iMessage Auto-Sender...')
    print(f'Debug mode: {DEBUG_MODE}')
    print('Open http://127.0.0.1:5001 in your browser')
    if APP_PASSWORD == 'changeme':
        print('WARNING: Using default password. Set IMESSAGE_PASSWORD in .env')
    app.run(debug=DEBUG_MODE, host='127.0.0.1', port=5001)
