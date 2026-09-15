
from pydantic import BaseModel, Field, HttpUrl
from typing import List


class TeamMember(BaseModel):
    name: str
    role: str = ""
    linkedin_url: str = ""


class CompanyIntelligence(BaseModel):
    domain: str
    company_overview: str = Field(description="Exactly two concise sentences describing the company.")
    target_audience_icp: str
    contact_emails: List[str] = Field(default_factory=list)
    key_leadership_team: List[TeamMember] = Field(default_factory=list)
    data_confidence_score: float = Field(ge=0.0, le=1.0)
    source_pages: List[str] = Field(default_factory=list)
