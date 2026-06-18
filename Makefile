.PHONY: help setup run makemigrations migrate lint format check clean test

help:
	@echo "Comandos disponiveis:"
	@echo "  make setup          - Prepara o ambiente (.env, migrate e superuser)"
	@echo "  make run            - Roda o servidor de desenvolvimento do Django"
	@echo "  make makemigrations - Cria novas migracoes baseadas nas mudancas dos modelos"
	@echo "  make migrate        - Aplica as migracoes do banco de dados"
	@echo "  make lint           - Executa o linter (ruff check)"
	@echo "  make format         - Formata o codigo (ruff format)"
	@echo "  make test           - Executa a suite de testes com pytest"
	@echo "  make check          - Valida lint e formatacao (usado no CI)"

setup:
	uv run python setup.py

run:
	uv run python manage.py runserver 127.0.0.1:8000 || uv run python manage.py runserver 127.0.0.1:8080

makemigrations:
	uv run python manage.py makemigrations

migrate:
	uv run python manage.py migrate

lint:
	uv run ruff check .

format:
	uv run ruff format .

test:
	uv run pytest

check: lint
	uv run ruff format --check .