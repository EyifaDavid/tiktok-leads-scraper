"""Quick test script to verify the codebase works."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from tiktok_leads.config import Settings
        print("  [OK] config module loaded")
    except Exception as e:
        print(f"  [FAIL] config failed: {e}")
        return False
    
    try:
        from tiktok_leads.parsers.contact_parser import ContactParser
        print("  [OK] parsers module loaded")
    except Exception as e:
        print(f"  [FAIL] parsers failed: {e}")
        return False
    
    try:
        from tiktok_leads.models.lead import Lead
        print("  [OK] models module loaded")
    except Exception as e:
        print(f"  [FAIL] models failed: {e}")
        return False
    
    try:
        from tiktok_leads.exceptions import ScraperError
        print("  [OK] exceptions module loaded")
    except Exception as e:
        print(f"  [FAIL] exceptions failed: {e}")
        return False
    
    try:
        from tiktok_leads.discovery.queries import SEARCH_QUERIES, HASHTAGS
        print("  [OK] discovery.queries module loaded")
    except Exception as e:
        print(f"  [FAIL] discovery.queries failed: {e}")
        return False
    
    return True


def test_contact_parser():
    """Test the contact parser functionality."""
    print("\nTesting contact parser...")
    
    from tiktok_leads.parsers.contact_parser import ContactParser
    
    # Test email extraction
    text1 = "Contact us at info@example.com or sales@test.org"
    emails = ContactParser.extract_emails(text1)
    assert len(emails) == 2, f"Expected 2 emails, got {len(emails)}"
    print(f"  [OK] Email extraction: {emails}")
    
    # Test phone extraction
    text2 = "Call +1-555-123-4567 or 555-987-6543"
    phones = ContactParser.extract_phones(text2)
    print(f"  [OK] Phone extraction: {phones}")
    
    # Test combined extraction
    contacts = ContactParser.extract_contacts(text1 + " " + text2)
    print(f"  [OK] Combined extraction: {contacts}")
    
    return True


def test_lead_model():
    """Test the Lead data model."""
    print("\nTesting lead model...")
    
    from tiktok_leads.models.lead import Lead
    
    lead = Lead(
        username="test_business",
        profile_url="https://www.tiktok.com/@test_business",
        bio="We provide business services",
        emails="info@test.com",
        phones="+1-555-123-4567",
    )
    
    assert lead.username == "test_business"
    assert lead.has_email() is True
    assert lead.has_phone() is True
    assert lead.has_contact_info() is True
    
    print(f"  [OK] Lead created: @{lead.username}")
    print(f"    Has email: {lead.has_email()}")
    print(f"    Has phone: {lead.has_phone()}")
    
    return True


def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    from tiktok_leads.config import Settings
    
    config = Settings()
    
    print(f"  [OK] Config loaded")
    print(f"    Search query: {config.search_query[:50]}...")
    print(f"    Max users: {config.max_users}")
    print(f"    Headless: {config.headless}")
    print(f"    Auto discover: {config.auto_discover}")
    
    return True


def test_discovery_queries():
    """Test discovery queries module."""
    print("\nTesting discovery queries...")
    
    from tiktok_leads.discovery.queries import SEARCH_QUERIES, HASHTAGS, INCLUDE_KEYWORDS
    
    print(f"  [OK] Loaded {len(SEARCH_QUERIES)} search queries")
    print(f"  [OK] Loaded {len(HASHTAGS)} hashtags")
    print(f"  [OK] Loaded {len(INCLUDE_KEYWORDS)} include keywords")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("TIKTOK LEADS SCRAPER - QUICK TEST")
    print("=" * 60)
    
    tests = [
        ("Imports", test_imports),
        ("Contact Parser", test_contact_parser),
        ("Lead Model", test_lead_model),
        ("Configuration", test_config),
        ("Discovery Queries", test_discovery_queries),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [FAIL] {name} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n[SUCCESS] All tests passed! The codebase is ready.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Install Playwright: playwright install chromium")
        print("3. Configure .env for your target industry")
        print("4. Run: python -m tiktok_leads --auto --max 10")
    else:
        print("\n[ERROR] Some tests failed. Check the errors above.")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
