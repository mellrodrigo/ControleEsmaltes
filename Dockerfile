FROM python:3.12-slim

WORKDIR /app

# Dependências do sistema para o Pillow (processamento das fotos)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo zlib1g \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# O banco SQLite e as fotos ficam em /app/data — monte um volume aqui
# para preservar os dados entre os deploys.
VOLUME ["/app/data"]

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
