"""Background agent that polls Railway for pending jobs and runs them locally.

Run it once — it stays alive, polling every 30 seconds:
    python scraper_agent.py

Environment variables:
    API_URL           - Backend URL (default: Railway)
    SCRAPER_EMAIL     - Railway login email
    SCRAPER_PASSWORD  - Railway login password
    TIKTOK_EMAIL      - TikTok login email
    TIKTOK_PASSWORD   - TikTok login password
"""

import asyncio
import json
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from tiktok_leads.config import get_settings
from tiktok_leads.scrapers.tiktok_scraper import TikTokScraper
from tiktok_leads.logging_config import setup_logging


POLL_INTERVAL = 30  # seconds
API_URL = os.getenv("API_URL", "https://tiktok-leads-scraper-production.up.railway.app").rstrip("/")


def _request(method: str, url: str, data: dict = None, token: str = None) -> dict:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        print(f"[agent] HTTP {e.code}: {msg[:200]}")
        return None


class ScraperAgent:
    def __init__(self, api_url: str, email: str, password: str):
        self.api_url = api_url
        self.email = email
        self.password = password
        self.token = None

    def login(self) -> bool:
        result = _request("POST", f"{self.api_url}/api/auth/login", {"email": self.email, "password": self.password})
        if result and "access_token" in result:
            self.token = result["access_token"]
            print(f"[agent] Logged in as {self.email}")
            return True
        print(f"[agent] Login failed")
        return False

    def get_pending_jobs(self) -> list:
        result = _request("GET", f"{self.api_url}/api/scrape/jobs?status=pending&limit=10", token=self.token)
        if result:
            return result.get("jobs", [])
        return []

    def claim_job(self, job_id: int) -> dict:
        return _request("POST", f"{self.api_url}/api/scrape/jobs/{job_id}/claim", token=self.token)

    def upload_leads(self, job_id: int, leads: list) -> bool:
        payload = {
            "job_id": job_id,
            "leads": [
                {
                    "username": l.username,
                    "profile_url": l.profile_url,
                    "bio": getattr(l, "bio", ""),
                    "emails": getattr(l, "emails", ""),
                    "phones": getattr(l, "phones", ""),
                    "followers": getattr(l, "followers", "0"),
                    "following": getattr(l, "following", "0"),
                    "likes": getattr(l, "likes", "0"),
                    "external_link": getattr(l, "external_link", ""),
                    "verified": getattr(l, "verified", False),
                }
                for l in leads
            ],
        }
        result = _request("POST", f"{self.api_url}/api/leads/bulk", payload, self.token)
        if result:
            print(f"[agent] Uploaded {result.get('uploaded', 0)} leads for job {job_id}")
            return True
        return False

    async def run_job(self, job: dict) -> None:
        job_id = job["id"]
        mode = job["mode"]
        query = job.get("query", "")
        max_leads = job.get("max_leads", 50)

        print(f"[agent] Running job {job_id}: mode={mode} query=\"{query}\" max={max_leads}")

        config = get_settings()
        tiktok_email = os.getenv("TIKTOK_EMAIL") or ""
        tiktok_password = os.getenv("TIKTOK_PASSWORD") or ""
        if tiktok_email:
            os.environ["TIKTOK_EMAIL"] = tiktok_email
        if tiktok_password:
            os.environ["TIKTOK_PASSWORD"] = tiktok_password

        try:
            async with TikTokScraper(config) as scraper:
                if mode == "auto":
                    leads = await scraper.auto_discover(max_leads)
                elif mode == "profile":
                    lead = await scraper.scrape_profile(query)
                    leads = [lead] if lead else []
                else:
                    leads = await scraper.scrape(query, max_leads)
        except Exception as e:
            print(f"[agent] Job {job_id} scraper error: {e}")
            leads = []

        if leads:
            self.upload_leads(job_id, leads)
        else:
            print(f"[agent] Job {job_id}: no leads found, marking as completed with 0 leads")
            self.upload_leads(job_id, [])

    async def poll_forever(self):
        print(f"[agent] Starting poll loop (every {POLL_INTERVAL}s) for {self.api_url}")
        while True:
            try:
                if not self.token:
                    if not self.login():
                        await asyncio.sleep(POLL_INTERVAL)
                        continue

                jobs = self.get_pending_jobs()
                if jobs:
                    print(f"[agent] Found {len(jobs)} pending job(s)")

                for job in jobs:
                    claimed = self.claim_job(job["id"])
                    if claimed:
                        await self.run_job(claimed)
                    else:
                        print(f"[agent] Could not claim job {job['id']} (taken by another agent)")

            except Exception as e:
                print(f"[agent] Poll error: {e}")
                self.token = None

            await asyncio.sleep(POLL_INTERVAL)


async def main():
    email = os.getenv("SCRAPER_EMAIL")
    password = os.getenv("SCRAPER_PASSWORD")

    if not email or not password:
        print("ERROR: Set SCRAPER_EMAIL and SCRAPER_PASSWORD env vars")
        sys.exit(1)

    setup_logging("INFO", "logs/agent.log")

    agent = ScraperAgent(API_URL, email, password)
    await agent.poll_forever()


if __name__ == "__main__":
    asyncio.run(main())
