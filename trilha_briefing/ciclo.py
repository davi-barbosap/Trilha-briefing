"""Fechamento de ciclo: guarda o estado do cliente antes da revisão trimestral.

Editar os arquivos apaga o que estava lá. Antes de revisar o plano com os dados do trimestre,
`fechar-ciclo` copia tudo para `historico/<nome>/` e escreve um resumo do que se aprendeu.
"""

from __future__ import annotations

import re
import shutil
from datetime import date
from pathlib import Path

from trilha_briefing.esquema import ARQUIVOS, ClienteCompleto, carregar_cliente
from trilha_briefing.revisao import NIVEIS, revisar

NOME = re.compile(r"^[0-9A-Za-z][0-9A-Za-z_-]{0,31}$")  # ex.: 2026-T4


def _resumo(c: ClienteCompleto, nome: str) -> str:
    linhas = [f"# Ciclo {nome} — {c.briefing.cliente.nome}", "", f"Fechado em {date.today().isoformat()}.", ""]
    hip = c.hipoteses.hipoteses
    if hip:
        linhas += ["## Hipóteses", "", "| id | resultado | conversões | aprendizado |", "|---|---|---|---|"]
        linhas += [f"| {h.id} | {h.resultado} | {h.conversoes_obtidas if h.conversoes_obtidas is not None else '—'} | "
                   f"{h.aprendizado or '—'} |" for h in hip]
        linhas.append("")
    if c.estrategia.economia and c.estrategia.economia.estimados:
        linhas += ["## Ainda estimado na economia", "", ", ".join(c.estrategia.economia.estimados), ""]
    avisos = revisar(c)
    linhas += ["## Revisão no fechamento", ""]
    linhas += [f"- {n}: {sum(1 for a in avisos if a.nivel == n)}" for n in NIVEIS]
    linhas += ["", "## Para o próximo ciclo", "",
               "- Atualizar `hipoteses.yaml` com os resultados e o aprendizado.",
               "- Trocar os `estimados` da economia pelas taxas reais do CRM.",
               "- Promover a `validada` o que a escuta e os dados confirmaram; marcar `refutada` o que caiu.",
               "- Revisar canais e grade; gerar a nova apresentação.", ""]
    return "\n".join(linhas)


def fechar_ciclo(pasta: str | Path, nome: str) -> Path:
    if not NOME.match(nome):
        raise ValueError("nome do ciclo: letras, números, - e _ (ex.: 2026-T4)")
    pasta = Path(pasta)
    c = carregar_cliente(pasta)
    destino = pasta / "historico" / nome
    if destino.exists():
        raise FileExistsError(f"{destino} já existe")
    destino.mkdir(parents=True)
    for arquivo, _ in ARQUIVOS.values():
        if (pasta / arquivo).exists():
            shutil.copy2(pasta / arquivo, destino / arquivo)
    if (pasta / "ofertas").is_dir():
        shutil.copytree(pasta / "ofertas", destino / "ofertas")
    (destino / "resumo.md").write_text(_resumo(c, nome), encoding="utf-8")
    return destino
