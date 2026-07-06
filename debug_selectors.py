"""Debug TikTok page selectors."""
import asyncio, sys
sys.path.insert(0, 'src')
from tiktok_leads.config import get_settings
from tiktok_leads.scrapers.tiktok_scraper import TikTokScraper
from tiktok_leads.logging_config import setup_logging

setup_logging('INFO', 'logs/debug2.log')

async def debug():
    config = get_settings()
    config.headless = False
    async with TikTokScraper(config) as scraper:
        await scraper._page.goto(
            'https://www.tiktok.com/search/user?q=twerking',
            wait_until='domcontentloaded', timeout=60000
        )
        await asyncio.sleep(8)
        
        title = await scraper._page.title()
        url = scraper._page.url
        print(f'Title: {title}')
        print(f'URL: {url}')
        
        all_e2e = await scraper._page.query_selector_all('[data-e2e]')
        print(f'Total data-e2e elements: {len(all_e2e)}')
        seen = set()
        for e in all_e2e:
            attr = await e.get_attribute('data-e2e')
            if attr and attr not in seen:
                seen.add(attr)
                print(f'  data-e2e="{attr}"')
        
        # Check search-specific selectors
        for sel in ['a[href^="/@"]', 'div[class*="search"]', 'div[class*="user-card"]', 'div[class*="UserCard"]']:
            elems = await scraper._page.query_selector_all(sel)
            if elems:
                print(f'{sel}: {len(elems)} found')

asyncio.run(debug())
