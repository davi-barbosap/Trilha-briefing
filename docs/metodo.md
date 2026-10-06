# Método

Antes de anunciar, entender o cliente. Antes de aprovar, saber medir. Depois de lançar, aprender com os dados.
Vale para qualquer segmento: o que muda de um cliente para outro é o conteúdo dos arquivos, não as etapas.

```
kickoff ─► pesquisa ─► marca ─► provas ─► ofertas ─► estratégia ─► aprovação
   ▲                                                                   │
   │                                                    Trilha (mídia, raio-x, relatório semanal)
   └──────────────────── revisão trimestral ◄─────── hipóteses + números ◄┘
```

## Princípios

1. **Vozes separadas.** O que a empresa diz (`fonte: empresa`), o que quem compra disse na escuta (`consumidor`), o que o mercado e os dados mostram (`mercado`, `dados`) e o que o assessor conclui (`assessor`). A opinião da empresa sobre o próprio cliente é ponto de partida, não conclusão. "Cliente" não é fonte: é ambíguo e a ferramenta recusa.
2. **Hipótese até prova.** Toda afirmação nasce `hipotese` e só vira `validada` com evidência (entrevista, conversa do CRM, relatório). A revisão acusa "validada sem evidência".
3. **Escuta antes de persona.** Dores e objeções vêm de conversas reais (`pesquisa.escuta`). Cada persona da oferta principal precisa de ao menos uma objeção vinda da escuta (`consumidor` ou `dados`); sem isso, a estratégia não é aprovada.
4. **Fato no lugar de adjetivo.** "Turmas de até 6" e não "atendimento de qualidade". A revisão acusa diferencial e promessa sem número.
5. **Promessa que dá para cobrar.** Resultado observável, prazo e condição (para quem vale). Sem isso, a promessa não diferencia e ainda gera cliente frustrado.
6. **Saber medir antes de lançar.** UTMs, origem gravada no CRM, conversão confirmada, motivos de perda, código do criativo e relatório combinado. Sem os seis, a estratégia não é aprovada.
7. **Uma variável por teste, volume antes de concluir.** Hipótese tem critério de sucesso definido antes e mínimo de conversões. Abaixo do mínimo, o resultado é inconclusivo, por mais bonito que pareça.
8. **Verba de validação é limite de perda.** É o máximo que o cliente aceita investir até saber se funciona, combinado antes. Os tetos de custo vêm da mesma calculadora do Trilha-ads.

## Etapas e arquivos

| Etapa | Arquivo | Pergunta | Quem preenche |
|---|---|---|---|
| Kickoff | `briefing.yaml` | O que o cliente quer, como vende hoje, o que já tentou, o que não pode? | cliente (formulário) + assessor |
| Pesquisa | `pesquisa.yaml` | Quem compra, por quê, o que trava; concorrentes, SWOT, sazonalidade, maturidade | assessor, com escuta real |
| Marca | `plataforma.yaml` | Como quer ser lembrada, como fala, sobre o que fala | assessor + cliente |
| Provas | `provas.yaml` | O que sustenta cada promessa (com fonte e autorização) | cliente fornece, assessor organiza |
| Ofertas | `ofertas/<id>.yaml` | O que se vende, para quem, com que promessa, em que degrau da escada | assessor |
| Estratégia | `estrategia.yaml` | Objetivo, economia, verba, canais, grade de criativos, riscos, marcos, medição | assessor; aprovado com o cliente |
| Plano de campanhas | `campanhas.yaml` | Que campanhas, com que verba, evento, público, células, testes, nomes e fase | assessor; aprovado com o cliente |
| Testes | `hipoteses.yaml` | O que está sendo testado e o que já se aprendeu | assessor |

## Ferramentas por etapa

**Kickoff.** O questionário tem três momentos (`trilha_briefing/questionario/perguntas.yaml`, editável):
- ★ **cliente:** o cliente responde sozinho, no formulário (`questionario --formulario`).
  - São cerca de 80 perguntas visíveis e outras que só aparecem pelo ramo ou por uma resposta anterior. Levam cerca de 40 minutos, com progresso salvo, e "não sei" é uma resposta aceita.
  - As respostas entram com `importar-respostas`.
- ● **reunião:** aprofundar com o dono e com quem atende (`questionario --para reuniao`, cerca de 90 minutos). É aqui que entram o que pede conversa: a história e a crença da marca, a big idea, os diferenciais com o "e daí?" e a visita aos bastidores.
- ◆ **assessor:** o que você levanta com acessos, dados e escuta (`questionario --para assessor` mostra tudo, com o campo de cada pergunta).

