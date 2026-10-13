"""Os vocabulários do padrão de texto da Trilha que o briefing usa (regras/padrao-vocabularios.yaml).

O padrão mora no Trilha-copy (trilha_copy/regras/padrao.yaml); aqui fica uma cópia só das listas que a revisão do
briefing usa, conferida na CI. A notação é a mesma de lá: termo inteiro, `radical*` (começo de palavra) e
`re:expressão` (borda de palavra no começo; no fim, não emenda em letra).
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import yaml

ARQUIVO = Path(__file__).parent / "regras" / "padrao-vocabularios.yaml"
BORDA = "(?<![a-z0-9])"
PALAVRA = re.compile(r"[a-z0-9]+")


def normalizar(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


@lru_cache(maxsize=1)
def carregar() -> dict:
    return yaml.safe_load(ARQUIVO.read_text(encoding="utf-8"))


@lru_cache(maxsize=512)
def _padrao(item: str) -> re.Pattern:
    if item.startswith("re:"):
        return re.compile(BORDA + "(?:" + item[3:] + ")(?![a-z])")
    if item.endswith("*"):
        return re.compile(BORDA + re.escape(item[:-1]) + "[a-z0-9]*")
    return re.compile(BORDA + re.escape(item) + "(?![a-z0-9])")


def posicoes(itens: list[str], texto: str) -> list[tuple[int, str]]:
    """(posição em palavras, trecho) de cada ocorrência dos itens no texto, sem acento e em minúsculas."""
    t = normalizar(texto)
    achados = []
    for item in itens:
        for m in _padrao(item).finditer(t):
            achados.append((len(PALAVRA.findall(t[:m.start()])), m.group(0)))
    return sorted(achados)


def achar(nome: str, texto: str) -> list[str]:
    """O primeiro trecho de cada item que casa, na ordem dos itens (igual ao trilha_copy.padrao.achar)."""
    t = normalizar(texto)
    return [m.group(0) for item in carregar()["vocabularios"][nome] if (m := _padrao(item).search(t))]


def contem_termo(texto: str, termo: str) -> bool:
    """Um termo do cliente (proibido, por exemplo) como termo inteiro: "corra" não pega "ocorra"."""
    return bool(posicoes([termo if termo.startswith("re:") else normalizar(termo)], texto))


def garante_resultado(frase: str) -> bool:
    """Garantia de algo que não depende só da empresa (valorização, aprovação, renda, cura, fluência…)."""
    if achar("garantia_de_resultado", frase):
        return True
    janela = carregar()["janela_garantia_palavras"]
    garantias = [i for i, _ in posicoes(["garant*"], frase)]
    resultados = [i for i, _ in posicoes(carregar()["vocabularios"]["resultado_garantivel"], frase)]
    return any(abs(g - r) <= janela for g in garantias for r in resultados) and not achar("inversao_de_risco", frase)
