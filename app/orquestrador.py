"""Orquestrador da conversa (s4-orquestrador-agentes): contrato do POST /orquestrar.

O contrato está em openspec/changes/s4-orquestrador-agentes/design.md ("Contrato do POST /orquestrar").
O navegador (web/conversa.js) trabalha com as respostas de exemplo em tests/orquestrar_exemplos.json,
validadas contra estes modelos por tests/test_orquestrar_contrato.py.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Agente = Literal["juridico", "beneficios", "triagem", "rede", "fora_do_tema"]
TipoBeneficio = Literal["direito", "explicacao"]
DecididoPor = Literal["regra", "llm", "reserva"]

# Os ids de regras/beneficios.json, mais "outro" para um benefício citado que não tem regra.
Beneficio = Literal["bolsa_familia", "bpc", "auxilio_aluguel", "aluguel_social_df", "outro"]

# As RAs de RAS_DF em web/dados.js, sem "Outra RA do DF" e "Prefiro não informar".
RAS_DO_SITE = (
    "Plano Piloto",
    "Ceilândia",
    "Taguatinga",
    "Samambaia",
    "Gama",
    "Planaltina",
    "Sobradinho",
    "Brazlândia",
    "Paranoá",
    "Núcleo Bandeirante",
    "Santa Maria",
    "Recanto das Emas",
    "Águas Claras",
    "Guará",
    "São Sebastião",
    "Itapoã",
    "Estrutural (SCIA)",
)
RaDoSite = Literal[RAS_DO_SITE]  # type: ignore[valid-type]

# Recusa padrão quando o orquestrador escolhe "fora do tema": sem buscar trechos e sem gerar texto com o LLM.
FORA_DO_TEMA = (
    "Esse assunto está fora do que consigo responder aqui. Posso ajudar com direitos e leis sobre "
    "violência contra a mulher, benefícios, avaliação de risco e serviços de atendimento no DF. "
    "Para conversar com alguém, ligue 180 (gratuito, 24 horas) ou procure a Defensoria Pública do DF, "
    "que atende de graça."
)


class PedidoOrquestrar(BaseModel):
    """Só o texto e duas indicações. Campos a mais (perfil, histórico) são recusados com 422."""

    model_config = ConfigDict(extra="forbid")

    texto: str = Field(min_length=1, max_length=2000)
    alerta_visto: bool = False
    ajudando: bool = False


class Campos(BaseModel):
    """Campos tirados do texto da mensagem (nunca do perfil)."""

    model_config = ConfigDict(extra="forbid")

    beneficio: Beneficio | None = None
    ra: RaDoSite | None = None
    # True: violência sexual recente ou sem dizer quando; False: dita como antiga; None: sem menção.
    violencia_sexual_recente: bool | None = None


class Citacao(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lei: str
    artigo: str
    citacao: str
    url: str
    data_acesso: str


class RespostaAgente(BaseModel):
    """O mesmo formato de app.rag.resposta.responder(), mais o aviso da explicação de benefícios."""

    model_config = ConfigDict(extra="forbid")

    resposta: str = Field(min_length=1)
    citacoes: list[Citacao]
    recusada: bool
    # s4-rag-beneficios: "Valores e regras podem mudar por decreto. Norma consultada em DD/MM/AAAA."
    aviso: str | None = None


class RespostaOrquestrar(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risco_imediato: bool
    categoria_risco: str | None
    alerta: str | None
    agente: Agente | None
    tipo: TipoBeneficio | None
    campos: Campos
    resposta: RespostaAgente | None
    outras_perguntas: list[str] = Field(max_length=2)
    excedeu: bool
    decidido_por: DecididoPor | None

    @model_validator(mode="after")
    def _coerente(self):
        so_alerta = self.agente is None
        if self.risco_imediato:
            if not self.alerta or not self.categoria_risco:
                raise ValueError("com risco imediato, alerta e categoria_risco são obrigatórios")
        elif self.alerta is not None or self.categoria_risco is not None:
            raise ValueError("sem risco imediato, alerta e categoria_risco vêm nulos")
        if so_alerta:
            # Sem alerta_visto: só o alerta, nada mais é feito.
            if not self.risco_imediato:
                raise ValueError("agente nulo só na resposta que traz apenas o alerta")
            if (
                self.tipo or self.resposta or self.decidido_por or self.outras_perguntas or self.excedeu
                or self.campos != Campos()
            ):
                raise ValueError("a resposta só com o alerta não traz agente, campos nem resposta")
            return self
        if self.decidido_por is None:
            raise ValueError("decidido_por é obrigatório quando há agente")
        if (self.tipo is not None) != (self.agente == "beneficios"):
            raise ValueError("tipo só é preenchido, e é obrigatório, quando o agente é beneficios")
        no_servidor = self.agente in ("juridico", "fora_do_tema") or self.tipo == "explicacao"
        if no_servidor != (self.resposta is not None):
            raise ValueError("resposta preenchida só para juridico, explicação de benefícios e fora do tema")
        if self.excedeu and len(self.outras_perguntas) != 2:
            raise ValueError("com excedeu, as duas sugestões possíveis são devolvidas")
        return self


class ErroOrquestrar(BaseModel):
    """Resposta 503 quando o LLM não responde ao gerar a resposta jurídica."""

    model_config = ConfigDict(extra="forbid")

    erro: str = Field(min_length=1)
