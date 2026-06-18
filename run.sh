#!/usr/bin/env bash
# Sobe o app de Controle de Esmaltes. Importa a planilha na primeira execução.
set -e
cd "$(dirname "$0")"

if [ ! -f data/esmaltes.db ]; then
  echo "Banco não encontrado — importando a planilha..."
  python -m app.importer --recriar
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
