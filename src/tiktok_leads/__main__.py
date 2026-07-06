"""CLI entry point for TikTok Leads Scraper."""

import asyncio
import argparse
import sys
from pathlib import Path

from tiktok_leads.config import get_settings, Settings
from tiktok_leads.logging_config import setup_logging
from tiktok_leads.scrapers.tiktok_scraper import TikTokScraper
from tiktok_leads.storage.database import Database
from tiktok_leads.storage.exporter import Exporter
from tiktok_leads.models.lead import LeadCreate
from tiktok_leads.parsers.contact_parser import ContactParser


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="TikTok Leads Scraper - Find leads on TikTok",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Automatic discovery (recommended)
  python -m tiktok_leads --auto --max 100
  
  # Manual search
  python -m tiktok_leads --query "your search term" --max 50
  
  # Scrape specific profile
  python -m tiktok_leads --profile https://www.tiktok.com/@username
        """,
    )
    
    # Discovery mode
    parser.add_argument(
        "-a", "--auto",
        action="store_true",
        help="Enable automatic discovery mode (uses configured queries and hashtags)",
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        help="Search query for finding leads (manual mode only)",
    )
    parser.add_argument(
        "-m", "--max",
        type=int,
        default=100,
        help="Maximum number of leads to collect (default: 100)",
    )
    parser.add_argument(
        "-p", "--profile",
        type=str,
        help="Scrape a specific TikTok profile URL",
    )
    
    # Export options
    parser.add_argument(
        "-e", "--export",
        choices=["csv", "json", "xlsx", "all"],
        default="csv",
        help="Export format (default: csv)",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output directory (default: from config)",
    )
    
    # Database options
    parser.add_argument(
        "--db",
        type=str,
        help="Database file path (default: from config)",
    )
    parser.add_argument(
        "--clear-db",
        action="store_true",
        help="Clear database before scraping",
    )
    
    # Scraper options
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser in visible mode (not headless)",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        help="Minimum delay between actions (seconds)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        help="Maximum delay between actions (seconds)",
    )
    
    # Logging
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    
    return parser.parse_args()


async def run_scraper(args: argparse.Namespace) -> None:
    """Run the scraper with parsed arguments."""
    # Load settings
    config = get_settings()
    
    # Override settings from arguments
    if args.no_headless:
        config.headless = False
    if args.delay_min is not None:
        config.min_delay = args.delay_min
    if args.delay_max is not None:
        config.max_delay = args.delay_max
    if args.db:
        config.db_file = args.db
    if args.output:
        config.output_dir = args.output
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else config.log_level
    setup_logging(log_level, config.log_file)
    
    # Initialize components
    db = Database(config.get_db_path())
    db.connect()
    db.create_tables()
    
    exporter = Exporter(config.output_dir)
    
    try:
        # Single profile scrape
        if args.profile:
            async with TikTokScraper(config) as scraper:
                lead = await scraper.scrape_profile(args.profile)
                if lead:
                    print(f"Successfully scraped: @{lead.username}")
                    print(f"Emails: {lead.emails or 'None'}")
                    print(f"Phones: {lead.phones or 'None'}")
                    print(f"Followers: {lead.followers}")
                    
                    # Save to database
                    lead_create = LeadCreate(**lead.model_dump())
                    db.insert_lead(lead_create)
                    
                    # Export
                    _export_leads([lead], exporter, args.export)
                else:
                    print("Failed to scrape profile")
                    sys.exit(1)
        
        # Automatic discovery mode
        elif args.auto:
            print("\n🔍 Starting automatic discovery...")
            print("   This will search multiple queries and hashtags to find leads.\n")
            
            async with TikTokScraper(config) as scraper:
                leads = await scraper.auto_discover(args.max)
                
                if leads:
                    # Save to database
                    for lead in leads:
                        lead_create = LeadCreate(**lead.model_dump())
                        db.insert_lead(lead_create)
                    
                    # Export
                    _export_leads(leads, exporter, args.export)
                    
                    # Print summary
                    print("\n" + "=" * 50)
                    print("🎯 AUTOMATIC DISCOVERY COMPLETE")
                    print("=" * 50)
                    print(f"Total leads: {len(leads)}")
                    
                    summary = exporter.get_export_summary(leads)
                    print(f"With email: {summary['with_email']} ({summary['email_rate']})")
                    print(f"With phone: {summary['with_phone']} ({summary['phone_rate']})")
                    print(f"With any contact: {summary['with_any_contact']}")
                    print("=" * 50)
                    print("\n💡 Tip: Use --export all to get CSV + JSON + Excel formats")
                else:
                    print("No leads found. Try adjusting max or check your connection.")
                    sys.exit(1)
        
        # Manual search mode
        else:
            query = args.query or config.search_query
            max_users = args.max or config.max_users
            
            async with TikTokScraper(config) as scraper:
                leads = await scraper.scrape(query, max_users)
                
                if leads:
                    # Save to database
                    for lead in leads:
                        lead_create = LeadCreate(**lead.model_dump())
                        db.insert_lead(lead_create)
                    
                    # Export
                    _export_leads(leads, exporter, args.export)
                    
                    # Print summary
                    print("\n" + "=" * 50)
                    print("SCRAPING COMPLETE")
                    print("=" * 50)
                    print(f"Total leads: {len(leads)}")
                    
                    summary = exporter.get_export_summary(leads)
                    print(f"With email: {summary['with_email']} ({summary['email_rate']})")
                    print(f"With phone: {summary['with_phone']} ({summary['phone_rate']})")
                    print(f"With contact: {summary['with_any_contact']}")
                    print("=" * 50)
                else:
                    print("No leads found")
                    sys.exit(1)
    
    finally:
        db.disconnect()


def _export_leads(leads, exporter: Exporter, export_format: str) -> None:
    """Export leads to specified format(s)."""
    if export_format == "csv" or export_format == "all":
        filepath = exporter.to_csv(leads)
        print(f"Exported to CSV: {filepath}")
    
    if export_format == "json" or export_format == "all":
        filepath = exporter.to_json(leads)
        print(f"Exported to JSON: {filepath}")
    
    if export_format == "xlsx" or export_format == "all":
        filepath = exporter.to_excel(leads)
        print(f"Exported to Excel: {filepath}")


def main() -> None:
    """Main entry point."""
    args = parse_args()
    asyncio.run(run_scraper(args))


if __name__ == "__main__":
    main()
