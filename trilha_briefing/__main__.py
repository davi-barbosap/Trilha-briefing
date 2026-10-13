"""Linha de comando do trilha-briefing.

    python -m trilha_briefing novo <id>                       cria clientes/<id>/ a partir do modelo
    python -m trilha_briefing questionario [--para cliente|reuniao|assessor]   perguntas do briefing
    python -m trilha_briefing questionario --formulario questionario.html [--cliente "Nome"] [--quem-recebe "Davi"]
    python -m trilha_briefing importar-respostas <respostas.json|-> <pasta>   respostas do formulário → pasta do cliente
    python -m trilha_briefing validar <pasta>                 confere o esquema de todos os arquivos
    python -m trilha_briefing lacunas <pasta>                 o que falta por etapa e o que bloqueia a aprovação
    python -m trilha_briefing revisar <pasta>                 avisos críticos (promessa, prova, verba, canais…)
    python -m trilha_briefing economia <pasta>                tetos de custo e verba de validação
    python -m trilha_briefing canais <pasta>                  ordem sugerida de canais × o que está no plano
    python -m trilha_briefing grade <pasta>                   grade públicos × argumentos com códigos
    python -m trilha_briefing plano <pasta> [--sugerir]       plano de campanhas: verba, aprendizado, testes, nomes, fases
    python -m trilha_briefing exportar <pasta> --para trilha|lp|copy [--saida dist]
    python -m trilha_briefing apresentar <pasta> [--saida dist]
    python -m trilha_briefing fechar-ciclo <pasta> --nome 2026-T4   guarda o estado antes da revisão trimestral
    python -m trilha_briefing registrar-resultados <retorno.yaml> <pasta>   o retorno do Trilha-ads nas hipóteses
    python -m trilha_briefing decidir <pasta> <hipotese> validada|refutada|inconclusiva --aprendizado "…"
"""

from __future__ import annotations

import argparse
import shutil
import sys
from datetime import date
from pathlib import Path

from trilha_briefing import campanhas as plano_campanhas
from trilha_briefing import questionario, resultados
from trilha_briefing.questionario import importar as importacao
from trilha_briefing.questionario.formulario import gerar_formulario
from trilha_briefing.apresentar import apresentar
from trilha_briefing.ciclo import fechar_ciclo
from trilha_briefing.canais import recomendacoes_gerais, sugerir
from trilha_briefing.economia import calcular, conversoes_na_validacao
from trilha_briefing.esquema import ErroCliente, carregar_cliente
from trilha_briefing.exportar import exportar_copy, exportar_lp, exportar_trilha
from trilha_briefing.lacunas import bloqueios_aprovacao, lacunas
from trilha_briefing.revisao import avisos_do_plano, revisar

MODELO = Path(__file__).parent / "modelo"


def _brl(v: float) -> str:
    return "R$ " + f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _carregar(pasta: str):
    try:
        return carregar_cliente(pasta)
    except ErroCliente as e:
        print(f"✗ {pasta}: arquivos com erro")
        for arquivo, erro in e.erros.items():
            print(f"\n[{arquivo}]\n{erro}")
        sys.exit(1)


def cmd_novo(a) -> int:
    destino = Path(a.pasta) / a.id
    if destino.exists():
        print(f"✗ {destino} já existe")
        return 1
    shutil.copytree(MODELO, destino)
    briefing = destino / "briefing.yaml"
    briefing.write_text(briefing.read_text(encoding="utf-8").replace("ID_DO_CLIENTE", a.id), encoding="utf-8")
    print(f"✓ {destino} criado. Próximos passos:\n"
          f"  1. python -m trilha_briefing questionario --formulario questionario-{a.id}.html --cliente \"Nome\"\n"
          f"     mande o arquivo (ou o link do formulário publicado) para o cliente responder\n"
          f"  2. python -m trilha_briefing importar-respostas respostas.json {destino}")
    return 0


