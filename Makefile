.PHONY: up down dev migrate test lint clean prod-build prod-up prod-down prod-logs prod-migrate prod-ps

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

# --- Production ---

prod-build:
	docker compose -f docker-compose.prod.yml build

prod-up:
	docker compose -f docker-compose.prod.yml --env-file .env.production up -d

prod-down:
	docker compose -f docker-compose.prod.yml down

prod-logs:
	docker compose -f docker-compose.prod.yml logs -f

prod-migrate:
	docker compose -f docker-compose.prod.yml exec backend alembic upgrade head

prod-ps:
	docker compose -f docker-compose.prod.yml ps
