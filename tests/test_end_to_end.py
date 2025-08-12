import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_create_and_summarize(monkeypatch):
    # monkeypatch llm.summarize to avoid network
    from app import llm
    def fake_sum(notes: str):
        from app.schemas import Summary, ActionItem
        return Summary(
            executive_summary="demo",
            agenda=["a"], decisions=["d"], risks=["r"],
            action_items=[ActionItem(owner="Alex", task="Do thing")]
        )
    monkeypatch.setattr(llm, "summarize", fake_sum)

    payload = {"title":"T1","date":"2025-08-01","attendees":["A"],"notes":"We decided X by Friday"}
    res = client.post("/api/notes", json=payload)
    assert res.status_code == 200
    meeting_id = res.json()["id"]

    res = client.post(f"/api/summarize/{meeting_id}")
    assert res.status_code == 200
    js = res.json()
    assert js["summary"]["executive_summary"] == "demo"
