"""Perguntas do briefing, em três momentos, cada uma apontando o campo que preenche.

    ★ cliente   o cliente responde sozinho antes da reunião (~30 min)
    ● reuniao   aprofundar no kickoff com o dono e o comercial (~90 min)
    ◆ assessor  o assessor levanta com acessos, dados e escuta (1–2 semanas)

Versões:
    gerar(para="cliente")   só ★, em linguagem do cliente, sem nomes de campo
    gerar(para="reuniao")   ● como roteiro do kickoff, com o ★ já respondido para conferir
    gerar(para="assessor")  tudo, com momento e campo, roteiro de escuta e sinais de alerta
"""

from __future__ import annotations

from typing import Literal

Momento = Literal["cliente", "reuniao", "assessor"]
SIMBOLO = {"cliente": "★", "reuniao": "●", "assessor": "◆"}

# (bloco, [(momento, pergunta, campo que preenche)])
BLOCOS: list[tuple[str, list[tuple[Momento, str, str]]]] = [
    ("Envie junto com as respostas", [
        ("cliente", "Acesso ao Gerenciador de Negócios do Meta, ao Google Ads, ao Gerenciador de Tags/GA4, ao CRM e ao domínio do site (ou diga quem tem).",
         "briefing.acessos; perfil.yaml do Trilha-ads (plataformas, crm)"),
        ("cliente", "Logo em arquivo editável, manual de marca (se houver), cores e fontes.", "briefing.ativos; plataforma.identidade_visual"),
        ("cliente", "Uma pasta com fotos e vídeos reais: equipe, produto, clientes, local.", "briefing.ativos; criativos; imagem da página"),
        ("cliente", "O link da política de privacidade do site (ou avise que não existe).", "briefing.ativos.politica_privacidade; plataforma.compliance"),
        ("cliente", "O número de WhatsApp comercial que vai nos anúncios.", "briefing.cliente.whatsapp"),
    ]),
    ("A empresa e quem decide", [
        ("cliente", "O que vocês vendem? Explique como contaria para alguém que nunca ouviu falar.", "briefing.negocio.o_que_vende"),
        ("cliente", "Há quanto tempo existem e onde atendem: cidades, raio em km, online?", "briefing.cliente.tempo_mercado; briefing.area"),
        ("cliente", "Quem decide sobre marketing? Quem mais precisa ser ouvido ou aprovar?", "briefing.stakeholders"),
        ("reuniao", "Quem aprova anúncio e texto, e em quanto tempo responde? Quem substitui quando essa pessoa não está?", "briefing.aprovacao"),
        ("reuniao", "O que fez vocês buscarem uma assessoria agora?", "expectativa do projeto (anotar no kickoff)"),
    ]),
    ("Onde querem chegar", [
        ("cliente", "Daqui a 12 meses, o que precisa ser verdade para dizerem que valeu a pena?", "briefing.resultado_desejado.em_12_meses; estrategia.objetivo"),
        ("cliente", "Que número vão olhar para saber se deu certo? Qual é esse número hoje?", "briefing.resultado_desejado.sucesso_significa; estrategia.objetivo.baseline"),
        ("reuniao", "Se precisar escolher um: crescer volume, lucro ou previsibilidade?", "estrategia.metrica_principal"),
        ("reuniao", "O que seria um fracasso nos primeiros 3 meses?", "estrategia.orcamento.verba_validacao; premissas"),
    ]),
    ("Ofertas e preço (uma rodada por oferta)", [
        ("cliente", "Quais produtos ou serviços querem vender mais? Qual é o principal?", "ofertas/<id>.yaml: degrau"),
        ("cliente", "Existe uma porta de entrada mais barata ou gratuita (avaliação, aula, amostra, diagnóstico)?", "ofertas: degrau isca/entrada"),
        ("cliente", "Preço, formas de pagamento e alguma condição especial, com prazo de validade?", "ofertas.condicoes; ofertas.escassez (só se real)"),
        ("cliente", "Do primeiro contato à entrega, quais são os passos?", "ofertas.como_funciona (3 a 5)"),
        ("cliente", "O que o cliente deixa de arriscar ao comprar com vocês (garantia, teste, devolução)?", "ofertas.inversao_risco"),
        ("reuniao", "O que o cliente consegue depois de comprar, em quanto tempo e em que condição?", "ofertas.promessa (resultado, prazo, condicao)"),
        ("reuniao", "Antes e depois: o que o cliente tem, como se sente, como é o dia a dia e como é visto?", "ofertas.antes_depois"),
        ("reuniao", "Por que alguém escolheria vocês e não outra opção? Diga com número, nome ou fato.", "ofertas.diferenciais; ofertas.raridade"),
        ("reuniao", "O que vocês fazem nos bastidores que parece óbvio para vocês, mas impressionaria quem visse?", "ofertas.bastidores"),
        ("reuniao", "No que o mercado acredita que vocês acham errado? Por que isso não resolve?", "ofertas.big_idea.crenca_comum, por_que_falha"),
        ("reuniao", "O que mais o cliente poderia fazer com esse dinheiro em vez de comprar de vocês? Por que não resolve?", "ofertas.alternativas"),
        ("reuniao", "Existe um prazo real (turma, lote, preço, evento)? Por que ele existe?", "ofertas.urgencia"),
        ("reuniao", "Que pergunta separa um bom contato de um curioso?", "ofertas.qualificacao (formulário da página)"),
    ]),
    ("Números do negócio", [
        ("cliente", "Quanto vale uma venda típica (ticket médio)?", "estrategia.economia.ticket_medio; ofertas.condicoes.ticket_medio"),
        ("cliente", "O cliente compra de novo ou paga todo mês? Por quantos meses fica, em média?", "briefing.negocio.modelo_receita; estrategia.economia.meses_retencao"),
        ("cliente", "De cada R$ 100 vendidos, quanto sobra depois dos custos diretos, mais ou menos?", "estrategia.economia.margem_contribuicao"),
        ("cliente", "De 10 pessoas que chamam vocês, quantas fecham?", "estrategia.economia.taxa_fechamento"),
        ("reuniao", "Dessas 10, quantas têm perfil? Quantas agendam? Quantas comparecem?", "estrategia.economia.taxa_qualificacao, taxa_agendamento (estimados até o CRM confirmar)"),
        ("reuniao", "Da margem de uma venda, quanto aceitam investir para conquistar um cliente novo?", "estrategia.economia.pct_investivel"),
        ("cliente", "Quanto podem investir por mês em anúncios, no máximo?", "briefing.restricoes.verba_mensal_max; estrategia.orcamento.teto_mensal"),
        ("cliente", "Até quanto aceitam investir para testar, antes de saber se funciona?", "estrategia.orcamento.verba_validacao"),
    ]),
    ("Atendimento e capacidade", [
        ("cliente", "Quem atende quem chega? Quantas pessoas, com que papéis, em que horários?", "briefing.negocio.time_comercial; plataforma.atendimento"),
        ("cliente", "Em quanto tempo vocês respondem um contato novo, de verdade?", "plataforma.atendimento.sla_resposta"),
        ("cliente", "Quantos contatos novos por dia o time consegue atender bem?", "briefing.capacidade.leads_dia"),
        ("cliente", "Quantos clientes novos por mês conseguem entregar (vagas, agenda, estoque)?", "briefing.capacidade.clientes_novos_mes"),
        ("reuniao", "Quais são as etapas do primeiro contato à venda? Usam CRM? Qual?", "briefing.negocio.crm; funil do Kommo no Trilha-ads"),
        ("reuniao", "Por que se perde uma venda? Quais são os 5 motivos mais comuns?", "motivos de perda do Kommo (Trilha-ads)"),
        ("reuniao", "Quantas vezes tentam falar com quem não responde, e por qual canal?", "diagnóstico de atendimento (raio-x do Trilha-ads)"),
        ("reuniao", "Fora do horário, quem responde? Há robô?", "plataforma.atendimento.handoff"),
    ]),
    ("Quem compra e quem não compra", [
        ("cliente", "Pense nos 5 melhores clientes que já tiveram: o que eles têm em comum?", "pesquisa.personas"),
        ("cliente", "E os 5 piores (deram trabalho, cancelaram, não pagaram)? O que tinham em comum?", "pesquisa.nao_atender"),
        ("cliente", "O que estava acontecendo na vida deles quando decidiram comprar?", "pesquisa.personas[].gatilho_compra; ganchos"),
        ("cliente", "Que dúvidas aparecem sempre antes de fechar?", "pesquisa.personas[].objecoes (fonte: empresa, até a escuta confirmar)"),
        ("cliente", "Do que seus clientes têm medo que aconteça se não resolverem isso?", "pesquisa.personas[].medos"),
        ("cliente", "Com que palavras exatas os clientes descrevem o problema? Copie mensagens reais, sem o nome de quem escreveu.", "pesquisa.personas[].frases"),
        ("cliente", "Onde esses clientes passam o tempo e se informam?", "pesquisa.personas[].onde_esta"),
        ("reuniao", "Quem procura vocês já sabe que precisa disso, ou precisa ser convencido de que tem o problema?", "pesquisa.personas[].nivel_consciencia"),
        ("reuniao", "Compram por necessidade (urgência, obrigação) ou por desejo?", "briefing.negocio.tipo_compra"),
        ("reuniao", "Quantas promessas parecidas esse cliente já ouviu? Ele já foi decepcionado por alguém do setor?", "pesquisa.personas[].sofisticacao"),
    ]),
    ("Escuta: autorização e material", [
        ("cliente", "Podemos entrevistar de 3 a 5 clientes recentes, 15 minutos cada?", "pesquisa.escuta (fonte: consumidor)"),
        ("cliente", "Podemos ler as conversas de WhatsApp e CRM dos últimos 60 dias, com dados pessoais ocultos?", "pesquisa.escuta (fonte: dados)"),
        ("assessor", "Avaliações no Google, comentários e mensagens nas redes: o que se repete?", "pesquisa.personas (dores, objeções); provas"),
        ("assessor", "Conversa de 20 minutos com quem atende: o que o cliente pergunta e por que desiste?", "pesquisa.personas[].objecoes; motivos de perda"),
        ("assessor", "Nas ligações e conversas, que crenças travam a compra: sobre o método, sobre si mesmo, sobre o ambiente? Quantas vezes cada uma aparece?", "pesquisa.personas[].crencas"),
    ]),
    ("Concorrência e mercado", [
        ("cliente", "Com quais 3 a 5 concorrentes o cliente compara vocês?", "pesquisa.concorrentes"),
        ("reuniao", "O que eles fazem melhor? E pior? Quanto cobram?", "pesquisa.concorrentes[].fortes, fracos, posicionamento_preco"),
        ("reuniao", "Quando perdem uma venda para um concorrente, por quê? E quando ganham?", "pesquisa.unicidade; ofertas.diferenciais"),
        ("cliente", "Em que meses vendem mais e em quais vendem menos? Por quê?", "pesquisa.sazonalidade"),
        ("cliente", "A sua categoria é vendida em algum marketplace ou plataforma (iFood, Mercado Livre, Doctoralia…)?", "briefing.negocio.marketplaces"),
        ("cliente", "Há regras do conselho profissional, de publicidade ou da lei que limitam o que podem dizer ou mostrar?", "briefing.restricoes.regras_legais; plataforma.compliance"),
        ("assessor", "Anúncios ativos dos concorrentes (Biblioteca de Anúncios do Meta, buscas no Google): o que prometem?", "pesquisa.concorrentes[].promessa"),
    ]),
    ("A marca", [
        ("cliente", "Por que a empresa começou? O que aconteceu para ela existir?", "plataforma.historia.catalisador"),
        ("cliente", "Em que vocês acreditam que muita gente do setor não acredita?", "plataforma.historia.verdade_central"),
        ("cliente", "Como acham que o mercado vê vocês hoje? E como gostariam de ser vistos?", "plataforma.posicionamento.percepcao_atual, percepcao_desejada"),
        ("cliente", "Pelo que querem ser lembrados? E pelo que não querem, de jeito nenhum?", "plataforma.associacoes"),
        ("cliente", "Quem aparece na comunicação: a empresa, uma pessoa ou as duas? A pessoa topa gravar vídeo?", "plataforma.voz.assinatura"),
        ("cliente", "Que palavras e promessas nunca devem aparecer?", "plataforma.voz.termos_proibidos; compliance.promessas_proibidas"),
        ("reuniao", "De 1 a 5, o quanto a comunicação pode soar vendedora (1 = sóbria, 5 = euforia de lançamento)?", "plataforma.voz.intensidade"),
        ("reuniao", "Mostre 3 textos ou posts de que gostaram e 3 de que não gostaram, e diga por quê.", "plataforma.voz.assim_sim, assim_nao"),
        ("reuniao", "Sobre que assuntos conseguem falar toda semana sem esgotar?", "plataforma.temas"),
        ("assessor", "Site, redes, perfil do Google e atendimento prometem a mesma coisa?", "plataforma.posicionamento.percepcao_atual"),
    ]),
    ("Provas", [
        ("cliente", "Que números têm orgulho de mostrar? De onde eles vêm (sistema, contrato, avaliação)?", "provas: numero, com fonte"),
        ("cliente", "Que clientes topariam dar depoimento com nome e foto ou vídeo? Há autorização por escrito?", "provas: depoimento, autorizado"),
        ("cliente", "Conte a história de um cliente: como estava antes, o que mudou, onde está hoje.", "provas.historias"),
        ("cliente", "Quem são as pessoas dos depoimentos (idade aproximada, profissão, situação de partida)?", "provas: perfil e personas"),
        ("cliente", "Prêmios, certificações, aparições na mídia, clientes conhecidos?", "provas: autoridade, midia, certificacao, com fonte"),
    ]),
    ("Histórico de marketing", [
        ("cliente", "O que já fizeram de marketing que funcionou? E o que não funcionou, e por quê?", "briefing.historico"),
        ("cliente", "Já anunciaram? Onde, com quanto por mês e com que resultado? A conta é de vocês ou da agência anterior?", "briefing.historico.ja_investiu_em_midia; pesquisa.maturidade.historico_conta"),
        ("reuniao", "O pixel e a tag do Google estão instalados? Os contatos chegam ao CRM com a origem?", "briefing.acessos; pesquisa.maturidade.rastreamento; estrategia.medicao"),
        ("reuniao", "Têm lista de clientes (e-mail ou telefone) com autorização de uso?", "briefing.ativos.lista_clientes_autorizada"),
        ("reuniao", "Têm site ou página de vendas? Quem mexe nela?", "Trilha-LP ou página do cliente"),
    ]),
    ("Combinados", [
        ("reuniao", "Quem recebe o relatório, com que frequência e quais números querem ver?", "estrategia.medicao.relatorio_definido"),
        ("cliente", "Há algum prazo fixo pela frente (lançamento, evento, data comemorativa)?", "briefing.restricoes.prazos; estrategia.marcos"),
    ]),
]

