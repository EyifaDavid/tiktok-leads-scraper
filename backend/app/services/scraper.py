import asyncio
import logging
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import ScrapeJob, Lead

logger = logging.getLogger(__name__)


def run_scrape_job(job_id: int):
    asyncio.run(_run_scrape_job_async(job_id))


async def _run_scrape_job_async(job_id: int):
    settings = get_settings()
    db_url = settings.database_url
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(bind=engine)

    db = SessionLocal()
    try:
        job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return

        job.status = "running"
        db.commit()

        from tiktok_leads.config import get_settings as get_scraper_settings
        from tiktok_leads.scrapers.tiktok_scraper import TikTokScraper

        scraper_config = get_scraper_settings()
        scraper_config.headless = settings.scraper_headless
        scraper_config.min_delay = settings.scraper_min_delay
        scraper_config.max_delay = settings.scraper_max_delay

        user = job.user
        remaining = user.quota_limit - user.quota_used
        max_to_scrape = min(job.max_leads, remaining)

        async with TikTokScraper(scraper_config) as scraper:
            if job.mode == "auto":
                leads = await scraper.auto_discover(max_to_scrape)
            elif job.mode == "manual":
                query = job.query or ""
                leads = await scraper.scrape(query, max_to_scrape)
            elif job.mode == "profile":
                query = job.query or ""
                leads = []
                if query:
                    lead = await scraper.scrape_profile(query)
                    if lead:
                        leads = [lead]
            else:
                leads = []

        for sl in leads:
            lead = Lead(
                job_id=job.id,
                user_id=job.user_id,
                username=sl.username,
                profile_url=sl.profile_url,
                bio=sl.bio,
                emails=sl.emails,
                phones=sl.phones,
                followers=sl.followers,
                following=sl.following,
                likes=sl.likes,
                external_link=sl.external_link,
                verified=sl.verified,
                scraped_at=datetime.utcnow(),
            )
            db.add(lead)

        user.quota_used += len(leads)
        job.leads_found = len(leads)
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.exception(f"Scrape job {job_id} failed")
        job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()
