"""Sugestão de ordem de canais: atenção × intenção.

Quem busca já tem intenção; quem é impactado no feed precisa ser convencido. A ordem base vai do
mais intencional ao menos. O tipo de compra e o nível de consciência das personas mexem nessa ordem.
É uma sugestão para o assessor justificar o mix, não uma decisão.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from trilha_briefing.esquema import ClienteCompleto

BASE = (
    "busca_marca", "busca_produto", "busca_concorrente", "busca_setor", "marketplace",
    "remarketing", "semelhantes", "interesses", "mensagem_ou_formulario_nativo", "display_video",
)
DESCOBERTA = {"semelhantes", "interesses", "mensagem_ou_formulario_nativo", "display_video"}
BUSCA = {"busca_produto", "busca_concorrente", "busca_setor"}
DEPENDE_DE_PUBLICO = {"remarketing", "semelhantes"}
FRIOS = {"inconsciente", "consciente_do_problema"}

MOTIVO = {
    "busca_marca": "protege quem já procura pelo nome; costuma ser o custo mais baixo",
    "busca_produto": "captura quem já procura pelo que o cliente vende",
    "busca_concorrente": "captura quem compara opções; exige aprovação do cliente",
    "busca_setor": "pega a demanda mais ampla do segmento; intenção menor",
    "marketplace": "onde a compra já acontece, quando o segmento tem um",
    "remarketing": "recupera quem já visitou ou conversou",
    "semelhantes": "amplia a partir de quem já comprou",
    "interesses": "gera demanda em quem ainda não procura",
    "mensagem_ou_formulario_nativo": "menos atrito para quem ainda não conhece a marca",
    "display_video": "alcance e lembrança; intenção mais baixa",
}


@dataclass
class Sugestao:
    canal: str
    motivo: str
    observacoes: list[str]
    no_plano: str  # status no estrategia.yaml, ou "" se não está


def sugerir(c: ClienteCompleto) -> list[Sugestao]:
    tipo = c.briefing.negocio.tipo_compra
    niveis = Counter(p.nivel_consciencia for p in c.pesquisa.personas if p.nivel_consciencia)
    frio = sum(v for k, v in niveis.items() if k in FRIOS) > sum(v for k, v in niveis.items() if k not in FRIOS)
    puxa_descoberta = tipo == "desejo" or (tipo == "misto" and frio)

    def peso(canal: str) -> float:
        i = float(BASE.index(canal))
        if puxa_descoberta and canal in DESCOBERTA:
            i -= 4.5  # descoberta sobe para logo depois da marca e do remarketing
        if puxa_descoberta and canal in BUSCA:
            i += 2
        return i

    ordem = sorted(BASE, key=peso)
    mat = c.pesquisa.maturidade
    plano = {cp.canal: cp.status for cp in c.estrategia.canais}
    saida = []
    for canal in ordem:
        obs = []
        if canal in DEPENDE_DE_PUBLICO and mat.historico_conta == 0:
            obs.append("depende de público acumulado: conta nova ainda não tem")
        if canal == "busca_marca":
            obs.append("confirme o volume de busca pelo nome antes de reservar verba")
        if canal == "busca_concorrente":
            obs.append("risco jurídico: só com aprovação por escrito do cliente")
        if canal in DESCOBERTA and frio:
            obs.append("personas pouco conscientes: o criativo precisa ensinar o problema antes de vender")
        saida.append(Sugestao(canal, MOTIVO[canal], obs, plano.get(canal, "")))
    return saida


def recomendacoes_gerais(c: ClienteCompleto) -> list[str]:
    r = []
    tipo = c.briefing.negocio.tipo_compra
    if tipo == "necessidade":
        r.append("compra por necessidade: comece capturando a demanda que já existe (busca) antes de gerar demanda")
    elif tipo == "desejo":
        r.append("compra por desejo: a demanda precisa ser criada; descoberta (Meta, vídeo) vem antes da busca")
    else:
        r.append("compra mista: busca para quem já procura, descoberta para despertar quem ainda não procura")
    if c.pesquisa.maturidade.verba is not None and c.pesquisa.maturidade.verba <= 1:
        r.append("verba na mínima ou abaixo: uma plataforma, uma oferta, poucos conjuntos, até ter dado")
    if c.pesquisa.maturidade.rastreamento is not None and c.pesquisa.maturidade.rastreamento <= 1:
        r.append("rastreamento fraco: otimizar por conversão real ainda não é possível; arrume a medição primeiro")
    return r
