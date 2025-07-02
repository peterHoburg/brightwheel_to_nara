# Brightwheel to Nara Transfer Tool

A Python tool to transfer childcare data from [Brightwheel](https://schools.mybrightwheel.com) to [Nara Baby Tracker](https://nara.com/pages/nara-baby-tracker).

## Features

- 🔐 Secure authentication with both platforms
- 📊 Transfer multiple activity types (diapers, feeding, sleep, etc.)
- 🔄 Incremental sync support
- 🧪 Dry-run mode for testing
- 📝 Comprehensive error logging
- ⚡ Concurrent processing for better performance

## Installation

This project uses `uv` for dependency management.

```bash
# Clone the repository
git clone <repository-url>
cd brightwheel_to_nara

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

## Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required: Brightwheel credentials
BRIGHTWHEEL_USERNAME="your.email@example.com"
BRIGHTWHEEL_PASSWORD="your_password"

# Optional: Brightwheel session cookie (to skip interactive login)
BRIGHTWHEEL_SESSION_COOKIE="your_session_cookie_value"

# Optional: Nara credentials (if not provided, runs in read-only mode)
NARA_EMAIL="your.email@example.com"
NARA_PASSWORD="your_password"

# Optional: Transfer settings
SYNC_DAYS_BACK=7
DRY_RUN=false
```

## Usage

### Basic Usage

```bash
# Run the transfer
btn

# Or using uv
uv run btn
```

### Command Line Options

```bash
# Dry run mode - preview what would be transferred
btn --dry-run

# Sync specific number of days
btn --days-back 14

# Set logging level
btn --log-level DEBUG

# Extract session cookie from browser (avoids captcha)
btn --extract-cookie
```

## Supported Activity Types

The tool currently supports transferring the following activity types:

- **Diaper Changes**: Wet, BM, or both
- **Feeding**: Bottle, breast, and solid foods
- **Sleep**: Naps with duration tracking
- **Health**: Temperature checks
- **Photos**: With captions
- **Notes**: General observations

## How It Works

1. **Authentication**: 
   - First tries to use a session cookie if provided (bypasses captcha)
   - Falls back to Playwright-based interactive login if needed
2. **Data Fetching**: Retrieves activities from Brightwheel for the specified date range
3. **Transformation**: Converts Brightwheel data format to Nara's format
4. **Upload**: Creates corresponding activities in Nara Baby Tracker

### Avoiding Captcha Challenges

To avoid interactive login and captcha challenges:

1. Use the cookie extraction feature:
   ```bash
   btn --extract-cookie
   ```

2. Or manually extract the session cookie:
   - Login to Brightwheel in your browser
   - Open Developer Tools (F12)
   - Go to Application/Storage tab
   - Find the `_brightwheel_session` cookie
   - Copy the value to your `.env` file

## API Structure

### Brightwheel Models

- `Student`: Child information
- `Guardian`: Parent/guardian details
- `Activity`: Various activity types (diaper, feeding, sleep, etc.)

### Nara Models

- `Baby`: Child information in Nara
- `Caregiver`: Parent/caregiver details
- `Activity Records`: Specific record types for each activity

## Development

### Project Structure

```
src/brightwheel_to_nara/
├── __init__.py         # CLI entry point
├── api/                # API clients
│   ├── brightwheel_client.py
│   └── nara_client.py
├── models/             # Pydantic models
│   ├── brightwheel.py
│   └── nara.py
├── utils/              # Utility functions
│   ├── transformers.py # Data transformation
│   └── errors.py       # Error handling
├── config.py           # Configuration management
└── transfer.py         # Main transfer logic
```

### Running Tests

```bash
# Run tests (when implemented)
uv run pytest
```

## Troubleshooting

### Authentication Issues

- If you encounter captcha challenges, the browser window will open for manual solving
- Ensure your credentials are correct in the `.env` file

### Mapping Issues

- The tool matches children by first name and birthdate
- Ensure names and birthdates match between platforms

### Rate Limiting

- The tool includes automatic retry with exponential backoff
- Adjust `BATCH_SIZE` and `RETRY_DELAY_SECONDS` if needed

## Security Notes

- Never commit your `.env` file with real credentials
- The tool stores session tokens temporarily in memory only
- All API communications use HTTPS

## Limitations

- Brightwheel's API requires handling captcha challenges
- Nara's API endpoints are hypothetical (update with actual endpoints)
- Some activity types may not have direct equivalents between platforms

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Your License Here]
