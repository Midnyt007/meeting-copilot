.PHONY: run test seed

run:
	uvicorn app.main:app --reload

test:
	pytest -q

seed:
	python -c "from app.store import seed_examples; seed_examples()"
