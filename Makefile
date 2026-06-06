.PHONY: help setup run migrate clean

help:
	@echo "Comandos disponiveis:"
	@echo "  make setup      - Prepara o ambiente (.env, migrate e superuser)"
	@echo "  make run        - Roda o servidor de desenvolvimento do Django"
	@echo "  make migrate    - Aplica as migracoes do banco de dados"

setup:
	uv run python setup.py

run:
	uv run python manage.py runserver

migrate:
	uv run python manage.py migrate