install:
	pip3 install -r requirements.txt

lint:
	isort --profile black .
	black .

make_migrations:
	alembic revision --autogenerate

migrate:
	alembic upgrade head

deps-up:
	docker compose -f docker-compose.yaml up -d

deps-down:
	docker compose -f docker-compose.yaml down

exec:
	docker compose -f docker-compose.yaml exec -it $(name) bash

logs:
	docker compose -f docker-compose.yaml logs -f $(name)


run:
	python3 app/main.py

