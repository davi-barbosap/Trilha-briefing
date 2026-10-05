"""O que falta em cada etapa, e o que impede a estratégia de ser aprovada.

Lacuna é informação que ainda não existe. Não é julgamento de qualidade: isso fica na revisão.
"""

from __future__ import annotations

from trilha_briefing.esquema import FONTES_DE_ESCUTA, ClienteCompleto, Persona
from trilha_briefing.revisao import bloqueantes

ETAPAS = ("briefing", "pesquisa", "plataforma", "provas", "ofertas", "estrategia")


def escutada(p: Persona) -> bool:
    """A persona tem ao menos uma objeção vinda de quem compra (escuta ou dados), não da empresa."""
    return any(o.fonte in FONTES_DE_ESCUTA for o in p.objecoes)


def _briefing(c: ClienteCompleto) -> list[str]:
    b, f = c.briefing, []
    if not b.resultado_desejado.sucesso_significa:
        f.append("como o cliente vai saber que deu certo (resultado_desejado.sucesso_significa)")
    if not b.negocio.como_vende_hoje:
        f.append("como vende hoje (negocio.como_vende_hoje)")
    if not b.negocio.time_comercial:
        f.append("quem atende o lead (negocio.time_comercial)")
    if not (b.historico.funcionou or b.historico.nao_funcionou):
        f.append("histórico: o que já funcionou e o que não funcionou")
    if b.restricoes.verba_mensal_max is None:
        f.append("verba mensal máxima (restricoes.verba_mensal_max)")
    if not b.stakeholders:
        f.append("quem decide do lado do cliente (stakeholders)")
    if "cliente" not in b.preenchido_por:
        f.append("o cliente ainda não respondeu o questionário (preenchido_por)")
    return f


def _pesquisa(c: ClienteCompleto) -> list[str]:
    p, f = c.pesquisa, []
    if "pesquisa.yaml" in c.ausentes:
        return ["arquivo pesquisa.yaml"]
    if not p.personas:
        f.append("ao menos uma persona")
    for pe in p.personas:
        falta = [n for n, v in (("dores", pe.dores), ("desejos", pe.desejos), ("objeções", pe.objecoes),
                                ("ganchos", pe.ganchos)) if not v]
        if pe.nivel_consciencia is None:
            falta.append("nível de consciência")
        if pe.objecoes and not escutada(pe):
            falta.append("objeção vinda da escuta (consumidor ou dados)")
        if falta:
            f.append(f"persona {pe.id}: {', '.join(falta)}")
    if not p.escuta:
        f.append("escuta: de onde vieram dores e objeções (entrevistas, CRM, avaliações)")
    if len(p.concorrentes) < 3:
        f.append(f"benchmark com {len(p.concorrentes)} concorrente(s); o mínimo útil é 3, o ideal 5")
    if not p.unicidade:
        f.append("unicidade: o que só este cliente tem")
    s = p.swot
    if not (s.forcas and s.fraquezas and s.oportunidades and s.ameacas):
        f.append("SWOT incompleta")
    if not p.sazonalidade:
        f.append("sazonalidade do segmento")
    if p.maturidade.pendentes():
        f.append(f"maturidade sem nota: {', '.join(p.maturidade.pendentes())}")
    return f


def _plataforma(c: ClienteCompleto) -> list[str]:
    if "plataforma.yaml" in c.ausentes:
        return ["arquivo plataforma.yaml"]
    pl, f = c.plataforma, []
    if not (pl.jornada.resultado and pl.jornada.conhecido_por):
        f.append("jornada da marca: resultado e conhecido_por")
    if not (pl.associacoes.queremos and pl.associacoes.nao_queremos):
        f.append("associações: o que queremos e o que não queremos que lembrem")
    po = pl.posicionamento
    if not (po.para_quem and po.diferenca):
        f.append("posicionamento: para quem e qual a diferença")
    if not (po.percepcao_atual and po.percepcao_desejada):
        f.append("lacuna de posicionamento: percepção atual e desejada")
    if not pl.historia.verdade_central:
        f.append("história da marca: verdade central")
    if pl.voz.assinatura is None or not pl.voz.tom:
        f.append("voz: assinatura e tom")
    if len(pl.voz.assim_sim) < 3 or len(pl.voz.assim_nao) < 3:
        f.append("voz: 3 exemplos de 'assim sim' e 3 de 'assim não'")
    if not {"primaria", "secundaria"} <= set(pl.identidade_visual.cores):
        f.append("identidade visual: cores primária e secundária")
    if not pl.temas:
        f.append("linha editorial: temas com peso, formato e canal")
    if not pl.compliance.politica_privacidade_url:
        f.append("política de privacidade (compliance.politica_privacidade_url)")
    return f


