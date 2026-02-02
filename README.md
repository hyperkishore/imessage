# iMessage Auto-Sender

A web-based tool for sending personalized iMessages from Google Sheet data. Built for macOS.

## Features

- Import contacts from Google Sheets
- Template-based personalized messages with `{variable}` placeholders
- Preview messages before sending
- Send individual or bulk messages
- Simple password authentication

## Requirements

- macOS with Messages app configured
- Python 3.9+
- Messages app must have iMessage enabled

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/imessage.git
cd imessage

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Set password (optional, defaults to 'changeme')
export IMESSAGE_PASSWORD=your_secure_password

# Run the server
python app.py
```

Open http://127.0.0.1:5001 in your browser.

## Google Sheet Format

Your sheet must:
1. Be publicly accessible ("Anyone with the link can view")
2. Have a `phone` column with phone numbers

Example:
| name | phone | company |
|------|-------|---------|
| John | +1234567890 | Acme Inc |
| Jane | +0987654321 | Tech Corp |

## Message Templates

Use `{column_name}` to insert values from your sheet:

```
Hi {name}, I'm reaching out regarding {company}...
```

## Phase 2: Multi-Mac / Distributed Mode

For teams that want to send from multiple phone numbers (e.g., escalation from VP's phone):

### Setup Central Server
Run the web app on a server accessible to all team members.

### Setup Mac Agents
On each Mac that should send messages:

```bash
# First time registration
python agent.py --server http://your-server:5001 --name "VP Sales" --phone "+1-555-VP-1234"

# Subsequent runs (config saved)
python agent.py --server http://your-server:5001
```

The agent will:
1. Register with the central server
2. Poll for pending messages every 5 seconds
3. Send messages via AppleScript
4. Report status back to server

### Sending from Remote Macs
In the web UI, use the "Send From" dropdown to select which registered Mac should send the message. Messages are queued and the remote agent picks them up.

## Version

See [VERSION](VERSION) file.

## License

MIT
