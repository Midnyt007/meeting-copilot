from __future__ import annotations
import os
from typing import Dict, Any
from openai import OpenAI
from pydantic import ValidationError
from .schemas import Summary, ActionItem

SYSTEM_PROMPT = (
    "You are a terse project manager. Extract structured minutes from the user's notes. "
    "Use crisp bullet points. Assign action items with owners. If dates are mentioned, parse them as ISO dates."
)

MODEL = os.environ.get("MODEL", "gpt-4o-mini")

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL") or None,
)

SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "executive_summary": {"type": "string"},
        "agenda": {"type": "array", "items": {"type": "string"}},
        "decisions": {"type": "array", "items": {"type": "string"}},
        "risks": {"type": "array", "items": {"type": "string"}},
        "action_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "task": {"type": "string"},
                    "due": {"type": ["string", "null"], "format": "date"},
                    "priority": {"type": "string"}
                },
                "required": ["owner", "task"]
            }
        }
    },
    "required": ["executive_summary", "action_items"]
}


def summarize(notes: str) -> Summary:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": notes},
    ]

    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        response_format={"type": "json_schema", "json_schema": {"name": "meeting_summary", "schema": SCHEMA}},
        temperature=0.2,
    )
    content = resp.choices[0].message.content or "{}"
    try:
        data = client._client._client_json.loads(content)  # reuse underlying json for speed
    except Exception:
        import json
        data = json.loads(content)
    try:
        return Summary.model_validate(data)
    except ValidationError as e:
        # fallback: force minimal structure to avoid breaking the app
        return Summary(executive_summary="(parse error)", agenda=[], decisions=[], risks=[], action_items=[ActionItem(owner="", task=str(e))])