def cmd_questionario(a) -> int:
    if a.formulario:
        destino = Path(a.formulario)
        destino.write_text(gerar_formulario(a.cliente, a.quem_recebe), encoding="utf-8")
        print(f"✓ {destino}: formulário do cliente ({len(questionario.perguntas('cliente'))} perguntas). Abre em qualquer "
              f"navegador, salva o progresso no aparelho e devolve um arquivo de respostas para importar-respostas.")
        return 0
    print(questionario.gerar(a.cliente, para="assessor" if a.assessor else a.para))
    return 0


def cmd_importar_respostas(a) -> int:
    try:
        # "-": o cliente usou "Copiar respostas" e o texto veio colado (pbpaste | … importar-respostas - <pasta>)
        respostas = importacao.ler_texto(sys.stdin.read()) if a.respostas == "-" else a.respostas
        rel = importacao.importar(respostas, a.pasta)
    except importacao.RespostasInvalidas as e:
        print(f"✗ {e}")
        return 1
    print(importacao.em_texto(rel), end="")
    if not rel.erro:
        print(f"Próximo passo: python -m trilha_briefing lacunas {a.pasta}")
    return 1 if rel.erro else 0


def cmd_validar(a) -> int:
    c = _carregar(a.pasta)
    print(f"✓ {a.pasta}: {len(c.ofertas)} oferta(s), {len(c.pesquisa.personas)} persona(s)")
    if c.ausentes:
        print(f"  ainda não criados: {', '.join(c.ausentes)}")
    return 0


def cmd_lacunas(a) -> int:
    c = _carregar(a.pasta)
    for etapa, faltas in lacunas(c).items():
        print(f"{'✓' if not faltas else '…'} {etapa}")
        for f in faltas:
            print(f"    - {f}")
    bloqueios = bloqueios_aprovacao(c)
    print()
    if bloqueios:
        print("Estratégia NÃO pronta para aprovação:")
        for b in bloqueios:
            print(f"  ✗ {b}")
        return 1
    print("✓ Estratégia pronta para levar ao cliente.")
    return 0


ICONE = {"bloqueia": "✗", "atencao": "⚠", "sugestao": "·"}
ROTULO = {"bloqueia": "Bloqueia", "atencao": "Atenção", "sugestao": "Sugestão"}


def cmd_revisar(a) -> int:
    c = _carregar(a.pasta)
    avisos = revisar(c)
    for nivel in ICONE:
        do_nivel = [av for av in avisos if av.nivel == nivel]
        if do_nivel:
            print(f"{ROTULO[nivel]} ({len(do_nivel)})")
            for av in do_nivel:
                print(f"  {ICONE[nivel]} {av.texto}")
    print(f"{len(avisos)} aviso(s).")
    return 1 if any(av.nivel == "bloqueia" for av in avisos) else 0


def cmd_economia(a) -> int:
    c = _carregar(a.pasta)
    est = c.estrategia
    if est.economia is None:
        print("✗ estrategia.economia não preenchida")
        return 1
    n = calcular(est.economia)
    print(f"Receita por venda:        {_brl(n.receita_bruta)}")
    print(f"CAC máximo:               {_brl(n.cac_max)}")
    for evento, custo in n.custo_max.items():
        marca = "←" if evento == est.metrica_principal else " "
        print(f"  custo máx. {evento:<17} {_brl(custo)} {marca}")
    print(f"Margem/CAC no teto:       {n.ltv_cac_no_teto:.1f}×")
    verba = est.orcamento.verba_mensal
    evento = est.evento_otimizacao or est.metrica_principal
    print(f"Verba/mês para otimizar por cada evento (50 por semana no custo máximo){'' if verba is None else f' — plano: {_brl(verba)}'}:")
    for degrau, v in n.verba_para_otimizar.items():
        ok = "" if verba is None else ("✓" if v <= verba else "✗")
        print(f"  {ok:1} {degrau:<17} {_brl(v)}{'  ← evento de otimização' if degrau == evento else ''}")
    conv = conversoes_na_validacao(est)
    if conv is not None:
        print(f"Validação: {_brl(est.orcamento.verba_validacao)} compram {conv:.0f} {est.metrica_principal} se o custo ficar no teto (menos, se ficar acima)")
    if est.economia.estimados:
        print(f"Estimados (trocar por dado real): {', '.join(est.economia.estimados)}")
    return 0


