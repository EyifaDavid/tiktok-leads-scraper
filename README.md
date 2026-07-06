# TikTok Leads Scraper v2

A modular, production-ready scraping tool for discovering and extracting leads from TikTok. Extracts emails, phone numbers, and other contact information automatically. Customize queries and filters for any industry.

## Features

- **Modular Architecture**: Clean separation of concerns with scrapers, parsers, storage, and utilities
- **Configuration Management**: Environment-based settings with Pydantic validation
- **Error Handling**: Exponential backoff with jitter for transient failures
- **Structured Logging**: JSON-formatted logs with rotation
- **Type Safety**: Full type hints throughout the codebase
- **Multiple Export Formats**: CSV, JSON, and Excel support
- **SQLite Storage**: Persistent lead storage with deduplication
- **Anti-Detection**: Stealth mode and human-like delays
- **Free Dependencies**: All packages are free and open-source

## Project Structure

```
tiktok_leads_scaffold/
├── src/
│   └── tiktok_leads/
│       ├── __init__.py
│       ├── __main__.py              # CLI entry point
│       ├── config.py                # Pydantic settings + .env
│       ├── logging_config.py        # Structured logging setup
│       ├── exceptions.py            # Custom exception hierarchy
│       ├── scrapers/
│       │   ├── __init__.py
│       │   ├── base_scraper.py      # Abstract base class
│       │   └── tiktok_scraper.py    # TikTok-specific implementation
│       ├── parsers/
│       │   ├── __init__.py
│       │   └── contact_parser.py    # Email/phone extraction
│       ├── storage/
│       │   ├── __init__.py
│       │   ├── database.py          # SQLite operations
│       │   └── exporter.py          # CSV/JSON/Excel export
│       ├── models/
│       │   ├── __init__.py
│       │   └── lead.py              # Pydantic data models
│       └── utils/
│           ├── __init__.py
│           ├── retry.py             # Exponential backoff
│           └── browser.py           # Playwright helpers
├── tests/
│   ├── __init__.py
│   └── test_parsers/
│       └── test_contact_parser.py
├── data/                            # Scraped output (gitignored)
├── logs/                            # Log files (gitignored)
├── .env                             # Environment variables (gitignored)
├── .env.example                     # Template
├── .gitignore
├── pyproject.toml                   # Modern dependencies
└── README.md
```

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/tiktok-leads-scraper.git
cd tiktok-leads-scraper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# - Add proxy addresses (optional)
# - Adjust delays and limits
# - Set output directories
```

### 3. Usage

#### Command Line Interface

```bash
# Automatic discovery (uses configured queries and hashtags)
python -m tiktok_leads --auto --max 100

# Basic search
python -m tiktok_leads --query "real estate agent" --max 50

# Scrape specific profile
python -m tiktok_leads --profile https://www.tiktok.com/@username

# Export to multiple formats
python -m tiktok_leads --query "marketing agency" --export all

# Verbose logging
python -m tiktok_leads -v --max 20

# Custom delays
python -m tiktok_leads --delay-min 3 --delay-max 10 --max 100
```

#### Programmatic Usage

```python
import asyncio
from tiktok_leads.config import get_settings
from tiktok_leads.scrapers.tiktok_scraper import TikTokScraper
from tiktok_leads.storage.database import Database
from tiktok_leads.storage.exporter import Exporter

async def main():
    config = get_settings()
    
    # Initialize database
    db = Database(config.get_db_path())
    db.connect()
    db.create_tables()
    
    # Scrape leads
    async with TikTokScraper(config) as scraper:
        leads = await scraper.scrape("your search query", max_results=50)
        
        # Export
        exporter = Exporter(config.output_dir)
        exporter.to_csv(leads)
        
        # Print summary
        summary = exporter.get_export_summary(leads)
        print(f"Found {summary['total_leads']} leads")
        print(f"With email: {summary['with_email']}")
        print(f"With phone: {summary['with_phone']}")

asyncio.run(main())
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SEARCH_QUERY` | `logistics company OR freight forwarder...` | TikTok search query (customize for your target) |
| `MAX_USERS` | `100` | Maximum users to scrape |
| `HEADLESS` | `true` | Run browser in headless mode |
| `MIN_DELAY` | `5` | Minimum delay between actions (seconds) |
| `MAX_DELAY` | `15` | Maximum delay between actions (seconds) |
| `DB_FILE` | `tiktok_leads.db` | SQLite database filename |
| `OUTPUT_DIR` | `data` | Output directory for exports |
| `PROXIES` | `""` | Comma-separated proxy list |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_FILE` | `logs/scraper.log` | Log file path |
| `DISCOVERY_QUERIES` | *(defaults)* | Comma-separated search queries for auto-discovery |
| `DISCOVERY_HASHTAGS` | *(defaults)* | Comma-separated hashtags for auto-discovery |
| `INCLUDE_KEYWORDS` | *(defaults)* | Comma-separated bio keywords to identify relevant accounts |
| `EXCLUDE_KEYWORDS` | *(defaults)* | Comma-separated keywords to filter out irrelevant accounts |

### Proxies

Add residential proxies to `.env`:

```env
PROXIES="http://user:pass@proxy1:port,http://user:pass@proxy2:port"
```

## Output Formats

### CSV Export
- Timestamped filename: `tiktok_leads_20260624_233200.csv`
- UTF-8 encoding
- All lead fields included

### JSON Export
- Structured JSON format
- Easy integration with other tools
- Pretty-printed for readability

### Excel Export
- `.xlsx` format
- Compatible with Microsoft Excel and Google Sheets

## Database Schema

```sql
CREATE TABLE leads (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    profile_url TEXT,
    bio TEXT,
    emails TEXT,
    phones TEXT,
    followers TEXT,
    following TEXT,
    likes TEXT,
    external_link TEXT,
    verified BOOLEAN,
    scraped_at TEXT,
    source_query TEXT
);
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=tiktok_leads

# Run specific test file
pytest tests/test_parsers/test_contact_parser.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## Error Handling

The scraper includes robust error handling:

- **Transient Errors**: Automatic retry with exponential backoff
- **Rate Limiting**: Detected and handled gracefully
- **Soft Blocks**: Detection of TikTok anti-scraping measures
- **Database Errors**: Proper connection and transaction handling

## Customization

The auto-discovery system is fully configurable for any industry:

```bash
# Customize for real estate
INCLUDE_KEYWORDS="real estate,realtor,property,agent,broker,realty,realtor®"
EXCLUDE_KEYWORDS="personal,vlog,entertainment,music,dance,comedy,beauty"
DISCOVERY_QUERIES="real estate agent,realtor,property broker,real estate broker,realty"
DISCOVERY_HASHTAGS="realestate,realtor,property,realestateagent,homebuying"

# Customize for healthcare
INCLUDE_KEYWORDS="doctor,clinic,medical,healthcare,nurse,therapist,wellness"
DISCOVERY_QUERIES="medical clinic,healthcare provider,therapy practice,wellness center"
```

## Next Steps

- [ ] Add proxy rotation support
- [ ] Implement scheduled scraping
- [ ] Add web dashboard
- [ ] Integrate with CRM systems
- [ ] Add email verification
- [ ] Implement lead scoring

## License

MIT License - see [LICENSE](LICENSE) for details.

## Disclaimer

This tool is for educational purposes only. Users are responsible for complying with TikTok's Terms of Service and applicable laws. Use responsibly and ethically.
