from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    plan = Column(String(50), default="free")
    quota_used = Column(Integer, default=0)
    quota_limit = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)

    jobs = relationship("ScrapeJob", back_populates="user", cascade="all, delete-orphan")
    leads = relationship("Lead", back_populates="user", cascade="all, delete-orphan")


class ScrapeJob(Base):
    __tablename__ = "scrape_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    mode = Column(String(50), nullable=False)
    query = Column(String(500), default="")
    max_leads = Column(Integer, default=100)
    status = Column(String(50), default="pending")
    leads_found = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    user = relationship("User", back_populates="jobs")
    leads = relationship("Lead", back_populates="job", cascade="all, delete-orphan")


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("scrape_jobs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(255), nullable=False)
    profile_url = Column(String(500), nullable=False)
    bio = Column(Text, default="")
    emails = Column(Text, default="")
    phones = Column(Text, default="")
    followers = Column(String(100), default="")
    following = Column(String(100), default="")
    likes = Column(String(100), default="")
    external_link = Column(String(500), default="")
    verified = Column(Boolean, default=False)
    scraped_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("ScrapeJob", back_populates="leads")
    user = relationship("User", back_populates="leads")
