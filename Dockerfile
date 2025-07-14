FROM python:3.12-slim
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app/

# Instala dependências do sistema necessárias para o opencv-python-headless funcionar
RUN apt-get update && apt-get install -y \
    ffmpeg \
    cmake \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*


COPY . .

RUN pip install poetry

RUN poetry config installer.max-workers 10
RUN poetry install --no-ansi --without dev && poetry run pip list

EXPOSE 8000
CMD poetry run uvicorn --host 0.0.0.0 focus_track_api.app:app