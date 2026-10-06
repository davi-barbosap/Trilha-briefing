# Mudanças

## 0.5.1 — padrão de texto da Trilha (out/2026)

- **O padrão de texto** mora no Trilha-copy (`trilha_copy/regras/padrao.yaml`). O briefing guarda a cópia das listas que usa em `trilha_briefing/regras/padrao-vocabularios.yaml`, e `tests/test_padrao.py` confere a cópia lista a lista contra o Trilha-copy na CI.
- **Termos casam como palavra inteira:** "corra" não pega mais "ocorra". Antes, o briefing procurava o termo dentro das palavras.
- **Regras novas no texto das ofertas:**
  - garantia de resultado (bloqueia);
  - prazo ou vaga no texto sem urgência ou escassez reais (bloqueia);
  - promessa de ganho com número e sem ressalva;
  - autoelogio;
  - lista de promessas proibidas do segmento (imobiliário pelo playbook; saúde pelos registros profissionais).
- **Adjetivo sem fato** usa a lista do padrão (mais ampla: "ótima localização", "perto de tudo", "profissionais qualificados"…) e a de prova vaga ("milhares de clientes").
- **`exportar --para copy`** leva `preco`, a regra comercial por canal, para a copy conferir o preço no anúncio e na página.

## 0.5.0 — questionário reformulado e formulário do cliente (out/2026)

### Novo
- **As perguntas viraram dado** (`trilha_briefing/questionario/perguntas.yaml`), conferido ao carregar:
  - o campo existe no esquema;
  - as opções cabem no campo;
  - a condição cita uma pergunta anterior que o cliente vê, com valores que ela tem.

  As regras para formular perguntas novas ficam no topo do arquivo.
- **Questionário reformulado:** 203 perguntas.
  - **Por momento:** 105 do cliente (cerca de 80 visíveis, o resto por condição), 58 da reunião e 40 do assessor.
  - **No formulário:** 27 perguntas de escolha. Só 11 são obrigatórias, e cada pergunta tem ajuda com exemplo.
  - **Genérico:** a primeira pergunta é o tipo de negócio, e as perguntas de saúde, imóveis, B2B, educação, produto digital, e-commerce e veículos só aparecem para quem é do ramo.
  - **Fatos no lugar de taxas:** contatos e vendas por mês. A margem vem como "de cada R$ 100", e a verba de teste como limite de perda.
  - **O técnico** (acessos, rastreamento, IDs do CRM) foi para o assessor.
  - **O abstrato** (história e crença da marca, big idea, "e daí?") foi para a reunião.
- **`questionario --formulario`:** formulário do cliente num HTML só.
  - Progresso salvo no aparelho, uma parte por bloco, perguntas condicionais e "não sei, prefiro falar na reunião".
  - No fim, a revisão das obrigatórias e as respostas para baixar ou copiar.
  - Gerado sem cliente, aceita o nome no link (`?cliente=…&quem=…`), para publicar num endereço só.
  - Testado em tela de celular no Chromium.
- **`importar-respostas <arquivo|-> <pasta>`:**
  - guarda as respostas em `respostas/<data>-questionario.json` e `.md`;
  - preenche sozinho os campos simples, como hipótese (`fonte: empresa`), sem reescrever o arquivo (os comentários ficam) e sem sobrescrever valor existente;
  - confere cada campo contra o esquema, e o que não cabe vai para "levar à mão" com o motivo (ex.: WhatsApp fora do padrão, bloco de economia incompleto);
  - se a pasta ficaria inválida, nada é gravado.

  No teste de ponta a ponta, 44 campos foram preenchidos sozinhos numa pasta nova.
- **Tipo `telefone`:** "(11) 98765-4321" vira `5511987654321`.
- **`briefing.negocio.contatos_mes` e `vendas_mes`:** a revisão avisa quando a economia supõe fechar mais do que a empresa fecha hoje.

### Mudou
- `questionario` em Markdown mostra quando uma pergunta é condicional.
- O `novo` indica o formulário e a importação como próximos passos.
- Decisão registrada em [docs/decisoes/002](docs/decisoes/002-questionario-e-formulario.md).

## 0.4.1 — plano de campanhas chega à copy (out/2026)

- **`exportar --para copy`** leva o bloco `veiculacao`: onde cada célula vira anúncio (plataforma, campanha, conjunto), com o nome do anúncio e os parâmetros de URL já resolvidos pelas regras de nomes do plano. O Trilha-copy só preenche o código e a versão da peça e gera a lista de subida. Antes, o nome e a UTM de cada anúncio eram montados à mão na hora de subir, longe do plano.
- Sem `campanhas.yaml`, o bloco não sai. É opcional e o contrato continua na versão 1.
- **`identidade_visual`** também vai para a copy (cores, tipografia, logo, estilo de imagem): o Trilha-copy põe no briefing do criativo de cada peça, para a equipe de criação.

