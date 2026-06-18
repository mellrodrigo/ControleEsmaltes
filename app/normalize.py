"""Normalização de dados de esmaltes.

Padroniza marca, status e motivo para corrigir as inconsistências
encontradas na planilha original (ex.: "impala" e "IMPALA" -> "Impala").
"""
from __future__ import annotations

import re
import unicodedata

# --- Status válidos ----------------------------------------------------------
STATUS_PRATELEIRA = "Prateleira"
STATUS_REMOVIDO = "Removido"
STATUS_DESAPARECIDO = "Desaparecido"
STATUS_VALIDOS = (STATUS_PRATELEIRA, STATUS_REMOVIDO, STATUS_DESAPARECIDO)

# --- Motivos canônicos -------------------------------------------------------
MOTIVOS_VALIDOS = (
    "Acabou",
    "Vencido",
    "Ficou duro",
    "Desaparecido",
    "Perdido",
    "Amarelou",
    "Ninguém usa",
    "Brinde",
    "Presente",
)


def _slug(valor: str) -> str:
    """Remove acentos, espaços extras e baixa a caixa para comparação."""
    texto = unicodedata.normalize("NFKD", valor)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip().lower()


# Mapa de marcas conhecidas (chave = slug) -> nome canônico
_MARCAS = {
    "risque": "Risqué",
    "impala": "Impala",
    "colorama": "Colorama",
    "anita": "Anita",
    "dailus": "Dailus",
    "vult": "Vult",
    "ana hickmann": "Ana Hickmann",
    "nati": "Nati",
    "hits": "Hits",
    "avon": "Avon",
    "real love": "Real Love",
    "dafu": "Dafu",
    "mark": "Mark",
    "mark.": "Mark",
    "marchetti": "Marchetti",
    "marcelo beauty": "Marcelo Beauty",
    "ludurana": "Ludurana",
    "bella brazil": "Bella Brazil",
    "top beauty": "Top Beauty",
    "o.p.i": "OPI",
    "opi": "OPI",
}


def normalizar_marca(valor) -> str | None:
    if valor is None:
        return None
    bruto = str(valor).strip()
    if not bruto:
        return None
    slug = _slug(bruto)
    if slug in _MARCAS:
        return _MARCAS[slug]
    # Marca desconhecida: usa Title Case preservando o texto original
    return bruto.title()


def normalizar_status(valor) -> str:
    if valor is None:
        return STATUS_PRATELEIRA
    slug = _slug(str(valor))
    if not slug:
        return STATUS_PRATELEIRA
    if slug.startswith("remov"):
        return STATUS_REMOVIDO
    if slug.startswith("desaparec"):
        return STATUS_DESAPARECIDO
    if slug.startswith("pratel"):
        return STATUS_PRATELEIRA
    return STATUS_PRATELEIRA


def normalizar_motivo(valor) -> str | None:
    if valor is None:
        return None
    slug = _slug(str(valor))
    if not slug:
        return None
    mapa = {
        "acabou": "Acabou",
        "acab0u": "Acabou",
        "vencido": "Vencido",
        "ficou duro": "Ficou duro",
        "duro": "Ficou duro",
        "desaparecido": "Desaparecido",
        "perdido": "Perdido",
        "amarelou": "Amarelou",
        "ninguem usa": "Ninguém usa",
    }
    if slug in mapa:
        return mapa[slug]
    if "brinde" in slug:
        return "Brinde"
    if "presente" in slug:
        return "Presente"
    # Mantém o texto original com a primeira letra maiúscula
    return slug.capitalize()


def normalizar_texto(valor) -> str | None:
    """Normaliza campos livres (série, cor): trim e caixa baixa coerente."""
    if valor is None:
        return None
    texto = re.sub(r"\s+", " ", str(valor)).strip()
    return texto or None
