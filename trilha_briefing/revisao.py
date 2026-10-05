"""Revisão crítica: o que está preenchido, mas pode dar errado.

Cada aviso tem uma gravidade:
    bloqueia   o plano não deve ir ao cliente assim (promessa proibida, dado contraditório, risco jurídico)
    atencao    funciona, mas vai custar caro ou dar resultado que não se sustenta
    sugestao   melhora a qualidade, sem urgência

Quem decide é o assessor. Nada aqui reescreve o conteúdo.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Literal

from trilha_briefing import campanhas as cp_
from trilha_briefing.economia import calcular, conversoes_no_teto
from trilha_briefing.esquema import ClienteCompleto, Item

Nivel = Literal["bloqueia", "atencao", "sugestao"]
NIVEIS: tuple[Nivel, ...] = ("bloqueia", "atencao", "sugestao")
PALAVRAS_VAGAS = re.compile(r"\b(melhor(es)?|qualidade|excelencia|excelente|incrivel|lider|unico no mercado)\b")
TOLERANCIA_TICKET = 0.10


@dataclass(frozen=True)
class Aviso:
    nivel: Nivel
    texto: str

    def __str__(self) -> str:
        return self.texto


def _brl(v: float) -> str:
    return "R$ " + f"{v:,.0f}".replace(",", ".")


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


def _origem(c: ClienteCompleto, avisos: list[Aviso]) -> None:
    itens = _itens(c)
    sem_fonte = [onde for onde, it in itens if it.fonte == "nao_informada"]
    if sem_fonte:
        avisos.append(Aviso("sugestao", f"{len(sem_fonte)} afirmação(ões) sem fonte (ex.: {sem_fonte[0]}): diga se veio da "
                                        "empresa, do consumidor, do mercado, dos dados ou de você"))
    for onde, it in itens:
        if it.status == "validada" and not it.evidencia:
            avisos.append(Aviso("atencao", f"{onde}: marcada como validada sem evidência"))


def _consistencia(c: ClienteCompleto, avisos: list[Aviso]) -> None:
    """O mesmo dado em dois arquivos precisa bater."""
    b, est = c.briefing, c.estrategia
    e = est.economia
    if e and e.modelo_receita != b.negocio.modelo_receita:
        avisos.append(Aviso("bloqueia", f"modelo de receita diferente: briefing diz {b.negocio.modelo_receita}, "
                                        f"economia diz {e.modelo_receita}"))
    principal = c.oferta_principal()
    if e and principal and principal.condicoes.ticket_medio:
        base = {"venda_direta": e.ticket_medio, "recorrencia": e.mensalidade, "comissao": e.valor_medio_bem}[e.modelo_receita]
        ticket = principal.condicoes.ticket_medio
        if base and abs(ticket - base) / base > TOLERANCIA_TICKET:
            avisos.append(Aviso("atencao", f"ticket da oferta principal ({_brl(ticket)}) diferente do usado na economia "
                                           f"({_brl(base)}): os tetos de custo partem de um valor que não é o vendido"))
    maximo, teto = b.restricoes.verba_mensal_max, est.orcamento.teto_mensal
    if maximo and teto and maximo != teto:
        avisos.append(Aviso("atencao", f"teto de verba diferente: briefing diz {_brl(maximo)}, estratégia diz {_brl(teto)}"))


def _copy(c: ClienteCompleto, avisos: list[Aviso]) -> None:
    pl = c.plataforma
    proibidos = [(t, "termo proibido") for t in pl.voz.termos_proibidos]
    ja = {_norm(t) for t in pl.voz.termos_proibidos}
    proibidos += [(t, "promessa proibida") for t in pl.compliance.promessas_proibidas if _norm(t) not in ja]
    for o in c.ofertas:
        textos = [("promessa", o.promessa.texto if o.promessa else ""), ("cta", o.cta), ("subtitulo", o.subtitulo)]
        textos += [(f"diferenciais[{i}]", d.texto) for i, d in enumerate(o.diferenciais)]
        textos += [(f"beneficios[{i}]", f"{x.titulo} {x.texto}") for i, x in enumerate(o.beneficios)]
        for onde, texto in textos:
            for termo, motivo in proibidos:
                if termo and _norm(termo) in _norm(texto):
                    avisos.append(Aviso("bloqueia", f"ofertas.{o.id}.{onde}: {motivo} — \"{termo}\""))
        if o.promessa:
            p = o.promessa
            if not p.prazo:
                avisos.append(Aviso("atencao", f"ofertas.{o.id}.promessa sem prazo: promessa que não dá para cobrar não diferencia"))
            if not re.search(r"\d", p.resultado or p.texto):
                avisos.append(Aviso("atencao", f"ofertas.{o.id}.promessa sem número no resultado: troque adjetivo por fato observável"))
            if not p.condicao:
                avisos.append(Aviso("atencao", f"ofertas.{o.id}.promessa sem condição: diga para quem e em que situação ela vale"))
        for i, d in enumerate(o.diferenciais):
            if PALAVRAS_VAGAS.search(_norm(d.texto)) and not re.search(r"\d", d.texto):
                avisos.append(Aviso("sugestao", f"ofertas.{o.id}.diferenciais[{i}]: adjetivo sem fato (\"{d.texto}\")"))
        if o.escassez and not (o.escassez.real and o.escassez.evidencia):
            avisos.append(Aviso("bloqueia", f"ofertas.{o.id}.escassez sem evidência: escassez falsa é publicidade enganosa (CDC)"))
        if o.urgencia:
            u = o.urgencia
            if not (u.real and (u.evidencia or u.motivo)):
                avisos.append(Aviso("bloqueia", f"ofertas.{o.id}.urgencia sem motivo ou evidência: prazo inventado é publicidade enganosa (CDC)"))
            if u.data and u.data < date.today():
                avisos.append(Aviso("atencao", f"ofertas.{o.id}.urgencia vencida em {u.data:%d/%m/%Y}: atualize antes de usar em peças"))
        sem_escada = [d.texto for d in o.diferenciais if not d.e_dai]
        if sem_escada and o.degrau == "principal":
            avisos.append(Aviso("sugestao", f"ofertas.{o.id}: {len(sem_escada)} diferencial(is) sem a escada do \"e daí?\" "
                                            f"(ex.: \"{sem_escada[0]}\"): a copy precisa do resultado, não da característica"))
        sem_resposta = [ob.objecao for ob in o.objecoes if not ob.resposta]
        if sem_resposta:
            avisos.append(Aviso("atencao", f"ofertas.{o.id}: objeção sem resposta — {sem_resposta[0]}"))


def _provas(c: ClienteCompleto, avisos: list[Aviso]) -> None:
    sem_persona = [p for p in c.provas.utilizaveis() if p.tipo in ("depoimento", "case") and not p.personas]
    if sem_persona:
        avisos.append(Aviso("sugestao", f"{len(sem_persona)} depoimento(s) sem persona: a copy não sabe para quem eles convencem "
                                        "(prova parecida com quem lê convence mais)"))
    for i, p in enumerate(c.provas.provas):
        if p.tipo in ("numero", "autoridade", "midia", "certificacao") and not p.fonte:
            avisos.append(Aviso("atencao", f"provas[{i}]: {p.tipo} sem fonte (\"{(p.numero + ' ' + p.texto).strip()}\")"))
        if p.tipo in ("depoimento", "case") and not p.autorizado:
            avisos.append(Aviso("atencao", f"provas[{i}]: {p.tipo} sem autorização de uso de {p.autor or 'quem aparece'}: "
                                           "fica fora de anúncios e páginas"))


def _crencas(c: ClienteCompleto, avisos: list[Aviso]) -> None:
    sem_quebra = [f"{p.id}: {cr.texto}" for p in c.pesquisa.personas for cr in p.crencas if not cr.quebra]
    if sem_quebra:
        avisos.append(Aviso("sugestao", f"{len(sem_quebra)} crença(s) sem a forma de derrubar (ex.: {sem_quebra[0]})"))


def _marca(c: ClienteCompleto, avisos: list[Aviso]) -> None:
    temas = c.plataforma.temas
    if temas and sum(t.peso for t in temas) != 100:
        avisos.append(Aviso("sugestao", f"plataforma.temas: pesos somam {sum(t.peso for t in temas)}%, não 100%"))
    if len(temas) > 5:
        avisos.append(Aviso("sugestao", f"plataforma.temas: {len(temas)} temas; poucos temas repetidos constroem associação, muitos diluem"))


def _economia(c: ClienteCompleto, avisos: list[Aviso]) -> None:
    est = c.estrategia
    if not est.economia:
        return
    n = calcular(est.economia)
    if n.ltv_cac_no_teto < 3:
        avisos.append(Aviso("atencao", f"economia.pct_investivel = {est.economia.pct_investivel:.0%}: no teto de custo, a margem "
                                       f"da venda fica {n.ltv_cac_no_teto:.1f}× o CAC (abaixo de 3×). Serve para validar; para escalar, reveja"))
    if est.economia.estimados:
        avisos.append(Aviso("sugestao", f"economia com taxas estimadas ({', '.join(est.economia.estimados)}): "
                                        "trocar por dado do CRM assim que houver"))
    verba = est.orcamento.verba_mensal
    if not verba:
        return
    if verba < n.verba_minima_viavel:
        avisos.append(Aviso("atencao", f"verba mensal {_brl(verba)} abaixo da mínima viável ({_brl(n.verba_minima_viavel)}, "
                                       "50 leads/semana no CPL máximo): concentre em uma plataforma e uma oferta"))
    capacidade = c.briefing.capacidade.leads_dia
    leads_dia = verba / n.custo_max["lead"] / (365.25 / 12)
    if capacidade and leads_dia > capacidade:
        avisos.append(Aviso("atencao", f"no CPL máximo a verba já traz {leads_dia:.0f} leads por dia (com custo menor, mais), "
                                       f"e o time atende bem {capacidade}: lead sem resposta é verba perdida"))
    teto = est.orcamento.teto_mensal or c.briefing.restricoes.verba_mensal_max
    if teto and verba > teto:
        avisos.append(Aviso("bloqueia", f"verba mensal {_brl(verba)} acima do teto combinado ({_brl(teto)})"))
    evento = est.evento_otimizacao or est.metrica_principal
    precisa = n.verba_para_otimizar.get(evento)
    viaveis = n.degraus_viaveis(verba)
    if precisa and precisa > verba and viaveis:
        avisos.append(Aviso("bloqueia", f"otimizar por {evento} pede {_brl(precisa)}/mês (50 por semana no custo máximo); com "
                                        f"{_brl(verba)}, otimize por {viaveis[-1]} e acompanhe {evento} no CRM"))


def _volume(c: ClienteCompleto, avisos: list[Aviso]) -> None:
    """Cada teste do núcleo precisa de mínimo × variações eventos dentro da verba de validação."""
    est = c.estrategia
    testes = [h for h in c.hipoteses.hipoteses if h.horizonte == "nucleo" and h.resultado in ("planejada", "rodando")]
    for h in testes or [None]:
        evento = (h.evento if h else None) or est.metrica_principal
        conv = conversoes_no_teto(est, evento)
        precisa = h.minimo_conversoes * h.variacoes if h else 30
        if conv is None or conv >= precisa:
            continue
        quem = f"hipótese {h.id} precisa de {precisa} {evento} ({h.minimo_conversoes} × {h.variacoes} variações)" if h \
            else f"a validação precisa de ao menos {precisa} {evento}"
        avisos.append(Aviso("atencao", f"{quem}, mas a verba de validação compra {conv:.0f} se o custo ficar no teto "
                                       "(e menos, se ficar acima): aumente a verba, alongue o prazo, reduza as variações "
                                       "ou meça numa etapa mais acima do funil"))
    for h in c.hipoteses.hipoteses:
        if h.resultado in ("validada", "refutada") and (h.conversoes_obtidas or 0) < h.minimo_conversoes * h.variacoes:
            avisos.append(Aviso("atencao", f"hipótese {h.id} concluída com {h.conversoes_obtidas or 0} conversões "
                                           f"(mínimo {h.minimo_conversoes * h.variacoes}): trate como inconclusiva"))
    variaveis = [h.variavel for h in c.hipoteses.hipoteses if h.resultado == "rodando"]
    if len(variaveis) != len(set(variaveis)):
        avisos.append(Aviso("atencao", "duas hipóteses rodando sobre a mesma variável: o resultado de uma contamina a outra"))


def _canais(c: ClienteCompleto, avisos: list[Aviso]) -> None:
    est = c.estrategia
    for cp in est.canais:
        if cp.canal == "busca_concorrente" and cp.status in ("ativo", "teste") and not cp.aprovado_cliente:
            avisos.append(Aviso("bloqueia", "canal busca_concorrente sem aprovação do cliente: há decisões no Brasil tratando o uso "
                                            "da marca do concorrente como palavra-chave como concorrência desleal"))
    pagos = [cp for cp in est.canais if cp.status in ("ativo", "teste") and cp.verba_pct is not None]
    if pagos and abs(sum(cp.verba_pct for cp in pagos) - 100) > 0.5:
        avisos.append(Aviso("atencao", f"estrategia.canais: verba_pct dos canais ativos/teste soma {sum(cp.verba_pct for cp in pagos):.0f}%, não 100%"))
    ciclo = c.briefing.negocio.ciclo_venda_dias
    if est.abordagem == "inbound" and ciclo is not None and ciclo <= 7:
        avisos.append(Aviso("sugestao", "abordagem só inbound com ciclo de venda curto: a demanda que já existe fica para o concorrente"))
    for r in est.riscos:
        if r.nota >= 12 and not r.resposta:
            avisos.append(Aviso("atencao", f"risco alto sem resposta: {r.descricao} (nota {r.nota})"))


def _campanhas(c: ClienteCompleto, avisos: list[Aviso]) -> None:
    """O plano de campanhas contra as regras (padrão do repositório + as do cliente) e contra a estratégia."""
    if not c.campanhas.campanhas:
        return
    regras = cp_.regras_do_plano(c.campanhas)

    def aviso(nivel: str, texto: str) -> None:
        if nivel != "desligada":
            avisos.append(Aviso(nivel, texto))  # type: ignore[arg-type]

    est = c.estrategia
    # verba: o plano e a estratégia precisam bater
    verbas = [cp_.verba_da(c, cp) for cp in c.campanhas.campanhas]
    soma = sum(v for v in verbas if v)
    teto = est.orcamento.teto_mensal or c.briefing.restricoes.verba_mensal_max
    if teto and soma > teto:
        aviso("bloqueia", f"campanhas.yaml: as campanhas somam {_brl(soma)}/mês, acima do teto combinado ({_brl(teto)})")
    elif est.orcamento.verba_mensal and abs(soma - est.orcamento.verba_mensal) > 0.05 * est.orcamento.verba_mensal:
        aviso("atencao", f"campanhas.yaml: as campanhas somam {_brl(soma)}/mês e a estratégia diz {_brl(est.orcamento.verba_mensal)}")
    # 4. nomes com o código da célula
    if "{codigo}" not in regras.nomes.anuncio:
        aviso(regras.nomes.nivel, "regras.nomes.anuncio sem {codigo}: o raio-x não consegue ligar o anúncio à célula da grade")
    if "{codigo}" not in regras.nomes.utm:
        aviso(regras.nomes.nivel, "regras.nomes.utm sem {codigo}: o lead chega ao Kommo sem o código do criativo")
    pendentes = est.medicao.pendentes()
    for cp in c.campanhas.campanhas:
        conta = cp_.contas(c, cp, regras)
        if not cp.conjuntos:
            aviso("atencao", f"{cp.id}: campanha sem conjunto")
        if cp.canal.startswith("busca_"):
            sem = [cj.id for cj in cp.conjuntos if not cj.palavras_chave]
            if sem:
                aviso("atencao", f"{cp.id}: campanha de busca com grupo sem palavra-chave ({', '.join(sem)})")
        # 2. poucos conjuntos, conforme a verba aguenta
        if conta.conjuntos_que_cabem is not None and cp.conjuntos:
            ritmo = (f"cerca de {conta.eventos_semana:.0f} {cp_.legivel(conta.evento, plural=True)} por semana no teto de custo "
                     f"({cp_.brl(conta.custo)}); o {cp_.legivel(cp.plataforma)} pede {conta.limite} por conjunto para sair "
                     "do aprendizado")
            if conta.conjuntos_que_cabem == 0:
                aviso(regras.aprendizado.nivel, f"{cp.id}: {ritmo}, e nem um conjunto chega lá"
                      + (": junte tudo em um conjunto só" if len(cp.conjuntos) > 1 else "")
                      + ". Ele vai ficar em aprendizado limitado: suba a verba ou otimize por um evento mais acima do funil")
            elif len(cp.conjuntos) > conta.conjuntos_que_cabem:
                aviso(regras.aprendizado.nivel, f"{cp.id}: {len(cp.conjuntos)} conjuntos, mas a verba aguenta "
                      f"{conta.conjuntos_que_cabem} ({ritmo}): junte as células em menos conjuntos")
        # 3. cada hipótese diz como vai ser testada
        onde = {x: cj.id for cj in cp.conjuntos for x in cj.celulas}
        for t in cp.testes:
            h = cp_.hipotese(c, t.hipotese)
            if h is None:
                continue
            metodo = cp_.metodo_do(t, regras)
            if metodo is None:
                aviso(regras.testes.nivel, f"{cp.id}: teste da {h.id} sem método (ab_plataforma, conjuntos_separados "
                                           "ou comparacao_no_conjunto)")
            fora = [x for x in h.codigos if x not in onde]
            if fora:
                aviso(regras.testes.nivel, f"{cp.id}: a {h.id} testa {', '.join(fora)}, que não estão em nenhum conjunto da campanha")
            elif metodo == "conjuntos_separados" and len({onde[x] for x in h.codigos}) < len(h.codigos):
                aviso(regras.testes.nivel, f"{cp.id}: a {h.id} usa conjuntos separados, mas as variações estão no mesmo conjunto")
            if metodo == "comparacao_no_conjunto" and not regras.testes.comparacao_conclui and regras.testes.nivel != "desligada":
                aviso("sugestao", f"{cp.id}: a {h.id} é comparação dentro do conjunto: a plataforma reparte a verba como "
                                  "quiser, então o resultado é direcional e não conclui a hipótese")
            ev = h.evento or est.metrica_principal
            semana = cp_.por_semana(conta.verba, cp_.custo_teto(c, ev))
            prazo = cp_.prazo_semanas(c, h)
            precisa = h.minimo_conversoes * h.variacoes
            if semana and prazo and precisa / semana > prazo:
                aviso(regras.testes.nivel, f"{cp.id}: a {h.id} precisa de {precisa} {cp_.legivel(ev, plural=True)}; a campanha compra cerca de "
                                           f"{semana:.0f} por semana no teto, ou seja, {precisa / semana:.0f} semanas, mais que "
                                           f"as {prazo:.0f} do prazo")
        # 5. fase só com o que ela exige
        if cp.fase in regras.fases.ordem and pendentes:
            ate = regras.fases.ordem[: regras.fases.ordem.index(cp.fase) + 1]
            if any(regras.fases.entrar.get(f) and regras.fases.entrar[f].medicao_completa for f in ate):
                aviso(regras.fases.nivel, f"{cp.id}: em {cp_.legivel(cp.fase)}, mas a medição não está completa "
                                          f"({', '.join(pendentes)})")
    # cobertura da grade e dos canais
    prioridade = {cel.codigo: cel.prioridade for cel in est.grade}
    sem = cp_.celulas_sem_campanha(c)
    if [x for x in sem if prioridade.get(x) == 1]:
        aviso("atencao", f"células de prioridade 1 sem campanha: {', '.join(x for x in sem if prioridade.get(x) == 1)}")
    if [x for x in sem if prioridade.get(x) != 1]:
        aviso("sugestao", f"células sem campanha: {', '.join(x for x in sem if prioridade.get(x) != 1)}")
    testadas = {t.hipotese for cp in c.campanhas.campanhas for t in cp.testes}
    for h in c.hipoteses.hipoteses:
        if (h.horizonte == "nucleo" and h.resultado in ("planejada", "rodando") and h.codigos and h.id not in testadas
                and regras.testes.nivel != "desligada"):
            aviso("sugestao", f"hipótese {h.id} sem teste em nenhuma campanha do plano")
    for canal in cp_.canais_sem_campanha(c):
        aviso("sugestao", f"canal {canal} ativo ou em teste na estratégia e sem campanha no plano")


REGRAS = [_origem, _consistencia, _copy, _provas, _crencas, _marca, _economia, _volume, _canais, _campanhas]


def revisar(c: ClienteCompleto) -> list[Aviso]:
    avisos: list[Aviso] = []
    for regra in REGRAS:
        regra(c, avisos)
    return sorted(avisos, key=lambda a: NIVEIS.index(a.nivel))


def avisos_do_plano(c: ClienteCompleto) -> list[Aviso]:
    avisos: list[Aviso] = []
    _campanhas(c, avisos)
    return sorted(avisos, key=lambda a: NIVEIS.index(a.nivel))


def bloqueantes(c: ClienteCompleto) -> list[Aviso]:
    return [a for a in revisar(c) if a.nivel == "bloqueia"]
