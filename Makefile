.PHONY: run ingest test build

run:
	docker-compose up --build

ingest:
	python -m agentturing.database.setup_knowledgebase --rebuild

test:
	pytest -q

build:
	docker build -f Dockerfile.backend -t agentturing-backend .
