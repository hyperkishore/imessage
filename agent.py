#!/usr/bin/env python3
"""
iMessage Agent - Runs on each Mac to send messages from the queue.

Usage:
    python agent.py --server http://central-server:5001 --name "John Smith" --phone "+1-555-123-4567"

The agent will:
1. Register with the central server (first run) or authenticate (subsequent runs)
2. Poll for pending messages every few seconds
3. Send messages via AppleScript
4. Report status back to the server
"""
import argparse
import json
import os
import sys
import time
import requests

from imessage import send_imessage

CONFIG_FILE = os.path.expanduser('~/.imessage-agent.json')
POLL_INTERVAL = 5  # seconds


def load_config() -> dict | None:
    """Load saved agent configuration."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None


def save_config(config: dict) -> None:
    """Save agent configuration."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)  # Secure the token file


def register_agent(server: str, name: str, phone: str) -> dict:
    """Register this agent with the central server."""
    response = requests.post(
        f'{server}/api/agents/register',
        json={'name': name, 'phone': phone},
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def heartbeat(server: str, token: str) -> dict:
    """Send heartbeat and get pending messages."""
    response = requests.post(
        f'{server}/api/agents/poll',
        headers={'Authorization': f'Bearer {token}'},
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def report_status(server: str, token: str, message_id: int, status: str, error: str = None) -> None:
    """Report message send status back to server."""
    requests.post(
        f'{server}/api/agents/report',
        headers={'Authorization': f'Bearer {token}'},
        json={'message_id': message_id, 'status': status, 'error': error},
        timeout=10
    )


def process_messages(server: str, token: str, messages: list) -> None:
    """Process and send pending messages."""
    for msg in messages:
        message_id = msg['id']
        phone = msg['recipient_phone']
        text = msg['message_text']

        print(f'  Sending to {phone}...')
        result = send_imessage(phone, text)

        if result['success']:
            print(f'  ✓ Sent to {phone}')
            report_status(server, token, message_id, 'sent')
        else:
            print(f'  ✗ Failed: {result.get("error")}')
            report_status(server, token, message_id, 'failed', result.get('error'))

        time.sleep(1)  # Small delay between sends


def run_agent(server: str, name: str = None, phone: str = None) -> None:
    """Main agent loop."""
    config = load_config()

    # Register if no saved config or new credentials provided
    if not config or (name and phone):
        if not name or not phone:
            print('Error: --name and --phone required for first-time registration')
            sys.exit(1)

        print(f'Registering agent: {name} ({phone})')
        result = register_agent(server, name, phone)
        config = {
            'server': server,
            'token': result['token'],
            'agent_id': result['id'],
            'name': name,
            'phone': phone
        }
        save_config(config)
        print(f'Registered successfully. Agent ID: {result["id"]}')
        print(f'Config saved to {CONFIG_FILE}')

    token = config['token']
    print(f'\nAgent running: {config.get("name", "Unknown")} ({config.get("phone", "Unknown")})')
    print(f'Server: {server}')
    print(f'Polling every {POLL_INTERVAL} seconds. Press Ctrl+C to stop.\n')

    while True:
        try:
            data = heartbeat(server, token)
            messages = data.get('messages', [])

            if messages:
                print(f'[{time.strftime("%H:%M:%S")}] {len(messages)} message(s) to send')
                process_messages(server, token, messages)
            else:
                print(f'[{time.strftime("%H:%M:%S")}] No pending messages', end='\r')

        except requests.RequestException as e:
            print(f'\n[{time.strftime("%H:%M:%S")}] Connection error: {e}')

        except KeyboardInterrupt:
            print('\n\nAgent stopped.')
            break

        time.sleep(POLL_INTERVAL)


def main():
    parser = argparse.ArgumentParser(description='iMessage Agent')
    parser.add_argument('--server', '-s', default='http://127.0.0.1:5001',
                        help='Central server URL (default: http://127.0.0.1:5001)')
    parser.add_argument('--name', '-n', help='Sender name (required for first registration)')
    parser.add_argument('--phone', '-p', help='Sender phone (required for first registration)')
    parser.add_argument('--reset', action='store_true', help='Reset saved configuration')

    args = parser.parse_args()

    if args.reset and os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
        print(f'Removed {CONFIG_FILE}')

    run_agent(args.server, args.name, args.phone)


if __name__ == '__main__':
    main()
