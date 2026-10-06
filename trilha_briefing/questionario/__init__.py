"""Questionário do briefing: as perguntas ficam em `perguntas.yaml`, editável sem mexer em código.

Três momentos:
    ★ cliente   o cliente responde sozinho, no formulário (python -m trilha_briefing questionario --formulario)
    ● reuniao   aprofundar no kickoff com o dono e com quem atende
    ◆ assessor  o assessor levanta com acessos, dados e escuta

Cada pergunta diz o campo que preenche (`campo`, conferido contra o esquema) ou o que alimenta (`alimenta`).
As respostas do formulário entram no cliente com `importar-respostas` (trilha_briefing/questionario/importar.py).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from trilha_briefing.questionario.campos import Campo, CampoInvalido, resolver

ARQUIVO = Path(__file__).parent / "perguntas.yaml"
Momento = Literal["cliente", "reuniao", "assessor"]
Tipo = Literal["texto_curto", "texto_longo", "numero", "moeda", "porcentagem", "escolha", "multipla", "lista",
               "sim_nao", "link", "telefone"]
SIMBOLO = {"cliente": "★", "reuniao": "●", "assessor": "◆"}


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Opcao(_Base):
    valor: str
    rotulo: str


class Condicao(_Base):
    """A pergunta só aparece se a resposta de outra pergunta estiver entre estes valores."""

    pergunta: str
    em: list[str]


class Bloco(_Base):
    id: str
    titulo: str
    objetivo: str = ""  # por que o bloco importa, numa frase para o cliente
    tempo_min: int | None = None


class Pergunta(_Base):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    momento: Momento
    bloco: str
    pergunta: str
    ajuda: str = ""  # por que perguntamos, ou um exemplo de boa resposta
    tipo: Tipo = "texto_longo"
    opcoes: list[Opcao] = Field(default_factory=list)
    obrigatoria: bool = False
    campo: str = ""  # caminho no esquema que a resposta preenche
    alimenta: str = ""  # quando não há campo direto: o que a resposta alimenta
    condicao: Condicao | None = None

    @model_validator(mode="before")
    @classmethod
    def _opcoes_simples(cls, v):
        if isinstance(v, dict) and v.get("opcoes"):
            v = dict(v, opcoes=[{"valor": o, "rotulo": o} if isinstance(o, str) else o for o in v["opcoes"]])
        return v

    @model_validator(mode="after")
    def _coerente(self) -> Pergunta:
        if self.tipo in ("escolha", "multipla") and not self.opcoes:
            raise ValueError(f"{self.id}: tipo {self.tipo} sem opções")
        if self.campo:
            try:
                campo = resolver(self.campo)
            except CampoInvalido as e:
                raise ValueError(f"{self.id}: {e}") from e
            fora = [o.valor for o in self.opcoes if campo.valores and o.valor not in campo.valores]
            if self.tipo == "escolha" and fora:
                raise ValueError(f"{self.id}: opções {fora} não cabem em {self.campo} ({', '.join(campo.valores)})")
        return self

    def valores(self) -> list[str]:
        """Respostas possíveis de escolha, múltipla e sim/não (vazio para texto livre)."""
        return ["sim", "nao"] if self.tipo == "sim_nao" else [o.valor for o in self.opcoes]

    @property
    def destino(self) -> Campo | None:
        return resolver(self.campo) if self.campo else None

    def onde(self) -> str:
        return f"`{self.campo}`" + (f" ({self.alimenta})" if self.alimenta else "") if self.campo else self.alimenta or "—"


class Questionario(_Base):
    versao: str
    blocos: list[Bloco]
    perguntas: list[Pergunta]
    roteiro_escuta: list[str] = Field(default_factory=list)
    sinais_de_alerta: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _referencias(self) -> Questionario:
        ids = [p.id for p in self.perguntas]
        repetidos = sorted({i for i in ids if ids.count(i) > 1})
        if repetidos:
            raise ValueError(f"ids de pergunta repetidos: {repetidos}")
        blocos = {b.id for b in self.blocos}
        vistas: dict[str, Pergunta] = {}
        for p in self.perguntas:
            if p.bloco not in blocos:
                raise ValueError(f"{p.id}: bloco '{p.bloco}' não existe")
            if p.condicao:
                base = vistas.get(p.condicao.pergunta)
                if base is None:
                    raise ValueError(f"{p.id}: a condição precisa citar uma pergunta que vem antes "
                                     f"('{p.condicao.pergunta}' não existe ou vem depois)")
                if p.momento == "cliente" and base.momento != "cliente":
                    raise ValueError(f"{p.id}: pergunta do formulário condicionada a '{base.id}', que o cliente não vê")
                fora = [v for v in p.condicao.em if base.valores() and v not in base.valores()]
                if fora or not base.valores():
                    raise ValueError(f"{p.id}: a condição usa valores que '{base.id}' não tem: {fora or p.condicao.em}")
            vistas[p.id] = p
        return self

    def do_momento(self, momento: Momento | None = None) -> list[Pergunta]:
        return [p for p in self.perguntas if momento is None or p.momento == momento]

    def pergunta(self, pid: str) -> Pergunta | None:
        return next((p for p in self.perguntas if p.id == pid), None)


@lru_cache(maxsize=4)
def carregar(caminho: str | Path = ARQUIVO) -> Questionario:
    return Questionario.model_validate(yaml.safe_load(Path(caminho).read_text(encoding="utf-8")))


def perguntas(momento: Momento | None = None) -> list[Pergunta]:
    return carregar().do_momento(momento)


def gerar(nome_cliente: str = "", assessor: bool = False, para: Momento = "cliente") -> str:
    """O questionário em Markdown: para o cliente (★), roteiro da reunião (★ + ●) ou completo, com os campos."""
    q = carregar()
    para = "assessor" if assessor else para
    titulo = {"cliente": "Questionário de início", "reuniao": "Roteiro do kickoff", "assessor": "Briefing completo"}[para]
    linhas = [f"# {titulo}{' — ' + nome_cliente if nome_cliente else ''}", ""]
    if para == "cliente":
        linhas += ["Responda com as palavras de vocês, do jeito que falariam com um cliente. Não existe resposta errada, "
                   "e \"não sei\" também ajuda. Prefira o formulário (python -m trilha_briefing questionario --formulario): "
                   "ele salva o progresso e devolve as respostas prontas para importar.", ""]
    elif para == "reuniao":
        linhas += ["Comece conferindo as respostas do questionário (★) e aprofunde as perguntas ●. "
                   "Fale com o dono e com quem atende.", ""]
    else:
        linhas += ["★ o cliente responde antes · ● aprofundar no kickoff · ◆ o assessor levanta com dados e escuta.",
                   "Cada pergunta mostra o campo que preenche ou o que alimenta.", ""]
    n = 0
    for bloco in q.blocos:
        visiveis = [p for p in q.perguntas if p.bloco == bloco.id
                    and (para == "assessor" or p.momento == para or (para == "reuniao" and p.momento == "cliente"))]
        if not visiveis:
            continue
        linhas += [f"## {bloco.titulo}", ""]
        if bloco.objetivo and para == "cliente":
            linhas += [bloco.objetivo, ""]
        for p in visiveis:
            n += 1
            marca = "" if para == "cliente" else f"{SIMBOLO[p.momento]} "
            linhas.append(f"{n}. {marca}{p.pergunta}")
            if p.condicao and para != "assessor":
                base = q.pergunta(p.condicao.pergunta)
                rotulos = {o.valor: o.rotulo for o in base.opcoes} | {"sim": "Sim", "nao": "Não"}
                linhas.append(f"   _Só se, em “{base.pergunta}”, a resposta foi: "
                              f"{' ou '.join(rotulos.get(v, v) for v in p.condicao.em)}_")
            if p.ajuda and para != "assessor":
                linhas.append(f"   _{p.ajuda}_")
            if p.opcoes and para == "cliente":
                linhas.append("   " + " · ".join(f"( ) {o.rotulo}" for o in p.opcoes))
            if para == "assessor":
                linhas.append(f"   - → {p.onde()}")
            linhas.append("")
    if para != "cliente":
        linhas += ["## Roteiro das entrevistas com clientes (escuta)", "",
                   "15 minutos por pessoa. Anote as palavras exatas: viram ganchos, dores e títulos. Registre em "
                   "`pesquisa.escuta` e use `fonte: consumidor`.", ""]
        linhas += [f"- {p}" for p in q.roteiro_escuta] + [""]
        linhas += ["## Sinais de alerta", "", "Pause antes de prometer resultado quando:", ""]
        linhas += [f"- {s}" for s in q.sinais_de_alerta] + [""]
    return "\n".join(linhas)
