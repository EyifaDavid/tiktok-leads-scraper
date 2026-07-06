"""Abstract base scraper class."""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from tiktok_leads.config import Settings
from tiktok_leads.models.lead import Lead

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""
    
    def __init__(self, config: Settings):
        """Initialize scraper with configuration.
        
        Args:
            config: Application settings
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._leads: List[Lead] = []

    @property
    def leads(self) -> List[Lead]:
        """Get collected leads."""
        return self._leads

    def add_lead(self, lead: Lead) -> None:
        """Add a lead to the collection.
        
        Args:
            lead: Lead to add
        """
        # Check for duplicates
        if any(l.username == lead.username for l in self._leads):
            self.logger.debug(f"Duplicate lead skipped: @{lead.username}")
            return
        
        self._leads.append(lead)
        self.logger.debug(f"Added lead: @{lead.username}")

    def clear_leads(self) -> None:
        """Clear collected leads."""
        self._leads.clear()
        self.logger.debug("Cleared all leads")

    @abstractmethod
    async def scrape(self, query: str, max_results: int) -> List[Lead]:
        """Scrape for leads using the given query.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
        
        Returns:
            List of Lead objects
        """
        pass

    @abstractmethod
    async def scrape_profile(self, profile_url: str) -> Optional[Lead]:
        """Scrape a single profile.
        
        Args:
            profile_url: URL of the profile to scrape
        
        Returns:
            Lead object or None if failed
        """
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
