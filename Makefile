.PHONY: help setup test lint format run-pipeline run-dashboard

help:
	@echo "Comandos disponibles:"
	@echo "  make setup          Instala dependencias"
	@echo "  make test           Ejecuta todos los tests"
	@echo "  make test-unit      Solo tests unitarios"
	@echo "  make lint           Verifica el codigo"
	@echo "  make format         Formatea el codigo"
	@echo "  make run-pipeline   Ejecuta el pipeline completo"
	@echo "  make run-dashboard  Inicia el dashboard Streamlit"

setup:
	pip install -r requirements.txt
	cp -n .env.example .env 2>/dev/null || true
	@echo "Setup completo. Edita .env con tu GCP_PROJECT_ID."

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

lint:
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

format:
	ruff format src/ tests/

run-pipeline:
	python -m src.pipeline.extract.main
	python -m src.pipeline.validate.main
	python -m src.pipeline.transform.main
	python -m src.pipeline.load.main

run-dashboard:
	streamlit run src/dashboard/app.py