## 0.4.0 — plano de campanhas (out/2026)

### Novo
- **`campanhas.yaml`:** o plano de campanhas do cliente. Cada campanha tem canal, plataforma, evento de otimização, fase e verba. Cada conjunto tem público, palavras-chave, correspondência, exclusões e as células da grade que viram anúncios ali. A campanha também guarda as negativas (Google) e os testes, com o método de cada um.
- **`plano`:** mostra o plano em números:
  - eventos por semana no teto de custo e quantos conjuntos cabem para sair do aprendizado;
  - prazo de cada teste;
  - nomes e UTMs;
  - o que cada campanha precisa para mudar de fase.
- **`plano --sugerir`:** grava um rascunho a partir dos canais, da grade, da verba e da economia. Junta as células num conjunto só quando a verba não aguenta um por persona.
- **Regras editáveis** em `trilha_briefing/regras/campanhas.yaml`, com override por cliente no bloco `regras:` e gravidade configurável (inclusive `desligada`):
  1. o plano registra decisões e não espelha a conta;
  2. poucos conjuntos, só quantos a verba aguenta;
  3. cada hipótese diz como vai ser testada;
  4. nomes curtos com o código da célula;
  5. mudança de fase quando os números batem.

### Revisão e lacunas
- **Bloqueia:**
  - verba das campanhas acima do teto;
  - nome de anúncio ou UTM sem `{codigo}` (gravidade configurável).
- **Atenção:**
  - soma das campanhas diferente da verba da estratégia;
  - mais conjuntos do que a verba aguenta, ou nem um conjunto sai do aprendizado;
  - teste sem método, com variações no mesmo conjunto quando deveriam estar separadas, ou que não fecha no prazo;
  - campanha numa fase sem a medição completa;
  - campanha de busca sem palavra-chave;
  - célula de prioridade 1 sem campanha.
- **Sugestão:**
  - comparação dentro do conjunto é só direcional;
  - hipótese do núcleo sem teste no plano;
  - célula ou canal sem campanha.
- **Lacuna:** plano de campanhas, quando há canal pago ativo. Só bloqueia a aprovação com `plano.obrigatorio_para_aprovar`.
- **Validação:**
  - canal, célula, hipótese e fase precisam existir;
  - ids não se repetem;
  - `id_plataforma` só com `espelho.ids_da_plataforma`.
- **Apresentação:** tabela "Como a verba se divide", sem nomes, UTMs nem regras.

## 0.3.1 — organização do ecossistema (out/2026)

Nenhuma mudança de comportamento.

- **Nomes:** as outras ferramentas passam a ser citadas pelo nome atual: Trilha-ads, Trilha-copy e Trilha-LP.
- **Clientes reais** ficam no repositório privado Trilha-clientes, pasta `briefing/`. A exportação grava direto na pasta de cada ferramenta (`--saida copy`, `--saida ads`, `--saida lp/<id>`).
- **Decisão 001 aceita:** este repositório é a fonte do cadastro. O Trilha-ads registrou o mesmo na ADR-005 dele.
- **CI:** clona o Trilha-ads e a Trilha-LP e roda o teste de contrato de verdade, em vez de pulá-lo. Também exporta para a copy.
- **README:** cada comando com o que faz, as duas etapas (diagnóstico e planejamento), o que não faz e a situação atual.

## 0.3.0 — campos para a copy (out/2026)

O que as aulas de copy mostraram que faltava na fonte, e o contrato com o Trilha-copywritter.

### Novo
- **Persona:**
  - `medos` (o que teme se não resolver);
  - `crencas` em três tipos (método, interna, externa), cada uma com a forma de derrubar;
  - `micro_problemas`;
  - `frases` literais de quem compra, sem nome;
  - `sofisticacao` (quantas promessas parecidas já ouviu).
- **Afirmações** (`Item`) ganham `mencoes`: quantas pessoas disseram isso na escuta.
- **Oferta:**
  - `bastidores` (o cuidado que ninguém conta);
  - `alternativas` e por que não resolvem;
  - `urgencia` real, com motivo e data;
  - `custo_inacao`;
  - `big_idea.crenca_comum` e `por_que_falha`;
  - escada do "e daí?" (`e_dai`) em cada diferencial.
