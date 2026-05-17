from typing import Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class LeadCreate(BaseModel):
    """
    Request schema for lead submission.

    Pydantic validates incoming form/API data before it reaches business logic.
    """

    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    company_name: str = Field(..., min_length=2, max_length=150)
    company_website: HttpUrl
    industry: Optional[str] = Field(default=None, max_length=100)
    message: Optional[str] = Field(default=None, max_length=1000)


class LeadResponse(BaseModel):
    """
    Response returned after lead submission.
    """

    id: int
    full_name: str
    email: str
    company_name: str
    report_status: str
    message: str