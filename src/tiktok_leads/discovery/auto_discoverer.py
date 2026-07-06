"""Automatic lead discovery using multiple strategies."""

import asyncio
import random
import logging
from typing import List, Set, Optional
from urllib.parse import quote_plus

from tiktok_leads.discovery.queries import (
    SEARCH_QUERIES as DEFAULT_SEARCH_QUERIES,
    HASHTAGS as DEFAULT_HASHTAGS,
    INCLUDE_KEYWORDS as DEFAULT_INCLUDE_KEYWORDS,
    EXCLUDE_KEYWORDS as DEFAULT_EXCLUDE_KEYWORDS,
)
from tiktok_leads.models.lead import Lead
from tiktok_leads.utils.browser import human_delay, scroll_page, safe_get_text

logger = logging.getLogger(__name__)


class AutoDiscoverer:
    """Automatically discovers target accounts on TikTok."""

    TIKTOK_BASE_URL = "https://www.tiktok.com"
    SEARCH_URL = f"{TIKTOK_BASE_URL}/search/user?q={{query}}"
    HASHTAG_URL = f"{TIKTOK_BASE_URL}/tag/{{hashtag}}"

    SELECTORS = {
        "user_card": 'div[data-e2e="search-user-card"]',
        "username_link": 'a[href^="/@"]',
        "user_bio": 'div[class*="UserBio"]',
        "hashtag_page": 'div[data-e2e="challenge-item"]',
    }

    def __init__(
        self,
        search_queries: Optional[List[str]] = None,
        hashtags: Optional[List[str]] = None,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None,
    ):
        """Initialize auto-discoverer.

        Args:
            search_queries: Custom search queries (defaults from queries.py if None)
            hashtags: Custom hashtags (defaults from queries.py if None)
            include_keywords: Keywords to identify relevant accounts (defaults from queries.py if None)
            exclude_keywords: Keywords to filter out irrelevant accounts (defaults from queries.py if None)
        """
        self._search_queries = search_queries or DEFAULT_SEARCH_QUERIES
        self._hashtags = hashtags or DEFAULT_HASHTAGS
        self._include_keywords = include_keywords or DEFAULT_INCLUDE_KEYWORDS
        self._exclude_keywords = exclude_keywords or DEFAULT_EXCLUDE_KEYWORDS
        self._discovered_usernames: Set[str] = set()
        self._discovery_stats = {
            "queries_searched": 0,
            "hashtags_searched": 0,
            "profiles_found": 0,
            "profiles_filtered": 0,
        }

    @property
    def stats(self) -> dict:
        """Get discovery statistics."""
        return self._discovery_stats.copy()

    def _is_relevant_account(self, bio: str, username: str) -> bool:
        """Check if account appears relevant based on include/exclude keywords.

        Args:
            bio: Profile bio text
            username: TikTok username

        Returns:
            True if account matches inclusion criteria
        """
        bio_lower = bio.lower()
        username_lower = username.lower()

        # Check for exclude keywords first
        for keyword in self._exclude_keywords:
            if keyword in bio_lower or keyword in username_lower:
                return False

        # Check for include keywords
        for keyword in self._include_keywords:
            if keyword in bio_lower or keyword in username_lower:
                return True

        return False

    def _get_random_queries(self, count: int = 5) -> List[str]:
        """Get random search queries.
        
        Args:
            count: Number of queries to return
        
        Returns:
            List of random queries
        """
        return random.sample(self._search_queries, min(count, len(self._search_queries)))

    def _get_random_hashtags(self, count: int = 3) -> List[str]:
        """Get random hashtags.
        
        Args:
            count: Number of hashtags to return
        
        Returns:
            List of random hashtags
        """
        return random.sample(self._hashtags, min(count, len(self._hashtags)))

    async def discover_from_search(
        self,
        page,
        max_results: int = 50,
        queries: Optional[List[str]] = None,
    ) -> List[Lead]:
        """Discover leads from TikTok search.
        
        Args:
            page: Playwright page object
            max_results: Maximum leads to find
            queries: Optional custom queries (uses random if None)
        
        Returns:
            List of discovered leads
        """
        from tiktok_leads.parsers.contact_parser import ContactParser
        
        leads = []
        queries_to_use = queries or self._get_random_queries(10)
        
        for query in queries_to_use:
            if len(leads) >= max_results:
                break
            
            self._discovery_stats["queries_searched"] += 1
            
            try:
                # Navigate to search
                search_url = self.SEARCH_URL.format(query=quote_plus(query))
                await page.goto(search_url, wait_until="domcontentloaded")
                await human_delay(5, 10)
                
                # Scroll and collect
                new_leads = await self._collect_from_page(
                    page, query, max_results - len(leads)
                )
                leads.extend(new_leads)
                
                logger.info(
                    f"Query '{query}': Found {len(new_leads)} leads "
                    f"(Total: {len(leads)})"
                )
                
                await human_delay(10, 20)
                
            except Exception as e:
                logger.warning(f"Failed to search query '{query}': {e}")
                continue
        
        return leads[:max_results]

    async def discover_from_hashtags(
        self,
        page,
        max_results: int = 50,
        hashtags: Optional[List[str]] = None,
    ) -> List[Lead]:
        """Discover leads from TikTok hashtags.
        
        Args:
            page: Playwright page object
            max_results: Maximum leads to find
            hashtags: Optional custom hashtags (uses random if None)
        
        Returns:
            List of discovered leads
        """
        leads = []
        hashtags_to_use = hashtags or self._get_random_hashtags(5)
        
        for hashtag in hashtags_to_use:
            if len(leads) >= max_results:
                break
            
            self._discovery_stats["hashtags_searched"] += 1
            
            try:
                # Navigate to hashtag page
                hashtag_url = self.HASHTAG_URL.format(hashtag=hashtag)
                await page.goto(hashtag_url, wait_until="domcontentloaded")
                await human_delay(5, 10)
                
                # Scroll and collect
                new_leads = await self._collect_from_page(
                    page, f"#{hashtag}", max_results - len(leads)
                )
                leads.extend(new_leads)
                
                logger.info(
                    f"Hashtag '#{hashtag}': Found {len(new_leads)} leads "
                    f"(Total: {len(leads)})"
                )
                
                await human_delay(10, 20)
                
            except Exception as e:
                logger.warning(f"Failed to search hashtag '#{hashtag}': {e}")
                continue
        
        return leads[:max_results]

    async def _collect_from_page(
        self,
        page,
        source: str,
        max_results: int,
    ) -> List[Lead]:
        """Collect leads from current page.
        
        Args:
            page: Playwright page object
            source: Source query/hashtag
            max_results: Maximum leads to collect
        
        Returns:
            List of leads found
        """
        from tiktok_leads.parsers.contact_parser import ContactParser
        
        leads = []
        scroll_attempts = 0
        max_scrolls = 10
        
        while len(leads) < max_results and scroll_attempts < max_scrolls:
            # Scroll to load more
            await scroll_page(page, 2000)
            await human_delay(3, 7)
            
            # Get user cards
            user_cards = await page.query_selector_all(self.SELECTORS["user_card"])
            
            if not user_cards:
                scroll_attempts += 1
                continue
            
            for card in user_cards:
                if len(leads) >= max_results:
                    break
                
                try:
                    # Extract username
                    username_link = await card.query_selector(
                        self.SELECTORS["username_link"]
                    )
                    if not username_link:
                        continue
                    
                    username_href = await username_link.get_attribute("href")
                    username = username_href.strip("/@")
                    
                    # Skip if already discovered
                    if username in self._discovered_usernames:
                        continue
                    
                    # Get bio from card
                    bio_elem = await card.query_selector(self.SELECTORS["user_bio"])
                    bio = await bio_elem.inner_text() if bio_elem else ""
                    
                    # Filter: only keep relevant accounts
                    if not self._is_relevant_account(bio, username):
                        self._discovery_stats["profiles_filtered"] += 1
                        continue
                    
                    # Extract contacts
                    contacts = ContactParser.extract_contacts(bio)
                    
                    # Create lead
                    profile_url = f"https://www.tiktok.com{username_href}"
                    lead = Lead(
                        username=username,
                        profile_url=profile_url,
                        bio=bio,
                        emails=ContactParser.format_emails(contacts["emails"]),
                        phones=ContactParser.format_phones(contacts["phones"]),
                        source_query=source,
                    )
                    
                    leads.append(lead)
                    self._discovered_usernames.add(username)
                    self._discovery_stats["profiles_found"] += 1
                    
                    has_email = "📧" if lead.has_email() else ""
                    has_phone = "📞" if lead.has_phone() else ""
                    logger.info(
                        f"✅ @{username} | {bio[:50]}... "
                        f"{has_email}{has_phone}"
                    )
                    
                except Exception as e:
                    logger.debug(f"Failed to process card: {e}")
                    continue
            
            await human_delay(5, 10)
        
        return leads

    async def discover_all(
        self,
        page,
        max_results: int = 100,
    ) -> List[Lead]:
        """Run full automatic discovery using all strategies.
        
        Args:
            page: Playwright page object
            max_results: Maximum total leads to find
        
        Returns:
            List of all discovered leads
        """
        logger.info("Starting automatic discovery...")
        logger.info(f"Strategies: Search queries + Hashtags")
        
        all_leads = []
        
        # Phase 1: Search-based discovery
        logger.info("Phase 1: Searching TikTok...")
        search_leads = await self.discover_from_search(page, max_results // 2)
        all_leads.extend(search_leads)
        
        # Phase 2: Hashtag-based discovery
        logger.info("Phase 2: Scanning hashtags...")
        hashtag_leads = await self.discover_from_hashtags(
            page, max_results - len(all_leads)
        )
        all_leads.extend(hashtag_leads)
        
        # Log final stats
        stats = self.stats
        logger.info(
            f"Discovery complete: "
            f"{stats['queries_searched']} queries, "
            f"{stats['hashtags_searched']} hashtags, "
            f"{stats['profiles_found']} profiles found, "
            f"{stats['profiles_filtered']} filtered out"
        )
        
        return all_leads[:max_results]
