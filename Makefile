.PHONY: up down dev migrate test lint clean

up:
	docker compose up -d

down:
	docker compose down

dev: up
	cd frontend && npm run dev

logs:
	docker compose logs -f

backend-logs:
	docker compose logs -f backend celery_worker

migrate:
	cd backend && alembic upgrade head

migrate-new:
	cd backend && alembic revision --autogenerate -m "$(msg)"

test-backend:
	cd backend && python -m pytest tests/ -v

test-frontend:
	cd frontend && npm test

test: test-backend test-frontend

lint-backend:
	cd backend && ruff check . && ruff format --check .

lint-frontend:
	cd frontend && npm run lint

lint: lint-backend lint-frontend

clean:
	docker compose down -v
	rm -rf postgres_data redis_data
