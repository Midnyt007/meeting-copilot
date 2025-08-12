LLM meeting minutes & action-items copilot. Paste a transcript, get:
- executive summary
- agenda recap + decisions made
- risks / blockers
- action items with owner, due date, and priority
- export to Markdown + optional ICS calendar events


Docker
- docker compose up --build


Environment
- OPENAI_API_KEY – for OpenAI-compatible chat completions
- Optional OPENAI_BASE_URL to point at a compatible server


API (selected)
- POST /api/notes – create meeting notes (raw transcript or free-form notes)
- POST /api/summarize/{meeting_id} – run LLM, store structured result
- GET  /api/meetings – list meetings
- GET  /api/report/{meeting_id}.md – export Markdown
- GET  / – minimal UI to paste notes and view outputs



Tests
- pytest -q
