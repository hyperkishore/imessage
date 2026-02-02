"""
iMessage Auto-Sender Webapp
Send iMessages from Google Sheet data with template support.
"""
import csv
import io
import os
import re
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import requests

from imessage import send_imessage
from database import (
    get_sender, save_sender,
    register_agent, get_agent_by_token, get_all_agents,
    update_agent_heartbeat, get_pending_messages, update_message_status,
    queue_message
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Simple password - change this!
APP_PASSWORD = os.environ.get('IMESSAGE_PASSWORD', 'changeme')


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


def sheet_url_to_csv(url: str) -> str:
    """
    Convert Google Sheet URL to CSV export URL.

    Handles formats:
    - https://docs.google.com/spreadsheets/d/SHEET_ID/edit...
    - https://docs.google.com/spreadsheets/d/SHEET_ID/...
    """
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not match:
        raise ValueError('Invalid Google Sheet URL')

    sheet_id = match.group(1)
    gid_match = re.search(r'gid=(\d+)', url)
    gid = gid_match.group(1) if gid_match else '0'

    return f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'


def fetch_sheet_data(url: str) -> tuple[list[str], list[dict]]:
    """Fetch and parse Google Sheet as CSV."""
    csv_url = sheet_url_to_csv(url)
    response = requests.get(csv_url, timeout=30)
    response.raise_for_status()

    reader = csv.DictReader(io.StringIO(response.text))
    headers = reader.fieldnames or []
    rows = list(reader)

    return headers, rows


def render_template_message(template: str, row: dict) -> str:
    """Replace {variable} placeholders with row values (case-insensitive)."""
    row_lower = {k.lower(): v for k, v in row.items()}

    def replace_var(match):
        var_name = match.group(1).lower()
        return str(row_lower.get(var_name, match.group(0)) or '')

    return re.sub(r'\{(\w+)\}', replace_var, template)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == APP_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid password')
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout and clear session."""
    session.clear()
    return redirect(url_for('login'))


@app.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """Sender profile setup page."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()

        if not name or not phone:
            return render_template('setup.html', error='Name and phone are required')

        save_sender(name, phone)
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
def preview():
    """Fetch sheet and preview messages."""
    data = request.json
    sheet_url = data.get('sheet_url', '').strip()
    template = data.get('template', '').strip()

    if not sheet_url:
        return jsonify({'error': 'Sheet URL is required'}), 400
    if not template:
        return jsonify({'error': 'Message template is required'}), 400

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

        message = render_template_message(template, row)
        previews.append({
            'id': idx,
            'phone': phone,
            'name': row_lower.get('name', ''),
            'message': message,
            'row': row
        })

    return jsonify({
        'headers': headers,
        'previews': previews,
        'count': len(previews)
    })


@app.route('/send-one', methods=['POST'])
@login_required
def send_one():
    """Send a single message."""
    data = request.json
    phone = data.get('phone', '').strip()
    message = data.get('message', '').strip()

    if not phone or not message:
        return jsonify({'success': False, 'error': 'Phone and message required'}), 400

    result = send_imessage(phone, message)
    return jsonify(result)


@app.route('/send-bulk', methods=['POST'])
@login_required
def send_bulk():
    """Send multiple messages."""
    data = request.json
    messages = data.get('messages', [])

    if not messages:
        return jsonify({'error': 'No messages to send'}), 400

    results = []
    for msg in messages:
        phone = msg.get('phone', '').strip()
        message = msg.get('message', '').strip()

        if not phone or not message:
            results.append({
                'phone': phone,
                'success': False,
                'error': 'Missing phone or message'
            })
            continue

        result = send_imessage(phone, message)
        results.append({
            'phone': phone,
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
def api_register_agent():
    """Register a new agent."""
    data = request.json
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()

    if not name or not phone:
        return jsonify({'error': 'Name and phone required'}), 400

    result = register_agent(name, phone)
    return jsonify(result)


@app.route('/api/agents/poll', methods=['POST'])
def api_agent_poll():
    """Agent heartbeat - returns pending messages."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'error': 'Invalid authorization'}), 401

    token = auth[7:]
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
def api_agent_report():
    """Agent reports message send status."""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'error': 'Invalid authorization'}), 401

    token = auth[7:]
    agent = get_agent_by_token(token)
    if not agent:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.json
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
def api_queue_message():
    """Queue a message to be sent by a specific agent."""
    data = request.json
    agent_id = data.get('agent_id')
    recipient_phone = data.get('phone', '').strip()
    message_text = data.get('message', '').strip()

    if not agent_id or not recipient_phone or not message_text:
        return jsonify({'error': 'agent_id, phone, and message required'}), 400

    message_id = queue_message(agent_id, recipient_phone, message_text)
    return jsonify({'success': True, 'message_id': message_id})


@app.route('/api/queue/bulk', methods=['POST'])
@login_required
def api_queue_bulk():
    """Queue multiple messages for a specific agent."""
    data = request.json
    agent_id = data.get('agent_id')
    messages = data.get('messages', [])

    if not agent_id or not messages:
        return jsonify({'error': 'agent_id and messages required'}), 400

    queued = []
    for msg in messages:
        phone = msg.get('phone', '').strip()
        text = msg.get('message', '').strip()
        if phone and text:
            message_id = queue_message(agent_id, phone, text)
            queued.append({'phone': phone, 'message_id': message_id})

    return jsonify({'success': True, 'queued': len(queued), 'messages': queued})


if __name__ == '__main__':
    print('Starting iMessage Auto-Sender...')
    print(f'Password: {APP_PASSWORD}')
    print('Open http://127.0.0.1:5001 in your browser')
    print('To change password: export IMESSAGE_PASSWORD=yourpassword')
    app.run(debug=True, host='0.0.0.0', port=5001)
