"""Importa as respostas do formulário para a pasta do cliente.

1. Guarda as respostas como vieram, em `respostas/<data>-questionario.json` e uma versão legível `.md`: é a fonte
   das afirmações com `fonte: empresa`, e fica no Trilha-clientes junto com o resto do cliente.
2. Preenche sozinho os campos simples (texto, número, escolha, listas) dos arquivos de uma instância só (briefing,
   pesquisa, plataforma, estratégia), sem reescrever o arquivo: só campo vazio ou ainda com o valor do modelo.
   Afirmações entram como hipótese (`fonte: empresa`, `status: hipotese`): é o que a empresa diz, não o que se provou.
3. Valida a pasta inteira; se algo ficar inválido, desfaz tudo.
4. Devolve o que entrou, o que já tinha valor (conflito, o assessor decide) e o que precisa ser levado à mão.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from trilha_briefing.esquema import ErroCliente, carregar_cliente
from trilha_briefing.questionario import Pergunta, Questionario, carregar
from trilha_briefing.questionario.campos import ARQUIVO_DE, MODELOS as VALIDADORES, Campo
from trilha_briefing.questionario.editor import Arquivo

MODELOS = Path(__file__).resolve().parent.parent / "modelo"
FORMULARIO = "trilha-briefing"


class RespostasInvalidas(ValueError):
    pass


@dataclass
class Relatorio:
    guardadas: list[Path] = field(default_factory=list)
    preenchidos: list[tuple[str, str]] = field(default_factory=list)  # (pergunta, campo)
    conflitos: list[tuple[str, str, Any, Any]] = field(default_factory=list)  # (pergunta, campo, atual, resposta)
    levar: dict[str, list[tuple[Pergunta, Any, str]]] = field(default_factory=dict)  # destino → [(pergunta, resposta, motivo)]
    nao_sei: list[str] = field(default_factory=list)
    desconhecidas: list[str] = field(default_factory=list)
    versao_diferente: str | None = None
    erro: str | None = None


def ler_texto(texto: str, origem: str = "texto colado") -> dict:
    """As respostas a partir do texto do arquivo, ou do que o cliente copiou e colou na conversa."""
    texto = texto.strip()
    inicio, fim = texto.find("{"), texto.rfind("}")  # tolera texto antes/depois do JSON (saudação, assinatura)
    try:
        dados = json.loads(texto[inicio:fim + 1] if inicio >= 0 else texto)
    except json.JSONDecodeError as e:
        raise RespostasInvalidas(f"{origem}: não é um arquivo de respostas ({e})") from e
    if not isinstance(dados, dict) or dados.get("formulario") != FORMULARIO or not isinstance(dados.get("respostas"), dict):
        raise RespostasInvalidas(f"{origem}: não é um arquivo de respostas do formulário do Trilha-briefing")
    return dados


def ler(caminho: str | Path) -> dict:
    try:
        texto = Path(caminho).read_text(encoding="utf-8")
    except OSError as e:
        raise RespostasInvalidas(f"{caminho}: não deu para ler ({e})") from e
    return ler_texto(texto, str(caminho))


def _vazio(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip()) or v == []


def _numero(texto: Any) -> float:
    """'1.200,50', 'R$ 1200', '35%' → número. Faixas ('10 a 20') e texto não viram número."""
    if isinstance(texto, (int, float)):
        return float(texto)
    s = re.sub(r"[R$%\s]", "", str(texto))
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", s) or re.fullmatch(r"\d+,\d+", s):
        s = s.replace(".", "").replace(",", ".")
    if not re.fullmatch(r"-?\d+(\.\d+)?", s):
        raise ValueError(f"'{texto}' não é um número")
    return float(s)


def _linhas(v: Any) -> list[str]:
    itens = v if isinstance(v, list) else str(v).splitlines()
    return [str(x).strip(" -•\t") for x in itens if str(x).strip(" -•\t")]


def telefone(valor: Any) -> str:
    """'(11) 98765-4321' → '5511987654321'. Só número brasileiro com DDD; o resto fica para o assessor."""
    digitos = re.sub(r"\D", "", str(valor))
    if len(digitos) in (10, 11):
        digitos = "55" + digitos
    if not re.fullmatch(r"55\d{10,11}", digitos):
        raise ValueError(f"'{valor}' não parece um telefone com DDD")
    return digitos


def converter(p: Pergunta, campo: Campo, valor: Any) -> Any:
    """A resposta no formato do campo, conferida contra as regras dele. ValueError quando não dá com segurança."""
    return campo.validar(_converter(p, campo, valor))


def _converter(p: Pergunta, campo: Campo, valor: Any) -> Any:
    tipo = campo.tipo_simples
    if p.tipo == "telefone" and tipo == "texto":
        return telefone(valor)
    if tipo == "texto":
        return "; ".join(_linhas(valor)) if isinstance(valor, list) else str(valor).strip()
    if tipo in ("inteiro", "numero"):
        n = _numero(valor)
        if p.tipo == "porcentagem" and n > 1:
            n = n / 100
        if tipo == "inteiro":
            if n != int(n):
                raise ValueError(f"'{valor}' não é inteiro")
            return int(n)
        return n
    if tipo == "booleano":
        if str(valor).lower() in ("sim", "true", "1"):
            return True
        if str(valor).lower() in ("nao", "não", "false", "0"):
            return False
        raise ValueError(f"'{valor}' não é sim ou não")
    if tipo == "escolha":
        if str(valor) not in campo.valores:
            raise ValueError(f"'{valor}' não é uma das opções do campo ({', '.join(campo.valores)})")
        return str(valor)
    if tipo == "lista_texto":
        return _linhas(valor)
    if tipo == "lista_item":
        return [{"texto": x, "fonte": "empresa", "status": "hipotese"} for x in _linhas(valor)]
    raise ValueError("campo sem preenchimento automático")


def _texto(valor: Any, p: Pergunta | None = None) -> str:
    rotulos = {o.valor: o.rotulo for o in p.opcoes} | {"sim": "Sim", "nao": "Não"} if p else {}
    if isinstance(valor, list):
        return "\n".join(f"- {rotulos.get(x, x)}" for x in valor)
    return str(rotulos.get(valor, valor))


def _uma_linha(valor: Any, p: Pergunta | None = None, limite: int = 200) -> str:
    """A resposta numa linha só, para o relatório no terminal (o .md guardado tem a resposta inteira)."""
    texto = " · ".join(x.removeprefix("- ") for x in _texto(valor, p).splitlines() if x.strip())
    return texto if len(texto) <= limite else texto[:limite - 1] + "…"


def legivel(q: Questionario, dados: dict) -> str:
    respostas, nao_sei = dados["respostas"], set(dados.get("nao_sei", []))
    linhas = [f"# Respostas do questionário — {dados.get('cliente', '')}", "",
              f"Preenchido em {dados.get('preenchido_em', '—')} · versão {dados.get('versao', '—')}", ""]
    for bloco in q.blocos:
        ps = [p for p in q.do_momento("cliente") if p.bloco == bloco.id and (p.id in respostas or p.id in nao_sei)]
        if not ps:
            continue
        linhas += [f"## {bloco.titulo}", ""]
        for p in ps:
            resposta = "_não sei / prefiro falar na reunião_" if p.id in nao_sei else _texto(respostas[p.id], p)
            linhas += [f"**{p.pergunta}**", "", resposta, ""]
    return "\n".join(linhas) + "\n"


def _guardar(pasta: Path, dados: dict, q: Questionario, hoje: date) -> list[Path]:
    destino = pasta / "respostas"
    destino.mkdir(exist_ok=True)
    base, n = f"{hoje.isoformat()}-questionario", 1
    while (destino / f"{base}.json").exists():
        n += 1
        base = f"{hoje.isoformat()}-questionario-{n}"
    js, md = destino / f"{base}.json", destino / f"{base}.md"
    js.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md.write_text(legivel(q, dados), encoding="utf-8")
    return [js, md]


def importar(respostas: str | Path | dict, pasta: str | Path, hoje: date | None = None) -> Relatorio:
    """`respostas`: o caminho do arquivo baixado do formulário, ou o dicionário já lido (ler_texto)."""
    pasta, hoje, q = Path(pasta), hoje or date.today(), carregar()
    if not (pasta / "briefing.yaml").exists():
        raise RespostasInvalidas(f"{pasta}: não é a pasta de um cliente (crie com: python -m trilha_briefing novo <id>)")
    dados = respostas if isinstance(respostas, dict) else ler(respostas)
    rel = Relatorio()
    if dados.get("versao") != q.versao:
        rel.versao_diferente = str(dados.get("versao"))
    abertos: dict[str, Arquivo] = {}
    for pid, valor in dados["respostas"].items():
        p = q.pergunta(pid)
        if p is None:
            rel.desconhecidas.append(pid)
            continue
        if _vazio(valor):
            continue
        campo = p.destino
        destino_texto = ARQUIVO_DE.get(campo.arquivo, "ofertas/<id>.yaml") if campo else "anotações do assessor"
        caminho = pasta / ARQUIVO_DE[campo.arquivo] if campo and campo.arquivo in ARQUIVO_DE else None
        if campo and campo.preenche_sozinho and caminho and caminho.exists():
            try:
                convertido = converter(p, campo, valor)
            except ValueError as e:
                rel.levar.setdefault(destino_texto, []).append((p, valor, str(e)))
                continue
            if campo.arquivo not in abertos:
                abertos[campo.arquivo] = Arquivo(caminho, MODELOS / ARQUIVO_DE[campo.arquivo], VALIDADORES[campo.arquivo])
            arq = abertos[campo.arquivo]
            atual = arq.atual(campo.partes)
            resultado = arq.preencher(campo.partes, convertido)
            if resultado == "preenchido":
                rel.preenchidos.append((p.id, p.campo))
            elif resultado == "conflito":
                rel.conflitos.append((p.id, p.campo, atual, valor))
            else:
                motivo = arq.motivo if resultado == "invalido" else "não deu para achar o campo no arquivo"
                rel.levar.setdefault(destino_texto, []).append((p, valor, motivo))
        else:
            rel.levar.setdefault(destino_texto, []).append((p, valor, ""))
    rel.nao_sei = [x for x in dados.get("nao_sei", []) if q.pergunta(x)]
    briefing = abertos.setdefault("briefing", Arquivo(pasta / "briefing.yaml", MODELOS / "briefing.yaml",
                                                      VALIDADORES["briefing"]))
    if briefing.vazio(("data",)):
        briefing.preencher(("data",), hoje.isoformat())
    briefing.acrescentar(("preenchido_por",), "cliente")
    for arq in abertos.values():
        arq.gravar()
    try:
        carregar_cliente(pasta)
    except ErroCliente as e:
        for arq in abertos.values():
            arq.desfazer()
        rel.erro = str(e)
        return rel
    rel.guardadas = _guardar(pasta, dados, q, hoje)
    return rel


def em_texto(rel: Relatorio) -> str:
    if rel.erro:
        return f"✗ nada foi gravado: a pasta ficaria inválida.\n{rel.erro}\n"
    linhas = []
    if rel.versao_diferente:
        linhas.append(f"⚠ respostas da versão {rel.versao_diferente} do questionário; as perguntas foram casadas pelo id")
    linhas += [f"✓ respostas guardadas: {', '.join(str(p) for p in rel.guardadas)}",
               f"✓ {len(rel.preenchidos)} campo(s) preenchido(s) sozinho(s) (fonte: empresa, status: hipótese)"]
    linhas += [f"    {campo}" for _, campo in rel.preenchidos]
    if rel.conflitos:
        linhas.append(f"⚠ {len(rel.conflitos)} campo(s) já tinham valor e não foram tocados:")
        linhas += [f"    {campo}: atual {atual!r} · resposta {_uma_linha(resp)!r}" for _, campo, atual, resp in rel.conflitos]
    if rel.levar:
        linhas.append("… levar à mão:")
        for destino, itens in rel.levar.items():
            linhas.append(f"  {destino}")
            for p, valor, motivo in itens:
                linhas.append(f"    · {p.pergunta}" + (f"  [não entrou sozinho: {motivo}]" if motivo else ""))
                linhas.append(f"      → {p.onde()}: {_uma_linha(valor, p)}")
    if rel.nao_sei:
        linhas.append(f"· para a reunião (o cliente marcou \"não sei\"): {', '.join(rel.nao_sei)}")
    if rel.desconhecidas:
        linhas.append(f"⚠ respostas de perguntas que não existem mais: {', '.join(rel.desconhecidas)}")
    return "\n".join(linhas) + "\n"

