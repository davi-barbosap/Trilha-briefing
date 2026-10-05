"""Revisão crítica: o que está preenchido, mas pode dar errado.

Devolve avisos; quem decide é o assessor. Nada aqui reescreve o conteúdo.
"""

from __future__ import annotations

import re
import unicodedata

from trilha_briefing.economia import calcular, conversoes_na_validacao
from trilha_briefing.esquema import ClienteCompleto, Item

def _brl(v: float) -> str:
    return "R$ " + f"{v:,.0f}".replace(",", ".")


PALAVRAS_VAGAS = ("melhor", "qualidade", "excelencia", "excelente", "incrivel", "unico no mercado", "lider")


def _norm(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()


def _itens(c: ClienteCompleto) -> list[tuple[str, Item]]:
    """Todos os Items do cliente, com o lugar onde estão."""
    saida = [(f"briefing.historico.funcionou[{i}]", it) for i, it in enumerate(c.briefing.historico.funcionou)]
    saida += [(f"briefing.historico.nao_funcionou[{i}]", it) for i, it in enumerate(c.briefing.historico.nao_funcionou)]
    for p in c.pesquisa.personas:
        for campo in ("dores", "desejos", "objecoes", "ganchos"):
            saida += [(f"pesquisa.personas.{p.id}.{campo}[{i}]", it) for i, it in enumerate(getattr(p, campo))]
    for campo in ("forcas", "fraquezas", "oportunidades", "ameacas"):
        saida += [(f"pesquisa.swot.{campo}[{i}]", it) for i, it in enumerate(getattr(c.pesquisa.swot, campo))]
    saida += [(f"plataforma.posicionamento.razoes_para_acreditar[{i}]", it)
              for i, it in enumerate(c.plataforma.posicionamento.razoes_para_acreditar)]
    for o in c.ofertas:
        saida += [(f"ofertas.{o.id}.diferenciais[{i}]", it) for i, it in enumerate(o.diferenciais)]
    return saida


def revisar(c: ClienteCompleto) -> list[str]:
    avisos: list[str] = []
    pl, est = c.plataforma, c.estrategia

    # Origem das afirmações
    itens = _itens(c)
    sem_fonte = [onde for onde, it in itens if it.fonte == "nao_informada"]
    if sem_fonte:
        avisos.append(f"{len(sem_fonte)} afirmação(ões) sem fonte (ex.: {sem_fonte[0]}): diga se veio da empresa, do consumidor, do mercado, dos dados ou de você")
    for onde, it in itens:
        if it.status == "validada" and not it.evidencia:
            avisos.append(f"{onde}: marcada como validada sem evidência")

    # Promessas e copy
    proibidos = [(t, "termo proibido") for t in pl.voz.termos_proibidos]
    ja = {_norm(t) for t in pl.voz.termos_proibidos}
    proibidos += [(t, "promessa proibida") for t in pl.compliance.promessas_proibidas if _norm(t) not in ja]
    for o in c.ofertas:
        textos = [("promessa", o.promessa.texto if o.promessa else ""), ("cta", o.cta)]
        textos += [(f"diferenciais[{i}]", d.texto) for i, d in enumerate(o.diferenciais)]
        for onde, texto in textos:
            for termo, motivo in proibidos:
                if termo and _norm(termo) in _norm(texto):
                    avisos.append(f"ofertas.{o.id}.{onde}: {motivo} — \"{termo}\"")
        if o.promessa:
            p = o.promessa
            if not p.prazo:
                avisos.append(f"ofertas.{o.id}.promessa sem prazo: promessa que não dá para cobrar não diferencia")
            if not re.search(r"\d", p.resultado or p.texto):
                avisos.append(f"ofertas.{o.id}.promessa sem número no resultado: troque adjetivo por fato observável")
            if not p.condicao:
                avisos.append(f"ofertas.{o.id}.promessa sem condição: diga para quem e em que situação ela vale")
        for i, d in enumerate(o.diferenciais):
            if any(v in _norm(d.texto) for v in PALAVRAS_VAGAS) and not re.search(r"\d", d.texto):
                avisos.append(f"ofertas.{o.id}.diferenciais[{i}]: adjetivo sem fato (\"{d.texto}\")")
        if o.escassez and not (o.escassez.real and o.escassez.evidencia):
            avisos.append(f"ofertas.{o.id}.escassez sem evidência: escassez falsa é publicidade enganosa (CDC)")
        sem_resposta = [ob.objecao for ob in o.objecoes if not ob.resposta]
        if sem_resposta:
            avisos.append(f"ofertas.{o.id}: objeção sem resposta — {sem_resposta[0]}")

    # Provas
    for i, p in enumerate(c.provas.provas):
        if p.tipo == "numero" and not p.fonte:
            avisos.append(f"provas[{i}]: número sem fonte (\"{p.numero} {p.texto}\")")
        if p.tipo in ("depoimento", "case") and not p.autorizado:
            avisos.append(f"provas[{i}]: {p.tipo} sem autorização de uso de {p.autor or 'quem aparece'}")

    # Marca
    if pl.temas and sum(t.peso for t in pl.temas) != 100:
        avisos.append(f"plataforma.temas: pesos somam {sum(t.peso for t in pl.temas)}%, não 100%")
    if len(pl.temas) > 5:
        avisos.append(f"plataforma.temas: {len(pl.temas)} temas; poucos temas repetidos constroem associação, muitos diluem")

    # Economia e verba
    if est.economia:
        n = calcular(est.economia)
        if n.ltv_cac_no_teto < 3:
            avisos.append(
                f"economia.pct_investivel = {est.economia.pct_investivel:.0%}: no teto de custo, a margem da venda "
                f"fica {n.ltv_cac_no_teto:.1f}× o CAC (abaixo de 3×). Funciona para validar; para escalar, reveja"
            )
        if est.economia.estimados:
            avisos.append(f"economia com taxas estimadas ({', '.join(est.economia.estimados)}): trocar por dado do CRM assim que houver")
        verba = est.orcamento.verba_mensal
        if verba and verba < n.verba_minima_viavel:
            avisos.append(
                f"verba mensal {_brl(verba)} abaixo da mínima viável ({_brl(n.verba_minima_viavel)}, "
                "50 leads/semana no CPL máximo): concentre em uma plataforma e uma oferta"
            )
        teto = est.orcamento.teto_mensal or c.briefing.restricoes.verba_mensal_max
        if verba and teto and verba > teto:
            avisos.append(f"verba mensal acima do teto combinado ({_brl(teto)})")
    conv = conversoes_na_validacao(est)
    # O volume que a validação precisa é o dos testes do núcleo (os que decidem se a estratégia segue).
    minimo = max((h.minimo_conversoes for h in c.hipoteses.hipoteses if h.horizonte == "nucleo"), default=30)
    if conv is not None and conv < minimo:
        avisos.append(
            f"a verba de validação compra no máximo {conv:.0f} conversões de {est.metrica_principal} (no custo máximo): "
            f"abaixo de {minimo}, o teste tende a terminar inconclusivo. Aumente a verba, alongue o prazo "
            "ou valide por uma métrica mais acima no funil"
        )

    # Canais
    for cp in est.canais:
        if cp.canal == "busca_concorrente" and cp.status in ("ativo", "teste") and not cp.aprovado_cliente:
            avisos.append(
                "canal busca_concorrente sem aprovação do cliente: há decisões no Brasil tratando o uso da marca "
                "do concorrente como palavra-chave como concorrência desleal"
            )
    pagos = [cp for cp in est.canais if cp.status in ("ativo", "teste") and cp.verba_pct is not None]
    if pagos and abs(sum(cp.verba_pct for cp in pagos) - 100) > 0.5:
        avisos.append(f"estrategia.canais: verba_pct dos canais ativos/teste soma {sum(cp.verba_pct for cp in pagos):.0f}%, não 100%")
    if est.abordagem == "inbound" and c.briefing.negocio.ciclo_venda_dias is not None and c.briefing.negocio.ciclo_venda_dias <= 7:
        avisos.append("abordagem só inbound com ciclo de venda curto: a demanda que já existe fica para o concorrente")

    # Riscos
    for r in est.riscos:
        if r.nota >= 12 and not r.resposta:
            avisos.append(f"risco alto sem resposta: {r.descricao} (nota {r.nota})")

    # Hipóteses
    for h in c.hipoteses.hipoteses:
        if h.resultado in ("validada", "refutada") and (h.conversoes_obtidas or 0) < h.minimo_conversoes:
            avisos.append(
                f"hipótese {h.id} concluída com {h.conversoes_obtidas or 0} conversões (mínimo {h.minimo_conversoes}): "
                "trate como inconclusiva"
            )
    rodando = [h for h in c.hipoteses.hipoteses if h.resultado == "rodando"]
    variaveis = [h.variavel for h in rodando]
    if len(variaveis) != len(set(variaveis)):
        avisos.append("duas hipóteses rodando sobre a mesma variável: o resultado de uma contamina a outra")
    return avisos
