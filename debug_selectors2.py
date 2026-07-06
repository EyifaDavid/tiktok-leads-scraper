"""Debug TikTok search error."""
import asyncio, sys
sys.path.insert(0, 'src')
from tiktok_leads.config import get_settings
from tiktok_leads.scrapers.tiktok_scraper import TikTokScraper
from tiktok_leads.logging_config import setup_logging

setup_logging('INFO', 'logs/debug3.log')

async def debug():
    config = get_settings()
    config.headless = False
    async with TikTokScraper(config) as scraper:
        await scraper._page.goto(
            'https://www.tiktok.com/search/user?q=twerking',
            wait_until='domcontentloaded', timeout=60000
        )
        await asyncio.sleep(5)
        
        # Get error text
        err_title = await scraper._page.text_content('[data-e2e="search-error-title"]')
        err_desc = await scraper._page.text_content('[data-e2e="search-error-desc"]')
        print(f'Error title: {err_title}')
        print(f'Error desc: {err_desc}')
        
        # Get page text
        body_text = await scraper._page.evaluate('document.body.innerText')
        print(f'Body text (first 1000): {body_text[:1000]}')
        
        # Check URL
        print(f'Current URL: {scraper._page.url}')

asyncio.run(debug())
