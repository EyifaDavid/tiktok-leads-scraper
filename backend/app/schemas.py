from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


# ── Auth ──

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    plan: str
    quota_used: int
    quota_limit: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Scrape Jobs ──

class ScrapeJobCreate(BaseModel):
    mode: str
    query: Optional[str] = ""
    max_leads: int = 100


class ScrapeJobOut(BaseModel):
    id: int
    user_id: int
    mode: str
    query: str
    max_leads: int
    status: str
    leads_found: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class ScrapeJobList(BaseModel):
    jobs: List[ScrapeJobOut]
    total: int


# ── Leads ──

class LeadCreate(BaseModel):
    job_id: int = 0
    username: str
    profile_url: str = ""
    bio: str = ""
    emails: str = ""
    phones: str = ""
    followers: str = "0"
    following: str = "0"
    likes: str = "0"
    external_link: str = ""
    verified: bool = False


class LeadOut(BaseModel):
    id: int
    job_id: int
    username: str
    profile_url: str
    bio: str
    emails: str
    phones: str
    followers: str
    following: str
    likes: str
    external_link: str
    verified: bool
    scraped_at: datetime

    model_config = {"from_attributes": True}


class LeadList(BaseModel):
    leads: List[LeadOut]
    total: int


class BulkLeadUpload(BaseModel):
    job_id: int
    leads: List[LeadCreate]


# ── Stats / Quota ──

class QuotaInfo(BaseModel):
    used: int
    limit: int
    remaining: int


class DashboardStats(BaseModel):
    total_leads: int
    total_jobs: int
    quota: QuotaInfo
    recent_jobs: List[ScrapeJobOut]
    leads_with_email: int
    leads_with_phone: int