ROTEIRO_ESCUTA = [
    "O que estava acontecendo quando você decidiu procurar isso?",
    "O que você já tinha tentado antes?",
    "O que quase te fez desistir de comprar?",
    "Por que escolheu esta empresa e não outra?",
    "O que mudou depois?",
    "Como você explicaria para um amigo o que eles fazem?",
]

SINAIS_DE_ALERTA = [
    "Não sabe a margem nem a taxa de fechamento: a economia fica toda estimada.",
    "Ninguém responde em menos de 2 horas: o problema é o atendimento, não a mídia.",
    "\"Nosso diferencial é a qualidade\": ainda não há posicionamento.",
    "Não autoriza nenhuma escuta: as personas serão opinião da empresa.",
    "A verba de validação não paga o volume mínimo dos testes: o teste vai terminar inconclusivo.",
    "As vendas fora do digital são fracas: o digital vai expor o problema mais rápido e mais caro.",
    "A capacidade de atendimento é menor do que os leads que a verba traz: lead sem resposta é verba perdida.",
]


def perguntas(momento: Momento | None = None) -> list[tuple[str, Momento, str, str]]:
    """(bloco, momento, pergunta, campo), na ordem do questionário."""
    return [(b, m, p, c) for b, itens in BLOCOS for m, p, c in itens if momento is None or m == momento]