- **Provas:** `id`, `personas` e `perfil` do protagonista, para usar a prova parecida com quem lê.
- **Voz:** `intensidade` de 1 a 5.
- **Grade:** `promessa` por célula, ajustada ao medo daquela persona.
- **`exportar --para copy`:** gera `copy.yaml`, o contrato versionado com o Trilha-copywritter.
- **Questionário:** 10 perguntas novas (medos, palavras exatas, sofisticação, crenças, bastidores, crença do mercado, alternativas, prazo real, intensidade, perfil dos depoimentos).

### Revisão e lacunas
- **Bloqueia:** urgência sem motivo ou evidência.
- **Atenção:** urgência vencida.
- **Sugestão:**
  - diferencial da oferta principal sem a escada do "e daí?";
  - crença sem a forma de derrubar;
  - depoimento sem persona.
- **Lacunas:**
  - persona sem frases, crenças ou sofisticação;
  - oferta principal sem bastidores, sem processo (crença comum e por que falha) ou sem alternativas;
  - voz sem intensidade.

## 0.2.0 — revisão crítica (out/2026)

### Corrige
- **Fontes:** "cliente" era ambíguo (a empresa ou quem compra dela) e deixava a opinião do dono passar como escuta. Agora as fontes são `empresa`, `consumidor`, `mercado`, `dados` e `assessor`, e `cliente` é recusado.
- **Escuta por persona:** a aprovação exige, para cada persona da oferta principal, ao menos uma objeção vinda da escuta. Antes, uma única objeção em qualquer persona bastava.
- **Volume da validação:**
  - a conta era descrita como "no máximo" e "otimista"; na verdade é o ponto de equilíbrio no teto de custo;
  - o mínimo agora é por variação e multiplicado pelo número de variações;
  - cada hipótese diz em que etapa do funil o volume é contado.
- **Evento de otimização:** a revisão bloqueia quando a verba não sustenta 50 eventos por semana no evento escolhido e indica o degrau viável. O exemplo otimizava por agendamento com R$ 5 mil, e isso pede R$ 54 mil.
- **WhatsApp ausente:** o rascunho da página saía com um número de reserva que passava na validação. Agora sai `PREENCHER`, que não passa.
- **Provas:** autoridade, mídia e certificação exigem fonte, não autorização de imagem.
- **Dados duplicados:** a revisão confere o modelo de receita, o ticket e o teto de verba entre briefing, ofertas e estratégia.
- **Apresentação:** hipóteses aparecem como "a confirmar", refutadas saem e riscos internos ficam fora.
- **Página:** o subtítulo não repete mais a solução do bloco de dor. Os benefícios escritos têm prioridade sobre o rascunho "Em vez de: …".
- **Palavras vagas:** "melhorar" deixa de contar como adjetivo vago.

### Novo
- **Revisão com gravidade** (bloqueia, atenção, sugestão). Bloqueios entram nas lacunas de aprovação, e `revisar` sai com erro quando há algum.
- **Briefing:**
  - `area` (no lugar de `cidade_atuacao`);
  - `capacidade`, com aviso quando a verba traz mais leads do que o time atende;
  - `aprovacao`, `acessos` e `ativos`;
  - `negocio.marketplaces`.
- **Pesquisa:** `nao_atender` (persona negativa e como filtrar).
- **Ofertas:** `subtitulo` e `beneficios` escritos para a página.
- **Estratégia:** `evento_otimizacao`; riscos com `interno`.
- **Hipóteses:** `codigos` (células da grade), `evento` e `variacoes`.
- **Validação na origem:** cores em #RRGGBB e regras de preço só com os valores que o Trilha entende.
- **Questionário em três momentos:** 77 perguntas (★ cliente, ● reunião, ◆ assessor), com roteiro de escuta e sinais de alerta. Gerado com `questionario --para`.
- **`fechar-ciclo`:** guarda o estado do cliente e um resumo em `historico/<ciclo>/` antes da revisão trimestral.
- **Teste de contrato** com o Trilha e a Trilha-LP (`tests/test_contrato.py`).
- **Decisão 001:** este repositório é a fonte de marca, ofertas e economia.

### Muda o formato
Se você já tinha pastas de clientes:
- troque `fonte: cliente` por `empresa` ou `consumidor`;
- troque `cliente.cidade_atuacao` por `area`;
- confira as cores (#RRGGBB) e as regras de preço.

O `validar` aponta cada caso.

## 0.1.0 — MVP (out/2026)
Briefing, pesquisa, plataforma, provas, ofertas, estratégia e hipóteses, com lacunas, revisão, canais, grade, exportação para o Trilha e a Trilha-LP e apresentação em HTML.