def _provas(c: ClienteCompleto) -> list[str]:
    if "provas.yaml" in c.ausentes:
        return ["arquivo provas.yaml"]
    f = []
    if not c.provas.utilizaveis("numero"):
        f.append("ao menos um número com fonte")
    if not c.provas.utilizaveis("depoimento"):
        f.append("ao menos um depoimento autorizado")
    if not any(h.autorizado for h in c.provas.historias):
        f.append("ao menos uma história de cliente autorizada (antes → virada → resultado)")
    return f


def _ofertas(c: ClienteCompleto) -> list[str]:
    if not c.ofertas:
        return ["ao menos uma oferta em ofertas/"]
    f = []
    if not any(o.degrau == "principal" for o in c.ofertas):
        f.append("nenhuma oferta marcada como degrau principal")
    for o in c.ofertas:
        falta = []
        if not o.personas:
            falta.append("personas")
        if o.promessa is None:
            falta.append("promessa")
        if not o.big_idea.mecanismo_unico:
            falta.append("mecanismo único")
        if len(o.diferenciais) < 3:
            falta.append("3 diferenciais")
        if len(o.objecoes) < 3:
            falta.append("3 objeções")
        if not 3 <= len(o.como_funciona) <= 5:
            falta.append("como funciona em 3 a 5 passos")
        if not o.antes_depois:
            falta.append("quadro antes/depois")
        if not o.inversao_risco:
            falta.append("inversão de risco")
        if o.aderencia.aderencia_digital == "nao_avaliado":
            falta.append("diagnóstico de aderência ao digital")
        if falta:
            f.append(f"oferta {o.id}: {', '.join(falta)}")
    return f


def _estrategia(c: ClienteCompleto) -> list[str]:
    if "estrategia.yaml" in c.ausentes:
        return ["arquivo estrategia.yaml"]
    e, f = c.estrategia, []
    if e.objetivo is None:
        f.append("objetivo com métrica, meta e prazo")
    if not e.krs:
        f.append("resultados-chave (krs)")
    if e.economia is None:
        f.append("economia unitária (mesmos campos do perfil.yaml do Trilha)")
    o = e.orcamento
    if o.verba_validacao is None or o.semanas_validacao is None:
        f.append("verba e prazo de validação: o máximo que o cliente aceita perder até saber se funciona")
    if o.verba_mensal is None:
        f.append("verba mensal")
    if e.abordagem is None:
        f.append("abordagem: direta, inbound ou direta com inbound")
    if not any(cp.status == "ativo" for cp in e.canais):
        f.append("ao menos um canal ativo")
    if not e.grade:
        f.append("grade públicos × argumentos")
    if not e.riscos:
        f.append("riscos com probabilidade, impacto e resposta")
    if not e.marcos:
        f.append("marcos")
    if e.medicao.pendentes():
        f.append(f"medição não pronta: {', '.join(e.medicao.pendentes())}")
    return f


VERIFICADORES = {
    "briefing": _briefing, "pesquisa": _pesquisa, "plataforma": _plataforma,
    "provas": _provas, "ofertas": _ofertas, "estrategia": _estrategia,
}


def lacunas(c: ClienteCompleto) -> dict[str, list[str]]:
    return {etapa: VERIFICADORES[etapa](c) for etapa in ETAPAS}


def bloqueios_aprovacao(c: ClienteCompleto) -> list[str]:
    """O mínimo para levar a estratégia ao cliente. O resto pode amadurecer com os dados."""
    b = []
    e = c.estrategia
    if e.objetivo is None or not e.krs:
        b.append("objetivo sem meta e prazo ou sem resultados-chave")
    if e.medicao.pendentes():
        b.append(f"medição não pronta ({', '.join(e.medicao.pendentes())}): sem isso não há como saber se funcionou")
    if e.economia is None or e.orcamento.verba_validacao is None:
        b.append("sem economia unitária ou sem verba de validação: não há teto de custo nem limite de perda combinado")
    principal = c.oferta_principal()
    personas = [c.persona(pid) for pid in (principal.personas if principal else [])]
    sem_escuta = [p.id for p in personas if p and not escutada(p)]
    if not c.pesquisa.escuta:
        b.append("nenhum registro de escuta: as personas ainda são opinião da empresa")
    elif sem_escuta or not personas:
        b.append(f"persona(s) da oferta principal sem objeção vinda da escuta: {', '.join(sem_escuta) or 'nenhuma persona ligada'}")
    if principal is None or principal.promessa is None:
        b.append("oferta principal sem promessa")
    if not (c.provas.utilizaveis("numero") or c.provas.utilizaveis("depoimento")):
        b.append("nenhuma prova utilizável (número com fonte ou depoimento autorizado)")
    if not any(cp.status == "ativo" for cp in e.canais):
        b.append("nenhum canal ativo")
    b += [f"revisão: {a.texto}" for a in bloqueantes(c)]
    return b