def cmd_canais(a) -> int:
    c = _carregar(a.pasta)
    for r in recomendacoes_gerais(c):
        print(f"• {r}")
    print()
    for i, s in enumerate(sugerir(c), start=1):
        no_plano = f"[{s.no_plano}]" if s.no_plano else "[fora do plano]"
        print(f"{i:>2}. {s.canal:<30} {no_plano:<15} {s.motivo}")
        for o in s.observacoes:
            print(f"      - {o}")
    return 0


def cmd_plano(a) -> int:
    c = _carregar(a.pasta)
    regras = plano_campanhas.regras_do_plano(c.campanhas)
    if a.sugerir:
        destino = Path(a.pasta) / "campanhas.yaml"
        if destino.exists():
            print(f"✗ {destino} já existe; para ver a sugestão sem gravar, apague ou renomeie o arquivo atual")
            return 1
        destino.write_text(plano_campanhas.sugestao_em_yaml(c, plano_campanhas.sugerir(c, regras)), encoding="utf-8")
        carregar_cliente(a.pasta)  # a sugestão precisa passar na validação
        print(f"✓ {destino} (sugestão: revise públicos, palavras-chave, verbas e o método de cada teste)")
        return 0
    if not c.campanhas.campanhas:
        print(f"✗ sem campanhas.yaml: python -m trilha_briefing plano {a.pasta} --sugerir")
        return 1
    print(plano_campanhas.em_texto(c, regras))
    avisos = avisos_do_plano(c)
    for x in avisos:
        print(f"{ICONE[x.nivel]} {x.texto}")
    return 1 if any(x.nivel == "bloqueia" for x in avisos) else 0


def cmd_grade(a) -> int:
    c = _carregar(a.pasta)
    grade = c.estrategia.grade
    if not grade:
        print("✗ estrategia.grade vazia")
        return 1
    publicos = list(dict.fromkeys(x.publico for x in grade))
    argumentos = list(dict.fromkeys(x.argumento for x in grade))
    largura = max(len(p) for p in publicos) + 2
    print(" " * largura + " | ".join(f"{f'A{i + 1}':<11}" for i in range(len(argumentos))))
    for p in publicos:
        celulas = []
        for arg in argumentos:
            x = next((g for g in grade if g.publico == p and g.argumento == arg), None)
            celulas.append(f"{f'{x.codigo}({x.prioridade})' if x else '—':<11}")
        print(f"{p:<{largura}}" + " | ".join(celulas))
    print()
    for i, arg in enumerate(argumentos, start=1):
        print(f"A{i}: {arg}")
    print("\n(n) = prioridade: 1 produz primeiro")
    return 0


def cmd_exportar(a) -> int:
    c = _carregar(a.pasta)
    if a.para == "trilha":
        for caminho in exportar_trilha(c, a.saida):
            print(f"✓ {caminho}")
        return 0
    if a.para == "copy":
        print(f"✓ {exportar_copy(c, a.saida)}")
        return 0
    origens = (a.origem,) if a.origem else ("meta", "google")
    for caminho, pend in exportar_lp(c, a.saida, a.oferta, origens):
        print(f"{'✓' if not pend else '…'} {caminho}")
        for p in pend:
            print(f"    - {p}")
    return 0


def cmd_apresentar(a) -> int:
    c = _carregar(a.pasta)
    print(f"✓ {apresentar(c, a.saida)}")
    return 0


def cmd_fechar_ciclo(a) -> int:
    try:
        destino = fechar_ciclo(a.pasta, a.nome)
    except ErroCliente as e:
        print(f"✗ {a.pasta}: arquivos com erro; corrija antes de fechar o ciclo\n{e}")
        return 1
    except (ValueError, FileExistsError) as e:
        print(f"✗ {e}")
        return 1
    print(f"✓ {destino} (cópia dos arquivos + resumo.md). Agora revise o plano com os dados do ciclo.")
    return 0


