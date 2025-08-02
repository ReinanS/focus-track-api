#!/bin/sh

# Executa as migrações do banco de dados
poetry run alembic upgrade head

# Inicia a aplicação com debugpy
poetry run python -m debugpy --listen 0.0.0.0:5678 --wait-for-client -m uvicorn focus_track_api.app:app --host 0.0.0.0 --port 8000 --reload