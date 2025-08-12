from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Row
from .schemas import MeetingIn, Meeting, Summary, MeetingSummary

DB_PATH = Path("./meetingcopilot.sqlite3").absolute()
engine: Engine = create_engine(f"sqlite:///{DB_PATH}", future=True)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS meetings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  date TEXT NOT NULL,
  attendees TEXT NOT NULL,
  notes TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS summaries (
  meeting_id INTEGER NOT NULL,
  model TEXT NOT NULL,
  json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  PRIMARY KEY (meeting_id)
);
"""

with engine.begin() as cx:
    for stmt in SCHEMA_SQL.strip().split(";\n\n"):
        if stmt.strip():
            cx.exec_driver_sql(stmt)


def create_meeting(data: MeetingIn) -> Meeting:
    with engine.begin() as cx:
        r = cx.exec_driver_sql(
            "INSERT INTO meetings (title, date, attendees, notes, created_at) VALUES (?, ?, ?, ?, ?)",
            (data.title, str(data.date), ",".join(data.attendees), data.notes, datetime.utcnow().isoformat()),
        )
        meeting_id = r.lastrowid
        row = cx.exec_driver_sql("SELECT id, title, date, attendees, notes FROM meetings WHERE id=?", (meeting_id,)).first()
    return _row_to_meeting(row)


def list_meetings(limit: int = 50) -> List[Meeting]:
    with engine.begin() as cx:
        rows = cx.exec_driver_sql("SELECT id, title, date, attendees, notes FROM meetings ORDER BY id DESC LIMIT ?", (limit,)).all()
    return [_row_to_meeting(r) for r in rows]


def save_summary(meeting_id: int, model: str, summary: Summary) -> MeetingSummary:
    import json
    js = json.dumps(summary.model_dump(), ensure_ascii=False)
    with engine.begin() as cx:
        cx.exec_driver_sql(
            "REPLACE INTO summaries (meeting_id, model, json, created_at) VALUES (?, ?, ?, ?)",
            (meeting_id, model, js, datetime.utcnow().isoformat()),
        )
    return MeetingSummary(meeting_id=meeting_id, model=model, summary=summary)


def get_summary(meeting_id: int) -> Optional[MeetingSummary]:
    import json
    with engine.begin() as cx:
        row = cx.exec_driver_sql("SELECT meeting_id, model, json FROM summaries WHERE meeting_id=?", (meeting_id,)).first()
    if not row:
        return None
    data = json.loads(row[2])
    return MeetingSummary(meeting_id=row[0], model=row[1], summary=Summary.model_validate(data))


def _row_to_meeting(row: Row) -> Meeting:
    return Meeting(
        id=row[0],
        title=row[1],
        date=row[2],
        attendees=[a for a in (row[3] or "").split(",") if a],
        notes=row[4],
    )


def seed_examples():
    from .schemas import MeetingIn
    p = Path("data/seed_examples.md")
    if not p.exists():
        return
    content = p.read_text(encoding="utf-8")
    create_meeting(MeetingIn(title="Seed Example", date="2025-07-02", attendees=["Alex","Priya","Chen"], notes=content))
