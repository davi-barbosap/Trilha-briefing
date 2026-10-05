# Mudanças

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
