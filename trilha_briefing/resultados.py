"""O caminho de volta: o retorno do Trilha-ads nas hipóteses do briefing.

O Trilha-ads grava o retorno de um período em ads/<id>/retornos/<inicio>_<fim>.yaml (contrato `retorno`): o resultado
de cada código de criativo e os motivos de perda. Aqui:

1. `registrar(retorno, pasta)` guarda uma cópia em briefing/<id>/resultados/ (o histórico fica no Trilha-clientes),
   liga os códigos às hipóteses e registra a medição: `conversoes_obtidas` (a da variação com menos volume) e
   `resultado: rodando` na hipótese que estava planejada. Diz quais já têm volume para decidir.
2. `decidir(pasta, hipotese, resultado, aprendizado)` registra a decisão do assessor: validada, refutada ou
   inconclusiva, com o aprendizado. A ferramenta mede; quem decide é o assessor, contra o critério combinado.

Os arquivos são editados por linha: os comentários ficam.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from trilha_briefing.esquema import ClienteCompleto, ErroCliente, Hipotese, Hipoteses, carregar_cliente
from trilha_briefing.questionario.editor import Arquivo

VERSOES_RETORNO = {1}
CONTAGEM = {"lead": "leads", "lead_qualificado": "qualificados", "agendamento": "agendamentos", "venda": "vendas"}
CUSTO = {"lead": "cpl", "lead_qualificado": "custo_por_qualificado", "venda": "custo_por_venda"}
DECISOES = ("validada", "refutada", "inconclusiva")


class RetornoInvalido(ValueError):
    pass


@dataclass
class Medicao:
    hipotese: Hipotese
    evento: str
    por_codigo: dict[str, tuple[int, float | None]]  # código → (conversões no evento, custo por conversão)
    faltam: list[str]  # códigos da hipótese que não aparecem no retorno
    comparavel: bool  # uma variação por código: o retorno separa as variações
    conversoes: int | None = None
    pronta: bool = False


@dataclass
class Relatorio:
    guardado: Path | None = None
    periodo: str = ""
    medicoes: list[Medicao] = field(default_factory=list)
    sem_hipotese: list[str] = field(default_factory=list)  # códigos com resultado e sem hipótese
    motivos: list[dict] = field(default_factory=list)
    alterados: list[str] = field(default_factory=list)
    erro: str | None = None


def ler_retorno(caminho: str | Path) -> dict:
    try:
        dados = yaml.safe_load(Path(caminho).read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as e:
        raise RetornoInvalido(f"{caminho}: não deu para ler ({e})") from e
    if dados.get("retorno") not in VERSOES_RETORNO or not isinstance(dados.get("por_codigo"), dict):
        raise RetornoInvalido(f"{caminho}: não é um retorno do Trilha-ads (versões aceitas: {sorted(VERSOES_RETORNO)})")
    return dados


def _custo(d: dict, evento: str) -> float | None:
    if evento in CUSTO:
        return d.get(CUSTO[evento])
    n = d.get(CONTAGEM[evento]) or 0
    return d["gasto"] / n if d.get("gasto") is not None and n else None


def medir(c: ClienteCompleto, retorno: dict) -> list[Medicao]:
    medicoes = []
    for h in c.hipoteses.hipoteses:
        if not h.codigos:
            continue
        evento = h.evento or c.estrategia.metrica_principal
        presentes = {cod: retorno["por_codigo"][cod] for cod in h.codigos if cod in retorno["por_codigo"]}
        if not presentes:
            continue
        por_codigo = {cod: (int(d.get(CONTAGEM[evento]) or 0), _custo(d, evento)) for cod, d in presentes.items()}
        comparavel = len(h.codigos) >= 2 and len(h.codigos) == h.variacoes
        m = Medicao(h, evento, por_codigo, [x for x in h.codigos if x not in presentes], comparavel)
        if comparavel:
            m.conversoes = min(n for n, _ in por_codigo.values()) if not m.faltam else 0
            m.pronta = not m.faltam and m.conversoes >= h.minimo_conversoes
        medicoes.append(m)
    return medicoes


def _guardar(retorno_caminho: Path, pasta: Path) -> Path:
    destino_dir = pasta / "resultados"
    destino_dir.mkdir(exist_ok=True)
    destino = destino_dir / retorno_caminho.name
    if destino.exists() and destino.read_bytes() != retorno_caminho.read_bytes():
        n = 2
        while (destino_dir / f"{retorno_caminho.stem}-{n}{retorno_caminho.suffix}").exists():
            n += 1
        destino = destino_dir / f"{retorno_caminho.stem}-{n}{retorno_caminho.suffix}"
    if not destino.exists():
        shutil.copyfile(retorno_caminho, destino)
    return destino


def registrar(retorno_caminho: str | Path, pasta: str | Path) -> Relatorio:
    retorno_caminho, pasta = Path(retorno_caminho), Path(pasta)
    rel = Relatorio()
    retorno = ler_retorno(retorno_caminho)
    c = carregar_cliente(pasta)
    if retorno.get("cliente") and retorno["cliente"] != c.briefing.cliente.id:
        rel.erro = f"o retorno é de '{retorno['cliente']}', e a pasta é de '{c.briefing.cliente.id}'"
        return rel
    p = retorno.get("periodo") or {}
    rel.periodo = f"{p.get('inicio', '?')} a {p.get('fim', '?')}"
    rel.medicoes = medir(c, retorno)
    com_hipotese = {cod for h in c.hipoteses.hipoteses for cod in h.codigos}
    rel.sem_hipotese = [cod for cod in retorno["por_codigo"] if cod not in com_hipotese and cod != "sem código"]
    rel.motivos = list(retorno.get("motivos_perda") or [])
    arq = Arquivo(pasta / "hipoteses.yaml", validador=Hipoteses)
    for m in rel.medicoes:
        h = m.hipotese
        if m.comparavel and m.conversoes is not None and m.conversoes != h.conversoes_obtidas:
            if arq.definir_no_item("hipoteses", h.id, "conversoes_obtidas", m.conversoes) == "preenchido":
                rel.alterados.append(f"{h.id}.conversoes_obtidas = {m.conversoes}")
        if h.resultado == "planejada":
            if arq.definir_no_item("hipoteses", h.id, "resultado", "rodando") == "preenchido":
                rel.alterados.append(f"{h.id}.resultado = rodando")
    arq.gravar()
    try:
        carregar_cliente(pasta)
    except ErroCliente as e:
        arq.desfazer()
        rel.erro = str(e)
        rel.alterados = []
        return rel
    rel.guardado = _guardar(retorno_caminho, pasta)
    return rel


def decidir(pasta: str | Path, hipotese: str, resultado: str, aprendizado: str, fim: date | None = None) -> list[str]:
    """Registra a decisão do assessor. Devolve o que mudou; ValueError quando não dá para registrar."""
    pasta = Path(pasta)
    if resultado not in DECISOES:
        raise ValueError(f"resultado precisa ser um de {', '.join(DECISOES)}")
    if resultado in ("validada", "refutada") and not aprendizado.strip():
        raise ValueError("diga o aprendizado (--aprendizado): é ele que vai para a copy e para a próxima rodada")
    c = carregar_cliente(pasta)
    if not any(h.id == hipotese for h in c.hipoteses.hipoteses):
        raise ValueError(f"a hipótese '{hipotese}' não existe em hipoteses.yaml")
    arq = Arquivo(pasta / "hipoteses.yaml", validador=Hipoteses)
    mudancas: list[tuple[str, Any]] = [("resultado", resultado), ("fim", (fim or date.today()).isoformat())]
    if aprendizado.strip():
        mudancas.append(("aprendizado", aprendizado.strip()))
    for campo, valor in mudancas:
        if arq.definir_no_item("hipoteses", hipotese, campo, valor) != "preenchido":
            raise ValueError(f"não deu para gravar {hipotese}.{campo}: {arq.motivo or 'edite hipoteses.yaml à mão'}")
    arq.gravar()
    return [f"{hipotese}.{campo} = {valor}" for campo, valor in mudancas]


def _num(v: float | None, moeda: bool = False) -> str:
    if v is None:
        return "—"
    return ("R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")) if moeda else f"{v:g}"


def em_texto(rel: Relatorio) -> str:
    if rel.erro:
        return f"✗ nada foi gravado: {rel.erro}\n"
    linhas = [f"✓ retorno de {rel.periodo} guardado em {rel.guardado}"]
    for m in rel.medicoes:
        h = m.hipotese
        linhas.append(f"\n{h.id} ({h.resultado}) — {h.hipotese}")
        for cod, (n, custo) in m.por_codigo.items():
            linhas.append(f"  {cod:<8} {n} {m.evento.replace('_', ' ')}(s)" + (f" · {_num(custo, True)} cada" if custo else ""))
        if m.faltam:
            linhas.append(f"  sem resultado no período: {', '.join(m.faltam)}")
        if not m.comparavel:
            linhas.append(f"  · as {h.variacoes} variações não são códigos diferentes: o retorno por código não as separa. "
                          "Decida com o relatório do Trilha-ads.")
        elif m.pronta:
            linhas.append(f"  ✓ pronta para decidir: todas as variações passaram de {h.minimo_conversoes}. Compare com o critério "
                          f"combinado (\"{h.criterio_sucesso}\") e registre:")
            linhas.append(f"    python -m trilha_briefing decidir <pasta> {h.id} validada|refutada|inconclusiva --aprendizado \"…\"")
        else:
            linhas.append(f"  … ainda sem volume: a variação mais fraca tem {m.conversoes} de {h.minimo_conversoes}. "
                          "Decidir agora é ler ruído.")
    if rel.sem_hipotese:
        linhas.append(f"\n· códigos com resultado e sem hipótese: {', '.join(rel.sem_hipotese)} (só medição, sem teste)")
    if rel.motivos:
        linhas.append("\nMotivos de perda do período (os 5 mais comuns):")
        linhas += [f"  {x['leads']:>4}  {x['motivo']} ({x['categoria']})" for x in rel.motivos[:5]]
        linhas.append("  Os de categoria comercial ou de oferta são objeções reais: confira se a oferta responde a cada uma "
                      "(ofertas/<id>.yaml, objecoes, com fonte: dados).")
    if rel.alterados:
        linhas.append("\nhipoteses.yaml: " + "; ".join(rel.alterados))
    return "\n".join(linhas) + "\n"
