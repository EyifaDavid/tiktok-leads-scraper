"""Tests for contact parser module."""

import pytest
from tiktok_leads.parsers.contact_parser import ContactParser


class TestContactParser:
    """Tests for ContactParser class."""

    def test_extract_emails_basic(self):
        """Test basic email extraction."""
        text = "Contact us at info@example.com or support@test.org"
        emails = ContactParser.extract_emails(text)
        assert len(emails) == 2
        assert "info@example.com" in emails
        assert "support@test.org" in emails

    def test_extract_emails_none(self):
        """Test email extraction with None input."""
        emails = ContactParser.extract_emails(None)
        assert emails == []

    def test_extract_emails_empty(self):
        """Test email extraction with empty string."""
        emails = ContactParser.extract_emails("")
        assert emails == []

    def test_extract_emails_no_emails(self):
        """Test email extraction when no emails present."""
        text = "No emails here, just regular text"
        emails = ContactParser.extract_emails(text)
        assert emails == []

    def test_extract_emails_duplicates(self):
        """Test email deduplication."""
        text = "Email: test@example.com or test@example.com again"
        emails = ContactParser.extract_emails(text)
        assert len(emails) == 1
        assert "test@example.com" in emails

    def test_extract_phones_basic(self):
        """Test basic phone extraction."""
        text = "Call us at +1-555-123-4567 or 555-987-6543"
        phones = ContactParser.extract_phones(text)
        assert len(phones) >= 1

    def test_extract_phones_none(self):
        """Test phone extraction with None input."""
        phones = ContactParser.extract_phones(None)
        assert phones == []

    def test_extract_phones_empty(self):
        """Test phone extraction with empty string."""
        phones = ContactParser.extract_phones("")
        assert phones == []

    def test_extract_phones_too_short(self):
        """Test phone extraction rejects short numbers."""
        text = "Call 1234567"
        phones = ContactParser.extract_phones(text)
        # Should not extract very short numbers
        assert all(len(p.replace("-", "").replace(" ", "").replace("+", "")) >= 7 for p in phones)

    def test_extract_contacts_combined(self):
        """Test combined email and phone extraction."""
        text = "Email: info@company.com, Phone: +1-555-123-4567"
        contacts = ContactParser.extract_contacts(text)
        assert "emails" in contacts
        assert "phones" in contacts
        assert len(contacts["emails"]) == 1
        assert len(contacts["phones"]) >= 1

    def test_format_emails(self):
        """Test email formatting."""
        emails = ["a@test.com", "b@test.com"]
        result = ContactParser.format_emails(emails)
        assert result == "a@test.com, b@test.com"

    def test_format_emails_empty(self):
        """Test email formatting with empty list."""
        result = ContactParser.format_emails([])
        assert result == ""

    def test_format_phones(self):
        """Test phone formatting."""
        phones = ["+1-555-123-4567"]
        result = ContactParser.format_phones(phones)
        assert result == "+1-555-123-4567"

    def test_format_phones_empty(self):
        """Test phone formatting with empty list."""
        result = ContactParser.format_phones([])
        assert result == ""

    def test_has_contact_info_true(self):
        """Test contact info detection with contacts."""
        text = "Email: test@example.com"
        assert ContactParser.has_contact_info(text) is True

    def test_has_contact_info_false(self):
        """Test contact info detection without contacts."""
        text = "No contact information here"
        assert ContactParser.has_contact_info(text) is False

    def test_has_contact_info_none(self):
        """Test contact info detection with None."""
        assert ContactParser.has_contact_info(None) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
