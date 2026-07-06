"""Browser utilities for Playwright operations."""

import asyncio
import random
import logging
from typing import Optional, Any, List, Tuple

from playwright.async_api import Page, Locator

logger = logging.getLogger(__name__)

# Common viewport sizes for realistic fingerprinting
VIEWPORTS = [
    (1920, 1080),
    (1366, 768),
    (1536, 864),
    (1440, 900),
    (1280, 720),
    (1600, 900),
    (1280, 800),
    (1920, 1200),
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
]


def random_viewport() -> Tuple[int, int]:
    """Pick a random viewport size."""
    return random.choice(VIEWPORTS)


def random_user_agent() -> str:
    """Pick a random user agent string."""
    return random.choice(USER_AGENTS)


async def human_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
    """Add human-like random delay.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


async def safe_get_text(
    locator: Locator,
    timeout: int = 5000,
    default: str = ""
) -> str:
    """Safely get text from a locator.
    
    Args:
        locator: Playwright locator
        timeout: Timeout in milliseconds
        default: Default value if element not found
    
    Returns:
        Text content or default value
    """
    try:
        if await locator.count() > 0:
            return await locator.inner_text(timeout=timeout)
    except Exception as e:
        logger.debug(f"Failed to get text from locator: {e}")
    return default


async def safe_get_attribute(
    locator: Locator,
    attribute: str,
    timeout: int = 5000,
    default: Optional[str] = None
) -> Optional[str]:
    """Safely get attribute from a locator.
    
    Args:
        locator: Playwright locator
        attribute: Attribute name
        timeout: Timeout in milliseconds
        default: Default value if attribute not found
    
    Returns:
        Attribute value or default value
    """
    try:
        if await locator.count() > 0:
            return await locator.get_attribute(attribute, timeout=timeout)
    except Exception as e:
        logger.debug(f"Failed to get attribute '{attribute}' from locator: {e}")
    return default


async def scroll_page(page: Page, pixels: int = 2000) -> None:
    """Scroll page by specified pixels.
    
    Args:
        page: Playwright page
        pixels: Number of pixels to scroll
    """
    await page.evaluate(f"window.scrollBy(0, {pixels})")


async def wait_for_selector(
    page: Page,
    selector: str,
    timeout: int = 10000,
    required: bool = False
) -> Optional[Locator]:
    """Wait for a selector to appear on the page.
    
    Args:
        page: Playwright page
        selector: CSS selector
        timeout: Timeout in milliseconds
        required: If True, raise exception when not found
    
    Returns:
        Locator or None if not found
    
    Raises:
        Exception if required=True and selector not found
    """
    try:
        locator = page.locator(selector)
        await locator.wait_for(timeout=timeout)
        return locator
    except Exception as e:
        if required:
            raise
        logger.debug(f"Selector '{selector}' not found: {e}")
        return None


async def check_element_exists(page: Page, selector: str) -> bool:
    """Check if an element exists on the page.
    
    Args:
        page: Playwright page
        selector: CSS selector
    
    Returns:
        True if element exists
    """
    try:
        locator = page.locator(selector)
        return await locator.count() > 0
    except Exception:
        return False