def cmd_registrar_resultados(a) -> int:
    try:
        rel = resultados.registrar(a.retorno, a.pasta)
    except resultados.RetornoInvalido as e:
        print(f"✗ {e}")
        return 1
    print(resultados.em_texto(rel), end="")
    return 1 if rel.erro else 0


def cmd_decidir(a) -> int:
    try:
        mudou = resultados.decidir(a.pasta, a.hipotese, a.resultado, a.aprendizado or "", a.fim)
    except ValueError as e:
        print(f"✗ {e}")
        return 1
    print("✓ " + "; ".join(mudou))
    print(f"Próximo passo: python -m trilha_briefing exportar {a.pasta} --para copy (o aprendizado vai para a copy)")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="trilha_briefing", description="Briefing, marca e estratégia por cliente")
    sub = ap.add_subparsers(dest="comando", required=True)
    s = sub.add_parser("novo"); s.add_argument("id"); s.add_argument("--pasta", default="clientes"); s.set_defaults(f=cmd_novo)
    s = sub.add_parser("questionario"); s.add_argument("--cliente", default="")
    s.add_argument("--para", choices=["cliente", "reuniao", "assessor"], default="cliente")
    s.add_argument("--assessor", action="store_true", help="o mesmo que --para assessor")
    s.add_argument("--formulario", metavar="ARQUIVO.html", help="gera o formulário do cliente (★) num HTML só")
    s.add_argument("--quem-recebe", default="a sua assessoria", help="para quem o cliente envia as respostas")
    s.set_defaults(f=cmd_questionario)
    s = sub.add_parser("importar-respostas", help="leva as respostas do formulário para a pasta do cliente")
    s.add_argument("respostas", help="arquivo .json baixado do formulário, ou - para colar o texto copiado")
    s.add_argument("pasta"); s.set_defaults(f=cmd_importar_respostas)
    for nome, f in (("validar", cmd_validar), ("lacunas", cmd_lacunas), ("revisar", cmd_revisar),
                    ("economia", cmd_economia), ("canais", cmd_canais), ("grade", cmd_grade)):
        s = sub.add_parser(nome); s.add_argument("pasta"); s.set_defaults(f=f)
    s = sub.add_parser("plano"); s.add_argument("pasta")
    s.add_argument("--sugerir", action="store_true", help="grava um rascunho de campanhas.yaml a partir da estratégia")
    s.set_defaults(f=cmd_plano)
    s = sub.add_parser("exportar"); s.add_argument("pasta"); s.add_argument("--para", choices=["trilha", "lp", "copy"], required=True)
    s.add_argument("--saida", default="dist"); s.add_argument("--oferta"); s.add_argument("--origem", choices=["meta", "google"])
    s.set_defaults(f=cmd_exportar)
    s = sub.add_parser("fechar-ciclo"); s.add_argument("pasta"); s.add_argument("--nome", required=True)
    s.set_defaults(f=cmd_fechar_ciclo)
    s = sub.add_parser("apresentar"); s.add_argument("pasta"); s.add_argument("--saida", default="dist"); s.set_defaults(f=cmd_apresentar)
    s = sub.add_parser("registrar-resultados", help="o retorno do Trilha-ads (ads/<id>/retornos) nas hipóteses")
    s.add_argument("retorno"); s.add_argument("pasta"); s.set_defaults(f=cmd_registrar_resultados)
    s = sub.add_parser("decidir", help="registra a decisão sobre uma hipótese, com o aprendizado")
    s.add_argument("pasta"); s.add_argument("hipotese"); s.add_argument("resultado", choices=resultados.DECISOES)
    s.add_argument("--aprendizado", help="o que aprendemos: vai para a copy e para a próxima rodada")
    s.add_argument("--fim", type=date.fromisoformat, help="data da decisão (padrão: hoje)")
    s.set_defaults(f=cmd_decidir)
    a = ap.parse_args(argv)
    return a.f(a)


if __name__ == "__main__":
    sys.exit(main())