Como formular as perguntas:
- **A linguagem é a do dono:** sem jargão.
- **Uma coisa por pergunta.**
- **Fato no lugar de taxa:** contatos e vendas por mês, e não "quantos de 10 fecham". A taxa sai da conta, e a revisão avisa quando a economia supõe fechar mais do que a empresa fecha hoje.
- **As palavras exatas do cliente,** sem nome.
- **Quem sabe responde:** o técnico fica com o assessor.

As regras completas estão no topo do `perguntas.yaml`. Por que formulário próprio, e não Google Forms: [decisão 002](decisoes/002-questionario-e-formulario.md).

**Ponto crítico.** O formulário é longo de propósito: é ele que poupa a primeira reunião de virar entrevista. Mas comprimento cobra adesão.
- **Se o cliente desistir no meio:** o que ele já respondeu está salvo, e o resto vira pauta da reunião.
- **Se acontecer sempre:** corte perguntas no `perguntas.yaml`, em vez de aceitar respostas pela metade.

Também entram:
- o mapa de stakeholders por influência × interesse;
- quem aprova anúncio, em quanto tempo e quem substitui;
- a capacidade de atendimento e de entrega;
- a área de atuação;
- os acessos e ativos que a fundação precisa.

**Pesquisa.**
- Personas com dores, desejos, objeções, ganchos, nível de consciência e gatilho de compra.
- Quem **não** atender (persona negativa) e como filtrar: exclusão de público, palavra-chave negativa, pergunta de qualificação.
- Benchmark de 3 a 5 concorrentes, terminando em **unicidade** (o que só este cliente tem).
- SWOT, calendário de sazonalidade e a nota de maturidade do Trilha-ads (0–3 em rastreamento, CRM, capacidade criativa, histórico de conta e verba).

**Marca.**
- Jornada (resultado → conhecido por → fazer → aprender) e associações (o que queremos e o que não queremos que lembrem).
- Posicionamento com a lacuna entre a percepção atual e a desejada.
- História (catalisador, verdade central, prova), voz com exemplos de "assim sim" e "assim não", e linha editorial com poucos temas e peso.

**Ofertas.**
- Escada de valor (isca → entrada → principal → premium → recorrente).
- Big idea (oportunidade, inimigo, mecanismo único), promessa, quadro antes/depois (ter, sentir, dia a dia, status), como funciona, objeções com resposta e inversão de risco.
- Escassez só se for real e com evidência.

**Estratégia.**
- **Por quê:** objetivo com meta, prazo e resultados-chave.
- **Quanto:** economia unitária (mesmos campos do Trilha-ads) e verba de validação.
- **Como:** abordagem (direta, inbound ou as duas) e canais com papel, status, verba e justificativa. `canais` sugere a ordem por **intenção**:
  - quem busca já quer comprar (busca da marca, do produto, do setor);
  - quem é impactado no feed precisa ser convencido (interesses, semelhantes, vídeo);
  - compra por necessidade puxa busca; compra por desejo puxa descoberta.
- **O que produzir:** grade públicos × argumentos, em que cada célula vira um briefing de criativo com código. O código vai na UTM e na mensagem do WhatsApp.
- **Riscos:** probabilidade × impacto e a resposta a cada um.
- **Quando:** marcos (fundação → validação → decisão), sem cronograma semana a semana.

**Plano de campanhas.** É como a estratégia vira campanhas, conjuntos e anúncios. `plano --sugerir` monta um rascunho a partir dos canais, da grade, da verba e da economia; `plano` mostra o que ele significa em números e o que não fecha. Cinco regras guiam o plano, e todas podem ser mudadas (abaixo):

