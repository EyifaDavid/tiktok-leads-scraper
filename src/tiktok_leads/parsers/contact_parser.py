"""Contact information parser for extracting emails and phone numbers."""

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ContactParser:
    """Parser for extracting contact information from text."""
    
    # Email pattern
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    )
    
    # Phone patterns (multiple formats)
    PHONE_PATTERNS = [
        # International format with country code
        re.compile(r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}'),
        # Local format
        re.compile(r'(\+?\d{1,3}[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'),
    ]
    
    # Minimum phone number length (after cleaning)
    MIN_PHONE_LENGTH = 7

    @classmethod
    def extract_emails(cls, text: str) -> List[str]:
        """Extract email addresses from text.
        
        Args:
            text: Text to search for emails
        
        Returns:
            List of unique email addresses
        """
        if not text:
            return []
        
        found = cls.EMAIL_PATTERN.findall(text)
        # Remove duplicates while preserving order
        unique_emails = list(dict.fromkeys(found))
        
        if unique_emails:
            logger.debug(f"Found {len(unique_emails)} email(s): {unique_emails}")
        
        return unique_emails

    @classmethod
    def extract_phones(cls, text: str) -> List[str]:
        """Extract phone numbers from text.
        
        Args:
            text: Text to search for phone numbers
        
        Returns:
            List of unique phone numbers
        """
        if not text:
            return []
        
        found_phones = set()
        
        for pattern in cls.PHONE_PATTERNS:
            for match in pattern.finditer(text):
                phone = match.group().strip()
                # Clean the phone number
                cleaned = re.sub(r'[^\d+]', '', phone)
                # Validate length
                if len(cleaned) >= cls.MIN_PHONE_LENGTH:
                    found_phones.add(phone)
        
        # Remove duplicates while preserving order
        unique_phones = list(dict.fromkeys(found_phones))
        
        if unique_phones:
            logger.debug(f"Found {len(unique_phones)} phone(s): {unique_phones}")
        
        return unique_phones

    @classmethod
    def extract_contacts(cls, text: str) -> dict:
        """Extract both emails and phones from text.
        
        Args:
            text: Text to search for contacts
        
        Returns:
            Dictionary with 'emails' and 'phones' lists
        """
        return {
            "emails": cls.extract_emails(text),
            "phones": cls.extract_phones(text),
        }

    @classmethod
    def format_emails(cls, emails: List[str]) -> str:
        """Format email list as comma-separated string.
        
        Args:
            emails: List of email addresses
        
        Returns:
            Comma-separated string
        """
        return ", ".join(emails) if emails else ""

    @classmethod
    def format_phones(cls, phones: List[str]) -> str:
        """Format phone list as comma-separated string.
        
        Args:
            phones: List of phone numbers
        
        Returns:
            Comma-separated string
        """
        return ", ".join(phones) if phones else ""

    @classmethod
    def has_contact_info(cls, text: str) -> bool:
        """Check if text contains any contact information.
        
        Args:
            text: Text to check
        
        Returns:
            True if emails or phones found
        """
        if not text:
            return False
        
        has_emails = bool(cls.EMAIL_PATTERN.search(text))
        has_phones = any(pattern.search(text) for pattern in cls.PHONE_PATTERNS)
        
        return has_emails or has_phones
