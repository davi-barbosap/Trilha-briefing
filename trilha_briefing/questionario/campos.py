"""Caminhos de campo ("briefing.negocio.o_que_vende") contra o esquema: existem? que tipo têm? dá para preencher sozinho?

Sintaxe: `<arquivo>.<campo>.<campo>…`, em que arquivo é um dos de esquema.ARQUIVOS (briefing, pesquisa, plataforma,
provas, estrategia, hipoteses, campanhas) ou `ofertas` (uma oferta). `[]` depois de um campo entra no item da lista:
`pesquisa.personas[].dores`.
"""

from __future__ import annotations

import types
import typing
from dataclasses import dataclass
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.fields import FieldInfo

from trilha_briefing import esquema

MODELOS: dict[str, type[BaseModel]] = {chave: modelo for chave, (_, modelo) in esquema.ARQUIVOS.items()}
MODELOS["ofertas"] = esquema.Oferta
ARQUIVO_DE = {chave: nome for chave, (nome, _) in esquema.ARQUIVOS.items()}
PREENCHE_SOZINHO = {"briefing", "plataforma", "estrategia", "pesquisa"}  # arquivos de uma instância só, no modelo comentado


class CampoInvalido(ValueError):
    pass


def _sem_annotated(t: Any) -> Any:
    while typing.get_origin(t) is Annotated:
        t = typing.get_args(t)[0]
    return t


def _sem_none(t: Any) -> tuple[Any, bool]:
    """(tipo sem None, aceita None?)"""
    t = _sem_annotated(t)
    origem = typing.get_origin(t)
    if origem in (Union, types.UnionType):
        args = [a for a in typing.get_args(t) if a is not type(None)]
        if len(args) == 1:
            return _sem_annotated(args[0]), True
    return t, False


@dataclass(frozen=True)
class Campo:
    caminho: str
    arquivo: str  # chave: briefing, ofertas…
    partes: tuple[str, ...]  # sem o arquivo; "[]" já tirado
    tipo: Any  # anotação final, sem Annotated e sem None
    opcional: bool
    dentro_de_lista: bool  # o caminho passa por um []
    info: FieldInfo | None = None  # regras do campo (padrão, mínimo…) para validar a resposta antes de gravar

    @property
    def tipo_simples(self) -> str | None:
        """texto, numero, inteiro, booleano, escolha, lista_texto, lista_item; None quando é estrutura."""
        t = self.tipo
        if t is str:
            return "texto"
        if t is int:
            return "inteiro"
        if t is float:
            return "numero"
        if t is bool:
            return "booleano"
        if typing.get_origin(t) is Literal:
            return "escolha"
        if typing.get_origin(t) is list:
            item = _sem_annotated(typing.get_args(t)[0])
            if item is str:
                return "lista_texto"
            if item is esquema.Item:
                return "lista_item"
        return None

    @property
    def valores(self) -> tuple[str, ...]:
        return typing.get_args(self.tipo) if typing.get_origin(self.tipo) is Literal else ()

    def validar(self, valor: Any) -> Any:
        """O valor como o esquema aceita, ou ValueError com o motivo (ex.: WhatsApp fora do padrão)."""
        if self.info is None or self.dentro_de_lista:
            return valor
        try:
            tipo = Annotated[(self.info.annotation, *self.info.metadata)] if self.info.metadata else self.info.annotation
            return TypeAdapter(tipo).validate_python(valor)
        except ValidationError as e:
            raise ValueError("; ".join(erro["msg"] for erro in e.errors())) from e

    @property
    def preenche_sozinho(self) -> bool:
        return self.arquivo in PREENCHE_SOZINHO and not self.dentro_de_lista and self.tipo_simples is not None


def resolver(caminho: str) -> Campo:
    arquivo, _, resto = caminho.partition(".")
    if arquivo not in MODELOS or not resto:
        raise CampoInvalido(f"'{caminho}': comece por um destes arquivos: {', '.join(MODELOS)}")
    modelo: Any = MODELOS[arquivo]
    partes, em_lista, tipo, opcional, info = [], False, None, False, None
    for pedaco in resto.split("."):
        nome, lista = (pedaco[:-2], True) if pedaco.endswith("[]") else (pedaco, False)
        if not (isinstance(modelo, type) and issubclass(modelo, BaseModel)) or nome not in modelo.model_fields:
            raise CampoInvalido(f"'{caminho}': '{nome}' não existe")
        info = modelo.model_fields[nome]
        tipo, opcional = _sem_none(info.annotation)
        partes.append(nome)
        if lista:
            if typing.get_origin(tipo) is not list:
                raise CampoInvalido(f"'{caminho}': '{nome}' não é lista")
            tipo, em_lista = _sem_annotated(typing.get_args(tipo)[0]), True
        modelo = tipo
    return Campo(caminho, arquivo, tuple(partes), tipo, opcional, em_lista, info)
