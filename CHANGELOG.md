# Mudanças

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
