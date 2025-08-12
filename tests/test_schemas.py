from app.schemas import Summary, ActionItem

def test_summary_model():
    s = Summary(executive_summary="ok", action_items=[ActionItem(owner="Alex", task="Ship")])
    assert s.executive_summary and s.action_items[0].owner == "Alex"
