from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Lead, ScrapeJob
from app.schemas import LeadOut, LeadList
from app.auth import get_current_user_id

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("", response_model=LeadList)
def list_leads(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    search: str = Query("", max_length=200),
    has_email: bool = Query(False),
    has_phone: bool = Query(False),
    job_id: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    q = db.query(Lead).filter(Lead.user_id == user_id)

    if search:
        like = f"%{search}%"
        q = q.filter(
            Lead.username.ilike(like)
            | Lead.bio.ilike(like)
            | Lead.emails.ilike(like)
            | Lead.phones.ilike(like)
        )
    if has_email:
        q = q.filter(Lead.emails != "")
    if has_phone:
        q = q.filter(Lead.phones != "")
    if job_id:
        q = q.filter(Lead.job_id == job_id)

    total = q.count()
    leads = q.order_by(Lead.scraped_at.desc()).offset(offset).limit(limit).all()
    return LeadList(leads=leads, total=total)


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id, Lead.user_id == user_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead
