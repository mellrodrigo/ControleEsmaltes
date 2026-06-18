"""API e servidor do Controle de Esmaltes (PWA)."""
from __future__ import annotations

import base64
import datetime as dt
import io
import os
import secrets
import uuid
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps

from app import db, normalize

app = FastAPI(title="Controle de Esmaltes")

STATIC_DIR = db.BASE_DIR / "static"
MAX_LADO = 1280  # px – maior dimensão das fotos salvas

# Proteção opcional por senha (HTTP Basic). Fica DESLIGADA enquanto as
# variáveis de ambiente não forem definidas — assim o deploy/local não trava.
# Para exigir login, defina ADMIN_USER e ADMIN_PASS no servidor.
ADMIN_USER = os.environ.get("ADMIN_USER", "")
ADMIN_PASS = os.environ.get("ADMIN_PASS", "")


@app.middleware("http")
async def _auth_basica(request, call_next):
    if ADMIN_USER and ADMIN_PASS:
        header = request.headers.get("authorization", "")
        autorizado = False
        if header.startswith("Basic "):
            try:
                usuario, _, senha = base64.b64decode(header[6:]).decode().partition(":")
                autorizado = (secrets.compare_digest(usuario, ADMIN_USER)
                              and secrets.compare_digest(senha, ADMIN_PASS))
            except Exception:
                autorizado = False
        if not autorizado:
            return Response(
                "Acesso restrito", status_code=401,
                headers={"WWW-Authenticate": 'Basic realm="Controle de Esmaltes"'},
            )
    return await call_next(request)


@app.on_event("startup")
def _startup() -> None:
    db.init_db()
    # Importa a planilha automaticamente na primeira execução (banco vazio).
    conn = db.get_conn()
    try:
        vazio = conn.execute("SELECT COUNT(*) AS c FROM esmaltes").fetchone()["c"] == 0
    finally:
        conn.close()
    if vazio:
        try:
            from app.importer import importar
            importar()
        except Exception:
            pass  # segue mesmo sem a planilha de seed


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalizar_validade(valor: Optional[str]) -> Optional[str]:
    """Aceita 'YYYY-MM', 'YYYY-MM-DD' ou vazio e devolve ISO (dia 01)."""
    if not valor:
        return None
    valor = valor.strip()
    try:
        if len(valor) == 7:  # YYYY-MM (campo <input type=month>)
            return dt.date.fromisoformat(valor + "-01").isoformat()
        return dt.date.fromisoformat(valor).isoformat()
    except ValueError:
        raise HTTPException(400, f"Data de validade inválida: {valor!r}")


def _salvar_foto(esmalte_id: int, upload: UploadFile, conn) -> str:
    conteudo = upload.file.read()
    if not conteudo:
        return ""
    try:
        img = Image.open(io.BytesIO(conteudo))
        img = ImageOps.exif_transpose(img)  # corrige orientação do celular
        img.thumbnail((MAX_LADO, MAX_LADO))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        nome = f"{uuid.uuid4().hex}.jpg"
        img.save(db.UPLOAD_DIR / nome, "JPEG", quality=82, optimize=True)
    except Exception:
        # Não é uma imagem reconhecida: guarda o arquivo cru
        nome = f"{uuid.uuid4().hex}_{upload.filename}"
        (db.UPLOAD_DIR / nome).write_bytes(conteudo)
    conn.execute(
        "INSERT INTO fotos (esmalte_id, arquivo, criada_em) VALUES (?,?,?)",
        (esmalte_id, nome, dt.datetime.now().isoformat(timespec="seconds")),
    )
    return nome


def _esmalte_dict(row, fotos) -> dict:
    d = dict(row)
    d["fotos"] = [f["arquivo"] for f in fotos]
    return d


# ---------------------------------------------------------------------------
# Endpoints de dados
# ---------------------------------------------------------------------------
@app.get("/api/proxima-etiqueta")
def proxima_etiqueta():
    conn = db.get_conn()
    try:
        return {"proxima_etiqueta": db.proxima_etiqueta(conn)}
    finally:
        conn.close()


@app.get("/api/sugestoes")
def sugestoes():
    """Valores distintos para autocomplete do formulário."""
    conn = db.get_conn()
    try:
        def distintos(col):
            rows = conn.execute(
                f"SELECT DISTINCT {col} AS v FROM esmaltes "
                f"WHERE {col} IS NOT NULL AND {col} != '' ORDER BY {col} COLLATE NOCASE"
            ).fetchall()
            return [r["v"] for r in rows]
        return {
            "marcas": distintos("marca"),
            "series": distintos("serie"),
            "cores": distintos("cor"),
            "motivos": list(normalize.MOTIVOS_VALIDOS),
            "status": list(normalize.STATUS_VALIDOS),
        }
    finally:
        conn.close()


@app.get("/api/stats")
def stats():
    conn = db.get_conn()
    try:
        hoje = dt.date.today()
        limite = (hoje + dt.timedelta(days=90)).isoformat()
        total = conn.execute("SELECT COUNT(*) c FROM esmaltes").fetchone()["c"]
        prateleira = conn.execute(
            "SELECT COUNT(*) c FROM esmaltes WHERE status='Prateleira'"
        ).fetchone()["c"]
        vencidos = conn.execute(
            "SELECT COUNT(*) c FROM esmaltes WHERE status='Prateleira' "
            "AND validade IS NOT NULL AND validade < ?",
            (hoje.isoformat(),),
        ).fetchone()["c"]
        vencendo = conn.execute(
            "SELECT COUNT(*) c FROM esmaltes WHERE status='Prateleira' "
            "AND validade IS NOT NULL AND validade >= ? AND validade <= ?",
            (hoje.isoformat(), limite),
        ).fetchone()["c"]
        return {"total": total, "prateleira": prateleira,
                "vencidos": vencidos, "vencendo": vencendo}
    finally:
        conn.close()


@app.get("/api/esmaltes")
def listar_esmaltes(
    status: Optional[str] = None,
    q: Optional[str] = None,
    filtro: Optional[str] = None,   # 'vencidos' | 'vencendo'
    ordem: str = "etiqueta",
    limite: int = 200,
    offset: int = 0,
):
    conn = db.get_conn()
    try:
        where = []
        params: list = []
        if status:
            where.append("status = ?")
            params.append(status)
        if q:
            where.append("(marca LIKE ? OR serie LIKE ? OR cor LIKE ? "
                         "OR CAST(etiqueta AS TEXT) LIKE ?)")
            termo = f"%{q}%"
            params += [termo, termo, termo, termo]

        hoje = dt.date.today().isoformat()
        if filtro == "vencidos":
            where.append("validade IS NOT NULL AND validade < ? AND status='Prateleira'")
            params.append(hoje)
        elif filtro == "vencendo":
            limite_data = (dt.date.today() + dt.timedelta(days=90)).isoformat()
            where.append("validade IS NOT NULL AND validade >= ? AND validade <= ? "
                         "AND status='Prateleira'")
            params += [hoje, limite_data]

        ordem_sql = {
            "etiqueta": "etiqueta DESC",
            "validade": "validade IS NULL, validade ASC",
            "cadastro": "data_cadastro DESC",
        }.get(ordem, "etiqueta DESC")

        sql = "SELECT * FROM esmaltes"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += f" ORDER BY {ordem_sql} LIMIT ? OFFSET ?"
        params += [limite, offset]

        rows = conn.execute(sql, params).fetchall()
        ids = [r["id"] for r in rows]
        fotos_por_esmalte: dict[int, list] = {i: [] for i in ids}
        if ids:
            ph = ",".join("?" * len(ids))
            for f in conn.execute(
                f"SELECT esmalte_id, arquivo FROM fotos WHERE esmalte_id IN ({ph})", ids
            ).fetchall():
                fotos_por_esmalte[f["esmalte_id"]].append(f)
        return [_esmalte_dict(r, fotos_por_esmalte[r["id"]]) for r in rows]
    finally:
        conn.close()


@app.get("/api/esmaltes/{esmalte_id}")
def obter_esmalte(esmalte_id: int):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT * FROM esmaltes WHERE id=?", (esmalte_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Esmalte não encontrado")
        fotos = conn.execute(
            "SELECT arquivo FROM fotos WHERE esmalte_id=? ORDER BY id", (esmalte_id,)
        ).fetchall()
        return _esmalte_dict(row, fotos)
    finally:
        conn.close()


@app.post("/api/esmaltes")
async def criar_esmalte(
    marca: Optional[str] = Form(None),
    serie: Optional[str] = Form(None),
    cor: Optional[str] = Form(None),
    validade: Optional[str] = Form(None),
    status: str = Form(normalize.STATUS_PRATELEIRA),
    fotos: list[UploadFile] = File(default=[]),
):
    conn = db.get_conn()
    try:
        etiqueta = db.proxima_etiqueta(conn)
        data_cadastro = dt.date.today().isoformat()
        cur = conn.execute(
            """INSERT INTO esmaltes
               (etiqueta, marca, serie, cor, validade, data_cadastro, status)
               VALUES (?,?,?,?,?,?,?)""",
            (etiqueta,
             normalize.normalizar_marca(marca),
             normalize.normalizar_texto(serie),
             normalize.normalizar_texto(cor),
             _normalizar_validade(validade),
             data_cadastro,
             normalize.normalizar_status(status)),
        )
        esmalte_id = cur.lastrowid
        for up in fotos or []:
            if up and up.filename:
                _salvar_foto(esmalte_id, up, conn)
        conn.commit()

        row = conn.execute("SELECT * FROM esmaltes WHERE id=?", (esmalte_id,)).fetchone()
        flist = conn.execute(
            "SELECT arquivo FROM fotos WHERE esmalte_id=? ORDER BY id", (esmalte_id,)
        ).fetchall()
        return JSONResponse(_esmalte_dict(row, flist), status_code=201)
    finally:
        conn.close()


@app.patch("/api/esmaltes/{esmalte_id}")
async def atualizar_esmalte(esmalte_id: int, payload: dict):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT * FROM esmaltes WHERE id=?", (esmalte_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Esmalte não encontrado")

        campos: dict = {}
        if "marca" in payload:
            campos["marca"] = normalize.normalizar_marca(payload["marca"])
        if "serie" in payload:
            campos["serie"] = normalize.normalizar_texto(payload["serie"])
        if "cor" in payload:
            campos["cor"] = normalize.normalizar_texto(payload["cor"])
        if "validade" in payload:
            campos["validade"] = _normalizar_validade(payload["validade"])
        if "status" in payload:
            novo = normalize.normalizar_status(payload["status"])
            campos["status"] = novo
            # Ao remover, registra a data automaticamente se não houver
            if novo != normalize.STATUS_PRATELEIRA and not row["data_removido"] \
                    and "data_removido" not in payload:
                campos["data_removido"] = dt.date.today().isoformat()
            if novo == normalize.STATUS_PRATELEIRA:
                campos["data_removido"] = None
                campos["motivo"] = None
        if "motivo" in payload:
            campos["motivo"] = normalize.normalizar_motivo(payload["motivo"])
        if "data_removido" in payload:
            campos["data_removido"] = payload["data_removido"] or None

        if campos:
            sets = ", ".join(f"{k}=?" for k in campos)
            conn.execute(f"UPDATE esmaltes SET {sets} WHERE id=?",
                         list(campos.values()) + [esmalte_id])
            conn.commit()

        row = conn.execute("SELECT * FROM esmaltes WHERE id=?", (esmalte_id,)).fetchone()
        fotos = conn.execute(
            "SELECT arquivo FROM fotos WHERE esmalte_id=? ORDER BY id", (esmalte_id,)
        ).fetchall()
        return _esmalte_dict(row, fotos)
    finally:
        conn.close()


@app.post("/api/esmaltes/{esmalte_id}/fotos")
async def adicionar_fotos(esmalte_id: int, fotos: list[UploadFile] = File(...)):
    conn = db.get_conn()
    try:
        row = conn.execute("SELECT id FROM esmaltes WHERE id=?", (esmalte_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Esmalte não encontrado")
        salvas = [_salvar_foto(esmalte_id, up, conn)
                  for up in fotos if up and up.filename]
        conn.commit()
        return {"adicionadas": [s for s in salvas if s]}
    finally:
        conn.close()


@app.delete("/api/esmaltes/{esmalte_id}")
def remover_esmalte(esmalte_id: int):
    conn = db.get_conn()
    try:
        fotos = conn.execute(
            "SELECT arquivo FROM fotos WHERE esmalte_id=?", (esmalte_id,)
        ).fetchall()
        conn.execute("DELETE FROM esmaltes WHERE id=?", (esmalte_id,))
        conn.commit()
        for f in fotos:
            try:
                (db.UPLOAD_DIR / f["arquivo"]).unlink(missing_ok=True)
            except OSError:
                pass
        return {"ok": True}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Arquivos estáticos (PWA) e uploads
# ---------------------------------------------------------------------------
@app.get("/uploads/{nome}")
def servir_upload(nome: str):
    caminho = db.UPLOAD_DIR / nome
    if not caminho.is_file():
        raise HTTPException(404)
    return FileResponse(caminho)


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
