"""Pydantic models for lead data."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class LeadBase(BaseModel):
    """Base lead model with common fields."""
    
    username: str = Field(..., description="TikTok username")
    profile_url: str = Field(..., description="Full TikTok profile URL")
    bio: str = Field(default="", description="Profile bio text")
    emails: str = Field(default="", description="Extracted email addresses (comma-separated)")
    phones: str = Field(default="", description="Extracted phone numbers (comma-separated)")
    followers: str = Field(default="", description="Follower count")
    following: str = Field(default="", description="Following count")
    likes: str = Field(default="", description="Total likes count")
    external_link: str = Field(default="", description="External website link")
    verified: bool = Field(default=False, description="Whether the account is verified")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate and clean username."""
        if not v:
            raise ValueError("Username cannot be empty")
        return v.strip().lstrip("@")

    @field_validator("profile_url")
    @classmethod
    def validate_profile_url(cls, v: str) -> str:
        """Validate profile URL format."""
        if not v:
            raise ValueError("Profile URL cannot be empty")
        if not v.startswith("http"):
            return f"https://www.tiktok.com/{v.lstrip('/')}"
        return v


class LeadCreate(LeadBase):
    """Model for creating new leads."""
    
    source_query: str = Field(default="", description="Search query that found this lead")
    
    model_config = {"from_attributes": True}


class Lead(LeadBase):
    """Complete lead model with database fields."""
    
    id: Optional[int] = Field(default=None, description="Database ID")
    scraped_at: Optional[datetime] = Field(default=None, description="When the lead was scraped")
    source_query: str = Field(default="", description="Search query that found this lead")

    model_config = {"from_attributes": True}

    def has_contact_info(self) -> bool:
        """Check if lead has any contact information."""
        return bool(self.emails or self.phones or self.external_link)

    def has_email(self) -> bool:
        """Check if lead has email address."""
        return bool(self.emails)

    def has_phone(self) -> bool:
        """Check if lead has phone number."""
        return bool(self.phones)

    def to_db_tuple(self) -> tuple:
        """Convert to tuple for database insertion."""
        return (
            self.username,
            self.profile_url,
            self.bio,
            self.emails,
            self.phones,
            self.followers,
            self.following,
            self.likes,
            self.external_link,
            self.verified,
            self.scraped_at.isoformat() if self.scraped_at else None,
            self.source_query,
        )
