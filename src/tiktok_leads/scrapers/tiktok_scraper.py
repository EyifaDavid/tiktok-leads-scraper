"""TikTok scraper implementation."""

import asyncio
import random
import logging
from datetime import datetime
from typing import Optional, List
from urllib.parse import quote_plus

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from playwright_stealth import Stealth

from tiktok_leads.scrapers.base_scraper import BaseScraper
from tiktok_leads.config import Settings
from tiktok_leads.models.lead import Lead, LeadCreate
from tiktok_leads.parsers.contact_parser import ContactParser
from tiktok_leads.discovery.auto_discoverer import AutoDiscoverer
from tiktok_leads.utils.browser import (
    human_delay,
    safe_get_text,
    safe_get_attribute,
    scroll_page,
    check_element_exists,
)
from tiktok_leads.utils.retry import retry_async, is_transient_error
from tiktok_leads.exceptions import BrowserError, SoftBlockError

logger = logging.getLogger(__name__)


class TikTokScraper(BaseScraper):
    """TikTok scraper for collecting leads."""
    
    SEARCH_URL_TEMPLATE = "https://www.tiktok.com/search/user?q={query}"
    PROFILE_URL_TEMPLATE = "https://www.tiktok.com/@{username}"
    
    # TikTok-specific selectors
    SELECTORS = {
        "user_card": 'div[data-e2e="search-user-card"]',
        "username_link": 'a[href^="/@"]',
        "user_bio": 'div[data-e2e="user-bio"]',
        "followers_count": '[data-e2e="followers-count"]',
        "following_count": '[data-e2e="following-count"]',
        "likes_count": '[data-e2e="likes-count"]',
        "verified_badge": 'svg[aria-label="Verified"]',
    }

    def __init__(self, config: Settings):
        """Initialize TikTok scraper.
        
        Args:
            config: Application settings
        """
        super().__init__(config)
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

    async def __aenter__(self):
        """Async context manager entry - launch browser."""
        await self._launch_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - close browser."""
        await self._close_browser()

    async def _launch_browser(self) -> None:
        """Launch Playwright browser."""
        try:
            self._playwright = await async_playwright().start()
            
            # Get proxy configuration
            proxy = self._get_random_proxy()
            launch_args = {
                "headless": self.config.headless,
                "args": ["--disable-blink-features=AutomationControlled"],
            }
            if proxy:
                launch_args["proxy"] = {"server": proxy}
            
            self._browser = await self._playwright.chromium.launch(**launch_args)
            
            # Create browser context
            context_args = {
                "viewport": {
                    "width": self.config.viewport_width,
                    "height": self.config.viewport_height,
                },
                "user_agent": self.config.user_agent,
            }
            self._context = await self._browser.new_context(**context_args)
            stealth = Stealth()
            await stealth.apply_stealth_async(self._context)
            
            self._page = await self._context.new_page()
            
            self.logger.info("Browser launched successfully")
        except Exception as e:
            raise BrowserError(f"Failed to launch browser: {e}") from e

    async def _close_browser(self) -> None:
        """Close Playwright browser."""
        try:
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()
            self.logger.info("Browser closed successfully")
        except Exception as e:
            self.logger.warning(f"Error closing browser: {e}")

    def _get_random_proxy(self) -> Optional[str]:
        """Get a random proxy from the configuration.
        
        Returns:
            Proxy URL or None for direct connection
        """
        proxies = self.config.proxy_list
        if proxies:
            return random.choice(proxies)
        return None

    async def scrape(self, query: str, max_results: int) -> List[Lead]:
        """Scrape TikTok for leads using search query.
        
        Args:
            query: Search query
            max_results: Maximum number of leads to collect
        
        Returns:
            List of Lead objects
        """
        self.logger.info(f"Starting TikTok scrape for: {query}")
        self.clear_leads()
        
        try:
            # Navigate to search page
            search_url = self.SEARCH_URL_TEMPLATE.format(query=quote_plus(query))
            await self._page.goto(search_url, wait_until="networkidle")
            await human_delay(5, 10)
            
            # Check for soft block
            if await self._is_soft_blocked():
                raise SoftBlockError("TikTok soft block detected")
            
            collected = 0
            scroll_attempts = 0
            max_scroll_attempts = 20
            
            while collected < max_results and scroll_attempts < max_scroll_attempts:
                # Scroll down to load more results
                await scroll_page(self._page, 2000)
                await human_delay(3, 7)
                
                # Get user cards
                user_cards = await self._page.query_selector_all(self.SELECTORS["user_card"])
                
                if not user_cards:
                    scroll_attempts += 1
                    self.logger.debug(f"No user cards found, scroll attempt {scroll_attempts}")
                    continue
                
                # Process each user card
                for card in user_cards:
                    if collected >= max_results:
                        break
                    
                    try:
                        lead = await self._process_user_card(card, query)
                        if lead:
                            self.add_lead(lead)
                            collected += 1
                            
                            # Log progress
                            has_email = "📧" if lead.has_email() else ""
                            has_phone = "📞" if lead.has_phone() else ""
                            self.logger.info(
                                f"✅ @{lead.username} | Followers: {lead.followers} "
                                f"{has_email}{has_phone} | Link: {lead.external_link}"
                            )
                            
                            # Delay between profiles
                            await human_delay(
                                self.config.min_delay,
                                self.config.max_delay,
                            )
                    except Exception as e:
                        self.logger.error(f"Failed to process user card: {e}")
                        continue
                
                # Delay between scrolls
                await human_delay(8, 15)
            
            self.logger.info(f"Scrape completed. Collected {len(self._leads)} leads")
            return self._leads
            
        except SoftBlockError:
            self.logger.error("Soft block detected, stopping scrape")
            raise
        except Exception as e:
            self.logger.error(f"Scrape failed: {e}")
            raise

    async def auto_discover(self, max_results: int = 100) -> List[Lead]:
        """Automatically discover leads using multiple strategies.
        
        Uses configured search queries and hashtags to find accounts
        matching the configured include/exclude keywords.
        
        Args:
            max_results: Maximum number of leads to discover
        
        Returns:
            List of discovered Lead objects
        """
        self.logger.info("Starting automatic discovery...")
        self.clear_leads()
        
        try:
            # Check for soft block
            if await self._is_soft_blocked():
                raise SoftBlockError("TikTok soft block detected")
            
            # Use auto-discoverer with config overrides
            discoverer = AutoDiscoverer(
                search_queries=self.config.discovery_queries_list,
                hashtags=self.config.discovery_hashtags_list,
                include_keywords=self.config.include_keywords_list,
                exclude_keywords=self.config.exclude_keywords_list,
            )
            discovered_leads = await discoverer.discover_all(self._page, max_results)
            
            # Deep scrape each discovered profile for more details
            for lead in discovered_leads:
                try:
                    # Scrape full profile for additional data
                    profile_data = await self._scrape_profile_page(lead.profile_url)
                    
                    if profile_data:
                        # Update lead with deep-scraped data
                        lead.bio = profile_data.get("bio") or lead.bio
                        lead.emails = profile_data.get("emails") or lead.emails
                        lead.phones = profile_data.get("phones") or lead.phones
                        lead.followers = profile_data.get("followers") or lead.followers
                        lead.following = profile_data.get("following") or lead.following
                        lead.likes = profile_data.get("likes") or lead.likes
                        lead.external_link = profile_data.get("external_link") or lead.external_link
                        lead.verified = profile_data.get("verified", False)
                    
                    self.add_lead(lead)
                    
                    # Log with contact indicators
                    has_email = "📧" if lead.has_email() else ""
                    has_phone = "📞" if lead.has_phone() else ""
                    self.logger.info(
                        f"✅ @{lead.username} | {lead.bio[:50]}... "
                        f"{has_email}{has_phone}"
                    )
                    
                    await human_delay(
                        self.config.min_delay,
                        self.config.max_delay,
                    )
                    
                except Exception as e:
                    self.logger.warning(f"Failed to deep scrape @{lead.username}: {e}")
                    # Still add the lead even if deep scrape fails
                    self.add_lead(lead)
            
            self.logger.info(f"Auto-discovery complete. Collected {len(self._leads)} leads")
            return self._leads
            
        except SoftBlockError:
            self.logger.error("Soft block detected, stopping discovery")
            raise
        except Exception as e:
            self.logger.error(f"Auto-discovery failed: {e}")
            raise

    async def scrape_profile(self, profile_url: str) -> Optional[Lead]:
        """Scrape a single TikTok profile.
        
        Args:
            profile_url: Full profile URL or username
        
        Returns:
            Lead object or None if failed
        """
        # Normalize URL
        if not profile_url.startswith("http"):
            profile_url = self.PROFILE_URL_TEMPLATE.format(
                username=profile_url.lstrip("@")
            )
        
        try:
            await self._page.goto(profile_url, wait_until="networkidle")
            await human_delay(4, 8)
            
            # Extract profile data
            profile_data = await self._extract_profile_data()
            
            # Create lead from profile data
            username = profile_url.split("@")[-1].split("/")[0]
            
            lead = Lead(
                username=username,
                profile_url=profile_url,
                bio=profile_data.get("bio", ""),
                emails=profile_data.get("emails", ""),
                phones=profile_data.get("phones", ""),
                followers=profile_data.get("followers", ""),
                following=profile_data.get("following", ""),
                likes=profile_data.get("likes", ""),
                external_link=profile_data.get("external_link", ""),
                verified=profile_data.get("verified", False),
                scraped_at=datetime.now(),
            )
            
            return lead
            
        except Exception as e:
            self.logger.warning(f"Failed to scrape profile {profile_url}: {e}")
            return None

    async def _process_user_card(self, card, query: str) -> Optional[Lead]:
        """Process a user card from search results.
        
        Args:
            card: Playwright element handle for user card
            query: Search query
        
        Returns:
            Lead object or None if failed
        """
        try:
            # Extract username and profile URL
            username_link = await card.query_selector(self.SELECTORS["username_link"])
            if not username_link:
                return None
            
            username_href = await username_link.get_attribute("href")
            username = username_href.strip("/@")
            profile_url = f"https://www.tiktok.com{username_href}"
            
            # Get basic bio from card
            bio_elem = await card.query_selector('div[class*="UserBio"]')
            basic_bio = await bio_elem.inner_text() if bio_elem else ""
            
            # Get followers from card
            followers_basic = await safe_get_text(
                card.locator('span[class*="Count"]'),
                timeout=5000,
            )
            
            # Deep scrape profile page for more data
            profile_data = await self._scrape_profile_page(profile_url)
            
            # Merge data (deep scrape takes priority)
            profile_bio = profile_data.get("bio") or basic_bio
            emails = profile_data.get("emails") or ContactParser.format_emails(
                ContactParser.extract_emails(basic_bio)
            )
            phones = profile_data.get("phones") or ContactParser.format_phones(
                ContactParser.extract_phones(basic_bio)
            )
            followers = profile_data.get("followers") or followers_basic
            
            # Create lead
            lead = Lead(
                username=username,
                profile_url=profile_url,
                bio=profile_bio,
                emails=emails,
                phones=phones,
                followers=followers,
                following=profile_data.get("following", ""),
                likes=profile_data.get("likes", ""),
                external_link=profile_data.get("external_link", ""),
                verified=profile_data.get("verified", False),
                scraped_at=datetime.now(),
                source_query=query,
            )
            
            return lead
            
        except Exception as e:
            self.logger.error(f"Failed to process user card: {e}")
            return None

    async def _scrape_profile_page(self, profile_url: str) -> dict:
        """Scrape a profile page for detailed information.
        
        Args:
            profile_url: Profile URL to scrape
        
        Returns:
            Dictionary with profile data
        """
        try:
            await self._page.goto(profile_url, wait_until="networkidle")
            await human_delay(4, 8)
            
            return await self._extract_profile_data()
        except Exception as e:
            self.logger.warning(f"Failed to scrape profile page: {e}")
            return {}

    async def _extract_profile_data(self) -> dict:
        """Extract profile data from current page.
        
        Returns:
            Dictionary with profile data
        """
        try:
            # Extract bio
            bio = ""
            if await check_element_exists(self._page, self.SELECTORS["user_bio"]):
                bio_elem = self._page.locator(self.SELECTORS["user_bio"])
                bio = await safe_get_text(bio_elem, timeout=10000)
            
            # Extract stats
            followers = await safe_get_text(
                self._page.locator(self.SELECTORS["followers_count"])
            )
            following = await safe_get_text(
                self._page.locator(self.SELECTORS["following_count"])
            )
            likes = await safe_get_text(
                self._page.locator(self.SELECTORS["likes_count"])
            )
            
            # Extract external link
            link_elem = self._page.locator(
                'a[href^="http"]:not([href*="tiktok.com"])'
            )
            external_link = await safe_get_attribute(link_elem, "href") or ""
            
            # Check verification
            verified = await check_element_exists(
                self._page, self.SELECTORS["verified_badge"]
            )
            
            # Extract contacts from bio
            contacts = ContactParser.extract_contacts(bio)
            
            return {
                "bio": bio.strip(),
                "emails": ContactParser.format_emails(contacts["emails"]),
                "phones": ContactParser.format_phones(contacts["phones"]),
                "followers": followers,
                "following": following,
                "likes": likes,
                "external_link": external_link,
                "verified": verified,
            }
        except Exception as e:
            self.logger.warning(f"Failed to extract profile data: {e}")
            return {}

    async def _is_soft_blocked(self) -> bool:
        """Check if we're soft blocked by TikTok.
        
        Returns:
            True if soft blocked
        """
        try:
            # Check for common block indicators
            page_content = await self._page.content()
            block_indicators = [
                "verify you are human",
                "captcha",
                "blocked",
                "suspicious activity",
            ]
            
            content_lower = page_content.lower()
            return any(indicator in content_lower for indicator in block_indicators)
        except Exception:
            return False
