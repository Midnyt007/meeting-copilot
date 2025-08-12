from __future__ import annotations
from datetime import date
from pydantic import BaseModel, Field
from typing import List, Optional

class ActionItem(BaseModel):
    owner: str = Field(..., description="Person responsible")
    task: str = Field(..., description="What to do")
    due: Optional[date] = Field(None, description="Due date if known")
    priority: str = Field("medium", description="low|medium|high")

class MeetingIn(BaseModel):
    title: str
    date: date
    attendees: List[str] = []
    notes: str = Field(..., description="Raw transcript or notes")

class Meeting(MeetingIn):
    id: int

class Summary(BaseModel):
    executive_summary: str
    agenda: List[str] = []
    decisions: List[str] = []
    risks: List[str] = []
    action_items: List[ActionItem] = []

class MeetingSummary(BaseModel):
    meeting_id: int
    model: str
    summary: Summary
