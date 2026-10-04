"""Gera os arquivos que as outras ferramentas leem, a partir da mesma fonte.

- Trilha: `marca.yaml`, `ofertas/<id>.yaml` (passam no esquema do Trilha) e `perfil.parcial.yaml`
  (economia, métrica e verba; contas, CRM e conversões o assessor completa no Trilha).
- Trilha-LP: rascunho de `pagina.yaml` por oferta e origem. O texto sai cru: reescrever com a voz da marca.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import yaml

from trilha_briefing.esquema import ClienteCompleto, Oferta

PESSOA_GRAMATICAL = {"pessoa": "eu", "marca_pessoa": "eu", "marca": "nós"}
WHATSAPP_RESERVA = "5500000000000"


def _yaml(dados: dict, cabecalho: list[str]) -> str:
    topo = "".join(f"# {linha}\n" for linha in cabecalho)
    return topo + yaml.safe_dump(dados, sort_keys=False, allow_unicode=True, width=120)


def _sem_vazios(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in ("", None, [], {})}


# ---------- Trilha ----------


def marca_trilha(c: ClienteCompleto) -> dict:
    pl, b = c.plataforma, c.briefing
    cores = pl.identidade_visual.cores
    numeros = [f"{p.numero} {p.texto} (fonte: {p.fonte})".strip() for p in c.provas.utilizaveis("numero")]
    depoimentos = c.provas.utilizaveis("depoimento")
    return {
        "marca": {"nome": b.cliente.nome, "segmento": b.cliente.playbook},
        "identidade_visual": {
            "cores": {"primaria": cores.get("primaria", ""), "secundaria": cores.get("secundaria", ""),
                      "apoio": cores.get("apoio", [])},
            "tipografia": dict(pl.identidade_visual.tipografia),
            "logo": {"arquivo": pl.identidade_visual.logo, "versoes": []},
            "estilo_imagem": pl.identidade_visual.estilo_imagem,
        },
        "voz": {
            "assinatura": pl.voz.assinatura or "",
            "nome_pessoa": pl.voz.nome_pessoa,
            "abordagem": pl.voz.abordagem or "",
            "pessoa_gramatical": PESSOA_GRAMATICAL.get(pl.voz.assinatura or "", ""),
            "tom": pl.voz.tom,
            "assim_sim": pl.voz.assim_sim,
            "assim_nao": pl.voz.assim_nao,
            "termos_obrigatorios": pl.voz.termos_obrigatorios,
            "termos_proibidos": pl.voz.termos_proibidos,
        },
        "atendimento": pl.atendimento.model_dump(),
        "regras_comerciais": {"preco": dict(pl.preco), "promessas_proibidas": pl.compliance.promessas_proibidas},
        "compliance": {
            "registros_profissionais": pl.compliance.registros_profissionais,
            "categoria_especial_anuncio": None,
            "avisos_legais": pl.compliance.avisos_legais,
            "lgpd": {"base_legal": pl.compliance.base_legal_lgpd,
                     "politica_privacidade_url": pl.compliance.politica_privacidade_url},
        },
        "prova_social": {
            "depoimentos_video": [f"{p.autor}: {p.link or p.texto}" for p in depoimentos if p.formato == "video"],
            "depoimentos_texto": [f"\"{p.texto}\" — {p.autor}" for p in depoimentos if p.formato != "video"],
            "numeros": numeros,
        },
    }


def oferta_trilha(c: ClienteCompleto, o: Oferta) -> dict:
    personas = [c.persona(p) for p in o.personas]
    a = o.aderencia
    perfil_lead = _sem_vazios({
        "perfil": "; ".join(f"{p.nome}: {p.quem_e}" for p in personas if p),
        "jornada_media_dias": c.briefing.negocio.ciclo_venda_dias,
    })
    return {
        "oferta": _sem_vazios({"nome": o.nome, "tipo": o.tipo, "estagio": o.estagio, "localizacao": o.localizacao}),
        "aderencia": {
            "perfil_compradores": a.perfil_compradores,
            "reputacao": a.reputacao,
            "reputacao_nota": a.reputacao_nota,
            "vendas_fora_do_digital": a.vendas_fora_do_digital.model_dump(),
            "aderencia_digital": a.aderencia_digital,
            "justificativa": a.justificativa,
        },
        "diferenciais": [d.texto for d in o.diferenciais],
        "raridade": o.raridade,
        "condicoes_comerciais": _sem_vazios(o.condicoes.model_dump()),
        "objecoes": [{"eixo": ob.eixo, "objecao": ob.objecao, "resposta_do_time": ob.resposta} for ob in o.objecoes],
        "perfil_lead": perfil_lead,
    }


def perfil_parcial(c: ClienteCompleto) -> dict:
    b, e = c.briefing, c.estrategia
    o = e.orcamento
    dados = {
        "versao": 1,
        "vigente_desde": e.aprovado_em or date.today(),
        "cliente": {"id": b.cliente.id, "nome": b.cliente.nome, "segmento": b.cliente.playbook},
        "metrica_principal": e.metrica_principal,
    }
    if e.economia:
        dados["economia"] = e.economia.model_dump(exclude_none=True, exclude_defaults=True)
    dados["verba"] = _sem_vazios({"mensal_planejada": o.verba_mensal,
                                  "teto_mensal": o.teto_mensal or b.restricoes.verba_mensal_max, "moeda": o.moeda})
    return dados


def exportar_trilha(c: ClienteCompleto, saida: str | Path) -> list[Path]:
    saida = Path(saida) / c.briefing.cliente.id
    (saida / "ofertas").mkdir(parents=True, exist_ok=True)
    origem = f"gerado pelo trilha-briefing a partir de clientes/{c.briefing.cliente.id}/ — edite lá, não aqui"
    escritos = []
    arquivos = [
        (saida / "marca.yaml", marca_trilha(c), [origem]),
        (saida / "perfil.parcial.yaml", perfil_parcial(c), [
            origem,
            "Parcial: falta o que só existe depois do acesso às contas — plataformas, crm (funis, mapa_eventos,",
            "campos), conversao, freio e operacao. Complete no Trilha e valide com: python -m trilha validar",
        ]),
    ]
    arquivos += [(saida / "ofertas" / f"{o.id}.yaml", oferta_trilha(c, o), [origem]) for o in c.ofertas]
    for caminho, dados, cabecalho in arquivos:
        caminho.write_text(_yaml(dados, cabecalho), encoding="utf-8")
        escritos.append(caminho)
    return escritos


# ---------- Trilha-LP ----------


def pagina_lp(c: ClienteCompleto, o: Oferta, origem: str) -> tuple[dict, list[str]]:
    """Rascunho de pagina.yaml. Devolve também o que ficou para preencher."""
    b, pl = c.briefing, c.plataforma
    pend: list[str] = []
    persona = next((c.persona(p) for p in o.personas if c.persona(p)), None)
    numeros = c.provas.utilizaveis("numero")
    depoimentos = c.provas.utilizaveis("depoimento")
    provas_curtas = [f"{p.numero} {p.texto}".strip() for p in numeros][:2]
    if not provas_curtas:
        provas_curtas = ["PREENCHER: prova (número com fonte)"]
        pend.append("topo.provas: nenhum número com fonte em provas.yaml")
    reducao = [t for t in (o.inversao_risco, o.condicoes.condicao_excepcional, o.condicoes.pagamento) if t][:3]

    whatsapp = b.cliente.whatsapp or WHATSAPP_RESERVA
    if not b.cliente.whatsapp:
        pend.append("contato.whatsapp: número de reserva; preencher briefing.cliente.whatsapp")
    cores = pl.identidade_visual.cores
    if not {"primaria", "secundaria"} <= set(cores):
        pend.append("marca.cores: definir primária e secundária em plataforma.yaml")
    if not pl.compliance.politica_privacidade_url:
        pend.append("marca.politica_privacidade_url: obrigatória")
    promessa = o.promessa.texto if o.promessa else "PREENCHER: promessa"
    if not o.promessa:
        pend.append("topo.titulo: oferta sem promessa")

    antes = {ad.dimensao: ad.antes for ad in o.antes_depois}
    dor = {
        "titulo": persona.dores[0].texto if persona and persona.dores else "PREENCHER: a dor, nas palavras do cliente",
        "problema": antes.get("dia_a_dia") or next(iter(antes.values()), "PREENCHER"),
        "agravamento": antes.get("sentir") or o.big_idea.inimigo or "PREENCHER",
        "solucao": o.big_idea.mecanismo_unico or "PREENCHER",
    }
    if "PREENCHER" in " ".join(dor.values()):
        pend.append("dor: completar dores da persona, quadro antes/depois e mecanismo único")

    beneficios = [{"titulo": ad.depois, "texto": f"Em vez de: {ad.antes[:1].lower()}{ad.antes[1:]}"} for ad in o.antes_depois]
    beneficios += [{"titulo": d.texto, "texto": d.evidencia} for d in o.diferenciais]
    beneficios = beneficios[:8]
    if len(beneficios) < 4:
        pend.append(f"beneficios: {len(beneficios)} itens; a página pede de 4 a 8")
    if not 3 <= len(o.como_funciona) <= 5:
        pend.append("como_funciona: a página pede de 3 a 5 passos")
    objecoes = [{"pergunta": ob.objecao, "resposta": ob.resposta} for ob in o.objecoes if ob.resposta]
    if len(objecoes) < 3:
        pend.append("objecoes: a página pede ao menos 3 com resposta")
    lista = (reducao + [d.texto for d in o.diferenciais])[:4]
    if len(lista) < 3:
        pend.append("fechamento.lista: a página pede de 3 a 4 itens")
    cta = o.cta or "Quero saber mais"

    prova_social = None
    if numeros or depoimentos:
        prova_social = _sem_vazios({
            "titulo": c.provas.historias[0].titulo if c.provas.historias else f"{numeros[0].numero} {numeros[0].texto}" if numeros else "PREENCHER",
            "numeros": [{"numero": p.numero, "texto": p.texto} for p in numeros[:4]],
            "depoimentos": [{"texto": p.texto, "autor": p.autor} for p in depoimentos[:4]],
        })
    elif origem == "google":
        pend.append("prova_social: origem google exige o bloco; nenhuma prova utilizável")

    pagina = {
        "pagina": {
            "id": f"{o.id}-{origem}", "cliente": b.cliente.id, "oferta": o.id, "segmento": b.cliente.playbook,
            "origem": origem, "titulo_seo": f"{o.nome} — {b.cliente.nome}",
            "descricao_seo": (o.promessa.texto if o.promessa else o.problema)[:155],
        },
        "marca": _sem_vazios({
            "nome": b.cliente.nome,
            "cores": _sem_vazios({k: cores.get(k) for k in ("primaria", "secundaria", "fundo", "texto")}),
            "fontes": dict(pl.identidade_visual.tipografia),
            "registro_profissional": pl.compliance.registros_profissionais[0] if pl.compliance.registros_profissionais else "",
            "avisos_legais": pl.compliance.avisos_legais,
            "politica_privacidade_url": pl.compliance.politica_privacidade_url or "PREENCHER",
            "termos_proibidos": pl.voz.termos_proibidos,
            "promessas_proibidas": pl.compliance.promessas_proibidas,
        }),
        "rastreio": {"gtm_id": "", "webhook_url": "", "pagina_obrigado": ""},
        "contato": {"whatsapp": whatsapp, "mensagem_whatsapp": f"Olá! Quero saber mais sobre {o.nome}"},
        "topo": {
            "titulo": promessa,
            "subtitulo": o.big_idea.mecanismo_unico or o.problema or "PREENCHER",
            "provas": provas_curtas,
            "cta": {"texto": cta, "acao": "formulario"},
            "reducao_medo": reducao,
            "imagem": {"src": "", "alt": o.nome},
        },
    }
    if origem == "meta":
        pagina["dor"] = dor
    if prova_social:
        pagina["prova_social"] = prova_social
    pagina["beneficios"] = {"titulo": f"O que muda com {o.nome}", "itens": beneficios}
    pagina["como_funciona"] = {"titulo": f"Como funciona, em {len(o.como_funciona)} passos",
                               "passos": [p.model_dump() for p in o.como_funciona]}
    pagina["objecoes"] = {"titulo": "As dúvidas de quem está decidindo", "garantias": [o.inversao_risco] if o.inversao_risco else [],
                          "itens": objecoes}
    pagina["fechamento"] = {"titulo": cta, "subtitulo": f"Deixe seu WhatsApp e a equipe da {b.cliente.nome} fala com você.",
                            "lista": lista, "provas": provas_curtas[:2] if numeros else []}
    formulario = {"pedir_email": False}
    if o.qualificacao:
        formulario["qualificacao"] = o.qualificacao.model_dump()
    formulario.update({
        "botao": cta,
        "consentimento": f"Ao enviar, você concorda em ser contatado pela {b.cliente.nome} sobre {o.nome}.",
        "confirmacao": f"Recebemos! A equipe da {b.cliente.nome} vai te chamar no WhatsApp.",
    })
    pagina["formulario"] = formulario
    return pagina, pend


def exportar_lp(c: ClienteCompleto, saida: str | Path, oferta: str | None = None,
                origens: tuple[str, ...] = ("meta", "google")) -> list[tuple[Path, list[str]]]:
    alvo = [c.oferta(oferta)] if oferta else c.ofertas
    if oferta and alvo[0] is None:
        raise ValueError(f"oferta '{oferta}' não existe")
    escritos = []
    for o in alvo:
        for origem in origens:
            dados, pend = pagina_lp(c, o, origem)
            pasta = Path(saida) / f"{o.id}-{origem}"
            pasta.mkdir(parents=True, exist_ok=True)
            cab = [
                f"Rascunho gerado pelo trilha-briefing (clientes/{c.briefing.cliente.id}, oferta {o.id}, origem {origem}).",
                "O texto sai cru: reescreva com a voz da marca e rode: python -m trilha_lp validar <este arquivo>",
            ]
            cab += [f"PENDENTE: {p}" for p in pend]
            caminho = pasta / "pagina.yaml"
            caminho.write_text(_yaml(dados, cab), encoding="utf-8")
            escritos.append((caminho, pend))
    return escritos
