# Trilha-briefing

Briefing, marca e estratégia por cliente. É a ferramenta que guia o assessor a entender o cliente antes de anunciar: o mercado, quem compra, a marca, as provas e as ofertas. Termina num plano com objetivo, economia, verba, canais, riscos e medição.

Serve para qualquer segmento. O exemplo (`clientes/_exemplo/`) é uma escola de inglês fictícia.

O que sai daqui alimenta as outras ferramentas:
- [Trilha](https://github.com/davi-barbosap/Trilha) recebe `marca.yaml`, `ofertas/` e a economia do `perfil.yaml`;
- [Trilha-LP](https://github.com/davi-barbosap/Trilha-LP) recebe o rascunho do `pagina.yaml`;
- [Trilha-copywritter](https://github.com/davi-barbosap/Trilha-copywritter) recebe o `copy.yaml`, com tudo o que a copy pode usar;
- o cliente recebe a apresentação do plano em HTML.

## Como usar

```bash
pip install -e .

python -m trilha_briefing novo minha-cliente                    # cria clientes/minha-cliente/
python -m trilha_briefing questionario --cliente "Minha Cliente" > questionario.md   # ★ envie ao cliente
python -m trilha_briefing questionario --para reuniao           # ● roteiro do kickoff + roteiro de escuta
python -m trilha_briefing questionario --para assessor          # tudo, com o momento e o campo de cada pergunta

python -m trilha_briefing validar   clientes/minha-cliente      # esquema de todos os arquivos
python -m trilha_briefing lacunas   clientes/minha-cliente      # o que falta e o que bloqueia a aprovação
python -m trilha_briefing revisar   clientes/minha-cliente      # avisos por gravidade; sai com erro se algo bloqueia
python -m trilha_briefing economia  clientes/minha-cliente      # tetos de custo, verba para otimizar por etapa, validação
python -m trilha_briefing canais    clientes/minha-cliente      # ordem sugerida de canais × o que está no plano
python -m trilha_briefing grade     clientes/minha-cliente      # públicos × argumentos com códigos

python -m trilha_briefing exportar  clientes/minha-cliente --para trilha   # dist/<id>/marca.yaml, ofertas/, perfil.parcial.yaml
python -m trilha_briefing exportar  clientes/minha-cliente --para lp       # dist/<oferta>-<origem>/pagina.yaml
python -m trilha_briefing exportar  clientes/minha-cliente --para copy     # dist/<id>/copy.yaml (contrato com o Trilha-copywritter)
python -m trilha_briefing apresentar clientes/minha-cliente                # dist/<id>/plano.html

python -m trilha_briefing fechar-ciclo clientes/minha-cliente --nome 2026-T4  # guarda o estado antes da revisão trimestral
```

## Arquivos de um cliente

```
clientes/<id>/
  briefing.yaml      o que a empresa diz: negócio, área, capacidade, aprovação, acessos, ativos
  pesquisa.yaml      personas, escuta, quem não atender, concorrentes, SWOT, sazonalidade, maturidade
  plataforma.yaml    jornada, associações, posicionamento, história, voz, identidade, temas
  provas.yaml        números com fonte, depoimentos autorizados, histórias de clientes
  ofertas/<id>.yaml  degrau, big idea, promessa, antes/depois, benefícios, objeções, inversão de risco
  estrategia.yaml    objetivo, economia, evento de otimização, verba, canais, grade, riscos, marcos, medição
  hipoteses.yaml     testes com códigos da grade, critério de sucesso e volume mínimo por variação
  historico/<ciclo>/ cópia do estado em cada fechamento de ciclo, com resumo.md
```

Toda afirmação importante diz de onde veio (`fonte`: empresa, consumidor, mercado, dados, assessor) e se já foi confirmada (`status`: hipótese, validada, refutada).

## O que bloqueia a aprovação

`lacunas` só libera a estratégia para o cliente quando houver:
- objetivo com meta, prazo e resultados-chave;
- os seis itens de medição prontos;
- economia unitária e verba de validação combinadas;
- registro de escuta e, para cada persona da oferta principal, ao menos uma objeção vinda da escuta (`consumidor` ou `dados`);
- promessa na oferta principal;
- ao menos uma prova utilizável;
- um canal ativo;
- nenhum aviso de gravidade **bloqueia** na revisão.

A revisão separa os avisos em três níveis:
- **Bloqueia:** promessa ou termo proibido, escassez sem evidência, palavra-chave de concorrente sem aprovação, dados que se contradizem entre arquivos, verba acima do teto, evento de otimização que a verba não sustenta.
- **Atenção:** volume insuficiente para concluir um teste, verba abaixo da mínima viável, verba que traz mais leads do que o time atende, promessa sem prazo ou sem número.
- **Sugestão:** afirmações sem fonte, taxas ainda estimadas, pesos dos temas.

## Documentação

- [Método](docs/metodo.md): princípios, etapas, ciclo trimestral e onde fomos críticos com as fontes.
- [Contrato com o Trilha e a Trilha-LP](docs/contrato.md): o que vai para onde.
- [Decisões](docs/decisoes/): por que as coisas são como são.
- [Mudanças](CHANGELOG.md).

## Dados de clientes

Clientes reais têm estratégia, números e dados pessoais (LGPD). Por padrão, o `.gitignore` deixa `clientes/*` fora do Git e versiona só o exemplo. Se o repositório for privado e você quiser versionar os clientes aqui, apague as duas linhas no fim do `.gitignore`.

## Testes

```bash
python -m unittest discover -s tests -v

# contrato com os outros repositórios (clonados ao lado deste):
PYTHONPATH=../Trilha:../Trilha-LP python -m unittest tests.test_contrato -v
```

Sem o Trilha e a Trilha-LP no `PYTHONPATH`, o teste de contrato é pulado. Rode-o sempre que mudar a exportação ou quando um dos outros repositórios mudar de formato.
