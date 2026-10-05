"""Esquema dos arquivos de um cliente em `clientes/<id>/`.

Cada arquivo responde a uma pergunta:

    briefing.yaml      o que o cliente diz (kickoff)
    pesquisa.yaml      o que o mercado e os clientes reais mostram
    plataforma.yaml    quem a marca é e como quer ser lembrada
    provas.yaml        o que sustenta cada promessa
    ofertas/<id>.yaml  o que se vende, para quem e com que promessa
    estrategia.yaml    o plano: objetivo, economia, verba, canais, riscos, medição
    hipoteses.yaml     o que está sendo testado e o que já se aprendeu

Afirmações importantes (dores, objeções, diferenciais…) são `Item`: dizem de onde vieram
(`fonte`) e se já foram confirmadas (`status`). Um texto solto vira hipótese de fonte não informada.

Fontes:
    empresa     o que o dono e o time da empresa dizem (opinião de quem vende)
    consumidor  o que quem compra disse: entrevistas, conversas, avaliações (escuta)
    mercado     concorrentes, buscas, anúncios ativos, notícias do setor
    dados       números do CRM, das plataformas, do sistema da empresa
    assessor    conclusão do assessor a partir das demais
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

Fonte = Literal["empresa", "consumidor", "mercado", "dados", "assessor", "nao_informada"]
FONTES_DE_ESCUTA = ("consumidor", "dados")
Status = Literal["hipotese", "validada", "refutada"]
Nivel = Literal["alta", "media", "baixa"]
Situacao = Literal["ok", "pendente", "nao_tem", "nao_sei"]
Cor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$")]
NivelConsciencia = Literal[
    "inconsciente", "consciente_do_problema", "consciente_da_solucao", "consciente_do_produto", "pronto_para_comprar"
]
Nota = Annotated[int, Field(ge=0, le=3)]
Id = Annotated[str, Field(pattern=r"^[a-z0-9_][a-z0-9_-]{0,63}$")]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _fonte_sem_ambiguidade(v: Any) -> Any:
    """'cliente' não é fonte: ninguém sabe se é a empresa ou quem compra dela."""
    if isinstance(v, dict) and v.get("fonte") == "cliente":
        raise ValueError(
            "fonte 'cliente' é ambígua: use 'empresa' (o que a empresa diz) "
            "ou 'consumidor' (o que quem compra disse, na escuta)"
        )
    return v


class Item(_Base):
    """Uma afirmação com origem: o que o cliente diz, o que o mercado e os dados mostram, o que o assessor conclui."""

    texto: str
    fonte: Fonte = "nao_informada"
    status: Status = "hipotese"
    evidencia: str = ""  # onde está a prova: entrevista, print, relatório, link
    mencoes: int | None = Field(default=None, ge=0)  # quantas pessoas disseram isso na escuta (alcance)

    @model_validator(mode="before")
    @classmethod
    def _de_texto(cls, v: Any) -> Any:
        return _fonte_sem_ambiguidade({"texto": v} if isinstance(v, str) else v)


class Crenca(_Base):
    """Crença que impede a compra. Cada uma pede uma peça ou um argumento que a derrube."""

    texto: str
    tipo: Literal["metodo", "interna", "externa"]  # o método não funciona | eu não consigo | o ambiente não deixa
    quebra: str = ""  # como derrubar: prova, lógica, história, demonstração
    fonte: Fonte = "nao_informada"
    status: Status = "hipotese"
    evidencia: str = ""
    mencoes: int | None = Field(default=None, ge=0)

    _fonte = model_validator(mode="before")(classmethod(lambda cls, v: _fonte_sem_ambiguidade(v)))


class Frase(_Base):
    """Fala literal de quem compra, sem nome (LGPD). A copy devolve essas palavras ao leitor."""

    texto: str
    origem: str  # ligação de vendas, entrevista, conversa no WhatsApp, avaliação
    sobre: Literal["dor", "desejo", "medo", "objecao", "crenca", "outro"] = "outro"


# ---------- briefing.yaml: o que o cliente diz ----------


class Cliente(_Base):
    id: Id
    nome: str
    segmento: str  # texto livre: odontologia, escola de idiomas, software B2B, loja de móveis…
    playbook: str = "padrao"  # playbooks/<playbook>/ no Trilha-ads
    site: str = ""
    redes: list[str] = Field(default_factory=list)
    whatsapp: Annotated[str, Field(pattern=r"^(55\d{10,11})?$")] = ""  # 55 + DDD + número, só dígitos
    tempo_mercado: str = ""


class Area(_Base):
    """Onde a empresa atende: define a geografia das campanhas."""

    alcance: Literal["local", "regional", "nacional", "online"]
    cidades: list[str] = Field(default_factory=list)
    raio_km: float | None = Field(default=None, gt=0)
    observacoes: str = ""

    def descricao(self) -> str:
        partes = [", ".join(self.cidades) or self.alcance]
        if self.raio_km:
            partes.append(f"raio de {self.raio_km:g} km")
        if self.observacoes:
            partes.append(self.observacoes)
        return " · ".join(partes)


class Negocio(_Base):
    o_que_vende: str
    modelo_receita: Literal["venda_direta", "comissao", "recorrencia"]
    tipo_compra: Literal["necessidade", "desejo", "misto"]  # necessidade puxa busca; desejo puxa descoberta
    como_vende_hoje: list[str] = Field(default_factory=list)  # indicação, loja, WhatsApp, representante…
    ciclo_venda_dias: int | None = None
    time_comercial: str = ""  # quem atende o lead, quantas pessoas, que papéis
    crm: str = ""
    marketplaces: list[str] = Field(default_factory=list)  # onde a categoria já é comprada (iFood, Mercado Livre…)


class Resultado(_Base):
    """Começo da jornada da marca: o resultado que o cliente quer, antes de qualquer tática."""

    em_12_meses: str
    conhecido_por: str = ""
    sucesso_significa: str = ""  # como o próprio cliente vai saber que deu certo


class Historico(_Base):
    funcionou: list[Item] = Field(default_factory=list)
    nao_funcionou: list[Item] = Field(default_factory=list)
    ja_investiu_em_midia: str = ""


class Restricoes(_Base):
    verba_mensal_max: float | None = None
    prazos: list[str] = Field(default_factory=list)
    regras_legais: list[str] = Field(default_factory=list)  # conselho profissional, publicidade regulada, LGPD
    nao_pode: list[str] = Field(default_factory=list)


class Capacidade(_Base):
    """Quanto a operação aguenta. Verba que gera mais do que isso queima lead."""

    leads_dia: int | None = Field(default=None, ge=0)  # contatos novos por dia que o time atende bem
    clientes_novos_mes: int | None = Field(default=None, ge=0)  # clientes novos por mês que a operação entrega
    observacoes: str = ""


class Aprovacao(_Base):
    """Quem aprova anúncio e texto do lado do cliente. É o gargalo mais comum do dia a dia."""

    responsavel: str = ""
    prazo_horas: int | None = Field(default=None, gt=0)
    substituto: str = ""


class Acessos(_Base):
    """O que a fundação precisa para começar. ok | pendente | nao_tem (precisa criar) | nao_sei."""

    meta_business: Situacao = "nao_sei"
    conta_anuncios_meta: Situacao = "nao_sei"
    pixel_meta: Situacao = "nao_sei"
    google_ads: Situacao = "nao_sei"
    tag_google: Situacao = "nao_sei"
    gtm: Situacao = "nao_sei"
    ga4: Situacao = "nao_sei"
    crm: Situacao = "nao_sei"
    dominio: Situacao = "nao_sei"

    def pendentes(self) -> list[str]:
        return [k for k in type(self).model_fields if getattr(self, k) != "ok"]


class Ativos(_Base):
    """Material que a empresa já tem para criativos e páginas."""

    logo_editavel: Situacao = "nao_sei"
    manual_marca: Situacao = "nao_sei"
    fotos_reais: Situacao = "nao_sei"
    videos_reais: Situacao = "nao_sei"
    politica_privacidade: Situacao = "nao_sei"
    lista_clientes_autorizada: Situacao = "nao_sei"  # para públicos semelhantes, com base legal

    def pendentes(self) -> list[str]:
        return [k for k in type(self).model_fields if getattr(self, k) != "ok"]


class Pessoa(_Base):
    """Quem decide ou é afetado do lado do cliente: influência × interesse."""

    nome: str
    papel: str
    influencia: Nivel
    interesse: Nivel
    espera: str = ""


class Briefing(_Base):
    cliente: Cliente
    area: Area | None = None
    negocio: Negocio
    capacidade: Capacidade = Field(default_factory=Capacidade)
    resultado_desejado: Resultado
    historico: Historico = Field(default_factory=Historico)
    restricoes: Restricoes = Field(default_factory=Restricoes)
    stakeholders: list[Pessoa] = Field(default_factory=list)
    aprovacao: Aprovacao = Field(default_factory=Aprovacao)
    acessos: Acessos = Field(default_factory=Acessos)
    ativos: Ativos = Field(default_factory=Ativos)
    preenchido_por: list[Literal["cliente", "assessor"]] = Field(default_factory=list)
    data: date | None = None


# ---------- pesquisa.yaml: mercado e clientes reais ----------


class Persona(_Base):
    id: Id
    nome: str
    quem_e: str
    dores: list[Item] = Field(default_factory=list)
    desejos: list[Item] = Field(default_factory=list)  # a transformação que procura
    objecoes: list[Item] = Field(default_factory=list)
    ganchos: list[Item] = Field(default_factory=list)  # o que faz parar e prestar atenção
    medos: list[Item] = Field(default_factory=list)  # o que teme que aconteça se não resolver (o "inferno")
    crencas: list[Crenca] = Field(default_factory=list)
    micro_problemas: list[Item] = Field(default_factory=list)  # os problemas que a pessoa acha que tem (pautas)
    frases: list[Frase] = Field(default_factory=list)
    nivel_consciencia: NivelConsciencia | None = None
    sofisticacao: Literal["baixa", "media", "alta"] | None = None  # quantas promessas parecidas já ouviu
    onde_esta: list[str] = Field(default_factory=list)
    gatilho_compra: str = ""  # o que faz decidir agora


class Escuta(_Base):
    """De onde vieram as dores e objeções reais. Sem escuta, persona é opinião."""

    fonte: str  # entrevistas, conversas do CRM, avaliações, comentários, time de vendas
    quantidade: int = Field(ge=0)
    data: date | None = None
    resumo: str = ""


class NaoAtender(_Base):
    """Persona negativa: quem não deve virar lead, e como filtrar antes de pagar por ele."""

    perfil: str
    motivo: str = ""
    como_filtrar: str = ""  # exclusão de público, palavra-chave negativa, pergunta de qualificação


class Concorrente(_Base):
    nome: str
    promessa: str = ""
    posicionamento_preco: Literal["abaixo", "media", "acima", "nao_avaliado"] = "nao_avaliado"
    fortes: list[str] = Field(default_factory=list)
    fracos: list[str] = Field(default_factory=list)
    canais: list[str] = Field(default_factory=list)
    aprender: str = ""


class Swot(_Base):
    forcas: list[Item] = Field(default_factory=list)
    fraquezas: list[Item] = Field(default_factory=list)
    oportunidades: list[Item] = Field(default_factory=list)
    ameacas: list[Item] = Field(default_factory=list)


class Sazonalidade(_Base):
    periodo: str
    efeito: Literal["alta", "baixa"]
    motivo: str = ""


class Maturidade(_Base):
    """Nota de maturidade do Trilha-ads (núcleo §3.2), de 0 a 3 por dimensão."""

    rastreamento: Nota | None = None
    crm: Nota | None = None
    capacidade_criativa: Nota | None = None
    historico_conta: Nota | None = None
    verba: Nota | None = None
    observacoes: str = ""

    def pendentes(self) -> list[str]:
        return [d for d in ("rastreamento", "crm", "capacidade_criativa", "historico_conta", "verba") if getattr(self, d) is None]


class Pesquisa(_Base):
    personas: list[Persona] = Field(default_factory=list)
    escuta: list[Escuta] = Field(default_factory=list)
    nao_atender: list[NaoAtender] = Field(default_factory=list)
    concorrentes: list[Concorrente] = Field(default_factory=list)
    unicidade: str = ""  # o que só este cliente tem, depois de olhar os concorrentes
    swot: Swot = Field(default_factory=Swot)
    sazonalidade: list[Sazonalidade] = Field(default_factory=list)
    maturidade: Maturidade = Field(default_factory=Maturidade)


# ---------- plataforma.yaml: a marca ----------


class Jornada(_Base):
    """Resultado → conhecido por → o que fazer → o que aprender."""

    resultado: str = ""
    conhecido_por: str = ""
    fazer: list[str] = Field(default_factory=list)
    aprender: list[str] = Field(default_factory=list)


class Associacoes(_Base):
    queremos: list[str] = Field(default_factory=list)
    nao_queremos: list[str] = Field(default_factory=list)


class Posicionamento(_Base):
    para_quem: str = ""
    categoria: str = ""
    diferenca: str = ""
    razoes_para_acreditar: list[Item] = Field(default_factory=list)
    percepcao_atual: str = ""  # como o mercado vê hoje
    percepcao_desejada: str = ""  # como quer ser visto; a distância entre as duas é o trabalho


class HistoriaMarca(_Base):
    catalisador: str = ""  # o que fez a empresa existir
    verdade_central: str = ""  # a crença que guia as decisões
    prova: str = ""  # um fato que mostra a crença na prática


class Voz(_Base):
    assinatura: Literal["marca", "pessoa", "marca_pessoa"] | None = None
    nome_pessoa: str = ""
    abordagem: Literal["scripted", "conversacional", "misto"] | None = None
    tom: list[str] = Field(default_factory=list)
    assim_sim: list[str] = Field(default_factory=list)
    assim_nao: list[str] = Field(default_factory=list)
    termos_obrigatorios: list[str] = Field(default_factory=list)
    termos_proibidos: list[str] = Field(default_factory=list)
    intensidade: int | None = Field(default=None, ge=1, le=5)  # termostato: 1 sóbrio … 5 euforia de lançamento


CHAVES_COR = {"primaria", "secundaria", "fundo", "texto", "apoio"}
PRECO_CANAIS = {"anuncio", "whatsapp", "landing"}
PRECO_REGRAS = {"nunca", "a_partir_de", "parcela", "valor_cheio"}


class IdentidadeVisual(_Base):
    cores: dict[str, Cor | list[Cor]] = Field(default_factory=dict)  # primaria, secundaria, fundo, texto (#RRGGBB), apoio
    tipografia: dict[str, str] = Field(default_factory=dict)  # titulos, texto
    logo: str = ""
    estilo_imagem: str = ""

    @model_validator(mode="after")
    def _chaves(self) -> IdentidadeVisual:
        estranhas = set(self.cores) - CHAVES_COR
        if estranhas:
            raise ValueError(f"cores aceita {sorted(CHAVES_COR)}; recebeu {sorted(estranhas)}")
        if isinstance(self.cores.get("apoio", []), str):
            raise ValueError("cores.apoio é uma lista de cores")
        return self


class Tema(_Base):
    """Linha editorial: tema × formato × canal. Poucos temas, repetidos, constroem a associação."""

    nome: str
    peso: int = Field(ge=0, le=100)  # % do conteúdo
    formatos: list[str] = Field(default_factory=list)
    canais: list[str] = Field(default_factory=list)
    exemplo: str = ""


class Compliance(_Base):
    registros_profissionais: list[str] = Field(default_factory=list)  # com número e onde exibir
    avisos_legais: list[str] = Field(default_factory=list)
    promessas_proibidas: list[str] = Field(default_factory=list)
    politica_privacidade_url: str = ""
    base_legal_lgpd: str = "consentimento"


class Atendimento(_Base):
    sla_resposta: str = ""  # 30min | 2h | dia | 24h+
    handoff: str = ""  # direto | bot | horario
    canais: list[str] = Field(default_factory=list)
    horario_comercial: str = ""


class Plataforma(_Base):
    jornada: Jornada = Field(default_factory=Jornada)
    associacoes: Associacoes = Field(default_factory=Associacoes)
    posicionamento: Posicionamento = Field(default_factory=Posicionamento)
    historia: HistoriaMarca = Field(default_factory=HistoriaMarca)
    voz: Voz = Field(default_factory=Voz)
    identidade_visual: IdentidadeVisual = Field(default_factory=IdentidadeVisual)
    temas: list[Tema] = Field(default_factory=list)
    compliance: Compliance = Field(default_factory=Compliance)
    atendimento: Atendimento = Field(default_factory=Atendimento)
    preco: dict[str, str] = Field(default_factory=dict)  # anuncio | whatsapp | landing → nunca, a_partir_de, parcela, valor_cheio

    @model_validator(mode="after")
    def _preco(self) -> Plataforma:
        canais = set(self.preco) - PRECO_CANAIS
        regras = set(self.preco.values()) - PRECO_REGRAS
        if canais or regras:
            raise ValueError(f"preco: canais {sorted(PRECO_CANAIS)} com regras {sorted(PRECO_REGRAS)}; "
                             f"recebeu {sorted(canais | regras)}")
        return self


# ---------- provas.yaml ----------


class Prova(_Base):
    id: Id | None = None  # para as peças de copy citarem a prova usada
    tipo: Literal["depoimento", "numero", "case", "autoridade", "midia", "certificacao"]
    texto: str
    numero: str = ""  # para tipo numero: "+300", "4,8/5", "92%"
    autor: str = ""
    fonte: str = ""  # de onde vem: CRM, Google, relatório, contrato
    autorizado: bool = False  # autorização de uso de nome, imagem e depoimento
    formato: Literal["texto", "video", "imagem", "print"] = "texto"
    link: str = ""
    personas: list[str] = Field(default_factory=list)  # para quem ela convence: prova parecida com quem lê
    perfil: str = ""  # quem é o protagonista: idade, segmento, situação de partida (sem dado sensível)


class HistoriaCliente(_Base):
    titulo: str
    antes: str
    virada: str
    resultado: str
    autorizado: bool = False
    personas: list[str] = Field(default_factory=list)
    perfil: str = ""


class Provas(_Base):
    provas: list[Prova] = Field(default_factory=list)
    historias: list[HistoriaCliente] = Field(default_factory=list)

    def utilizaveis(self, tipo: str | None = None) -> list[Prova]:
        """Provas que podem ir para anúncio e página.

        Fato (número, autoridade, mídia, certificação) precisa de fonte; pessoa (depoimento, case)
        precisa de autorização de uso de nome e imagem.
        """
        ok = [p for p in self.provas if (p.autorizado if p.tipo in ("depoimento", "case") else p.fonte)]
        return [p for p in ok if tipo is None or p.tipo == tipo]


# ---------- ofertas/<id>.yaml ----------


class BigIdea(_Base):
    oportunidade: str = ""  # o que mudou no mercado ou na vida do cliente
    inimigo: str = ""  # o que mantém o problema (um hábito, uma crença, um método ruim), nunca uma pessoa
    mecanismo_unico: str = ""  # como a oferta resolve de um jeito que só ela resolve
    crenca_comum: str = ""  # o que o mercado acredita ("todos acham X")
    por_que_falha: str = ""  # por que isso não resolve ("está errado porque Y"); o mecanismo é o Z


class Promessa(_Base):
    """Promessa que dá para cobrar: resultado observável, prazo e para quem vale."""

    texto: str
    resultado: str = ""
    prazo: str = ""
    condicao: str = ""


class AntesDepois(_Base):
    dimensao: Literal["ter", "sentir", "dia_a_dia", "status"]
    antes: str
    depois: str


class Passo(_Base):
    titulo: str
    texto: str


class ObjecaoOferta(_Base):
    eixo: str  # preco, confianca, tempo, produto, urgencia…
    objecao: str
    resposta: str = ""
    fonte: Fonte = "nao_informada"
    status: Status = "hipotese"

    _fonte = model_validator(mode="before")(classmethod(lambda cls, v: _fonte_sem_ambiguidade(v)))


class Diferencial(Item):
    """Diferencial com a escada do "e daí?": característica → benefício → resultado → quem a pessoa vira."""

    e_dai: list[str] = Field(default_factory=list)


class Alternativa(_Base):
    """O que mais a pessoa pode fazer com o mesmo dinheiro ou esforço. A oferta compete com isso também."""

    alternativa: str
    por_que_nao: str = ""


class Urgencia(_Base):
    tipo: Literal["prazo", "lote", "preco", "evento", "sazonal"]
    texto: str
    motivo: str = ""  # por que existe o limite; urgência sem motivo soa a truque
    data: date | None = None
    real: bool = False
    evidencia: str = ""


class Escassez(_Base):
    texto: str
    real: bool = False
    evidencia: str = ""


class Condicoes(_Base):
    faixa_preco: str = ""
    ticket_medio: float | None = None
    pagamento: str = ""
    condicao_excepcional: str = ""
    validade: str = ""
    posicionamento_preco: str = ""


class VendasForaDoDigital(_Base):
    canais: list[str] = Field(default_factory=list)
    ritmo: str = ""
    avaliacao: Literal["boa", "regular", "fraca", "nao_avaliado"] = "nao_avaliado"


class Aderencia(_Base):
    """Diagnóstico de aderência ao digital do Trilha-ads (núcleo §3.5), na parte que vale para qualquer segmento."""

    perfil_compradores: str = ""
    reputacao: Literal["ativo", "neutra", "obstaculo", "nao_avaliado"] = "nao_avaliado"
    reputacao_nota: str = ""
    vendas_fora_do_digital: VendasForaDoDigital = Field(default_factory=VendasForaDoDigital)
    aderencia_digital: Literal["alta", "media", "baixa", "nao_avaliado"] = "nao_avaliado"
    justificativa: str = ""


class PerguntaQualificacao(_Base):
    rotulo: str
    opcoes: Annotated[list[str], Field(min_length=2)]


class Oferta(_Base):
    id: Id
    nome: str
    tipo: str  # produto, serviço, curso, assinatura, empreendimento…
    degrau: Literal["isca", "entrada", "principal", "premium", "recorrente"]
    personas: list[str] = Field(default_factory=list)  # ids de pesquisa.personas
    problema: str = ""
    big_idea: BigIdea = Field(default_factory=BigIdea)
    promessa: Promessa | None = None
    antes_depois: list[AntesDepois] = Field(default_factory=list)
    diferenciais: list[Diferencial] = Field(default_factory=list)
    raridade: str = ""
    bastidores: list[Item] = Field(default_factory=list)  # o cuidado que o setor inteiro tem e ninguém conta (Schlitz)
    alternativas: list[Alternativa] = Field(default_factory=list)
    como_funciona: list[Passo] = Field(default_factory=list)
    subtitulo: str = ""  # topo da página: dor + como a oferta resolve; vazio = 3 primeiros diferenciais
    beneficios: list[Passo] = Field(default_factory=list)  # 4 a 8 { titulo, texto } escritos para a página
    objecoes: list[ObjecaoOferta] = Field(default_factory=list)
    inversao_risco: str = ""  # o que o cliente deixa de arriscar: garantia, teste, devolução
    escassez: Escassez | None = None
    urgencia: Urgencia | None = None
    custo_inacao: str = ""  # o que custa continuar como está (por mês, por ciclo)
    condicoes: Condicoes = Field(default_factory=Condicoes)
    aderencia: Aderencia = Field(default_factory=Aderencia)
    cta: str = ""
    qualificacao: PerguntaQualificacao | None = None
    estagio: str = ""
    localizacao: dict[str, str] = Field(default_factory=dict)


# ---------- estrategia.yaml ----------

MetricaPrincipal = Literal["lead", "lead_qualificado", "agendamento", "venda"]

# Canais em ordem de intenção: quem busca já quer; quem é impactado precisa ser convencido.
CANAIS = (
    "busca_marca", "busca_produto", "busca_concorrente", "busca_setor", "marketplace", "remarketing",
    "semelhantes", "interesses", "mensagem_ou_formulario_nativo", "display_video",
    "organico", "email_crm", "indicacao", "parcerias", "offline",
)
Canal = Literal[CANAIS]  # type: ignore[valid-type]


class Objetivo(_Base):
    descricao: str
    metrica: str
    meta: float
    prazo: str
    baseline: float | None = None


class Kr(_Base):
    descricao: str
    metrica: str
    meta: float
    baseline: float | None = None


class Economia(_Base):
    """Mesmos campos do `economia` do perfil.yaml do Trilha-ads (núcleo §3.1)."""

    modelo_receita: Literal["venda_direta", "comissao", "recorrencia"]
    ticket_medio: float | None = None
    valor_medio_bem: float | None = None
    comissao_pct: float | None = None
    participacao_comissao: float = 1.0
    mensalidade: float | None = None
    meses_retencao: float | None = None
    margem_contribuicao: float = Field(gt=0, le=1)
    pct_investivel: float = Field(gt=0, le=1)
    taxa_fechamento: float = Field(gt=0, le=1)
    taxa_qualificacao: float = Field(gt=0, le=1)
    taxa_agendamento: float | None = Field(default=None, gt=0, le=1)
    estimados: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _coerencia(self) -> Economia:
        exigidos = {
            "venda_direta": ("ticket_medio",),
            "comissao": ("valor_medio_bem", "comissao_pct"),
            "recorrencia": ("mensalidade", "meses_retencao"),
        }[self.modelo_receita]
        faltando = [c for c in exigidos if getattr(self, c) is None]
        if faltando:
            raise ValueError(f"modelo_receita={self.modelo_receita} exige: {', '.join(faltando)}")
        if self.taxa_qualificacao < self.taxa_fechamento:
            raise ValueError("taxa_qualificacao não pode ser menor que taxa_fechamento")
        if self.taxa_agendamento is not None and not (
            self.taxa_fechamento <= self.taxa_agendamento <= self.taxa_qualificacao
        ):
            raise ValueError("esperado taxa_fechamento ≤ taxa_agendamento ≤ taxa_qualificacao")
        return self


class Orcamento(_Base):
    verba_validacao: float | None = None  # o máximo que o cliente aceita perder até saber se funciona
    semanas_validacao: int | None = None
    verba_mensal: float | None = None
    teto_mensal: float | None = None
    moeda: str = "BRL"


class CanalPlano(_Base):
    canal: Canal
    plataforma: str = ""  # google, meta, tiktok, linkedin, marketplace…
    papel: str = ""  # capturar demanda, gerar demanda, recuperar, reter
    status: Literal["ativo", "teste", "futuro", "descartado"] = "teste"
    verba_pct: float | None = Field(default=None, ge=0, le=100)
    justificativa: str = ""
    aprovado_cliente: bool = False


class Celula(_Base):
    """Uma célula da grade públicos × argumentos: vira um briefing de criativo com código."""

    codigo: Annotated[str, Field(pattern=r"^[A-Z0-9]{2,8}$")]
    publico: str
    argumento: str
    persona: str = ""
    oferta: str = ""
    nivel_consciencia: NivelConsciencia | None = None
    formato: str = ""
    prioridade: int = Field(default=2, ge=1, le=3)
    promessa: str = ""  # a promessa da oferta ajustada ao medo desta persona; vazio = a da oferta


class Risco(_Base):
    descricao: str
    categoria: Literal["escopo", "prazo", "custo", "recurso", "qualidade", "externo"]
    probabilidade: int = Field(ge=1, le=5)
    impacto: int = Field(ge=1, le=5)
    resposta: str = ""
    interno: bool = False  # fica fora da apresentação ao cliente (ex.: risco que envolve uma pessoa do time dele)

    @property
    def nota(self) -> int:
        return self.probabilidade * self.impacto


class Marco(_Base):
    nome: str
    quando: str  # "semana 2", "15/11", "fim do 1º mês"
    entrega: str = ""
    responsavel: str = ""


class Medicao(_Base):
    """Saber medir antes de lançar. Todos precisam estar prontos para a estratégia ser aprovada."""

    utm_padrao: bool = False
    campos_crm: bool = False  # UTMs e identificadores de clique gravados no lead
    evento_conversao: bool = False  # disparando só depois do recebimento confirmado
    etapas_e_motivos_perda: bool = False  # funil padrão e motivos de perda obrigatórios no CRM
    codigo_criativo: bool = False  # código do criativo chegando no lead (inclusive pelo WhatsApp)
    relatorio_definido: bool = False  # quem recebe, com que frequência, com que métricas
    notas: str = ""

    def pendentes(self) -> list[str]:
        return [k for k in type(self).model_fields if k != "notas" and not getattr(self, k)]


class Estrategia(_Base):
    objetivo: Objetivo | None = None
    krs: list[Kr] = Field(default_factory=list)
    metrica_principal: MetricaPrincipal = "lead_qualificado"
    evento_otimizacao: MetricaPrincipal | None = None  # o que a campanha otimiza; vazio = a métrica principal
    economia: Economia | None = None
    orcamento: Orcamento = Field(default_factory=Orcamento)
    abordagem: Literal["direta", "inbound", "direta_com_inbound"] | None = None
    canais: list[CanalPlano] = Field(default_factory=list)
    grade: list[Celula] = Field(default_factory=list)
    premissas: list[str] = Field(default_factory=list)
    restricoes: list[str] = Field(default_factory=list)
    riscos: list[Risco] = Field(default_factory=list)
    marcos: list[Marco] = Field(default_factory=list)
    medicao: Medicao = Field(default_factory=Medicao)
    aprovado_em: date | None = None


# ---------- hipoteses.yaml ----------


class Hipotese(_Base):
    id: Id
    hipotese: str
    variavel: Literal["criativo", "publico", "objetivo", "pagina", "oferta", "canal", "copy", "atendimento"]
    codigos: list[str] = Field(default_factory=list)  # células da grade em teste (PT01, PT02…)
    metrica: str
    criterio_sucesso: str
    evento: MetricaPrincipal | None = None  # em que etapa do funil se conta o volume; vazio = a métrica principal
    minimo_conversoes: int = Field(default=30, ge=1)  # por variação
    variacoes: int = Field(default=2, ge=1)  # quantas versões disputam (A/B = 2)
    horizonte: Literal["nucleo", "adjacente", "ruptura"] = "nucleo"
    inicio: date | None = None
    fim: date | None = None
    resultado: Literal["planejada", "rodando", "validada", "refutada", "inconclusiva"] = "planejada"
    conversoes_obtidas: int | None = None
    aprendizado: str = ""


class Hipoteses(_Base):
    hipoteses: list[Hipotese] = Field(default_factory=list)


# ---------- campanhas.yaml ----------

MetodoTeste = Literal["ab_plataforma", "conjuntos_separados", "comparacao_no_conjunto"]


class Conjunto(_Base):
    """Conjunto de anúncios (Meta, TikTok) ou grupo de anúncios (Google)."""

    id: Id
    publico: str = ""  # quem: região, idade, interesses ou "amplo"
    palavras_chave: list[str] = Field(default_factory=list)  # Google: as buscas do grupo
    correspondencia: Literal["ampla", "frase", "exata"] | None = None
    exclusoes: list[str] = Field(default_factory=list)  # "leads dos últimos 30 dias", "clientes"
    celulas: list[str] = Field(default_factory=list)  # códigos da grade que viram anúncios aqui
    verba_mensal: float | None = Field(default=None, gt=0)  # só se o orçamento for do conjunto; vazio = o da campanha
    id_plataforma: str = ""  # só com regras.espelho.ids_da_plataforma


class TestePlanejado(_Base):
    hipotese: str
    metodo: MetodoTeste | None = None  # vazio = regras.testes.metodo_padrao


class Campanha(_Base):
    id: Id
    canal: Canal  # um dos canais de estrategia.yaml
    plataforma: str  # meta, google, tiktok, linkedin…
    evento: MetricaPrincipal | None = None  # vazio = evento de otimização da estratégia
    fase: str = "fundacao"  # uma das fases de regras.fases.ordem
    verba_mensal: float | None = Field(default=None, gt=0)  # vazio = verba_pct do canal × verba mensal
    conjuntos: list[Conjunto] = Field(default_factory=list)
    negativas: list[str] = Field(default_factory=list)  # Google: palavras-chave negativas
    testes: list[TestePlanejado] = Field(default_factory=list)
    id_plataforma: str = ""
    observacoes: str = ""


class PlanoCampanhas(_Base):
    """As decisões de mídia aprovadas com o cliente. A estrutura real fica nas plataformas."""

    regras: dict[str, Any] = Field(default_factory=dict)  # sobrescreve as regras padrão só para este cliente
    campanhas: list[Campanha] = Field(default_factory=list)


# ---------- leitura da pasta ----------

ARQUIVOS = {
    "briefing": ("briefing.yaml", Briefing),
    "pesquisa": ("pesquisa.yaml", Pesquisa),
    "plataforma": ("plataforma.yaml", Plataforma),
    "provas": ("provas.yaml", Provas),
    "estrategia": ("estrategia.yaml", Estrategia),
    "hipoteses": ("hipoteses.yaml", Hipoteses),
    "campanhas": ("campanhas.yaml", PlanoCampanhas),
}


@dataclass
class ClienteCompleto:
    pasta: Path
    briefing: Briefing
    pesquisa: Pesquisa = field(default_factory=Pesquisa)
    plataforma: Plataforma = field(default_factory=Plataforma)
    provas: Provas = field(default_factory=Provas)
    ofertas: list[Oferta] = field(default_factory=list)
    estrategia: Estrategia = field(default_factory=Estrategia)
    hipoteses: Hipoteses = field(default_factory=Hipoteses)
    campanhas: PlanoCampanhas = field(default_factory=PlanoCampanhas)
    ausentes: list[str] = field(default_factory=list)

    def persona(self, pid: str) -> Persona | None:
        return next((p for p in self.pesquisa.personas if p.id == pid), None)

    def oferta(self, oid: str) -> Oferta | None:
        return next((o for o in self.ofertas if o.id == oid), None)

    def oferta_principal(self) -> Oferta | None:
        return next((o for o in self.ofertas if o.degrau == "principal"), self.ofertas[0] if self.ofertas else None)


class ErroCliente(Exception):
    def __init__(self, erros: dict[str, str]):
        self.erros = erros
        super().__init__("\n".join(f"{k}: {v}" for k, v in erros.items()))


def _ler(caminho: Path) -> Any:
    with open(caminho, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def carregar_cliente(pasta: str | Path) -> ClienteCompleto:
    """Lê e valida a pasta inteira. Junta os erros de todos os arquivos antes de falhar."""
    pasta = Path(pasta)
    erros: dict[str, str] = {}
    lidos: dict[str, Any] = {}
    ausentes = []
    for chave, (nome, modelo) in ARQUIVOS.items():
        caminho = pasta / nome
        if not caminho.exists():
            ausentes.append(nome)
            continue
        try:
            lidos[chave] = modelo.model_validate(_ler(caminho))
        except (ValidationError, yaml.YAMLError) as e:
            erros[nome] = str(e)
    ofertas = []
    for caminho in sorted((pasta / "ofertas").glob("*.yaml")):
        try:
            o = Oferta.model_validate(_ler(caminho))
        except (ValidationError, yaml.YAMLError) as e:
            erros[f"ofertas/{caminho.name}"] = str(e)
            continue
        if o.id != caminho.stem:
            erros[f"ofertas/{caminho.name}"] = f"id '{o.id}' diferente do nome do arquivo"
        ofertas.append(o)
    if "briefing" not in lidos and "briefing.yaml" not in erros:
        erros["briefing.yaml"] = "arquivo obrigatório"
    if not erros:
        erros.update(_referencias(lidos, ofertas, pasta))
    if erros:
        raise ErroCliente(erros)
    return ClienteCompleto(pasta=pasta, ofertas=ofertas, ausentes=ausentes, **lidos)


def _referencias(lidos: dict[str, Any], ofertas: list[Oferta], pasta: Path) -> dict[str, str]:
    """Ids citados entre arquivos precisam existir."""
    erros = {}
    briefing: Briefing = lidos["briefing"]
    if briefing.cliente.id != pasta.name:
        erros["briefing.yaml"] = f"cliente.id '{briefing.cliente.id}' diferente da pasta '{pasta.name}'"
    personas = {p.id for p in lidos.get("pesquisa", Pesquisa()).personas}
    ids_ofertas = {o.id for o in ofertas}
    for o in ofertas:
        faltam = [p for p in o.personas if p not in personas]
        if faltam:
            erros[f"ofertas/{o.id}.yaml"] = f"personas inexistentes em pesquisa.yaml: {faltam}"
    est: Estrategia = lidos.get("estrategia", Estrategia())
    problemas = []
    codigos = [c.codigo for c in est.grade]
    repetidos = sorted({c for c in codigos if codigos.count(c) > 1})
    if repetidos:
        problemas.append(f"códigos de criativo repetidos na grade: {repetidos}")
    for c in est.grade:
        if c.persona and c.persona not in personas:
            problemas.append(f"grade {c.codigo}: persona '{c.persona}' inexistente")
        if c.oferta and c.oferta not in ids_ofertas:
            problemas.append(f"grade {c.codigo}: oferta '{c.oferta}' inexistente")
    if problemas:
        erros["estrategia.yaml"] = "; ".join(problemas)
    hip = lidos.get("hipoteses", Hipoteses()).hipoteses
    ids = [h.id for h in hip]
    problemas = []
    if len(ids) != len(set(ids)):
        problemas.append("ids de hipótese repetidos")
    for h in hip:
        faltam = [x for x in h.codigos if x not in codigos]
        if faltam:
            problemas.append(f"{h.id}: códigos fora da grade {faltam}")
    if problemas:
        erros["hipoteses.yaml"] = "; ".join(problemas)
    provas: Provas = lidos.get("provas", Provas())
    problemas = []
    ids_provas = [p.id for p in provas.provas if p.id]
    if len(ids_provas) != len(set(ids_provas)):
        problemas.append("ids de prova repetidos")
    for i, p in enumerate([*provas.provas, *provas.historias]):
        faltam = [x for x in p.personas if x not in personas]
        if faltam:
            rotulo = getattr(p, "id", None) or getattr(p, "titulo", None) or f"#{i}"
            problemas.append(f"{rotulo}: personas inexistentes {faltam}")
    if problemas:
        erros["provas.yaml"] = "; ".join(problemas)
    plano = lidos.get("campanhas")
    if plano is not None:
        problemas = _referencias_do_plano(plano, est, codigos, ids)
        if problemas:
            erros["campanhas.yaml"] = "; ".join(problemas)
    return erros


def _referencias_do_plano(plano: PlanoCampanhas, est: Estrategia, codigos: list[str], hipoteses: list[str]) -> list[str]:
    from trilha_briefing.campanhas import ErroRegras, regras_do_plano  # campanhas importa este módulo

    try:
        regras = regras_do_plano(plano)
    except ErroRegras as e:
        return [str(e)]
    problemas = []
    ids = [cp.id for cp in plano.campanhas]
    if len(ids) != len(set(ids)):
        problemas.append("ids de campanha repetidos")
    canais = {cp.canal for cp in est.canais if cp.status != "descartado"}
    for cp in plano.campanhas:
        if cp.canal not in canais:
            problemas.append(f"{cp.id}: canal '{cp.canal}' não está entre os canais ativos, em teste ou futuros da estratégia")
        if cp.fase not in regras.fases.ordem:
            problemas.append(f"{cp.id}: fase '{cp.fase}' fora de regras.fases.ordem {regras.fases.ordem}")
        conj = [cj.id for cj in cp.conjuntos]
        if len(conj) != len(set(conj)):
            problemas.append(f"{cp.id}: ids de conjunto repetidos")
        for cj in cp.conjuntos:
            faltam = [x for x in cj.celulas if x not in codigos]
            if faltam:
                problemas.append(f"{cp.id}.{cj.id}: células fora da grade {faltam}")
        faltam = [t.hipotese for t in cp.testes if t.hipotese not in hipoteses]
        if faltam:
            problemas.append(f"{cp.id}: hipóteses inexistentes {faltam}")
        if not regras.espelho.ids_da_plataforma and (cp.id_plataforma or any(cj.id_plataforma for cj in cp.conjuntos)):
            problemas.append(f"{cp.id}: id_plataforma preenchido, mas regras.espelho.ids_da_plataforma está desligado")
    return problemas
