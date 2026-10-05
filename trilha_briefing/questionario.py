"""Questionário de kickoff para o cliente responder antes da reunião.

As perguntas são em linguagem do cliente. Com `assessor=True`, cada pergunta mostra o campo
que ela preenche, para a transcrição para os arquivos YAML.
"""

from __future__ import annotations

PERGUNTAS: list[tuple[str, list[tuple[str, str]]]] = [
    ("Sobre a empresa", [
        ("O que vocês vendem? Descreva como contaria para alguém que nunca ouviu falar.", "briefing: negocio.o_que_vende"),
        ("Como o cliente chega até vocês hoje? (indicação, loja, WhatsApp, redes, representante…)", "briefing: negocio.como_vende_hoje"),
        ("Quem atende quem chega? Quantas pessoas, quem faz o quê, em que horário?", "briefing: negocio.time_comercial; plataforma: atendimento"),
        ("Quanto tempo, em média, entre o primeiro contato e a compra?", "briefing: negocio.ciclo_venda_dias"),
        ("Usam algum sistema para acompanhar os contatos (CRM, planilha, caderno)?", "briefing: negocio.crm"),
    ]),
    ("Onde querem chegar", [
        ("Daqui a 12 meses, o que precisa ser verdade para vocês dizerem que valeu a pena?", "briefing: resultado_desejado.em_12_meses"),
        ("Como vão saber que deu certo? Que número vão olhar?", "briefing: resultado_desejado.sucesso_significa"),
        ("Pelo que querem ser lembrados quando alguém pensar no seu setor?", "briefing: resultado_desejado.conhecido_por; plataforma: jornada.conhecido_por"),
    ]),
    ("Quem compra", [
        ("Pense nos 5 melhores clientes que vocês já tiveram. O que eles têm em comum?", "pesquisa: personas"),
        ("O que estava acontecendo na vida deles quando decidiram comprar?", "pesquisa: personas[].gatilho_compra, dores"),
        ("O que eles dizem depois de comprar? O que mudou para eles?", "pesquisa: personas[].desejos; ofertas: antes_depois"),
        ("Quais perguntas ou dúvidas aparecem antes de alguém fechar?", "pesquisa: personas[].objecoes; ofertas: objecoes"),
        ("Por que alguém desiste de comprar com vocês?", "pesquisa: personas[].objecoes"),
        ("Podemos conversar com 3 a 5 clientes ou ler as conversas recentes de atendimento?", "pesquisa: escuta"),
    ]),
    ("Concorrência e mercado", [
        ("Quem são os 3 a 5 concorrentes que o cliente compara com vocês?", "pesquisa: concorrentes"),
        ("O que eles fazem melhor que vocês? E pior?", "pesquisa: concorrentes[].fortes/fracos"),
        ("O que só vocês oferecem, que ninguém mais consegue dizer?", "pesquisa: unicidade; ofertas: raridade"),
        ("Em que meses vendem mais e em quais vendem menos? Por quê?", "pesquisa: sazonalidade"),
    ]),
    ("A marca", [
        ("Por que a empresa começou? O que aconteceu para ela existir?", "plataforma: historia.catalisador"),
        ("Em que vocês acreditam que muitos no setor não acreditam?", "plataforma: historia.verdade_central"),
        ("Como acham que o mercado vê vocês hoje? E como gostariam de ser vistos?", "plataforma: posicionamento.percepcao_atual/desejada"),
        ("Que palavras nunca devem aparecer na comunicação de vocês?", "plataforma: voz.termos_proibidos"),
        ("Quem aparece na comunicação: a empresa, uma pessoa, ou os dois?", "plataforma: voz.assinatura"),
        ("Há regras do conselho profissional ou da lei que limitam o que podem anunciar?", "briefing: restricoes.regras_legais; plataforma: compliance"),
    ]),
    ("Provas", [
        ("Que números vocês têm orgulho de mostrar? De onde eles vêm?", "provas: numero (com fonte)"),
        ("Há clientes que topariam dar um depoimento (texto ou vídeo) com nome?", "provas: depoimento (autorizado)"),
        ("Conte a história de um cliente: como estava antes, o que mudou, onde está hoje.", "provas: historias"),
        ("Prêmios, certificações, aparições na mídia?", "provas: autoridade, midia, certificacao"),
    ]),
    ("Ofertas", [
        ("Quais produtos ou serviços vocês querem vender mais? Qual é o principal?", "ofertas: degrau"),
        ("Qual o preço, as formas de pagamento e alguma condição especial (com prazo)?", "ofertas: condicoes"),
        ("O que o cliente deixa de arriscar ao comprar com vocês? (garantia, teste, devolução)", "ofertas: inversao_risco"),
        ("Do primeiro contato à entrega, quais são os passos?", "ofertas: como_funciona"),
    ]),
    ("Histórico e limites", [
        ("O que já fizeram de marketing que funcionou? E o que não funcionou?", "briefing: historico"),
        ("Já investiram em anúncios? Quanto, onde e com que resultado?", "briefing: historico.ja_investiu_em_midia; pesquisa: maturidade.historico_conta"),
        ("Quanto podem investir por mês em mídia, no máximo?", "briefing: restricoes.verba_mensal_max"),
        ("Até quanto aceitam investir para testar, antes de saber se funciona?", "estrategia: orcamento.verba_validacao"),
        ("Qual a margem de lucro de uma venda, mais ou menos?", "estrategia: economia.margem_contribuicao"),
        ("Quem decide sobre marketing na empresa? Quem mais precisa ser ouvido?", "briefing: stakeholders"),
    ]),
]


def gerar(nome_cliente: str = "", assessor: bool = False) -> str:
    linhas = [f"# Questionário de início{' — ' + nome_cliente if nome_cliente else ''}", ""]
    if assessor:
        linhas += ["_Versão do assessor: cada pergunta mostra o campo que ela preenche._", ""]
    else:
        linhas += [
            "Responda com as palavras de vocês, do jeito que falariam com um cliente. "
            "Não existe resposta errada, e \"não sei\" também ajuda. Leva cerca de 40 minutos.", "",
        ]
    n = 0
    for secao, perguntas in PERGUNTAS:
        linhas += [f"## {secao}", ""]
        for texto, campo in perguntas:
            n += 1
            linhas.append(f"{n}. {texto}")
            if assessor:
                linhas.append(f"   - → `{campo}`")
            linhas.append("")
    return "\n".join(linhas)
