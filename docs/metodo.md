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
8. **Verba de validação é limite de perda.** É o máximo que o cliente aceita investir até saber se funciona, combinado antes. Os tetos de custo vêm da mesma calculadora do Trilha.

## Etapas e arquivos

| Etapa | Arquivo | Pergunta | Quem preenche |
|---|---|---|---|
| Kickoff | `briefing.yaml` | O que o cliente quer, como vende hoje, o que já tentou, o que não pode? | cliente (questionário) + assessor |
| Pesquisa | `pesquisa.yaml` | Quem compra, por quê, o que trava; concorrentes, SWOT, sazonalidade, maturidade | assessor, com escuta real |
| Marca | `plataforma.yaml` | Como quer ser lembrada, como fala, sobre o que fala | assessor + cliente |
| Provas | `provas.yaml` | O que sustenta cada promessa (com fonte e autorização) | cliente fornece, assessor organiza |
| Ofertas | `ofertas/<id>.yaml` | O que se vende, para quem, com que promessa, em que degrau da escada | assessor |
| Estratégia | `estrategia.yaml` | Objetivo, economia, verba, canais, grade de criativos, riscos, marcos, medição | assessor; aprovado com o cliente |
| Testes | `hipoteses.yaml` | O que está sendo testado e o que já se aprendeu | assessor |

## Ferramentas por etapa

**Kickoff.** 77 perguntas em três momentos:
- ★ **cliente:** o cliente responde sozinho antes da reunião (`questionario`, cerca de 30 minutos);
- ● **reunião:** aprofundar com o dono e com quem atende (`questionario --para reuniao`, cerca de 90 minutos);
- ◆ **assessor:** o que você levanta com acessos, dados e escuta (`questionario --para assessor` mostra tudo, com o campo de cada pergunta).

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
- SWOT, calendário de sazonalidade e a nota de maturidade do Trilha (0–3 em rastreamento, CRM, capacidade criativa, histórico de conta e verba).

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
- **Quanto:** economia unitária (mesmos campos do Trilha) e verba de validação.
- **Como:** abordagem (direta, inbound ou as duas) e canais com papel, status, verba e justificativa. `canais` sugere a ordem por **intenção**:
  - quem busca já quer comprar (busca da marca, do produto, do setor);
  - quem é impactado no feed precisa ser convencido (interesses, semelhantes, vídeo);
  - compra por necessidade puxa busca; compra por desejo puxa descoberta.
- **O que produzir:** grade públicos × argumentos, em que cada célula vira um briefing de criativo com código. O código vai na UTM e na mensagem do WhatsApp.
- **Riscos:** probabilidade × impacto e a resposta a cada um.
- **Quando:** marcos (fundação → validação → decisão), sem cronograma semana a semana.

**Testes.**
- A ordem para mexer quando algo não vai bem: criativo → público → objetivo → página → oferta. É a mesma ordem de diagnóstico do dossiê do Trilha.
- Cada hipótese aponta os códigos da grade que testa, a etapa do funil em que o volume é contado, o mínimo **por variação** e quantas variações disputam. A verba de validação precisa pagar mínimo × variações; a conta usa o custo no teto, que é o ponto de equilíbrio. Acima do teto, a verba compra menos.
- O evento de otimização (`evento_otimizacao`) é o que a verba sustenta com cerca de 50 eventos por semana. A métrica principal pode ficar mais abaixo no funil e ser acompanhada no CRM.
- Horizonte de cada teste: núcleo (o que já funciona), adjacente (novo público ou oferta próxima) ou ruptura.

## Ciclo

- **Semanal:** fica no Trilha (dossiê, raio-x do funil, relatório). Esta ferramenta não repete esses números.
- **Trimestral:**
  - `fechar-ciclo --nome 2026-T4` guarda uma cópia do estado e um resumo em `historico/`;
  - atualize as hipóteses com os resultados;
  - troque `estimados` da economia por taxas reais do CRM;
  - promova a `validada` o que a escuta e os dados confirmaram;
  - revise canais e grade;
  - gere uma nova apresentação.

## De onde vem e onde fomos críticos

O método junta uma aula de branding (jornada, associações, história, provas, escuta, temas) e um curso geral de marketing de agência (método científico, pesquisa em 8 itens, canvas de planejamento, riscos, canais por intenção, grade de públicos × argumentos, big idea, antes/depois, retenção). Ficaram de fora ou foram ajustados:

- **Números de case e autopromoção** não viram benchmark. A referência é o histórico dos próprios clientes.
- **Palavra-chave de concorrente:** há decisões no Brasil tratando o uso da marca do concorrente como palavra-chave como concorrência desleal. O canal exige aprovação do cliente.
- **Escassez e medo:** só com evidência. Escassez falsa é publicidade enganosa (CDC), e conselhos profissionais têm regras próprias.
- **CPL e CAC:** uma definição só, a do dicionário de métricas do Trilha. A economia usa as mesmas fórmulas.
- **Degraus de maturidade:** usamos a nota de maturidade do Trilha, que já liga e desliga módulos lá.
- **Gantt semanal:** virou marcos. Para um assessor, o cronograma detalhado vira peso.
- **Temas internos de agência** (contratação, papéis de squad) não entram na ferramenta do cliente.
