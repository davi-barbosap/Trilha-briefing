"""Quanto o cliente pode pagar por resultado, quanto custa validar e por qual evento dá para otimizar.

As fórmulas são as do Trilha (`trilha/core/economia.py`, núcleo §3.1). Se mudarem lá, mudam aqui:
a estratégia não pode prometer um teto de custo que o Trilha depois calcula diferente.
"""

from __future__ import annotations

from dataclasses import dataclass

from trilha_briefing.esquema import Economia, Estrategia

SEMANAS_POR_MES = 365.25 / 12 / 7
EVENTOS_SEMANA_APRENDIZADO = 50  # o que as plataformas pedem para sair do aprendizado
DEGRAUS = ("lead", "lead_qualificado", "agendamento", "venda")


def receita_bruta_por_venda(e: Economia) -> float:
    if e.modelo_receita == "venda_direta":
        return e.ticket_medio
    if e.modelo_receita == "comissao":
        return e.valor_medio_bem * e.comissao_pct * e.participacao_comissao
    return e.mensalidade * e.meses_retencao


@dataclass
class Numeros:
    receita_bruta: float
    cac_max: float
    custo_max: dict[str, float]  # lead, lead_qualificado, agendamento, venda
    verba_para_otimizar: dict[str, float]  # verba mensal para 50 eventos/semana no custo máximo
    ltv_cac_no_teto: float  # margem da venda / CAC quando o custo chega no teto

    @property
    def verba_minima_viavel(self) -> float:
        return self.verba_para_otimizar["lead"]

    def custo_da_metrica(self, metrica: str) -> float | None:
        return self.custo_max.get(metrica)

    def degraus_viaveis(self, verba_mensal: float) -> list[str]:
        return [d for d in DEGRAUS if d in self.verba_para_otimizar and self.verba_para_otimizar[d] <= verba_mensal]


def calcular(e: Economia) -> Numeros:
    receita = receita_bruta_por_venda(e)
    cac = receita * e.margem_contribuicao * e.pct_investivel
    custos = {"lead": cac * e.taxa_fechamento, "lead_qualificado": cac * e.taxa_fechamento / e.taxa_qualificacao}
    if e.taxa_agendamento:
        custos["agendamento"] = cac * e.taxa_fechamento / e.taxa_agendamento
    custos["venda"] = cac
    return Numeros(
        receita_bruta=receita,
        cac_max=cac,
        custo_max=custos,
        verba_para_otimizar={d: EVENTOS_SEMANA_APRENDIZADO * c * SEMANAS_POR_MES for d, c in custos.items()},
        # No teto o CAC é margem × pct_investivel, então a razão é sempre 1 / pct_investivel.
        ltv_cac_no_teto=1 / e.pct_investivel,
    )


def conversoes_no_teto(est: Estrategia, evento: str | None = None) -> float | None:
    """Quantos eventos a verba de validação compra SE o custo ficar exatamente no teto.

    Não é otimista nem pessimista: é o ponto de equilíbrio. Na validação o custo costuma
    ficar acima do teto, e então a verba compra menos do que isso.
    """
    if not est.economia or not est.orcamento.verba_validacao:
        return None
    custo = calcular(est.economia).custo_da_metrica(evento or est.metrica_principal)
    return est.orcamento.verba_validacao / custo if custo else None


def conversoes_na_validacao(est: Estrategia) -> float | None:
    """Conversões da métrica principal que a verba de validação compra no teto de custo."""
    return conversoes_no_teto(est)
