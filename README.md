# Trilha-briefing

Diagnóstico e planejamento de cada cliente da Trilha. É a primeira etapa e a fonte de tudo:
- o que o cliente vende e para quem;
- a marca, as provas e as ofertas;
- a estratégia: objetivo, economia, verba, canais, grade de criativos, hipóteses e medição.

As outras ferramentas só usam o que está aqui.

Serve para qualquer segmento. O exemplo (`clientes/_exemplo/`) é uma escola de inglês fictícia.

## Ecossistema Trilha

| Etapa | Repositório | Papel |
|---|---|---|
| 1. Diagnóstico e planejamento | **Trilha-briefing (este)** | entende o cliente e decide a estratégia; é a fonte de tudo o que as outras ferramentas usam |
| 2. Copy | [Trilha-copy](https://github.com/davi-barbosap/Trilha-copy) | estrutura e revisa os textos dos anúncios, fiel ao briefing |
| 3. Página | [Trilha-LP](https://github.com/davi-barbosap/Trilha-LP) | landing page com o rastreamento que leva a origem do lead até o Kommo |
| 4. Execução e medição | [Trilha-ads](https://github.com/davi-barbosap/Trilha-ads) | coleta, confere e calcula: raio-x do funil, conversão real, freio, material das reuniões |
| Dados dos clientes | Trilha-clientes (privado) | os arquivos reais de cada cliente; esta ferramenta usa a pasta `briefing/` e exporta para as outras |

O código da célula da grade (`PT01`, `GB01`…) amarra as etapas: nasce aqui, vai no anúncio como `utm_content` e na mensagem do WhatsApp da página, e chega ao lead no Kommo.

## O que faz

### 1. Diagnóstico: entender o cliente

| Comando | O que faz |
|---|---|
| `novo <id>` | Cria a pasta do cliente a partir do modelo comentado. |
| `questionario` | Gera as perguntas do briefing em três momentos. ★ É o questionário que o cliente responde sozinho, em uns 30 minutos (`--para cliente`). ● É o roteiro da reunião de kickoff e da escuta (`--para reuniao`). ◆ É o que o assessor levanta com dados. A versão `--para assessor` mostra o momento e o campo que cada pergunta preenche. |
| `validar` | Confere o esquema de todos os arquivos e as referências entre eles: personas e ofertas citadas existem, ids não se repetem e a pasta tem o nome do cliente. |
| `lacunas` | Mostra o que falta em cada etapa e o que bloqueia a aprovação da estratégia. |
| `revisar` | Dá avisos em três gravidades e sai com erro se algo bloqueia (lista abaixo). |

### 2. Planejamento: decidir a estratégia

| Comando | O que faz |
|---|---|
| `economia` | Calcula os tetos de custo (CAC, custo por lead, por qualificado e por agendamento) e a verba mínima viável. Compara as conversões que a verba de validação compra com o mínimo de cada hipótese. |
| `canais` | Sugere a ordem dos canais por intenção e atenção e compara com o que está no plano. A busca vem antes quando há demanda; a descoberta sobe quando a compra é por desejo ou o público ainda não conhece o problema. |
| `grade` | Monta a grade públicos × argumentos, com o código de cada célula. Cada célula vira peças de copy com aquele código. |
| `plano [--sugerir]` | Mostra o **plano de campanhas** em números: verba de cada campanha, quantos eventos ela compra por semana no teto de custo, quantos conjuntos cabem para sair do aprendizado, os testes e o prazo para concluir, os nomes e UTMs, e o que cada campanha precisa para mudar de fase. `--sugerir` grava um rascunho a partir dos canais, da grade, da verba e da economia. |
| `apresentar` | Gera o plano em HTML para o cliente. O que ainda não foi validado aparece marcado como hipótese; afirmações refutadas e riscos marcados como internos ficam de fora. |
| `fechar-ciclo --nome 2026-T4` | Guarda uma cópia do estado e um resumo antes da revisão trimestral. |

### 3. Exportação: o contrato com as outras ferramentas

| Comando | Gera | Para |
|---|---|---|
| `exportar --para trilha` | `marca.yaml`, `ofertas/`, `perfil.parcial.yaml` | Trilha-ads (cadastro, economia e verba) |
| `exportar --para lp --oferta <id> [--origem meta\|google]` | rascunho de `pagina.yaml` por oferta e origem | Trilha-LP |
| `exportar --para copy` | `copy.yaml`: personas, voz, ofertas, provas utilizáveis, compliance, grade e hipóteses | Trilha-copy |

Os arquivos exportados trazem no topo o aviso "edite lá, não aqui": a próxima exportação sobrescreve o que for mudado à mão. Detalhes em [contrato](docs/contrato.md).

## Como faz

- **Origem de cada afirmação.** Toda afirmação importante diz de onde veio (`fonte`: empresa, consumidor, mercado, dados, assessor) e se já foi confirmada (`status`: hipótese, validada, refutada). A opinião do dono não passa como voz do consumidor.
- **Escuta antes da estratégia.** A aprovação exige registro de escuta e uma objeção vinda dela para cada persona da oferta principal.
- **Economia antes da verba.** As metas saem da economia unitária, com as mesmas fórmulas do Trilha-ads; um teste de contrato confere que os números batem.
- **Medição antes de lançar.** Seis itens precisam estar prontos:
  - UTMs no padrão;
  - campos no CRM;
  - evento de conversão;
  - etapas e motivos de perda;
  - código do criativo chegando no lead;
  - relatório definido.
- **Hipóteses que dá para concluir.** Cada uma tem célula da grade, critério de sucesso e volume mínimo por variação. A revisão avisa quando a verba não compra conversões suficientes para concluir o teste.
- **Plano de campanhas com regras editáveis.** Cinco regras guiam o plano: ele registra decisões e não espelha a conta; poucos conjuntos, só quantos a verba aguenta; cada hipótese diz como vai ser testada; nomes curtos com o código da célula; e mudança de fase quando os números batem. Todas mudam em `trilha_briefing/regras/campanhas.yaml` (para todos) ou no bloco `regras:` do `campanhas.yaml` (para um cliente), inclusive a gravidade de cada uma ([método](docs/metodo.md)).

**O que bloqueia a aprovação.** `lacunas` só libera a estratégia para o cliente quando houver:
- objetivo com meta, prazo e resultados-chave;
- os seis itens de medição prontos;
- economia unitária e verba de validação combinadas;
- registro de escuta e, para cada persona da oferta principal, ao menos uma objeção vinda da escuta (`consumidor` ou `dados`);
- promessa na oferta principal;
- ao menos uma prova utilizável;
- um canal ativo;
- nenhum aviso de gravidade **bloqueia** na revisão.

**A revisão** separa os avisos em três níveis:
- **Bloqueia:**
  - promessa ou termo proibido;
  - escassez sem evidência e urgência sem motivo;
  - palavra-chave de concorrente sem aprovação;
  - dados que se contradizem entre arquivos;
  - verba acima do teto;
  - evento de otimização que a verba não sustenta.
- **Atenção:**
  - volume insuficiente para concluir um teste;
  - verba abaixo da mínima viável;
  - verba que traz mais leads do que o time atende;
  - promessa sem prazo ou sem número;
  - urgência vencida.
- **Sugestão:**
  - afirmações sem fonte;
  - taxas ainda estimadas;
  - diferencial sem a escada do "e daí?";
  - crença sem a forma de derrubar;
  - depoimento sem persona.

## Arquivos de um cliente

```
<id>/
  briefing.yaml      o que a empresa diz: negócio, área, capacidade, aprovação, acessos, ativos
  pesquisa.yaml      personas (dores, desejos, medos, crenças, frases literais, sofisticação), escuta,
                     quem não atender, concorrentes, SWOT, sazonalidade, maturidade
  plataforma.yaml    jornada, associações, posicionamento, história, voz (com intensidade), identidade, temas
  provas.yaml        números com fonte, depoimentos autorizados, histórias de clientes, cada um com o perfil
  ofertas/<id>.yaml  degrau, big idea, promessa, antes/depois, diferenciais, bastidores, alternativas,
                     objeções, inversão de risco, urgência e escassez reais
  estrategia.yaml    objetivo, economia, evento de otimização, verba, canais, grade, riscos, marcos, medição
  hipoteses.yaml     testes com códigos da grade, critério de sucesso e volume mínimo por variação
  campanhas.yaml     plano de campanhas: canal, evento, verba, fase, conjuntos, células, testes e regras do cliente
  historico/<ciclo>/ cópia do estado em cada fechamento de ciclo, com resumo.md
```

## O que não faz

- **Não escreve copy nem página.** O rascunho de página sai cru, para reescrever na Trilha-LP; a copy é estruturada e revisada no Trilha-copy.
- **Não lê as contas de anúncio nem o Kommo.** Isso é do Trilha-ads.
- **Não decide.** Sugere a ordem dos canais e confere a consistência; quem decide é o assessor, com o cliente.
- **Não espelha a conta de anúncios.** O plano registra decisões; a estrutura real fica nas plataformas e quem compara é o Trilha-ads (quando houver coleta).
- **Ainda não recebe os resultados de volta.** O resultado de cada hipótese é registrado à mão em `hipoteses.yaml`.
- **O questionário é Markdown:** as respostas do cliente são transcritas à mão para os arquivos.

## Situação atual

Versão 0.4.0, em uso no exemplo e sem cliente real ainda. Próximos passos:
- o caminho de volta dos resultados do Trilha-ads para as hipóteses e as personas;
- o Trilha-ads comparar o plano com o que está rodando, quando houver coleta.

## Como usar

```bash
pip install -e .

# Clientes reais ficam no Trilha-clientes (privado), pasta briefing/
cd ../Trilha-clientes
python -m trilha_briefing novo minha-cliente --pasta briefing
python -m trilha_briefing questionario --cliente "Minha Cliente" > questionario.md   # ★ envie ao cliente
python -m trilha_briefing questionario --para reuniao           # ● roteiro do kickoff e da escuta
python -m trilha_briefing questionario --para assessor          # tudo, com o momento e o campo de cada pergunta

python -m trilha_briefing validar   briefing/minha-cliente
python -m trilha_briefing lacunas   briefing/minha-cliente
python -m trilha_briefing revisar   briefing/minha-cliente
python -m trilha_briefing economia  briefing/minha-cliente
python -m trilha_briefing canais    briefing/minha-cliente
python -m trilha_briefing grade     briefing/minha-cliente
python -m trilha_briefing plano     briefing/minha-cliente --sugerir   # rascunho do campanhas.yaml
python -m trilha_briefing plano     briefing/minha-cliente             # o plano em números e o que não fecha

python -m trilha_briefing exportar  briefing/minha-cliente --para copy   --saida copy                   # copy/minha-cliente/copy.yaml
python -m trilha_briefing exportar  briefing/minha-cliente --para trilha --saida ads                    # ads/minha-cliente/...
python -m trilha_briefing exportar  briefing/minha-cliente --para lp --oferta X --saida lp/minha-cliente # lp/minha-cliente/X-meta/...
python -m trilha_briefing apresentar briefing/minha-cliente     # dist/minha-cliente/plano.html (não versionar)

python -m trilha_briefing fechar-ciclo briefing/minha-cliente --nome 2026-T4
```

Neste repositório, os comandos rodam também sobre o exemplo: `python -m trilha_briefing lacunas clientes/_exemplo`.

## Documentação

- [Método](docs/metodo.md): princípios, etapas, ciclo trimestral e onde fomos críticos com as fontes.
- [Contrato](docs/contrato.md): o que vai para o Trilha-ads, a Trilha-LP e o Trilha-copy.
- [Decisões](docs/decisoes/): por que as coisas são como são.
- [Mudanças](CHANGELOG.md).

## Testes

```bash
python -m unittest discover -s tests -v
```

O teste de contrato (`tests/test_contrato.py`) confere que o que exportamos passa nos esquemas reais do Trilha-ads e da Trilha-LP. Ele roda quando os dois estão instalados; sem eles, é pulado. A CI clona os dois repositórios e roda o teste a cada push.

Mudança que atravessa repositórios: abra os PRs juntos e faça o merge primeiro do lado que exporta.

## Dados de clientes

Clientes reais têm estratégia, números e dados pessoais (LGPD). Eles ficam no repositório privado Trilha-clientes. Aqui, o `.gitignore` deixa `clientes/*` fora do Git e versiona só o exemplo fictício.
