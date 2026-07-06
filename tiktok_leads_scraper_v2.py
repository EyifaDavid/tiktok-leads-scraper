import asyncio
import sqlite3
import random
import logging
import re
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
import pandas as pd

# ================== CONFIG ==================
SEARCH_QUERY = "logistics company OR freight forwarder OR shipping agent OR cargo"  # Logistics / freight forwarding niche
MAX_USERS = 100
PROXIES = [  # Format: "http://user:pass@ip:port" or "http://ip:port"
    # Add your residential proxies here
    "http://your-residential-proxy1:port",
]
HEADLESS = True
DB_FILE = "tiktok_leads.db"
OUTPUT_CSV = f"tiktok_leads_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
MIN_DELAY = 5
MAX_DELAY = 15
# ===========================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_emails(text):
    if not text:
        return ""
    found = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    return ", ".join(set(found))

def extract_phones(text):
    if not text:
        return ""
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
        r'(\+?\d{1,3}[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
    ]
    found = set()
    for p in patterns:
        for match in re.finditer(p, text):
            cleaned = re.sub(r'[^\d+]', '', match.group())
            if len(cleaned) >= 7:
                found.add(match.group().strip())
    return ", ".join(found)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute('''CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        profile_url TEXT,
        bio TEXT,
        emails TEXT,
        phones TEXT,
        followers TEXT,
        following TEXT,
        likes TEXT,
        external_link TEXT,
        verified BOOLEAN,
        scraped_at TEXT,
        source_query TEXT
    )''')
    conn.commit()
    return conn

async def get_random_proxy():
    return random.choice(PROXIES) if PROXIES and PROXIES[0] != "http://your-residential-proxy1:port" else None

async def human_delay(min_d=MIN_DELAY, max_d=MAX_DELAY):
    await asyncio.sleep(random.uniform(min_d, max_d))

async def scrape_profile(page, profile_url):
    try:
        await page.goto(profile_url, wait_until="networkidle", timeout=60000)
        await human_delay(4, 8)
        
        bio = await page.inner_text('div[data-e2e="user-bio"]', timeout=10000) if await page.locator('div[data-e2e="user-bio"]').count() > 0 else ""
        followers = await safe_text(page, '[data-e2e="followers-count"]')
        following = await safe_text(page, '[data-e2e="following-count"]')
        likes = await safe_text(page, '[data-e2e="likes-count"]')
        
        # External link
        link_elem = page.locator('a[href^="http"]:not([href*="tiktok.com"])')
        external_link = await link_elem.get_attribute('href') if await link_elem.count() > 0 else ""
        
        verified = await page.locator('svg[aria-label="Verified"]').count() > 0
        
        bio_text = bio.strip()
        return {
            "bio": bio_text,
            "emails": extract_emails(bio_text),
            "phones": extract_phones(bio_text),
            "followers": followers,
            "following": following,
            "likes": likes,
            "external_link": external_link,
            "verified": verified
        }
    except Exception as e:
        logging.warning(f"Profile scrape failed for {profile_url}: {e}")
        return {}

async def safe_text(page, selector):
    try:
        elem = page.locator(selector)
        return await elem.inner_text(timeout=5000) if await elem.count() > 0 else ""
    except:
        return ""

async def main():
    conn = init_db()
    leads = []
    cursor = conn.cursor()
    
    async with async_playwright() as p:
        proxy = await get_random_proxy()
        browser = await p.chromium.launch(
            headless=HEADLESS,
            proxy={"server": proxy} if proxy else None,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36"
        )
        await stealth_async(context)
        page = await context.new_page()
        
        search_url = f"https://www.tiktok.com/search/user?q={SEARCH_QUERY.replace(' ', '%20')}"
        await page.goto(search_url, wait_until="networkidle")
        await human_delay(5, 10)
        
        collected = 0
        while collected < MAX_USERS:
            await page.evaluate("window.scrollBy(0, 2000)")
            await human_delay(3, 7)
            
            user_cards = await page.query_selector_all('div[data-e2e="search-user-card"]')
            
            for card in user_cards:
                if collected >= MAX_USERS:
                    break
                try:
                    username_link = await card.query_selector('a[href^="/@"]')
                    if not username_link:
                        continue
                    username_href = await username_link.get_attribute('href')
                    username = username_href.strip('/@')
                    profile_url = f"https://www.tiktok.com{username_href}"
                    
                    # Basic card data
                    bio_elem = await card.query_selector('div[class*="UserBio"]')
                    basic_bio = await bio_elem.inner_text() if bio_elem else ""
                    followers_basic = await safe_text(card, 'span[class*="Count"]')
                    
                    # Deep scrape
                    profile_data = await scrape_profile(page, profile_url)
                    
                    profile_bio = profile_data.get("bio") or basic_bio
                    lead = {
                        "username": username,
                        "profile_url": profile_url,
                        "bio": profile_bio,
                        "emails": profile_data.get("emails") or extract_emails(basic_bio),
                        "phones": profile_data.get("phones") or extract_phones(basic_bio),
                        "followers": profile_data.get("followers") or followers_basic,
                        "following": profile_data.get("following"),
                        "likes": profile_data.get("likes"),
                        "external_link": profile_data.get("external_link"),
                        "verified": profile_data.get("verified", False),
                        "scraped_at": datetime.now().isoformat(),
                        "source_query": SEARCH_QUERY
                    }
                    
                    # Dedupe & save
                    cursor.execute("INSERT OR IGNORE INTO leads (username, profile_url, bio, emails, phones, followers, following, likes, external_link, verified, scraped_at, source_query) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                   (lead["username"], lead["profile_url"], lead["bio"], lead["emails"], lead["phones"], lead["followers"], lead["following"], lead["likes"], lead["external_link"], lead["verified"], lead["scraped_at"], lead["source_query"]))
                    conn.commit()
                    
                    leads.append(lead)
                    collected += 1
                    has_email = "📧" if lead["emails"] else ""
                    has_phone = "📞" if lead["phones"] else ""
                    logging.info(f"✅ @{username} | Followers: {lead['followers']} {has_email}{has_phone} | Link: {lead['external_link']}")
                    
                    await human_delay()
                    
                except Exception as e:
                    logging.error(f"Card error: {e}")
                    continue
            
            await human_delay(8, 15)
        
        await browser.close()
    
    # Export CSV
    if leads:
        df = pd.DataFrame(leads)
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        logging.info(f"✅ Exported {len(leads)} leads to {OUTPUT_CSV} and {DB_FILE}")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(main())
