from __future__ import annotations
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from .schemas import MeetingIn
from . import store, llm, calendar

load_dotenv()
app = FastAPI(title="meeting-copilot")
BASE = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE / "templates"))

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/meetings")
def list_meetings():
    return JSONResponse([m.model_dump() for m in store.list_meetings()])

@app.post("/api/notes")
def create_notes(data: MeetingIn):
    m = store.create_meeting(data)
    return JSONResponse(m.model_dump())

@app.post("/api/summarize/{meeting_id}")
def run_summary(meeting_id: int):
    # fetch notes
    meetings = store.list_meetings()
    match = next((m for m in meetings if m.id == meeting_id), None)
    if not match:
        raise HTTPException(404, "meeting not found")
    summary = llm.summarize(match.notes)
    store.save_summary(meeting_id, os.environ.get("MODEL", "gpt-4o-mini"), summary)
    # Export ICS if action items have due dates
    out_path = calendar.to_ics(match.title, summary.action_items, Path("out") / f"meeting_{meeting_id}")
    return JSONResponse({"summary": summary.model_dump(), "ics": str(out_path)})

@app.get("/api/report/{meeting_id}.md")
def report_md(meeting_id: int):
    s = store.get_summary(meeting_id)
    if not s:
        raise HTTPException(404, "summary not found — run /api/summarize/<id> first")
    m = next((x for x in store.list_meetings() if x.id == meeting_id), None)
    if not m:
        raise HTTPException(404, "meeting not found")
    lines = [
        f"# {m.title} ({m.date})",
        f"Attendees: {', '.join(m.attendees) if m.attendees else '-'}",
        "",
        "## Executive Summary",
        s.summary.executive_summary,
        "",
        "## Decisions",
        *[f"- {d}" for d in s.summary.decisions],
        "",
        "## Risks",
        *[f"- {r}" for r in s.summary.risks],
        "",
        "## Action Items",
        *[f"- [{a.priority}] {a.owner}: {a.task} {f'(due {a.due})' if a.due else ''}" for a in s.summary.action_items],
        "",
    ]
    return PlainTextResponse("\n".join(lines), media_type="text/markdown")

# Minimal CLI entry point for convenience

def cli():
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
