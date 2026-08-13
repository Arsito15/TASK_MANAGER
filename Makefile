.PHONY: up down build logs backend frontend test lint clean

# Build and start both services
up:
	docker compose up --build -d

# Start without rebuilding
start:
	docker compose up -d

# Stop all services
down:
	docker compose down

# Build images without starting
build:
	docker compose build

# View logs (both services)
logs:
	docker compose logs -f

# View backend logs only
backend-logs:
	docker compose logs -f backend

# View frontend logs only
frontend-logs:
	docker compose logs -f frontend

# Run backend tests inside container
test:
	docker compose exec backend python manage.py test

# Run backend migrations
migrate:
	docker compose exec backend python manage.py migrate

# Create Django superuser
superuser:
	docker compose exec backend python manage.py createsuperuser

# Rebuild and restart (after code changes that affect Dockerfile)
rebuild:
	docker compose up --build -d --force-recreate

# Stop and remove containers + volumes (fresh start)
clean:
	docker compose down -v

# Check status
status:
	docker compose ps