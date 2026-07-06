import asyncio
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, ScrapeJob
from app.schemas import ScrapeJobCreate, ScrapeJobOut, ScrapeJobList
from app.auth import get_current_user_id
from app.services.scraper import run_scrape_job

router = APIRouter(prefix="/api/scrape", tags=["scrape"])


@router.post("", response_model=ScrapeJobOut)
def start_scrape(
    body: ScrapeJobCreate,
    background_tasks: BackgroundTasks,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    local: bool = Query(False, description="Skip background task; scraper runs locally"),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.quota_used >= user.quota_limit:
        raise HTTPException(status_code=429, detail="Monthly quota exceeded")

    if body.mode not in ("auto", "manual", "profile"):
        raise HTTPException(status_code=400, detail="Invalid mode. Use: auto, manual, or profile")

    job = ScrapeJob(
        user_id=user_id,
        mode=body.mode,
        query=body.query or "",
        max_leads=body.max_leads,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    if not local:
        background_tasks.add_task(run_scrape_job, job.id)

    return job


@router.get("/jobs", response_model=ScrapeJobList)
def list_jobs(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    total = db.query(ScrapeJob).filter(ScrapeJob.user_id == user_id).count()
    jobs = (
        db.query(ScrapeJob)
        .filter(ScrapeJob.user_id == user_id)
        .order_by(ScrapeJob.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return ScrapeJobList(jobs=list(jobs), total=total)


@router.get("/jobs/{job_id}", response_model=ScrapeJobOut)
def get_job(job_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    job = db.query(ScrapeJob).filter(ScrapeJob.id == job_id, ScrapeJob.user_id == user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
