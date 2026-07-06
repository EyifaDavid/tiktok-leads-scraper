"""Local TikTok scraper that uploads results to the Railway backend.

Usage:
    python local_scrape.py --query "twerking" --max 50
    python local_scrape.py --auto --max 100
    python local_scrape.py --profile https://www.tiktok.com/@username

Environment variables:
    API_URL          - Backend URL (default: Railway)
    SCRAPER_EMAIL    - Login email
    SCRAPER_PASSWORD - Login password
"""

import asyncio
import json
import os
import sys
import argparse
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from tiktok_leads.config import get_settings
from tiktok_leads.scrapers.tiktok_scraper import TikTokScraper
from tiktok_leads.logging_config import setup_logging


API_URL = os.getenv("API_URL", "https://tiktok-leads-scraper-production.up.railway.app")
EMAIL = os.getenv("SCRAPER_EMAIL")
PASSWORD = os.getenv("SCRAPER_PASSWORD")


def parse_args():
    parser = argparse.ArgumentParser(description="Local TikTok scraper with Railway sync")
    parser.add_argument("-q", "--query", help="Search query")
    parser.add_argument("-a", "--auto", action="store_true", help="Auto discovery mode")
    parser.add_argument("-p", "--profile", help="Profile URL to scrape")
    parser.add_argument("-m", "--max", type=int, default=50, help="Max leads")
    parser.add_argument("--no-headless", action="store_true", help="Visible browser")
    parser.add_argument("--api-url", default=API_URL, help="Railway backend URL")
    parser.add_argument("--email", default=EMAIL, help="Login email")
    parser.add_argument("--password", default=PASSWORD, help="Login password")
    parser.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    return parser.parse_args()


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
        print(f"HTTP {e.code}: {msg}", file=sys.stderr)
        sys.exit(1)


def login(email: str, password: str, api_url: str) -> str:
    return _request("POST", f"{api_url}/api/auth/login", {"email": email, "password": password})["access_token"]


def create_job(token: str, api_url: str, mode: str, query: str, max_leads: int) -> dict:
    return _request("POST", f"{api_url}/api/scrape?local=true", {"mode": mode, "query": query, "max_leads": max_leads}, token)


def upload_leads(token: str, api_url: str, job_id: int, leads: list) -> int:
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
    return _request("POST", f"{api_url}/api/leads/bulk", payload, token)["uploaded"]


async def main():
    args = parse_args()
    api_url = args.api_url.rstrip("/")
    email = args.email
    password = args.password

    if not email or not password:
        print("ERROR: Set SCRAPER_EMAIL and SCRAPER_PASSWORD env vars, or pass --email / --password")
        sys.exit(1)

    if not args.query and not args.auto and not args.profile:
        print("ERROR: Provide --query, --auto, or --profile")
        sys.exit(1)

    setup_logging("DEBUG" if args.verbose else "INFO", None)

    print(f"Logging into {api_url}...")
    token = login(email, password, api_url)

    if args.auto:
        mode = "auto"
        query = ""
    elif args.profile:
        mode = "profile"
        query = args.profile
    else:
        mode = "manual"
        query = args.query

    print(f"Creating {mode} job on backend...")
    job = create_job(token, api_url, mode, query, args.max)
    job_id = job["id"]
    print(f"Job {job_id} created (status: {job['status']})")

    config = get_settings()
    if args.no_headless:
        config.headless = False
    config.max_users = args.max

    print("Running local scraper...")
    async with TikTokScraper(config) as scraper:
        if mode == "auto":
            leads = await scraper.auto_discover(args.max)
        elif mode == "profile":
            lead = await scraper.scrape_profile(query)
            leads = [lead] if lead else []
        else:
            leads = await scraper.scrape(query, args.max)

    if not leads:
        print("No leads found.")
        return

    print(f"Uploading {len(leads)} leads to job {job_id}...")
    uploaded = upload_leads(token, api_url, job_id, leads)
    print(f"Done! {uploaded} leads uploaded.")
    print(f"View at: {api_url}")


if __name__ == "__main__":
    asyncio.run(main())
