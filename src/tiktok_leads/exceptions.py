"""Custom exception hierarchy for TikTok Leads Scraper."""


class ScraperError(Exception):
    """Base exception for all scraper errors."""
    pass


class ConfigurationError(ScraperError):
    """Raised for configuration issues."""
    pass


class RateLimitError(ScraperError):
    """Raised when rate limited (HTTP 429)."""
    pass


class SoftBlockError(ScraperError):
    """Raised when response looks like a block (HTTP 200 but useless content)."""
    pass


class ParseError(ScraperError):
    """Raised when HTML parsing fails."""
    pass


class DatabaseError(ScraperError):
    """Raised for database operation failures."""
    pass


class ExportError(ScraperError):
    """Raised for data export failures."""
    pass


class BrowserError(ScraperError):
    """Raised for browser operation failures."""
    pass


class ProxyError(ScraperError):
    """Raised for proxy-related issues."""
    pass
