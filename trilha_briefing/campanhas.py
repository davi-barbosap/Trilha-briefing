"""Plano de campanhas: como a estratégia vira campanhas, conjuntos e anúncios.

O plano registra decisões aprovadas com o cliente: canal, plataforma, evento de otimização, verba, fase,
públicos, palavras-chave, quais células da grade rodam onde, como cada hipótese vai ser testada e os
nomes. A estrutura real fica nas plataformas; o Trilha-ads compara o planejado com o que está rodando.

As regras ficam em `regras/campanhas.yaml` (padrão para todos os clientes) e podem ser mudadas por
cliente no bloco `regras:` do `campanhas.yaml` dele. Esta ferramenta sugere e confere; quem decide é o
assessor.
"""

from __future__ import annotations

import math
import string
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from trilha_briefing.economia import SEMANAS_POR_MES, calcular
from trilha_briefing.esquema import (
    Campanha, ClienteCompleto, Conjunto, Hipotese, MetodoTeste, PlanoCampanhas, TestePlanejado,
)

ARQUIVO_PADRAO = Path(__file__).parent / "regras" / "campanhas.yaml"
NivelRegra = Literal["bloqueia", "atencao", "sugestao", "desligada"]
CANAIS_SEM_MIDIA = {"organico", "email_crm", "indicacao", "parcerias", "offline"}
METODO = {
    "ab_plataforma": "teste A/B da plataforma",
    "conjuntos_separados": "conjuntos separados com a mesma verba",
    "comparacao_no_conjunto": "comparação dentro do conjunto",
}
CAMPOS_NOME = {"cliente", "campanha", "conjunto", "codigo", "versao", "plataforma", "canal", "evento", "fase"}
PLATAFORMA = {"meta": "Meta", "google": "Google", "tiktok": "TikTok", "linkedin": "LinkedIn"}
FASE = {"fundacao": "fundação", "validacao": "validação", "otimizacao": "otimização", "escala": "escala"}
PLURAL = {"lead": "leads", "lead_qualificado": "leads qualificados", "agendamento": "agendamentos", "venda": "vendas"}


# ---------- regras ----------


