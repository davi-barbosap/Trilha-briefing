# Implantação em 10 dias úteis

O site da Trilha promete **dez dias úteis entre o contrato e a campanha no ar**, em seis etapas, e afirma que "nenhuma etapa depende de o cliente descobrir o que precisa entregar. O briefing é nosso."

Este documento liga cada etapa às ferramentas (Trilha-briefing, [Trilha-copy](https://github.com/davi-barbosap/Trilha-copy), [Trilha-LP](https://github.com/davi-barbosap/Trilha-LP) e [Trilha-ads](https://github.com/davi-barbosap/Trilha-ads)) e registra onde o prazo e as regras das ferramentas ainda não conversam.

## As seis etapas

O site fixa duas datas: o kickoff no dia 1 e o setup pronto até o dia 5. As demais faixas de dias abaixo são uma proposta, para validar com a operação.

| Dias | Etapa (site) | O que o site diz |
|---|---|---|
| 1 | **Kick-off** | Antes de falar de campanha, entendemos como o seu comercial fecha hoje. |
| 1–5 | **Setup** | Acessos, CRM, cronograma e canal de comunicação. Tudo no lugar até o quinto dia. |
| 3–8 | **Criativos** | Briefing produzido pela Trilha, peças entregues e validadas antes da ativação. |
| 3–8 | **CRM** | Funil com as suas etapas, campos do seu negócio, motivos de perda e integrações. |
| 9–10 | **Treinamento e ativação** | Seu time aprende a operar o que foi construído. As campanhas sobem. |
| depois do 10 | **Rotina** | Reunião, relatório e decisão. Toda análise termina em para onde vai a verba do próximo mês. |

## Etapa a etapa

### 1. Kick-off (dia 1)

**Antes do dia 1**, logo depois da assinatura: mandar o questionário do cliente (cerca de 30 minutos para responder).

```bash
python -m trilha_briefing novo <cliente>
python -m trilha_briefing questionario --cliente "<Nome>" > questionario.md   # ★ vai para o cliente
python -m trilha_briefing questionario --para reuniao                         # ● roteiro do kickoff (cerca de 90 min)
```

**No dia 1:** reunião com o dono e com quem atende os leads. A pergunta central do site, "como o seu comercial fecha hoje", é o campo `negocio.como_vende_hoje` do `briefing.yaml`, junto com o time comercial, o histórico, a capacidade de atendimento e quem aprova anúncio.

**Sai do dia 1:** `briefing.yaml` preenchido, com os acessos marcados como `ok`, `pendente` ou `nao_tem`.

### 2. Setup (dias 1 a 5)

| Item | Onde fica | Pronto quando |
|---|---|---|
| Acessos (Meta, Google, Kommo, site, GTM) | `briefing.yaml` → `acessos` | `lacunas` não lista nenhum acesso pendente |
| CRM do cliente no padrão | Kommo; `perfil.yaml` do Trilha-ads (`crm`) | funil padrão, campos de rastreamento e motivos de perda cadastrados (ver CRM, abaixo) |
| Cronograma | pasta do cliente no ClickUp | etapas com data até o dia 10 |
| Canal de comunicação | grupo com o cliente | assessor e cliente no grupo, com quem aprova anúncio |
| Rastreamento do site (GA4, GTM, pixel) | ferramenta paralela ([ecossistema](https://github.com/davi-barbosap/Trilha-ads/blob/main/docs/ecossistema.md) §3) | tag do Google e pixel disparando |

### 3. Criativos (dias 3 a 8)

1. **Briefing feito pela Trilha:** `pesquisa.yaml`, `plataforma.yaml`, `provas.yaml`, `ofertas/` e a grade de `estrategia.yaml` (públicos × argumentos, um código por célula).
2. **Copy:** `exportar --para copy` → Trilha-copy (`pacote`, `nova`, `revisar`, `aprovar`). Só peças aprovadas saem no `anuncios.csv`.
3. **Produção:** foto e vídeo pela equipe de audiovisual, a partir dos roteiros aprovados.
4. **Landing page:** `exportar --para lp` → Trilha-LP (`validar`, `construir --todas`).
5. **Validação com o cliente:** quem aprova anúncio (`briefing.aprovacao`) aprova peças e página antes do dia 9.

O código de cada célula da grade vai no `utm_content`, na mensagem do WhatsApp e no raio-x do Trilha-ads. Usar o mesmo código nas três pontas.

### 4. CRM (dias 3 a 8)

O site fala em "funil com as suas etapas". Na prática, as etapas seguem o **funil padrão** da Trilha ([ADR-008](https://github.com/davi-barbosap/Trilha-ads/blob/main/docs/decisoes/008-funil-padrao.md)) com os **nomes** do negócio do cliente (o playbook do segmento renomeia: "visita agendada", "test drive realizado"…). Funis extras (SDR, closer, nutrição) entram com o papel de cada um. É assim que o raio-x consegue comparar clientes e mostrar onde está o vazamento.

| Item | Referência |
|---|---|
| Etapas do funil padrão com os nomes do segmento | [playbooks](https://github.com/davi-barbosap/Trilha-ads/tree/main/playbooks) |
| Motivos de perda nativos e obrigatórios, com a lista do playbook | [raio-x do funil](https://github.com/davi-barbosap/Trilha-ads/blob/main/docs/raio-x-do-funil.md) |
| Campos de rastreamento (UTMs, `gclid`, `gbraid`, `wbraid`, `fbclid`) e os dois que a Trilha-LP acrescenta (`landing_page`, `event_id_lead`) | [Kommo](https://github.com/davi-barbosap/Trilha-ads/blob/main/docs/integracoes/kommo.md) §4; [contrato da Trilha-LP](https://github.com/davi-barbosap/Trilha-LP/blob/main/docs/contrato.md) |
| Responsável em todo lead | idem |
| Pré-atendimento (salesbot) e fluxos | `briefing-trilha` (ferramenta paralela) |
| Mapa de eventos para a conversão real | `perfil.yaml` → `crm.mapa_eventos`; fluxo W01 no n8n |

### 5. Treinamento e ativação (dias 9 e 10)

**Treinamento do time comercial do cliente.** Nenhuma ferramenta cobre esta etapa ainda. O conteúdo mínimo:
- mover o lead de etapa no mesmo dia do contato, porque é o que alimenta o raio-x e a conversão real;
- registrar o motivo de perda sempre (o Kommo vai exigir);
- responder primeiro por uma pessoa, não só pelo bot (o raio-x mede o primeiro contato humano em horário de expediente);
- não apagar lead duplicado: marcar com o motivo "Lead duplicado".

**Ativação.**
1. [Checklist de publicação](https://github.com/davi-barbosap/Trilha-LP/blob/main/docs/checklist-publicacao.md) da página inteiro marcado, com lead de teste chegando ao Kommo.
2. Conversão real em modo de teste (`META_TEST_EVENT_CODE`) antes de produção.
3. Modo do freio de emergência combinado com o cliente (`freio.modo`: `pausar` ou `avisar`).
4. Campanhas no ar.

### 6. Rotina (depois do dia 10)

A rotina é a do [modelo operacional](https://github.com/davi-barbosap/Trilha-ads/blob/main/docs/modelo-operacional.md) do Trilha-ads: otimização semanal com o dossiê, relatório semanal, reunião mensal com o pacote e painel da carteira.

O site promete que "toda análise termina em para onde vai a verba do próximo mês". O pacote da reunião mensal traz os números de apoio (item 10: escalar, pausar, investigar), mas não um bloco de verba proposta. Sugestão: acrescentar ao pacote mensal um bloco **"Verba do próximo mês"**, com a distribuição atual por canal e campanha, o custo por venda de cada um contra o teto e o espaço até o teto mensal, para o assessor fechar a proposta.

## Onde o prazo e as ferramentas não conversam

### A trava de aprovação do briefing

Hoje o `lacunas` só libera a estratégia quando há, entre outras coisas:
- registro de escuta e, para cada persona da oferta principal, ao menos uma objeção vinda de quem compra (`consumidor` ou `dados`);
- os seis itens de medição prontos (UTMs, campos no CRM, evento de conversão, etapas e motivos de perda, código do criativo, relatório definido);
- economia unitária e verba de validação combinadas;
- promessa, ao menos uma prova utilizável e um canal ativo.

A escuta é o item que mais ameaça o prazo: entrevistas com quem compra raramente cabem em dez dias. Quando o cliente já tem conversas no CRM ou avaliações públicas, elas valem como `dados` e resolvem. Quando não tem, o briefing trava.

**Regra proposta: duas aprovações.**

| Aprovação | Quando | Exige |
|---|---|---|
| **Ativação** | até o dia 10 | os seis itens de medição, economia e verba de validação, promessa, uma prova utilizável, um canal ativo, nada que bloqueie na revisão. Personas podem ter objeções só da empresa, marcadas como `hipotese` |
| **Estratégia completa** | até o dia 30 | tudo o que o `lacunas` exige hoje, com a escuta feita sobre as primeiras conversas que as campanhas trouxeram |

Assim a medição nunca é dispensada (sem ela a campanha não sobe) e a escuta vira a primeira tarefa da rotina, em vez de impedir o início. Para valer, o `lacunas` precisa ganhar o nível "ativação". Esta é uma mudança de código, ainda não feita.

### O que nenhuma ferramenta acompanha

- **O relógio dos 10 dias:** nenhuma ferramenta sabe a data do contrato nem avisa quando uma etapa atrasa. Hoje isso fica no cronograma do ClickUp.
- **O treinamento:** sem roteiro nem registro de que foi feito.
- **Acessos que o cliente não tem** (`nao_tem`): criar conta de anúncios ou Business Manager do zero pode levar dias e não depende só da Trilha.
- **Segmentos sem playbook:** hotelaria, automotivo e gastronomia ainda usam o funil padrão sem os nomes nem os motivos de perda do segmento ([playbooks](https://github.com/davi-barbosap/Trilha-ads/blob/main/playbooks/README.md)).
