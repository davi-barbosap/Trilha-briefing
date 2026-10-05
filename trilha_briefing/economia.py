"""Quanto o cliente pode pagar por resultado e quanto custa validar.

As fórmulas são as do Trilha (`trilha/core/economia.py`, núcleo §3.1). Se mudarem lá, mudam aqui:
a estratégia não pode prometer um teto de custo que o Trilha depois calcula diferente.
"""

from __future__ import annotations

from dataclasses import dataclass

from trilha_briefing.esquema import Economia, Estrategia

SEMANAS_POR_MES = 365.25 / 12 / 7
EVENTOS_SEMANA_APRENDIZADO = 50


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
    verba_minima_viavel: float  # 50 leads por semana no CPL máximo
    ltv_cac_no_teto: float  # LTV / CAC quando o custo chega no teto

    def custo_da_metrica(self, metrica: str) -> float | None:
        return self.custo_max.get(metrica)


def calcular(e: Economia) -> Numeros:
    receita = receita_bruta_por_venda(e)
    cac = receita * e.margem_contribuicao * e.pct_investivel
    custos = {
        "lead": cac * e.taxa_fechamento,
        "lead_qualificado": cac * e.taxa_fechamento / e.taxa_qualificacao,
        "venda": cac,
    }
    if e.taxa_agendamento:
        custos["agendamento"] = cac * e.taxa_fechamento / e.taxa_agendamento
    return Numeros(
        receita_bruta=receita,
        cac_max=cac,
        custo_max=custos,
        verba_minima_viavel=EVENTOS_SEMANA_APRENDIZADO * custos["lead"] * SEMANAS_POR_MES,
        # LTV aqui é a margem que a venda deixa; no teto o CAC é margem × pct_investivel.
        ltv_cac_no_teto=1 / e.pct_investivel,
    )


def conversoes_na_validacao(est: Estrategia) -> float | None:
    """Quantas conversões da métrica principal a verba de validação compra, no custo máximo (cenário otimista)."""
    if not est.economia or not est.orcamento.verba_validacao:
        return None
    custo = calcular(est.economia).custo_da_metrica(est.metrica_principal)
    return est.orcamento.verba_validacao / custo if custo else None