class _R(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Espelho(_R):
    ids_da_plataforma: bool = False


class Aprendizado(_R):
    nivel: NivelRegra = "atencao"
    eventos_por_semana: dict[str, int | None] = Field(default_factory=dict)


class Testes(_R):
    nivel: NivelRegra = "atencao"
    metodo_padrao: MetodoTeste | None = None
    comparacao_conclui: bool = False


class Nomes(_R):
    nivel: NivelRegra = "bloqueia"
    campanha: str
    conjunto: str
    anuncio: str
    utm: str


class Entrar(_R):
    medicao_completa: bool = False
    custo_ate_x_teto: float | None = Field(default=None, gt=0)
    eventos_minimos: int | None = Field(default=None, ge=1)
    semanas_estaveis: int | None = Field(default=None, ge=1)


class Fases(_R):
    nivel: NivelRegra = "atencao"
    ordem: list[str]
    entrar: dict[str, Entrar] = Field(default_factory=dict)
    escala_aumento_max_pct: float = Field(gt=0)
    escala_intervalo_dias: int = Field(ge=1)

    @model_validator(mode="after")
    def _fases_conhecidas(self) -> Fases:
        fora = [f for f in self.entrar if f not in self.ordem]
        if fora:
            raise ValueError(f"fases.entrar cita fases fora de fases.ordem: {fora}")
        return self


class RegraPlano(_R):
    obrigatorio_para_aprovar: bool = False


class Regras(_R):
    espelho: Espelho
    aprendizado: Aprendizado
    testes: Testes
    nomes: Nomes
    fases: Fases
    plano: RegraPlano

    @model_validator(mode="after")
    def _nomes_validos(self) -> Regras:
        for chave in ("campanha", "conjunto", "anuncio", "utm"):
            molde = getattr(self.nomes, chave)
            campos = {c for _, c, _, _ in string.Formatter().parse(molde) if c}
            if campos - CAMPOS_NOME:
                raise ValueError(f"nomes.{chave} usa campos desconhecidos {sorted(campos - CAMPOS_NOME)}; "
                                 f"os possíveis são {sorted(CAMPOS_NOME)}")
        return self


class ErroRegras(Exception):
    pass


@lru_cache(maxsize=1)
def _padrao() -> dict[str, Any]:
    return yaml.safe_load(ARQUIVO_PADRAO.read_text(encoding="utf-8"))


def _mesclar(base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    saida = dict(base)
    for chave, valor in extra.items():
        if isinstance(valor, dict) and isinstance(saida.get(chave), dict):
            saida[chave] = _mesclar(saida[chave], valor)
        else:
            saida[chave] = valor
    return saida


def regras_do_plano(plano: PlanoCampanhas | None = None) -> Regras:
    """Regras padrão do repositório com o que o cliente mudou por cima."""
    dados = _mesclar(_padrao(), (plano.regras if plano else {}) or {})
    try:
        return Regras.model_validate(dados)
    except ValidationError as e:
        raise ErroRegras(f"regras do plano inválidas: {e}") from e


# ---------- contas ----------


def nome(molde: str, **campos: Any) -> str:
    return molde.format(**{c: campos.get(c, f"{{{c}}}") for c in CAMPOS_NOME})


def brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def legivel(valor: str, plural: bool = False) -> str:
    """Plataforma, fase ou evento como se escreve: Meta, validação, lead qualificado."""
    if plural and valor in PLURAL:
        return PLURAL[valor]
    return PLATAFORMA.get(valor) or FASE.get(valor) or valor.replace("_", " ")


def vezes(x: float) -> str:
    return f"{x:g}".replace(".", ",") + "×"


def evento_da(c: ClienteCompleto, cp: Campanha) -> str:
    return cp.evento or c.estrategia.evento_otimizacao or c.estrategia.metrica_principal


def custo_teto(c: ClienteCompleto, evento: str) -> float | None:
    return calcular(c.estrategia.economia).custo_max.get(evento) if c.estrategia.economia else None


def _canal_do_plano(c: ClienteCompleto, cp: Campanha):
    candidatos = [x for x in c.estrategia.canais if x.canal == cp.canal and x.status != "descartado"]
    return next((x for x in candidatos if x.plataforma == cp.plataforma), next(iter(candidatos), None))


def verba_da(c: ClienteCompleto, cp: Campanha, campanhas: list[Campanha] | None = None) -> float | None:
    """A verba da campanha, ou a parte dela na fatia do canal quando não foi definida."""
    if cp.verba_mensal:
        return cp.verba_mensal
    canal, total = _canal_do_plano(c, cp), c.estrategia.orcamento.verba_mensal
    if canal is None or canal.verba_pct is None or not total:
        return None
    mesmas = [x for x in (campanhas if campanhas is not None else c.campanhas.campanhas)
              if x.canal == cp.canal and _canal_do_plano(c, x) is canal]
    fixas = sum(x.verba_mensal for x in mesmas if x.verba_mensal)
    abertas = [x for x in mesmas if not x.verba_mensal] or [cp]
    return max(0.0, total * canal.verba_pct / 100 - fixas) / len(abertas)


def verba_do_conjunto(cp: Campanha, cj: Conjunto, verba_campanha: float | None) -> float | None:
    if cj.verba_mensal:
        return cj.verba_mensal
    if verba_campanha is None or not cp.conjuntos:
        return None
    fixas = sum(x.verba_mensal for x in cp.conjuntos if x.verba_mensal)
    abertos = [x for x in cp.conjuntos if not x.verba_mensal]
    return max(0.0, verba_campanha - fixas) / len(abertos)


def por_semana(verba_mensal: float | None, custo: float | None) -> float | None:
    return verba_mensal / SEMANAS_POR_MES / custo if verba_mensal and custo else None


@dataclass
class Conta:
    """O que o plano de uma campanha significa em números, no teto de custo."""

    campanha: Campanha
    evento: str
    verba: float | None
    custo: float | None
    eventos_semana: float | None
    limite: int | None  # eventos por semana para sair do aprendizado nesta plataforma
    conjuntos_que_cabem: int | None
    verba_conjuntos: dict[str, float | None] = field(default_factory=dict)


def contas(c: ClienteCompleto, cp: Campanha, regras: Regras, campanhas: list[Campanha] | None = None) -> Conta:
    evento = evento_da(c, cp)
    verba = verba_da(c, cp, campanhas)
    custo = custo_teto(c, evento)
    semana = por_semana(verba, custo)
    limite = regras.aprendizado.eventos_por_semana.get(cp.plataforma)
    cabem = math.floor(semana / limite) if semana is not None and limite else None
    return Conta(cp, evento, verba, custo, semana, limite, cabem,
                 {cj.id: verba_do_conjunto(cp, cj, verba) for cj in cp.conjuntos})


def prazo_semanas(c: ClienteCompleto, h: Hipotese) -> float | None:
    if h.inicio and h.fim:
        return (h.fim - h.inicio).days / 7
    return c.estrategia.orcamento.semanas_validacao


def hipotese(c: ClienteCompleto, hid: str) -> Hipotese | None:
    return next((h for h in c.hipoteses.hipoteses if h.id == hid), None)


def metodo_do(t: TestePlanejado, regras: Regras) -> MetodoTeste | None:
    return t.metodo or regras.testes.metodo_padrao


def criterio_de_fase(c: ClienteCompleto, conta: Conta, fase: str, regras: Regras) -> str:
    e = regras.fases.entrar.get(fase)
    if e is None:
        return "sem critério definido em regras.fases.entrar"
    partes = []
    if e.medicao_completa:
        partes.append("medição completa (os seis itens de estrategia.medicao)")
    if e.custo_ate_x_teto and conta.custo:
        partes.append(f"custo por {legivel(conta.evento)} até {brl(conta.custo * e.custo_ate_x_teto)} ({vezes(e.custo_ate_x_teto)} o teto)")
    if e.eventos_minimos:
        partes.append(f"{e.eventos_minimos} {legivel(conta.evento, plural=True)} ou mais na fase atual")
    if e.semanas_estaveis:
        partes.append(f"{e.semanas_estaveis} semanas seguidas dentro do custo")
    return "; ".join(partes) or "sem critério definido"


def proxima_fase(fase: str, regras: Regras) -> str | None:
    ordem = regras.fases.ordem
    i = ordem.index(fase) if fase in ordem else -1
    return ordem[i + 1] if 0 <= i < len(ordem) - 1 else None


def celulas_sem_campanha(c: ClienteCompleto) -> list[str]:
    usadas = {x for cp in c.campanhas.campanhas for cj in cp.conjuntos for x in cj.celulas}
    return [cel.codigo for cel in c.estrategia.grade if cel.codigo not in usadas]


def canais_sem_campanha(c: ClienteCompleto) -> list[str]:
    def planejado(x) -> bool:
        return any(cp.canal == x.canal and (not x.plataforma or cp.plataforma == x.plataforma) for cp in c.campanhas.campanhas)
    return [f"{x.canal} ({x.plataforma})" if x.plataforma else x.canal for x in c.estrategia.canais
            if x.status in ("ativo", "teste") and x.canal not in CANAIS_SEM_MIDIA and not planejado(x)]


# ---------- sugestão ----------


def _plataforma_da_celula(cel) -> str:
    texto = f"{cel.publico} {cel.formato}".lower()
    return next((p for p in ("google", "meta", "tiktok", "linkedin") if p in texto), "")


def sugerir(c: ClienteCompleto, regras: Regras | None = None) -> PlanoCampanhas:
    """Um rascunho a partir dos canais, da grade, da verba e da economia. É para revisar, não para usar como está."""
    regras = regras or regras_do_plano(None)
    campanhas: list[Campanha] = []
    for canal in c.estrategia.canais:
        if canal.status not in ("ativo", "teste") or canal.canal in CANAIS_SEM_MIDIA or not canal.plataforma:
            continue
        cp = Campanha(id=f"{canal.plataforma}-{canal.canal}".replace("_", "-"), canal=canal.canal,
                      plataforma=canal.plataforma, fase=regras.fases.ordem[0])
        campanhas.append(cp)
    for cp in campanhas:
        celulas = [cel for cel in c.estrategia.grade if _plataforma_da_celula(cel) == cp.plataforma]
        busca = cp.canal.startswith("busca_")
        if cp.canal == "busca_marca":
            cp.conjuntos = [Conjunto(id="marca", palavras_chave=[c.briefing.cliente.nome], correspondencia="frase")]
            continue
        if cp.canal == "remarketing":
            cp.conjuntos = [Conjunto(id="visitantes-30d", publico="visitou a página ou conversou nos últimos 30 dias",
                                     exclusoes=["quem já virou lead"])]
            continue
        if busca:
            cp.conjuntos = [Conjunto(id=cel.codigo.lower(), celulas=[cel.codigo], correspondencia="frase") for cel in celulas] \
                or [Conjunto(id="principal", correspondencia="frase")]
        else:
            conta = contas(c, cp, regras, campanhas)
            cabem = max(1, conta.conjuntos_que_cabem) if conta.conjuntos_que_cabem is not None else None
            grupos: dict[str, list[str]] = {}
            for cel in celulas:
                grupos.setdefault(cel.persona or "amplo", []).append(cel.codigo)
            if cabem is not None and len(grupos) > cabem:
                grupos = {"amplo": [x for g in grupos.values() for x in g]}  # a verba não aguenta um conjunto por persona
            cp.conjuntos = [Conjunto(id=g, publico="amplo" if g == "amplo" else f"persona {g}", celulas=cods)
                            for g, cods in grupos.items()] or [Conjunto(id="amplo", publico="amplo")]
        celulas_da = {x for cj in cp.conjuntos for x in cj.celulas}
        cp.testes = [TestePlanejado(hipotese=h.id, metodo=regras.testes.metodo_padrao) for h in c.hipoteses.hipoteses
                     if h.resultado in ("planejada", "rodando") and h.codigos and set(h.codigos) <= celulas_da]
    return PlanoCampanhas(campanhas=campanhas)


def sugestao_em_yaml(c: ClienteCompleto, plano: PlanoCampanhas) -> str:
    dados = plano.model_dump(mode="json", exclude_defaults=True)
    dados.setdefault("campanhas", [])
    sem = [cel.codigo for cel in c.estrategia.grade
           if cel.codigo not in {x for cp in plano.campanhas for cj in cp.conjuntos for x in cj.celulas}]
    cabecalho = [
        "# Plano de campanhas: as decisões de mídia aprovadas com o cliente. A estrutura real fica nas plataformas.",
        "# SUGESTÃO gerada por `python -m trilha_briefing plano --sugerir`: revise tudo antes de usar.",
        "#   - públicos, palavras-chave e negativas são do assessor;",
        "#   - a verba vem da fatia de cada canal (verba_pct) quando a campanha não tem verba_mensal;",
        "#   - cada teste precisa de um método: ab_plataforma | conjuntos_separados | comparacao_no_conjunto.",
        "#",
        "# campanha: id, canal (de estrategia.yaml), plataforma, evento (vazio = o da estratégia), fase, verba_mensal,",
        "#           conjuntos, negativas (Google), testes ({ hipotese, metodo }), observacoes",
        "# conjunto: id, publico, palavras_chave (Google), correspondencia (ampla | frase | exata), exclusoes,",
        "#           celulas (códigos da grade que viram anúncios), verba_mensal (vazio = a da campanha)",
        "# Regras padrão: trilha_briefing/regras/campanhas.yaml. Para mudar só para este cliente: bloco `regras:`.",
    ]
    if sem:
        cabecalho.append(f"# Células sem campanha (coloque num conjunto ou deixe de fora de propósito): {', '.join(sem)}")
    corpo = yaml.safe_dump({"regras": {}, **dados}, allow_unicode=True, sort_keys=False, width=120)
    return "\n".join(cabecalho) + "\n" + corpo


# ---------- texto ----------


def em_texto(c: ClienteCompleto, regras: Regras) -> str:
    est, linhas = c.estrategia, [f"Plano de campanhas — {c.briefing.cliente.nome}"]
    verbas = [verba_da(c, cp) for cp in c.campanhas.campanhas]
    soma = sum(v for v in verbas if v)
    linhas.append(f"Verba: as campanhas somam {brl(soma)}/mês"
                  + (f" (estratégia: {brl(est.orcamento.verba_mensal)})" if est.orcamento.verba_mensal else ""))
    for cp in c.campanhas.campanhas:
        conta = contas(c, cp, regras)
        linhas += ["", f"{cp.id} · {legivel(cp.canal)} · {legivel(cp.plataforma)} · fase {legivel(cp.fase)} · otimiza por {legivel(conta.evento)} · "
                       f"{brl(conta.verba) + '/mês' if conta.verba else 'sem verba definida'}"]
        cliente = c.briefing.cliente.id
        linhas.append(f"  Nome: {nome(regras.nomes.campanha, cliente=cliente, campanha=cp.id, plataforma=cp.plataforma, canal=cp.canal, evento=conta.evento, fase=cp.fase)}")
        linhas.append(f"  UTM: {nome(regras.nomes.utm, cliente=cliente, campanha=cp.id, plataforma=cp.plataforma, canal=cp.canal)}")
        if conta.eventos_semana is not None:
            ev = legivel(conta.evento)
            texto = (f"  No teto ({brl(conta.custo)} por {ev}): cerca de {conta.eventos_semana:.0f} "
                     f"{legivel(conta.evento, plural=True)} por semana")
            if conta.limite:
                texto += (f"; o {legivel(cp.plataforma)} pede {conta.limite} por conjunto para sair do aprendizado → "
                          f"cabem {conta.conjuntos_que_cabem}")
            linhas.append(texto)
        for cj in cp.conjuntos:
            quem = cj.publico or (", ".join(cj.palavras_chave) if cj.palavras_chave else "—")
            v = conta.verba_conjuntos.get(cj.id)
            anuncios = ", ".join(nome(regras.nomes.anuncio, codigo=x, versao=1) for x in cj.celulas) or "nenhuma célula"
            linhas.append(f"  · {nome(regras.nomes.conjunto, conjunto=cj.id, campanha=cp.id)} ({quem})"
                          + (f" · {brl(v)}/mês" if v and len(cp.conjuntos) > 1 else "") + f": {anuncios}")
        for t in cp.testes:
            h, metodo = hipotese(c, t.hipotese), metodo_do(t, regras)
            if h is None:
                continue
            ev = h.evento or est.metrica_principal
            semana = por_semana(conta.verba, custo_teto(c, ev))
            precisa = h.minimo_conversoes * h.variacoes
            prazo = f", cerca de {precisa / semana:.0f} semanas no teto" if semana else ""
            linhas.append(f"  Teste {h.id}: {METODO.get(metodo, 'sem método')} · precisa de {precisa} {legivel(ev, plural=True)}{prazo}")
        prox = proxima_fase(cp.fase, regras)
        if prox:
            linhas.append(f"  Para entrar em {legivel(prox)}: {criterio_de_fase(c, conta, prox, regras)}")
        if cp.fase == regras.fases.ordem[-1]:
            linhas.append(f"  Na {legivel(cp.fase)}: suba a verba no máximo {regras.fases.escala_aumento_max_pct:g}% a cada "
                          f"{regras.fases.escala_intervalo_dias} dias")
        if cp.negativas:
            linhas.append(f"  Negativas: {', '.join(cp.negativas)}")
    sem = celulas_sem_campanha(c)
    if sem:
        linhas += ["", f"Células da grade sem campanha: {', '.join(sem)}"]
    return "\n".join(linhas) + "\n"
