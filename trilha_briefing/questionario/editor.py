"""Preenche um campo de um YAML comentado sem reescrever o resto do arquivo.

Os arquivos do cliente nascem dos modelos comentados (trilha_briefing/modelo/). Reescrever com um dumper apagaria os
comentários que explicam cada campo, então a edição é por linha:

- a chave está escrita em bloco → troca só o valor e mantém o comentário da linha;
- a chave está dentro de um mapa em linha (`historia: { catalisador: "" }`) ou o pai está vazio (`economia: null`)
  → reescreve só aquela linha, ainda em linha;
- a chave não está escrita → acrescenta no fim do bloco do pai (ou do arquivo).

Só preenche campo vazio (ou ainda com o valor do modelo); campo já preenchido não é tocado e volta como conflito.
Com um `validador` (o modelo pydantic do arquivo), cada mudança é conferida na hora: se o arquivo ficaria inválido,
só aquela mudança é desfeita e volta como inválida, com o motivo.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

VAZIOS = (None, "", "PREENCHER", "nao_sei", [], {})


def _significativa(linha: str) -> bool:
    s = linha.strip()
    return bool(s) and not s.startswith("#")


def _indent(linha: str) -> int:
    return len(linha) - len(linha.lstrip(" "))


def _eh_chave(linha: str, parte: str) -> bool:
    return bool(re.match(rf"{re.escape(parte)}\s*:(\s|$)", linha.lstrip()))


@dataclass
class Posicao:
    escritas: int  # quantas partes do caminho estão escritas como chave em bloco
    linha: int | None  # linha da última chave achada
    em_linha: bool  # a última chave achada tem o valor na própria linha (sem filhos em bloco)
    nivel_filhos: int  # indentação dos filhos (para acrescentar)
    depois_de: int  # onde acrescentar: depois da última linha significativa do bloco


def caminhar(linhas: list[str], partes: tuple[str, ...]) -> Posicao:
    inicio, fim, nivel, achou = 0, len(linhas), 0, None
    ultimo = max((j for j in range(len(linhas)) if _significativa(linhas[j])), default=-1) + 1
    for k, parte in enumerate(partes):
        i = next((i for i in range(inicio, fim)
                  if _significativa(linhas[i]) and _indent(linhas[i]) == nivel and _eh_chave(linhas[i], parte)), None)
        if i is None:
            return Posicao(k, achou, False, nivel, ultimo)
        achou = i
        filhos = [j for j in range(i + 1, fim) if _significativa(linhas[j])]
        if not filhos or _indent(linhas[filhos[0]]) <= nivel:
            return Posicao(k + 1, i, True, nivel + 2, i + 1)
        nivel_filho = _indent(linhas[filhos[0]])
        do_bloco = [j for j in filhos if _indent(linhas[j]) > nivel]
        fim = next((j for j in filhos if _indent(linhas[j]) <= nivel), fim)
        do_bloco = [j for j in do_bloco if j < fim]
        inicio, nivel, ultimo = i + 1, nivel_filho, do_bloco[-1] + 1
    return Posicao(len(partes), achou, True, nivel, ultimo)


def localizar(linhas: list[str], partes: tuple[str, ...]) -> int | None:
    """Índice da linha da última chave do caminho, ou None se o caminho não estiver escrito em bloco."""
    pos = caminhar(linhas, partes)
    return pos.linha if pos.escritas == len(partes) else None


def _valor_e_comentario(resto: str) -> tuple[str, str]:
    """Separa '"texto"   # comentário' em (valor, comentário), respeitando aspas."""
    aspas = None
    for i, ch in enumerate(resto):
        if ch in "\"'" and aspas is None:
            aspas = ch
        elif ch == aspas:
            aspas = None
        elif ch == "#" and aspas is None and (i == 0 or resto[i - 1] in " \t"):
            return resto[:i].rstrip(), resto[i:]
    return resto.rstrip(), ""


PALAVRAS_YAML = {"y", "n", "yes", "no", "on", "off", "true", "false", "null"}


def _escalar(v: Any) -> str:
    if isinstance(v, str):
        if re.fullmatch(r"[a-z][a-z0-9_-]*", v) and v not in PALAVRAS_YAML:
            return v  # identificador simples (rodando, venda_direta) fica sem aspas, como no resto do arquivo
        return json.dumps(v, ensure_ascii=False)  # string JSON é escalar YAML válido
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    return f"{v:g}" if isinstance(v, float) else str(v)


def _fluxo(v: Any) -> str:
    """Valor em estilo de fluxo (uma linha): { a: 1, b: [x, y] }."""
    if isinstance(v, dict):
        return "{ " + ", ".join(f"{k}: {_fluxo(x)}" for k, x in v.items()) + " }" if v else "{}"
    if isinstance(v, list):
        return "[" + ", ".join(_fluxo(x) for x in v) + "]"
    return _escalar(v)


def _novas(partes: tuple[str, ...], valor: Any, nivel: int) -> list[str]:
    """As linhas de `a:\\n  b: valor` a partir de `nivel`."""
    linhas = [f"{' ' * (nivel + 2 * d)}{p}:" for d, p in enumerate(partes[:-1])]
    ind = " " * (nivel + 2 * (len(partes) - 1))
    if isinstance(valor, list):
        return linhas + [f"{ind}{partes[-1]}:"] + [f"{ind}  - {_fluxo(x)}" for x in valor]
    return linhas + [f"{ind}{partes[-1]}: {_escalar(valor)}"]


def _erros(validador: type[BaseModel] | None, dados: Any) -> dict[tuple, str]:
    """Erros de validação por (local, tipo) → mensagem; vazio quando válido ou sem validador."""
    if validador is None:
        return {}
    try:
        validador.model_validate(dados)
    except ValidationError as e:
        return {(tuple(erro["loc"]), erro["type"]): f"{'.'.join(str(x) for x in erro['loc'])}: {erro['msg']}"
                for erro in e.errors()}
    return {}


class Arquivo:
    """Um YAML do cliente aberto para preencher campos."""

    def __init__(self, caminho: Path, modelo: Path | None = None, validador: type[BaseModel] | None = None):
        self.caminho = caminho
        self.original = caminho.read_text(encoding="utf-8")
        self.linhas = self.original.splitlines()
        self.dados = yaml.safe_load(self.original) or {}
        self.modelo = (yaml.safe_load(modelo.read_text(encoding="utf-8")) or {}) if modelo and modelo.exists() else {}
        self.validador = validador
        self.ja_invalido = _erros(validador, self.dados)  # erros de antes não são culpa do preenchimento
        self.motivo = ""  # por que a última mudança não entrou

    @staticmethod
    def _pegar(dados: Any, partes: tuple[str, ...]) -> Any:
        for p in partes:
            if not isinstance(dados, dict) or p not in dados:
                return None
            dados = dados[p]
        return dados

    def atual(self, partes: tuple[str, ...]) -> Any:
        return self._pegar(self.dados, partes)

    def vazio(self, partes: tuple[str, ...]) -> bool:
        v = self.atual(partes)
        return v in VAZIOS or (self.modelo and v == self._pegar(self.modelo, partes))

    def _aplicar(self, novas_linhas: list[str]) -> str:
        """Troca as linhas, conferindo que o YAML continua legível e, com validador, que não surge erro novo."""
        try:
            dados = yaml.safe_load("\n".join(novas_linhas) + "\n") or {}
        except yaml.YAMLError as e:
            self.motivo = f"o arquivo ficaria ilegível ({e})"
            return "invalido"
        novos = {k: m for k, m in _erros(self.validador, dados).items() if k not in self.ja_invalido}
        if novos:
            faltam = [k[0] for k in novos if k[1] == "missing"]
            if faltam and len(faltam) == len(novos) and len({c[:-1] for c in faltam}) == 1:
                bloco, campos = ".".join(map(str, faltam[0][:-1])), ", ".join(str(c[-1]) for c in faltam)
                self.motivo = (f"o bloco {bloco} só vale completo (falta {campos}); monte o bloco à mão com esta "
                               "resposta como ponto de partida")
            else:
                self.motivo = "; ".join(novos.values())
            return "invalido"
        self.linhas, self.dados, self.motivo = novas_linhas, dados, ""
        return "preenchido"

    def preencher(self, partes: tuple[str, ...], valor: Any) -> str:
        """'preenchido', 'conflito' (já tinha valor), 'invalido' (motivo em self.motivo) ou 'ausente'."""
        if not self.vazio(partes):
            return "conflito"
        pos = caminhar(self.linhas, partes)
        linhas = list(self.linhas)
        if pos.escritas == len(partes):  # a chave está escrita: troca o valor
            linha = linhas[pos.linha]
            chave, _, resto = linha.partition(":")
            _, comentario = _valor_e_comentario(resto)
            sufixo = f"  {comentario}" if comentario else ""
            if isinstance(valor, list):
                novas = [f"{chave}:{sufixo}"] + [f"{' ' * (_indent(linha) + 2)}- {_fluxo(x)}" for x in valor]
            else:
                novas = [f"{chave}: {_escalar(valor)}{sufixo}"]
            linhas[pos.linha:pos.linha + 1] = novas
        elif pos.linha is not None and pos.em_linha:  # o pai tem o valor na linha: mapa em linha, {} ou null
            linha = linhas[pos.linha]
            chave, _, resto = linha.partition(":")
            texto, comentario = _valor_e_comentario(resto)
            try:
                atual = yaml.safe_load(texto) if texto.strip() else None
            except yaml.YAMLError:
                return "ausente"
            atual = {} if atual is None else atual
            alvo = atual
            for p in partes[pos.escritas:-1]:
                alvo = alvo.setdefault(p, {}) if isinstance(alvo, dict) else None
            if not isinstance(alvo, dict):
                return "ausente"
            alvo[partes[-1]] = valor
            linhas[pos.linha] = f"{chave}: {_fluxo(atual)}" + (f"  {comentario}" if comentario else "")
        else:  # a chave não está escrita: acrescenta no fim do bloco do pai
            linhas[pos.depois_de:pos.depois_de] = _novas(partes[pos.escritas:], valor, pos.nivel_filhos)
        return self._aplicar(linhas)

    def definir_no_item(self, lista: str, id_item: str, campo: str, valor: Any) -> str:
        """Define `campo` no item da lista de topo `lista` cujo id é `id_item`, sobrescrevendo (é registro explícito,
        não preenchimento): 'preenchido', 'invalido' (motivo em self.motivo) ou 'ausente' (lista, item ou formato
        que não dá para editar por linha, como item em uma linha só)."""
        topo = localizar(self.linhas, (lista,))
        if topo is None:
            return "ausente"
        cabeca = re.compile(rf"^(\s*)-\s+id:\s*[\"']?{re.escape(id_item)}[\"']?\s*(#.*)?$")
        inicio = next((i for i in range(topo + 1, len(self.linhas)) if cabeca.match(self.linhas[i])), None)
        if inicio is None:
            return "ausente"
        traco = len(cabeca.match(self.linhas[inicio]).group(1))
        nivel = traco + 2
        fim = next((j for j in range(inicio + 1, len(self.linhas)) if _significativa(self.linhas[j])
                    and _indent(self.linhas[j]) <= traco), len(self.linhas))
        linhas = list(self.linhas)
        alvo = next((j for j in range(inicio + 1, fim) if _indent(linhas[j]) == nivel and _eh_chave(linhas[j], campo)), None)
        nova = f"{' ' * nivel}{campo}: {_escalar(valor)}"
        if alvo is None:
            ultima = max(j for j in range(inicio, fim) if _significativa(linhas[j]))
            linhas.insert(ultima + 1, nova)
        else:
            _, _, resto = linhas[alvo].partition(":")
            texto, comentario = _valor_e_comentario(resto)
            continua = alvo + 1  # valor em bloco (| ou >) ocupa as linhas mais recuadas que seguem
            if texto.strip()[:1] in ("|", ">"):
                while continua < fim and (not linhas[continua].strip() or _indent(linhas[continua]) > nivel):
                    continua += 1
            linhas[alvo:continua] = [nova + (f"  {comentario}" if comentario and texto.strip()[:1] not in ("|", ">") else "")]
        return self._aplicar(linhas)

    def acrescentar(self, partes: tuple[str, ...], item: Any) -> str:
        """Acrescenta um item a uma lista escrita em fluxo ([a, b]); 'ja_tinha', 'acrescentado' ou 'ausente'."""
        i = localizar(self.linhas, partes)
        atual = self.atual(partes)
        if i is None or not isinstance(atual, list):
            return "ausente"
        if item in atual:
            return "ja_tinha"
        chave, _, resto = self.linhas[i].partition(":")
        valor, comentario = _valor_e_comentario(resto)
        if not valor.strip().startswith("["):
            return "ausente"  # lista em bloco: não mexe
        sufixo = f"  {comentario}" if comentario else ""
        linhas = list(self.linhas)
        linhas[i] = f"{chave}: [{', '.join(_escalar(x) if not isinstance(x, str) else x for x in [*atual, item])}]{sufixo}"
        return "acrescentado" if self._aplicar(linhas) == "preenchido" else "ausente"

    def gravar(self) -> None:
        self.caminho.write_text("\n".join(self.linhas) + "\n", encoding="utf-8")

    def desfazer(self) -> None:
        self.caminho.write_text(self.original, encoding="utf-8")
