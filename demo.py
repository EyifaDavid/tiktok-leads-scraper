"""Demo script showing how to use the TikTok Leads Scraper."""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


async def demo_contact_parser():
    """Demo: Extract contacts from text."""
    print("\n" + "=" * 60)
    print("DEMO 1: Contact Extraction")
    print("=" * 60)
    
    from tiktok_leads.parsers.contact_parser import ContactParser
    
    # Sample bio texts
    bios = [
        "Global Business Solutions | info@globalbiz.com | +1-555-123-4567",
        "Tech services worldwide | sales@techfast.com",
        "Consulting | Dubai | call us: +971-4-555-0123",
        "No contact info here, just a regular account",
    ]
    
    for i, bio in enumerate(bios, 1):
        print(f"\nBio {i}: {bio}")
        contacts = ContactParser.extract_contacts(bio)
        
        if contacts["emails"] or contacts["phones"]:
            print(f"  -> Emails: {contacts['emails'] or 'None'}")
            print(f"  -> Phones: {contacts['phones'] or 'None'}")
        else:
            print("  -> No contacts found")


async def demo_lead_model():
    """Demo: Create and use Lead models."""
    print("\n" + "=" * 60)
    print("DEMO 2: Lead Data Model")
    print("=" * 60)
    
    from tiktok_leads.models.lead import Lead
    
    # Create sample leads
    leads = [
        Lead(
            username="global_biz_solutions",
            profile_url="https://www.tiktok.com/@global_biz_solutions",
            bio="Global business solutions | info@global.com",
            emails="info@global.com",
            followers="15.2K",
        ),
        Lead(
            username="tech_services_co",
            profile_url="https://www.tiktok.com/@tech_services_co",
            bio="Tech services worldwide | +1-555-0123",
            phones="+1-555-0123",
            followers="8.5K",
        ),
    ]
    
    for lead in leads:
        print(f"\n@{lead.username}")
        print(f"  Bio: {lead.bio[:50]}...")
        print(f"  Has email: {lead.has_email()}")
        print(f"  Has phone: {lead.has_phone()}")
        print(f"  Has any contact: {lead.has_contact_info()}")


async def demo_auto_discovery():
    """Demo: Show auto-discovery configuration."""
    print("\n" + "=" * 60)
    print("DEMO 3: Auto-Discovery Configuration")
    print("=" * 60)
    
    from tiktok_leads.discovery.queries import (
        SEARCH_QUERIES,
        HASHTAGS,
        INCLUDE_KEYWORDS,
    )
    
    print(f"\nSearch Queries ({len(SEARCH_QUERIES)} total):")
    for q in SEARCH_QUERIES[:5]:
        print(f"  - {q}")
    print("  ...")
    
    print(f"\nHashtags ({len(HASHTAGS)} total):")
    for h in HASHTAGS[:5]:
        print(f"  - #{h}")
    print("  ...")
    
    print(f"\nInclude Keywords ({len(INCLUDE_KEYWORDS)} total):")
    for k in INCLUDE_KEYWORDS[:5]:
        print(f"  - {k}")
    print("  ...")


async def demo_config():
    """Demo: Show configuration options."""
    print("\n" + "=" * 60)
    print("DEMO 4: Configuration Settings")
    print("=" * 60)
    
    from tiktok_leads.config import Settings
    
    config = Settings()
    
    print(f"\nCurrent Settings:")
    print(f"  Auto-discover mode: {config.auto_discover}")
    print(f"  Max users: {config.max_users}")
    print(f"  Headless browser: {config.headless}")
    print(f"  Min delay: {config.min_delay}s")
    print(f"  Max delay: {config.max_delay}s")
    print(f"  Database: {config.db_file}")
    print(f"  Output dir: {config.output_dir}")


async def main():
    """Run all demos."""
    print("\n" + "=" * 60)
    print("TIKTOK LEADS SCRAPER - DEMO")
    print("=" * 60)
    
    await demo_contact_parser()
    await demo_lead_model()
    await demo_auto_discovery()
    await demo_config()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    
    print("\nTo run the actual scraper with auto-discovery:")
    print("  python -m tiktok_leads --auto --max 10")
    print("\nCustomize for your industry via .env:")
    print("  INCLUDE_KEYWORDS=\"your keywords\" DISCOVERY_QUERIES=\"your queries\"")
    print("\nFor more options:")
    print("  python -m tiktok_leads --help")


if __name__ == "__main__":
    asyncio.run(main())
