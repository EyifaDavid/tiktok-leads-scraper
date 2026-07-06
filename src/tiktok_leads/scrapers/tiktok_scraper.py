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
    random_viewport,
    random_user_agent,
)
from tiktok_leads.utils.retry import retry_async, is_transient_error
from tiktok_leads.exceptions import BrowserError, SoftBlockError

logger = logging.getLogger(__name__)


class TikTokScraper(BaseScraper):
    """TikTok scraper for collecting leads."""
    
    SEARCH_URL_TEMPLATE = "https://www.tiktok.com/search/user?q={query}"
    PROFILE_URL_TEMPLATE = "https://www.tiktok.com/@{username}"
    HOME_URL = "https://www.tiktok.com"
    
    SELECTORS = {
        "user_card": 'div[data-e2e="search-user-card"]',
        "username_link": 'a[href^="/@"]',
        "user_bio": 'div[data-e2e="user-bio"]',
        "followers_count": '[data-e2e="followers-count"]',
        "following_count": '[data-e2e="following-count"]',
        "likes_count": '[data-e2e="likes-count"]',
        "verified_badge": 'svg[aria-label="Verified"]',
    }

    MAX_CONTEXT_ROTATIONS = 3

    def __init__(self, config: Settings):
        """Initialize TikTok scraper."""
        super().__init__(config)
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._context_rotations = 0
        self._visited_home = False

    async def __aenter__(self):
        await self._launch_browser()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_browser()

    async def _launch_browser(self) -> None:
        """Launch Playwright browser."""
        try:
            self._playwright = await async_playwright().start()
            proxy = self._get_random_proxy()
            launch_args = {
                "headless": self.config.headless,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                ],
            }
            if proxy:
                launch_args["proxy"] = {"server": proxy}

            self._browser = await self._playwright.chromium.launch(**launch_args)
            await self._create_context()
            self.logger.info("Browser launched successfully")
        except Exception as e:
            raise BrowserError(f"Failed to launch browser: {e}") from e

    async def _create_context(self) -> None:
        """Create a fresh browser context with random fingerprint."""
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass

        vp_width, vp_height = random_viewport()
        ua = random_user_agent()

        context_args = {
            "viewport": {"width": vp_width, "height": vp_height},
            "user_agent": ua,
            "locale": "en-US",
            "timezone_id": random.choice([
                "America/New_York", "America/Chicago", "America/Los_Angeles",
                "Europe/London", "Europe/Paris", "Asia/Tokyo",
            ]),
            "geolocation": {"latitude": 40.7128, "longitude": -74.0060},
            "permissions": ["geolocation"],
        }

        self._context = await self._browser.new_context(**context_args)
        stealth = Stealth()
        await stealth.apply_stealth_async(self._context)

        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)

        self._page = await self._context.new_page()
        self._visited_home = False
        self.logger.info(f"Created new context: {vp_width}x{vp_height}, {ua[:50]}...")

    async def _rotate_context(self) -> bool:
        """Rotate to a fresh browser context (new fingerprint).
        
        Returns:
            True if rotation succeeded, False if max rotations reached
        """
        self._context_rotations += 1
        if self._context_rotations > self.MAX_CONTEXT_ROTATIONS:
            self.logger.error(f"Max context rotations ({self.MAX_CONTEXT_ROTATIONS}) reached")
            return False

        self.logger.info(f"Rotating context (attempt {self._context_rotations}/{self.MAX_CONTEXT_ROTATIONS})...")
        await self._create_context()
        await human_delay(5, 10)
        return True

    async def _visit_homepage_first(self) -> None:
        """Visit TikTok homepage before any search to appear as a real user."""
        if self._visited_home:
            return
        try:
            self.logger.info("Visiting TikTok homepage first...")
            await self._page.goto(self.HOME_URL, wait_until="domcontentloaded", timeout=30000)
            await human_delay(3, 6)
            await scroll_page(self._page, random.randint(300, 800))
            await human_delay(2, 4)
            self._visited_home = True
        except Exception as e:
            self.logger.warning(f"Homepage visit failed (non-critical): {e}")

    async def _login_to_tiktok(self) -> bool:
        """Log into TikTok if credentials are configured.

        Returns:
            True if already logged-in or login succeeded, False on failure.
        """
        email = self.config.tiktok_email
        password = self.config.tiktok_password
        if not email or not password:
            self.logger.info("No TikTok credentials configured, skipping login")
            return True

        try:
            self.logger.info("Logging into TikTok...")
            await self._page.goto(f"{self.HOME_URL}/login", wait_until="domcontentloaded", timeout=30000)
            await human_delay(3, 6)

            # Try "Use phone / email / username" to switch to email login
            switch_btn = await self._page.query_selector('[data-e2e="login-other-methods"]')
            if switch_btn:
                await switch_btn.click()
                await human_delay(2, 4)

            email_input = await self._page.query_selector('input[name="username"]')
            if not email_input:
                email_input = await self._page.query_selector('input[type="text"][placeholder*="email" i]')
            if not email_input:
                email_input = await self._page.query_selector('input[placeholder*="Phone" i]')

            if not email_input:
                self.logger.warning("Could not find email input on login page")
                return False

            await email_input.click()
            await email_input.fill(email)
            await human_delay(1, 3)

            pass_input = await self._page.query_selector('input[type="password"]')
            if not pass_input:
                self.logger.warning("Could not find password input on login page")
                return False

            await pass_input.click()
            await pass_input.fill(password)
            await human_delay(1, 3)

            login_btn = await self._page.query_selector('button[data-e2e="login-submit"]')
            if login_btn:
                await login_btn.click()
            else:
                await pass_input.press("Enter")

            await human_delay(5, 10)

            current_url = self._page.url
            if "/login" not in current_url and "/verify" not in current_url:
                self.logger.info("TikTok login successful")
                return True

            self.logger.warning("TikTok login may have failed (still on login page)")
            return False
        except Exception as e:
            self.logger.warning(f"TikTok login failed: {e}")
            return False

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
        proxies = self.config.proxy_list
        if proxies:
            return random.choice(proxies)
        return None

    async def _scrape_with_block_recovery(
        self,
        scrape_fn,
        *args,
        **kwargs,
    ) -> List[Lead]:
        """Run a scrape function with automatic block recovery via context rotation.
        
        Retries up to MAX_CONTEXT_ROTATIONS times, rotating browser context on soft block.
        """
        for attempt in range(self.MAX_CONTEXT_ROTATIONS + 1):
            try:
                if attempt > 0:
                    ok = await self._rotate_context()
                    if not ok:
                        break
                    self.logger.info(f"Retry attempt {attempt} with fresh context...")

                return await scrape_fn(*args, **kwargs)

            except SoftBlockError as e:
                self.logger.warning(f"Soft block on attempt {attempt}: {e}")
                if attempt >= self.MAX_CONTEXT_ROTATIONS:
                    self.logger.error("All retries exhausted due to soft blocks")
                    return self._leads
                await human_delay(10, 20)

        return self._leads

    async def scrape(self, query: str, max_results: int) -> List[Lead]:
        """Scrape TikTok for leads using search query."""
        self.logger.info(f"Starting TikTok scrape for: {query}")
        self.clear_leads()
        self._context_rotations = 0

        return await self._scrape_with_block_recovery(
            self._scrape_impl, query, max_results
        )

    async def _scrape_impl(self, query: str, max_results: int) -> List[Lead]:
        """Internal scrape implementation (called with block recovery)."""
        await self._visit_homepage_first()
        await self._login_to_tiktok()

        search_url = self.SEARCH_URL_TEMPLATE.format(query=quote_plus(query))
        await self._page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await human_delay(5, 10)

        if await self._is_soft_blocked():
            raise SoftBlockError("TikTok soft block detected on search page")

        collected = 0
        scroll_attempts = 0
        max_scroll_attempts = 20

        while collected < max_results and scroll_attempts < max_scroll_attempts:
            await scroll_page(self._page, random.randint(1500, 2500))
            await human_delay(3, 7)

            if await self._is_soft_blocked():
                raise SoftBlockError("Soft block detected during scroll")

            user_cards = await self._page.query_selector_all(self.SELECTORS["user_card"])

            if not user_cards:
                scroll_attempts += 1
                self.logger.debug(f"No user cards found, scroll attempt {scroll_attempts}")
                continue

            for card in user_cards:
                if collected >= max_results:
                    break

                try:
                    lead = await self._process_user_card(card, query)
                    if lead:
                        self.add_lead(lead)
                        collected += 1

                        has_email = "📧" if lead.has_email() else ""
                        has_phone = "📞" if lead.has_phone() else ""
                        self.logger.info(
                            f"✅ @{lead.username} | Followers: {lead.followers} "
                            f"{has_email}{has_phone} | Link: {lead.external_link}"
                        )

                        await human_delay(
                            self.config.min_delay,
                            self.config.max_delay,
                        )
                except Exception as e:
                    self.logger.error(f"Failed to process user card: {e}")
                    continue

            await human_delay(8, 15)

        self.logger.info(f"Scrape completed. Collected {len(self._leads)} leads")
        return self._leads

    async def auto_discover(self, max_results: int = 100) -> List[Lead]:
        """Automatically discover leads using multiple strategies."""
        self.logger.info("Starting automatic discovery...")
        self.clear_leads()
        self._context_rotations = 0

        return await self._scrape_with_block_recovery(
            self._auto_discover_impl, max_results
        )

    async def _auto_discover_impl(self, max_results: int = 100) -> List[Lead]:
        """Internal auto-discover implementation."""
        await self._visit_homepage_first()
        await self._login_to_tiktok()

        if await self._is_soft_blocked():
            raise SoftBlockError("TikTok soft block detected on homepage")

        discoverer = AutoDiscoverer(
            search_queries=self.config.discovery_queries_list,
            hashtags=self.config.discovery_hashtags_list,
            include_keywords=self.config.include_keywords_list,
            exclude_keywords=self.config.exclude_keywords_list,
        )
        discovered_leads = await discoverer.discover_all(self._page, max_results)

        for lead in discovered_leads:
            try:
                profile_data = await self._scrape_profile_page(lead.profile_url)

                if profile_data:
                    lead.bio = profile_data.get("bio") or lead.bio
                    lead.emails = profile_data.get("emails") or lead.emails
                    lead.phones = profile_data.get("phones") or lead.phones
                    lead.followers = profile_data.get("followers") or lead.followers
                    lead.following = profile_data.get("following") or lead.following
                    lead.likes = profile_data.get("likes") or lead.likes
                    lead.external_link = profile_data.get("external_link") or lead.external_link
                    lead.verified = profile_data.get("verified", False)

                self.add_lead(lead)

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
                self.add_lead(lead)

        self.logger.info(f"Auto-discovery complete. Collected {len(self._leads)} leads")
        return self._leads

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
            await self._page.goto(profile_url, wait_until="domcontentloaded")
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
            await self._page.goto(profile_url, wait_until="domcontentloaded")
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
            page_content = await self._page.content()
            content_lower = page_content.lower()

            block_indicators = [
                "verify you are human",
                "verify your identity",
                "captcha",
                "unusual traffic",
                "automated requests",
                "blocked",
                "suspicious activity",
                "please try again later",
                "access denied",
                "challenge",
                "robot",
                "automated behavior",
            ]

            if any(indicator in content_lower for indicator in block_indicators):
                return True

            title = await self._page.title()
            if any(t in title.lower() for t in ["challenge", "verify", "blocked", "captcha"]):
                return True

            page_url = self._page.url
            if any(p in page_url.lower() for p in ["challenge", "captcha", "verify"]):
                return True

            return False
        except Exception:
            return False