1. **O plano registra decisões, não espelha a conta.** Ele guarda o que o cliente aprova: canal, plataforma, evento de otimização, verba, fase, públicos, palavras-chave, que célula roda onde. A estrutura real (IDs, conjuntos pausados) fica nas plataformas, e o Trilha-ads compara o planejado com o que está rodando. Subir campanha a partir do plano não é o objetivo: as interfaces mudam e o erro sai caro.
2. **Poucos conjuntos, só quantos a verba aguenta.** Um conjunto precisa de cerca de 50 eventos de otimização por semana para sair do aprendizado no Meta. O plano calcula, no teto de custo, quantos eventos a verba de cada campanha compra e quantos conjuntos cabem. As células da grade viram anúncios dentro de poucos conjuntos; o criativo escolhe a pessoa.
3. **Cada hipótese diz como vai ser testada.** Duas células no mesmo conjunto não são um teste justo: a plataforma reparte a verba como quiser. O plano pede o método (teste A/B da plataforma, conjuntos separados com a mesma verba, ou comparação dentro do conjunto, que é só direcional) e confere se o volume fecha no prazo.
4. **Nomes curtos, com o código da célula como âncora.** O anúncio se chama `PT01 | v1` e o `utm_content` é o código. As características do criativo (persona, argumento, formato) ficam nos arquivos, ligadas ao código, e não no nome, que alguém digita à mão.
5. **Muda de fase quando os números batem, não pelo calendário.** Fundação → validação → otimização → escala. Cada fase tem o que exige para entrar (medição completa; custo até um múltiplo do teto com um volume mínimo; semanas estáveis), e o `plano` mostra isso em reais. Na escala, a verba sobe aos poucos.

**Onde mudar as regras.**
- **Para todos os clientes:** `trilha_briefing/regras/campanhas.yaml`. Registre no CHANGELOG.
- **Só para um cliente:** bloco `regras:` no `campanhas.yaml` dele, com só as chaves que mudam. Exemplo: `regras: { aprendizado: { nivel: sugestao } }`.
- **Cada regra tem gravidade:** bloqueia, atenção, sugestão ou `desligada`. Também é configurável se o plano é obrigatório para aprovar a estratégia (`plano.obrigatorio_para_aprovar`, desligado por padrão).

**Testes.**
- A ordem para mexer quando algo não vai bem: criativo → público → objetivo → página → oferta. É a mesma ordem de diagnóstico do dossiê do Trilha-ads.
- Cada hipótese aponta os códigos da grade que testa, a etapa do funil em que o volume é contado, o mínimo **por variação** e quantas variações disputam. A verba de validação precisa pagar mínimo × variações; a conta usa o custo no teto, que é o ponto de equilíbrio. Acima do teto, a verba compra menos.
- O evento de otimização (`evento_otimizacao`) é o que a verba sustenta com cerca de 50 eventos por semana. A métrica principal pode ficar mais abaixo no funil e ser acompanhada no CRM.
- Horizonte de cada teste: núcleo (o que já funciona), adjacente (novo público ou oferta próxima) ou ruptura.

## Ciclo

- **Semanal:** fica no Trilha-ads (dossiê, raio-x do funil, relatório). Esta ferramenta não repete esses números.
- **A cada período de teste:**
  - o Trilha-ads grava o retorno (`raio-x … --retorno ads/<id>/retornos`);
  - `registrar-resultados` liga os códigos às hipóteses e diz quais têm volume para decidir;
  - o assessor decide contra o critério combinado (`decidir … --aprendizado`), e o aprendizado vai para a copy.

  Decidir antes do volume mínimo é ler ruído: a ferramenta avisa, mas não impede.
- **Trimestral:**
  - `fechar-ciclo --nome 2026-T4` guarda uma cópia do estado e um resumo em `historico/`;
  - confira se nenhuma hipótese ficou `rodando` sem retorno registrado;
  - troque `estimados` da economia por taxas reais do CRM;
  - promova a `validada` o que a escuta e os dados confirmaram;
  - revise canais e grade;
  - gere uma nova apresentação.

## De onde vem e onde fomos críticos

O método junta uma aula de branding (jornada, associações, história, provas, escuta, temas) e um curso geral de marketing de agência (método científico, pesquisa em 8 itens, canvas de planejamento, riscos, canais por intenção, grade de públicos × argumentos, big idea, antes/depois, retenção). Ficaram de fora ou foram ajustados:

- **Números de case e autopromoção** não viram benchmark. A referência é o histórico dos próprios clientes.
- **Palavra-chave de concorrente:** há decisões no Brasil tratando o uso da marca do concorrente como palavra-chave como concorrência desleal. O canal exige aprovação do cliente.
- **Escassez e medo:** só com evidência. Escassez falsa é publicidade enganosa (CDC), e conselhos profissionais têm regras próprias.
- **CPL e CAC:** uma definição só, a do dicionário de métricas do Trilha-ads. A economia usa as mesmas fórmulas.
- **Degraus de maturidade:** usamos a nota de maturidade do Trilha-ads, que já liga e desliga módulos lá.
- **Gantt semanal:** virou marcos. Para um assessor, o cronograma detalhado vira peso.
- **Temas internos de agência** (contratação, papéis de squad) não entram na ferramenta do cliente.
