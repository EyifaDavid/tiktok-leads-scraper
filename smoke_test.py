"""Live smoke test - scrapes 3 leads to verify everything works."""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from tiktok_leads.config import get_settings
from tiktok_leads.logging_config import setup_logging
from tiktok_leads.scrapers.tiktok_scraper import TikTokScraper
from tiktok_leads.storage.database import Database
from tiktok_leads.storage.exporter import Exporter


async def main():
    config = get_settings()
    config.headless = False  # visible browser so you can see it working
    config.min_delay = 2
    config.max_delay = 5

    setup_logging("DEBUG", config.log_file)

    db = Database(config.get_db_path())
    db.connect()
    db.create_tables()
    exporter = Exporter(config.output_dir)

    print("=" * 50)
    print("SMOKE TEST: Scraping 3 leads (visible browser)")
    print("=" * 50)

    try:
        async with TikTokScraper(config) as scraper:
            leads = await scraper.auto_discover(max_results=3)

            if leads:
                from tiktok_leads.models.lead import LeadCreate
                for lead in leads:
                    db.insert_lead(LeadCreate(**lead.model_dump()))

                filepath = exporter.to_csv(leads)
                summary = exporter.get_export_summary(leads)

                print("\n" + "=" * 50)
                print("RESULTS")
                print("=" * 50)
                for lead in leads:
                    print(f"  @{lead.username} | emails={lead.emails or 'none'} | phones={lead.phones or 'none'}")
                print(f"\nTotal: {summary['total_leads']}")
                print(f"With email: {summary['with_email']}")
                print(f"With phone: {summary['with_phone']}")
                print(f"CSV saved: {filepath}")
                print(f"Database: {config.db_file}")
                print("=" * 50)
            else:
                print("No leads found.")
    finally:
        db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
