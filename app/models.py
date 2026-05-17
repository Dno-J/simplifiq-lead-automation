from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class Lead(SQLModel, table=True):
    """
    Database model for storing submitted leads, enrichment output,
    generated report content, PDF path, email status, Google Sheets status,
    and workflow status.
    """

    id: Optional[int] = Field(default=None, primary_key=True)

    full_name: str
    email: str
    company_name: str
    company_website: str
    industry: Optional[str] = None
    message: Optional[str] = None

    # Workflow/report tracking
    report_status: str = Field(default="pending")
    report_file_path: Optional[str] = None
    error_message: Optional[str] = None

    # Email tracking
    email_status: str = Field(default="pending")
    email_sent_at: Optional[datetime] = None

    # Google Sheets tracking
    sheets_status: str = Field(default="pending")
    sheets_logged_at: Optional[datetime] = None

    # Company enrichment fields
    enrichment_status: str = Field(default="pending")
    website_title: Optional[str] = None
    website_meta_description: Optional[str] = None
    website_headings: Optional[str] = None
    website_summary_text: Optional[str] = None
    detected_keywords: Optional[str] = None

    # AI-generated report fields
    ai_generation_status: str = Field(default="pending")
    executive_summary: Optional[str] = None
    company_overview: Optional[str] = None
    observed_positioning: Optional[str] = None
    potential_pain_points: Optional[str] = None
    automation_opportunities: Optional[str] = None
    recommended_workflow: Optional[str] = None
    next_steps: Optional[str] = None
    personalized_email_body: Optional[str] = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )