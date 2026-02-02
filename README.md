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

## Version

See [VERSION](VERSION) file.

## License

MIT
