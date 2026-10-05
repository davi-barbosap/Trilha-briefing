"""Apresentação do plano para o cliente: uma página HTML, sem dependências, pronta para imprimir em PDF.

Mostra o que foi entendido, o que se propõe e como será medido. Fica de fora o que é só do
assessor: fonte de cada afirmação, avisos da revisão e anotações internas.
"""

from __future__ import annotations

from html import escape
from pathlib import Path

from trilha_briefing.economia import calcular, conversoes_na_validacao
from trilha_briefing.esquema import ClienteCompleto

NIVEL = {
    "inconsciente": "ainda não percebe o problema",
    "consciente_do_problema": "sente o problema, não conhece soluções",
    "consciente_da_solucao": "conhece soluções, não conhece a nossa",
    "consciente_do_produto": "conhece a oferta, ainda não decidiu",
    "pronto_para_comprar": "pronto para comprar",
}
DIMENSAO = {"ter": "O que tem", "sentir": "Como se sente", "dia_a_dia": "O dia a dia", "status": "Como é visto"}
MEDICAO = {
    "utm_padrao": "Padrão de UTMs em todos os links",
    "campos_crm": "Origem do lead gravada no CRM",
    "evento_conversao": "Conversão confirmada antes de contar",
    "etapas_e_motivos_perda": "Etapas do funil e motivos de perda no CRM",
    "codigo_criativo": "Código do criativo chegando no lead",
    "relatorio_definido": "Relatório combinado (quem, quando, o quê)",
}
STATUS_CANAL = {"ativo": "começa agora", "teste": "em teste", "futuro": "próxima fase", "descartado": "fora por agora"}


def _brl(v: float) -> str:
    return "R$ " + f"{v:,.0f}".replace(",", ".")


def _lista(itens: list[str], classe: str = "") -> str:
    if not itens:
        return ""
    return f"<ul class=\"{classe}\">" + "".join(f"<li>{escape(i)}</li>" for i in itens) + "</ul>"


MARCA_HIPOTESE = ' <span class="hip">a confirmar</span>'


def _itens(itens) -> str:
    """Afirmações para o cliente: refutadas saem; hipóteses aparecem marcadas como 'a confirmar'."""
    vivos = [i for i in itens if i.status != "refutada"]
    if not vivos:
        return ""
    linhas = [f"<li>{escape(i.texto)}{'' if i.status == 'validada' else MARCA_HIPOTESE}</li>" for i in vivos]
    return "<ul>" + "".join(linhas) + "</ul>"


def _secao(titulo: str, corpo: str, numero: int) -> str:
    if not corpo.strip():
        return ""
    return f"<section><p class=\"num\">{numero:02d}</p><h2>{escape(titulo)}</h2>{corpo}</section>"


