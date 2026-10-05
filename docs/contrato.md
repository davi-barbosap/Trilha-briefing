# Contrato com o Trilha e a Trilha-LP

O trilha-briefing é a fonte. O Trilha e a Trilha-LP recebem arquivos gerados por ele. O contrato é de dados, não de código: nenhum dos repositórios importa o outro.

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
| `contato.whatsapp` | `briefing.cliente.whatsapp` |
| `topo.titulo` / `subtitulo` | `promessa.texto` / `big_idea.mecanismo_unico` |
| `topo.provas` | até 2 números com fonte |
| `topo.reducao_medo` | inversão de risco, condição excepcional, pagamento |
| `dor` | 1ª dor da persona → título; antes/depois (`dia_a_dia`, `sentir`) → problema e agravamento; mecanismo único → solução |
| `prova_social` | história de cliente (título), números com fonte, depoimentos autorizados |
| `beneficios` | `antes_depois` (o "depois" é o título) + diferenciais, de 4 a 8 |
| `como_funciona`, `objecoes` | os mesmos campos da oferta |
| `formulario.qualificacao` | `oferta.qualificacao` |

O que faltar sai como `# PENDENTE:` no topo do arquivo. O texto sai cru: reescreva com a voz da marca e valide com `python -m trilha_lp validar`.

## Grade de criativos

O `codigo` de cada célula da grade (`estrategia.grade`) é o código do criativo:
- vai no `utm_content`;
- vai na mensagem pré-preenchida do WhatsApp (Trilha-LP);
- é lido pelo raio-x do Trilha (`codigo_criativo`).

Use o mesmo código nas três pontas.
