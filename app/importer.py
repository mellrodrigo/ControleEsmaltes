"""Importa a planilha original para o banco SQLite, normalizando os dados."""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import openpyxl

from app import db, normalize

SEED_XLSX = db.BASE_DIR / "seed" / "Controle_prateleira_esmaltes_202606.xlsx"


def _to_iso(valor) -> str | None:
    if valor is None:
        return None
    if isinstance(valor, dt.datetime):
        return valor.date().isoformat()
    if isinstance(valor, dt.date):
        return valor.isoformat()
    return str(valor).strip() or None


def importar(caminho: Path = SEED_XLSX, *, recriar: bool = False) -> dict:
    if recriar and db.DB_PATH.exists():
        db.DB_PATH.unlink()
    db.init_db()

    wb = openpyxl.load_workbook(caminho, data_only=True)
    ws = wb["Esmaltes"]
    linhas = list(ws.iter_rows(values_only=True))

    conn = db.get_conn()
    inseridos = 0
    ignorados = 0
    try:
        ja_tem = conn.execute("SELECT COUNT(*) AS c FROM esmaltes").fetchone()["c"]
        if ja_tem and not recriar:
            return {"inseridos": 0, "ignorados": 0, "mensagem": "Banco já populado; nada a fazer."}

        for linha in linhas[1:]:  # pula o cabeçalho
            etiqueta, marca, serie, cor, validade, cadastro, status, motivo, removido = (
                linha + (None,) * (9 - len(linha))
            )[:9]

            marca_n = normalize.normalizar_marca(marca)
            serie_n = normalize.normalizar_texto(serie)
            cor_n = normalize.normalizar_texto(cor)
            validade_iso = _to_iso(validade)

            # Linhas sem nenhum dado útil (apenas o número de etiqueta reservado)
            if not any([marca_n, serie_n, cor_n, validade_iso]):
                ignorados += 1
                continue

            try:
                etiqueta_int = int(etiqueta)
            except (TypeError, ValueError):
                ignorados += 1
                continue

            cadastro_iso = _to_iso(cadastro) or dt.date.today().isoformat()
            status_n = normalize.normalizar_status(status)
            motivo_n = normalize.normalizar_motivo(motivo)
            removido_iso = _to_iso(removido)

            cur = conn.execute(
                """INSERT OR IGNORE INTO esmaltes
                   (etiqueta, marca, serie, cor, validade, data_cadastro,
                    status, motivo, data_removido)
                   VALUES (?,?,?,?,?,?,?,?,?)""",
                (etiqueta_int, marca_n, serie_n, cor_n, validade_iso,
                 cadastro_iso, status_n, motivo_n, removido_iso),
            )
            inseridos += cur.rowcount or 0
        conn.commit()
        total = conn.execute("SELECT COUNT(*) AS c FROM esmaltes").fetchone()["c"]
    finally:
        conn.close()

    return {"inseridos": inseridos, "total": total, "ignorados": ignorados,
            "mensagem": f"{inseridos} esmaltes importados (total {total}), "
                        f"{ignorados} linhas ignoradas."}


if __name__ == "__main__":
    recriar = "--recriar" in sys.argv
    resultado = importar(recriar=recriar)
    print(resultado["mensagem"])