def gerar(nome_cliente: str = "", assessor: bool = False, para: Momento = "cliente") -> str:
    para = "assessor" if assessor else para
    titulo = {"cliente": "Questionário de início", "reuniao": "Roteiro do kickoff", "assessor": "Briefing completo"}[para]
    linhas = [f"# {titulo}{' — ' + nome_cliente if nome_cliente else ''}", ""]
    if para == "cliente":
        linhas += ["Responda com as palavras de vocês, do jeito que falariam com um cliente. "
                   "Não existe resposta errada, e \"não sei\" também ajuda. Leva cerca de 30 minutos.", ""]
    elif para == "reuniao":
        linhas += ["Comece conferindo as respostas do questionário (★) e aprofunde as perguntas ●. "
                   "Fale com o dono e com quem atende. Cerca de 90 minutos.", ""]
    else:
        linhas += ["★ o cliente responde antes · ● aprofundar no kickoff · ◆ o assessor levanta com dados e escuta.",
                   "Cada pergunta mostra o campo que ela preenche.", ""]
    n = 0
    for bloco, itens in BLOCOS:
        visiveis = [(m, p, c) for m, p, c in itens if para == "assessor" or m == para or (para == "reuniao" and m == "cliente")]
        if not visiveis:
            continue
        linhas += [f"## {bloco}", ""]
        for m, p, c in visiveis:
            n += 1
            marca = "" if para == "cliente" else f"{SIMBOLO[m]} "
            linhas.append(f"{n}. {marca}{p}")
            if para == "assessor":
                linhas.append(f"   - → `{c}`")
            linhas.append("")
    if para != "cliente":
        linhas += ["## Roteiro das entrevistas com clientes (escuta)", "",
                   "15 minutos por pessoa. Anote as palavras exatas: viram ganchos, dores e títulos. Registre em `pesquisa.escuta` "
                   "e use `fonte: consumidor`.", ""]
        linhas += [f"- {p}" for p in ROTEIRO_ESCUTA] + [""]
        linhas += ["## Sinais de alerta", "", "Pause antes de prometer resultado quando:", ""]
        linhas += [f"- {s}" for s in SINAIS_DE_ALERTA] + [""]
    return "\n".join(linhas)
