# Trilha-briefing

Briefing, marca e estratégia por cliente. É a ferramenta que guia o assessor a entender o cliente antes de anunciar: o mercado, quem compra, a marca, as provas e as ofertas. Termina num plano com objetivo, economia, verba, canais, riscos e medição.

Serve para qualquer segmento. O exemplo (`clientes/_exemplo/`) é uma escola de inglês fictícia.

O que sai daqui alimenta as outras ferramentas:
- [Trilha](https://github.com/davi-barbosap/Trilha) recebe `marca.yaml`, `ofertas/` e a economia do `perfil.yaml`;
- [Trilha-LP](https://github.com/davi-barbosap/Trilha-LP) recebe o rascunho do `pagina.yaml`;
- o cliente recebe a apresentação do plano em HTML.

## Como usar

```bash
pip install -e .

python -m trilha_briefing novo minha-cliente                    # cria clientes/minha-cliente/
python -m trilha_briefing questionario --cliente "Minha Cliente" > questionario.md   # envie ao cliente
python -m trilha_briefing questionario --assessor               # mesma lista, com o campo de cada pergunta

python -m trilha_briefing validar   clientes/minha-cliente      # esquema de todos os arquivos
python -m trilha_briefing lacunas   clientes/minha-cliente      # o que falta e o que bloqueia a aprovação
python -m trilha_briefing revisar   clientes/minha-cliente      # avisos críticos
python -m trilha_briefing economia  clientes/minha-cliente      # tetos de custo e verba de validação
python -m trilha_briefing canais    clientes/minha-cliente      # ordem sugerida de canais × o que está no plano
python -m trilha_briefing grade     clientes/minha-cliente      # públicos × argumentos com códigos

python -m trilha_briefing exportar  clientes/minha-cliente --para trilha   # dist/<id>/marca.yaml, ofertas/, perfil.parcial.yaml
python -m trilha_briefing exportar  clientes/minha-cliente --para lp       # dist/<oferta>-<origem>/pagina.yaml
python -m trilha_briefing apresentar clientes/minha-cliente                # dist/<id>/plano.html
```

## Arquivos de um cliente

```
clientes/<id>/
  briefing.yaml      o que o cliente diz (kickoff)
  pesquisa.yaml      personas, escuta, concorrentes, SWOT, sazonalidade, maturidade
  plataforma.yaml    jornada, associações, posicionamento, história, voz, identidade, temas
  provas.yaml        números com fonte, depoimentos autorizados, histórias de clientes
  ofertas/<id>.yaml  degrau, big idea, promessa, antes/depois, objeções, inversão de risco
  estrategia.yaml    objetivo, economia, verba, canais, grade, riscos, marcos, medição
  hipoteses.yaml     testes com critério de sucesso e volume mínimo
```

Toda afirmação importante diz de onde veio (`fonte`: empresa, consumidor, mercado, dados, assessor) e se já foi confirmada (`status`: hipótese, validada, refutada).

## O que bloqueia a aprovação

`lacunas` só libera a estratégia para o cliente quando houver:
- objetivo com meta, prazo e resultados-chave;
- os seis itens de medição prontos;
- economia unitária e verba de validação combinadas;
- objeções vindas de escuta real;
- promessa na oferta principal;
- ao menos uma prova utilizável;
- um canal ativo.

## Documentação

- [Método](docs/metodo.md): princípios, etapas, ciclo trimestral e onde fomos críticos com as fontes.
- [Contrato com o Trilha e a Trilha-LP](docs/contrato.md): o que vai para onde.

## Dados de clientes

Clientes reais têm estratégia, números e dados pessoais (LGPD). Por padrão, o `.gitignore` deixa `clientes/*` fora do Git e versiona só o exemplo. Se o repositório for privado e você quiser versionar os clientes aqui, apague as duas linhas no fim do `.gitignore`.

## Testes

```bash
python -m unittest discover -s tests -v
```