def gerar_html(c: ClienteCompleto) -> str:
    b, p, pl, est = c.briefing, c.pesquisa, c.plataforma, c.estrategia
    cores = pl.identidade_visual.cores
    primaria = cores.get("primaria", "#1F3A5F")
    secundaria = cores.get("secundaria", "#F2A541")
    secoes: list[tuple[str, str]] = []

    # 1. Onde queremos chegar
    corpo = f"<p class=\"destaque\">{escape(b.resultado_desejado.em_12_meses)}</p>"
    if b.resultado_desejado.sucesso_significa:
        corpo += f"<p><strong>Como vamos saber que deu certo:</strong> {escape(b.resultado_desejado.sucesso_significa)}</p>"
    if pl.jornada.conhecido_por:
        corpo += f"<p><strong>Ser conhecido por:</strong> {escape(pl.jornada.conhecido_por)}</p>"
    secoes.append(("Onde queremos chegar", corpo))

    # 2. Para quem
    cards = ""
    for pe in p.personas:
        cards += "<div class=\"cartao\">"
        cards += f"<h3>{escape(pe.nome)}</h3><p>{escape(pe.quem_e)}</p>"
        if pe.nivel_consciencia:
            cards += f"<p class=\"etiqueta\">{escape(NIVEL[pe.nivel_consciencia])}</p>"
        if pe.dores:
            cards += "<p class=\"rotulo\">O que dói</p>" + _itens(pe.dores[:3])
        if pe.desejos:
            cards += "<p class=\"rotulo\">O que procura</p>" + _itens(pe.desejos[:3])
        if pe.objecoes:
            cards += "<p class=\"rotulo\">O que trava a decisão</p>" + _itens(pe.objecoes[:3])
        cards += "</div>"
    if p.escuta:
        total = sum(e.quantidade for e in p.escuta)
        cards += f"<p class=\"nota\">Baseado em {total} registros de escuta: {escape(', '.join(e.fonte for e in p.escuta))}.</p>"
    secoes.append(("Para quem falamos", f"<div class=\"grade\">{cards}</div>" if p.personas else ""))

    # 3. Mercado
    corpo = ""
    if p.concorrentes:
        linhas = "".join(
            f"<tr><td>{escape(x.nome)}</td><td>{escape(x.promessa)}</td><td>{escape(x.aprender)}</td></tr>" for x in p.concorrentes
        )
        corpo += f"<div class=\"tabela\"><table><thead><tr><th>Concorrente</th><th>O que promete</th><th>O que aprendemos</th></tr></thead><tbody>{linhas}</tbody></table></div>"
    if p.unicidade:
        corpo += f"<p class=\"destaque\">O que só vocês têm: {escape(p.unicidade)}</p>"
    s = p.swot
    if any((s.forcas, s.fraquezas, s.oportunidades, s.ameacas)):
        corpo += "<div class=\"swot\">"
        for nome, itens in (("Forças", s.forcas), ("Fraquezas", s.fraquezas), ("Oportunidades", s.oportunidades), ("Ameaças", s.ameacas)):
            corpo += f"<div><h3>{nome}</h3>{_itens(itens)}</div>"
        corpo += "</div>"
    if p.sazonalidade:
        corpo += "<p class=\"rotulo\">Calendário</p>" + _lista(
            [f"{z.periodo}: {'alta' if z.efeito == 'alta' else 'baixa'}{' — ' + z.motivo if z.motivo else ''}" for z in p.sazonalidade])
    secoes.append(("O mercado", corpo))

    # 4. Marca
    po, corpo = pl.posicionamento, ""
    if po.para_quem or po.diferenca:
        corpo += (f"<p class=\"destaque\">Para {escape(po.para_quem)}, {escape(b.cliente.nome)} é {escape(po.categoria)} "
                  f"que {escape(po.diferenca)}.</p>")
    if po.percepcao_atual and po.percepcao_desejada:
        corpo += (f"<div class=\"de-para\"><div><p class=\"rotulo\">Hoje somos vistos como</p><p>{escape(po.percepcao_atual)}</p></div>"
                  f"<div><p class=\"rotulo\">Queremos ser vistos como</p><p>{escape(po.percepcao_desejada)}</p></div></div>")
    a = pl.associacoes
    if a.queremos or a.nao_queremos:
        corpo += (f"<div class=\"de-para\"><div><p class=\"rotulo\">Queremos que lembrem</p>{_lista(a.queremos)}</div>"
                  f"<div><p class=\"rotulo\">Não queremos que lembrem</p>{_lista(a.nao_queremos)}</div></div>")
    if pl.historia.verdade_central:
        corpo += f"<p><strong>No que acreditamos:</strong> {escape(pl.historia.verdade_central)}</p>"
    if pl.temas:
        corpo += "<p class=\"rotulo\">Sobre o que vamos falar</p>" + _lista(
            [f"{t.nome} ({t.peso}%){' — ' + ', '.join(t.formatos) if t.formatos else ''}" for t in pl.temas])
    secoes.append(("A marca", corpo))

    # 5. Ofertas
    corpo = ""
    ordem = ("principal", "entrada", "isca", "premium", "recorrente")
    for o in sorted(c.ofertas, key=lambda o: ordem.index(o.degrau)):
        corpo += f"<div class=\"oferta\"><p class=\"etiqueta\">{escape(o.degrau)}</p><h3>{escape(o.nome)}</h3>"
        if o.promessa:
            corpo += f"<p class=\"destaque\">{escape(o.promessa.texto)}</p>"
        if o.antes_depois:
            linhas = "".join(f"<tr><td>{DIMENSAO[x.dimensao]}</td><td>{escape(x.antes)}</td><td>{escape(x.depois)}</td></tr>" for x in o.antes_depois)
            corpo += f"<div class=\"tabela\"><table><thead><tr><th></th><th>Antes</th><th>Depois</th></tr></thead><tbody>{linhas}</tbody></table></div>"
        if o.como_funciona:
            corpo += "<ol class=\"passos\">" + "".join(f"<li><strong>{escape(x.titulo)}</strong> {escape(x.texto)}</li>" for x in o.como_funciona) + "</ol>"
        if o.inversao_risco:
            corpo += f"<p><strong>Risco que o cliente não corre:</strong> {escape(o.inversao_risco)}</p>"
        corpo += "</div>"
    secoes.append(("O que vamos vender", corpo))

    # 6. Plano
    corpo = ""
    if est.objetivo:
        ob = est.objetivo
        corpo += f"<p class=\"destaque\">{escape(ob.descricao)}</p><p>Meta: <strong>{ob.meta:g} {escape(ob.metrica)}</strong> até {escape(ob.prazo)}"
        corpo += f" (hoje: {ob.baseline:g})</p>" if ob.baseline is not None else "</p>"
    if est.krs:
        corpo += "<p class=\"rotulo\">Resultados-chave</p>" + _lista(
            [f"{k.descricao}: {k.meta:g} {k.metrica}" + (f" (hoje {k.baseline:g})" if k.baseline is not None else "") for k in est.krs])
    if est.economia:
        n = calcular(est.economia)
        custo = n.custo_da_metrica(est.metrica_principal)
        corpo += "<div class=\"numeros\">"
        corpo += f"<div><strong>{_brl(n.cac_max)}</strong><span>custo máximo por venda</span></div>"
        if custo:
            corpo += f"<div><strong>{_brl(custo)}</strong><span>custo máximo por {escape(est.metrica_principal.replace('_', ' '))}</span></div>"
        if est.orcamento.verba_validacao:
            corpo += f"<div><strong>{_brl(est.orcamento.verba_validacao)}</strong><span>verba de validação em {est.orcamento.semanas_validacao or '?'} semanas</span></div>"
        if est.orcamento.verba_mensal:
            corpo += f"<div><strong>{_brl(est.orcamento.verba_mensal)}</strong><span>verba mensal depois de validar</span></div>"
        corpo += "</div>"
        if est.economia.estimados:
            corpo += ("<p class=\"nota\">Parte das taxas é estimativa e será trocada pelos números reais do CRM "
                      "nas primeiras semanas; os tetos de custo serão recalculados.</p>")
        conv = conversoes_na_validacao(est)
        if conv is not None:
            corpo += (f"<p class=\"nota\">A verba de validação é o máximo que se aceita investir até saber se funciona. "
                      f"Se o custo ficar no teto, ela compra cerca de {conv:.0f} conversões em "
                      f"{escape(est.metrica_principal.replace('_', ' '))}; se ficar acima, menos.</p>")
    ativos = [cp for cp in est.canais if cp.status != "descartado"]
    if ativos:
        linhas = "".join(
            f"<tr><td>{escape(cp.canal.replace('_', ' '))}</td><td>{escape(cp.plataforma)}</td><td>{STATUS_CANAL[cp.status]}</td>"
            f"<td>{'' if cp.verba_pct is None else f'{cp.verba_pct:g}%'}</td><td>{escape(cp.justificativa)}</td></tr>" for cp in ativos)
        corpo += f"<div class=\"tabela\"><table><thead><tr><th>Canal</th><th>Onde</th><th>Quando</th><th>Verba</th><th>Por quê</th></tr></thead><tbody>{linhas}</tbody></table></div>"
    if est.marcos:
        corpo += "<p class=\"rotulo\">Marcos</p><ol class=\"passos\">" + "".join(
            f"<li><strong>{escape(m.quando)}</strong> — {escape(m.nome)}{': ' + escape(m.entrega) if m.entrega else ''}</li>" for m in est.marcos) + "</ol>"
    secoes.append(("O plano", corpo))

    # 7. Riscos e premissas
    corpo = ""
    if est.premissas:
        corpo += "<p class=\"rotulo\">Contamos com</p>" + _lista(est.premissas)
    riscos = sorted((r for r in est.riscos if not r.interno), key=lambda r: -r.nota)[:5]
    if riscos:
        corpo += "<p class=\"rotulo\">Riscos e o que faremos</p>" + _lista([f"{r.descricao} → {r.resposta}" for r in riscos])
    secoes.append(("Premissas e riscos", corpo))

    # 8. Medição e testes
    corpo = "<ul class=\"checklist\">" + "".join(
        f"<li class=\"{'ok' if getattr(est.medicao, k) else 'pendente'}\">{escape(v)}</li>" for k, v in MEDICAO.items()) + "</ul>"
    hip = [h for h in c.hipoteses.hipoteses if h.resultado in ("planejada", "rodando")]
    if hip:
        corpo += "<p class=\"rotulo\">O que vamos testar primeiro</p>" + _lista([f"{h.hipotese} — sucesso: {h.criterio_sucesso}" for h in hip])
    secoes.append(("Como vamos medir", corpo))

    legenda = ("<p class=\"nota legenda\">Itens marcados <span class=\"hip\">a confirmar</span> são hipóteses: "
               "entram no plano e são confirmados com a escuta e os dados.</p>")
    html_secoes = legenda + "".join(_secao(t, corpo, i) for i, (t, corpo) in enumerate([s for s in secoes if s[1].strip()], start=1))
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Plano de marketing — {escape(b.cliente.nome)}</title>
<style>
:root{{--p:{escape(primaria)};--s:{escape(secundaria)};--t:#1A1A1A;--f:#FFFFFF;--l:#E6E6E6}}
*{{box-sizing:border-box}}body{{margin:0;font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--t);background:var(--f)}}
header{{background:var(--p);color:#fff;padding:56px 20px}}header div,main{{max-width:960px;margin:0 auto}}
header h1{{margin:0;font-size:clamp(1.8rem,5vw,2.8rem);line-height:1.1}}header p{{margin:.5em 0 0;opacity:.85}}
main{{padding:0 20px 64px}}section{{padding:40px 0;border-bottom:1px solid var(--l);break-inside:avoid-page}}
.num{{color:var(--s);font-weight:800;margin:0;letter-spacing:.08em}}h2{{margin:.1em 0 .6em;font-size:1.6rem;color:var(--p)}}
h3{{margin:0 0 .4em;font-size:1.1rem}}.destaque{{font-size:1.2rem;font-weight:600;border-left:4px solid var(--s);padding-left:14px}}
.rotulo{{font-size:.8rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;opacity:.7;margin:1.2em 0 .3em}}
.etiqueta{{display:inline-block;font-size:.8rem;font-weight:600;padding:2px 10px;border-radius:999px;background:color-mix(in srgb,var(--s) 25%,var(--f))}}
.nota{{font-size:.9rem;opacity:.75}}.hip{{font-size:.75rem;font-weight:600;padding:1px 8px;border-radius:999px;border:1px dashed currentColor;opacity:.7;white-space:nowrap}}ul,ol{{margin:.3em 0 1em;padding-left:1.2em}}
.grade{{display:grid;gap:16px}}.cartao,.oferta{{border:1px solid var(--l);border-radius:14px;padding:20px}}.oferta+.oferta{{margin-top:16px}}
.swot,.de-para{{display:grid;gap:16px;margin:1em 0}}.swot>div,.de-para>div{{background:color-mix(in srgb,var(--p) 5%,var(--f));border-radius:12px;padding:14px 16px}}
.tabela{{overflow-x:auto}}table{{width:100%;min-width:480px;border-collapse:collapse;margin:1em 0;font-size:.95rem}}th,td{{text-align:left;padding:8px;border-bottom:1px solid var(--l);vertical-align:top}}
th{{font-size:.8rem;text-transform:uppercase;letter-spacing:.04em;opacity:.7}}
.numeros{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:1.2em 0}}
.numeros div{{background:color-mix(in srgb,var(--p) 6%,var(--f));border-radius:12px;padding:14px}}.numeros strong{{display:block;font-size:1.4rem;color:var(--p)}}
.numeros span{{font-size:.85rem;opacity:.8}}.checklist{{list-style:none;padding:0}}.checklist li::before{{content:"○ ";font-weight:700}}
.checklist li.ok::before{{content:"✓ ";color:var(--p)}}.checklist li.pendente{{opacity:.7}}
@media(min-width:760px){{.grade{{grid-template-columns:repeat(2,1fr)}}.swot,.de-para{{grid-template-columns:1fr 1fr}}}}
@media print{{header{{-webkit-print-color-adjust:exact;print-color-adjust:exact}}section{{padding:24px 0}}}}
</style></head>
<body><header><div><p>Plano de marketing</p><h1>{escape(b.cliente.nome)}</h1><p>{escape(b.cliente.segmento)}{' · ' + escape(b.area.descricao()) if b.area else ''}</p></div></header>
<main>{html_secoes}</main></body></html>
"""


def apresentar(c: ClienteCompleto, saida: str | Path) -> Path:
    caminho = Path(saida) / c.briefing.cliente.id / "plano.html"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(gerar_html(c), encoding="utf-8")
    return caminho
