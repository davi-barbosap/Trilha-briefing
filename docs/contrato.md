# Contrato com o Trilha e a Trilha-LP

O trilha-briefing é a fonte. O Trilha-ads e a Trilha-LP recebem arquivos gerados por ele. O contrato é de dados, não de código: nenhum dos repositórios importa o outro.

Os arquivos exportados trazem no topo o comentário "edite lá, não aqui". Uma mudança feita direto no arquivo gerado se perde na próxima exportação.

## Trilha — `exportar --para trilha`

| Gerado | Vem de | Observação |
|---|---|---|
| `marca.yaml` | `plataforma.yaml` (voz, identidade, compliance, atendimento, preço) + `provas.yaml` | formato do núcleo §5.1; `pessoa_gramatical` derivada da assinatura; só provas utilizáveis (número com fonte, depoimento autorizado) |
| `ofertas/<id>.yaml` | `ofertas/<id>.yaml` | passa no esquema de oferta do Trilha; `objecoes[].resposta` → `resposta_do_time`; `condicoes` → `condicoes_comerciais`; personas → `perfil_lead.perfil`; `ciclo_venda_dias` → `perfil_lead.jornada_media_dias` |
| `perfil.parcial.yaml` | `briefing.yaml` + `estrategia.yaml` | `cliente`, `metrica_principal`, `economia` e `verba`. **Parcial:** `plataformas`, `crm`, `conversao`, `freio` e `operacao` só existem depois do acesso às contas e são completados no Trilha |

`cliente.playbook` vira o `segmento` do Trilha (aponta para `playbooks/<segmento>/`). `cliente.segmento` é texto livre e fica só aqui.

### Economia

`economia.py` usa as mesmas fórmulas de `trilha/core/economia.py`:
- CAC máximo = receita por venda × margem × % investível;
- custo máximo por lead = CAC × taxa de fechamento;
- custo por qualificado e por agendamento dividem pela taxa de cada etapa;
- verba mínima viável = 50 leads por semana no CPL máximo.

Se as fórmulas mudarem no Trilha, mudam aqui. O teste `test_mesmos_numeros_do_trilha` fixa os valores do exemplo.

A margem sobre o CAC, no teto de custo, é sempre `1 / pct_investivel`. Com `pct_investivel` acima de 33%, ela fica abaixo de 3×, e a revisão avisa.

## Trilha-LP — `exportar --para lp`

Gera um rascunho de `pagina.yaml` por oferta e origem (`meta` abre com a dor, `google` com a prova social).

| Bloco da página | Vem de |
|---|---|
| `marca` | `plataforma.yaml` (cores, tipografia, registro, avisos, termos e promessas proibidas, política de privacidade) |
| `contato.whatsapp` | `briefing.cliente.whatsapp`; sem ele, sai `PREENCHER`, que não passa no `trilha_lp validar` |
| `topo.titulo` / `subtitulo` | `promessa.texto` / `oferta.subtitulo` (ou os três primeiros diferenciais) |
| `topo.provas` | até 2 números com fonte |
| `topo.reducao_medo` | inversão de risco, condição excepcional, pagamento |
| `dor` | 1ª dor da persona → título; antes/depois (`dia_a_dia`, `sentir`) → problema e agravamento; mecanismo único → solução |
| `prova_social` | história de cliente (título), números com fonte, depoimentos autorizados |
| `beneficios` | `oferta.beneficios` (4 a 8, escritos para a página); sem eles, o "depois" do antes/depois e os diferenciais, com o texto de apoio marcado como pendente |
| `como_funciona`, `objecoes` | os mesmos campos da oferta |
| `formulario.qualificacao` | `oferta.qualificacao` |

O que faltar sai como `# PENDENTE:` no topo do arquivo. O texto sai cru: reescreva com a voz da marca e valide com `python -m trilha_lp validar`.

## Trilha-copywritter — `exportar --para copy`

Gera `dist/<id>/copy.yaml`, versionado pelo campo `contrato` (hoje `1`). A ferramenta de copy recusa versões que não conhece.

| Bloco | Vem de | Observação |
|---|---|---|
| `cliente` | `briefing.yaml` | id, nome, segmento, playbook, WhatsApp, área |
| `voz`, `posicionamento` | `plataforma.yaml` | inclui `voz.intensidade`, o termostato de 1 a 5 |
| `compliance` | `plataforma.yaml` + `briefing.restricoes` | termos e promessas proibidas, registros, avisos, regras legais, o que não pode |
| `personas`, `nao_atender` | `pesquisa.yaml` | com medos, crenças (método, interna, externa), micro-problemas, frases literais, sofisticação |
| `concorrentes` | `pesquisa.yaml` | **só os nomes**, para a revisão avisar quando uma peça cita um concorrente |
| `ofertas` | `ofertas/` | com bastidores, alternativas, urgência, custo de não agir, escada do "e daí?" |
| `provas`, `historias` | `provas.yaml` | **só as utilizáveis**: número e autoridade com fonte, depoimento e história autorizados |
| `grade`, `hipoteses` | `estrategia.yaml`, `hipoteses.yaml` | a peça de copy nasce de uma célula da grade e se liga a uma hipótese |

O que não é utilizável nem chega à ferramenta de copy: um depoimento sem autorização não pode ir parar num anúncio por engano.

Mudou um campo que a copy usa? Suba a versão do contrato e ajuste o `trilha_copy` junto.

## Teste de contrato

`tests/test_contrato.py` exporta o exemplo e valida o resultado com o código real dos outros repositórios:
- as ofertas passam no esquema do Trilha;
- a economia dá os mesmos números na calculadora do Trilha;
- a página da oferta principal passa no esquema da Trilha-LP;
- a página sem WhatsApp não passa.

Os repositórios não dependem um do outro, então o teste só roda com os dois clonados ao lado:

```bash
PYTHONPATH=../Trilha:../Trilha-LP python -m unittest tests.test_contrato -v
```

## Grade de criativos

O `codigo` de cada célula da grade (`estrategia.grade`) é o código do criativo:
- vai no `utm_content`;
- vai na mensagem pré-preenchida do WhatsApp (Trilha-LP);
- é lido pelo raio-x do Trilha (`codigo_criativo`).

Use o mesmo código nas três pontas.
