"""Orquestrador da conversa (s4-orquestrador-agentes): contrato do POST /orquestrar e etapa de regra.

O contrato está em openspec/changes/s4-orquestrador-agentes/design.md ("Contrato do POST /orquestrar").
O navegador (web/conversa.js) trabalha com as respostas de exemplo em tests/orquestrar_exemplos.json,
validadas contra estes modelos por tests/test_orquestrar_contrato.py.

A primeira etapa (por_regra) usa as palavras de regras/roteamento.json e só decide quando casa
exatamente um agente numa mensagem sem marca de várias perguntas; nos demais casos, quem escolhe é o LLM.
"""
import json
import logging
import re
import typing
from collections.abc import Callable
from functools import cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app import llm, risco
from app.rag import resposta as rag
from app.risco import normalizar

ARQUIVO_ROTEAMENTO = Path(__file__).resolve().parents[1] / "regras" / "roteamento.json"

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


class Decisao(BaseModel):
    """Agente escolhido para uma pergunta, com o tipo (só em benefícios) e os campos tirados do texto."""

    model_config = ConfigDict(extra="forbid")

    agente: Agente
    tipo: TipoBeneficio | None = None
    campos: Campos = Field(default_factory=Campos)

    @model_validator(mode="after")
    def _tipo_so_em_beneficios(self):
        if (self.tipo is not None) != (self.agente == "beneficios"):
            raise ValueError("tipo só é preenchido, e é obrigatório, quando o agente é beneficios")
        return self


@cache
def _roteamento() -> dict:
    dados = json.loads(ARQUIVO_ROTEAMENTO.read_text(encoding="utf-8"))

    def compilar(padroes: list[str]) -> list[re.Pattern]:
        return [re.compile(p) for p in padroes]

    sexual = dados["violencia_sexual"]
    return {
        "minimo_interrogacoes": dados["minimo_interrogacoes_para_varias"],
        "varias": compilar(dados["marcas_varias_perguntas"]),
        "direito": compilar(dados["marcas_direito"]),
        "auxilio_aluguel": compilar(dados["auxilio_aluguel"]),
        "agentes": {agente: compilar(p) for agente, p in dados["agentes"].items()},
        "beneficios": {beneficio: compilar(p) for beneficio, p in dados["beneficios"].items()},
        "ras": {ra: compilar(p) for ra, p in dados["ras"].items()},
        "sexual": compilar(sexual["menciona"]),
        "sexual_antiga": compilar(sexual["antiga"]),
    }


def _casa(padroes: list[re.Pattern], texto: str) -> bool:
    return any(p.search(texto) for p in padroes)


def _unico(encontrados: list[str]) -> str | None:
    # Mais de um valor citado: não dá para saber qual vale, então fica nulo.
    return encontrados[0] if len(encontrados) == 1 else None


def varias_perguntas(texto: str) -> bool:
    """Marcas de mais de uma pergunta: 2+ "?" separados por texto, "e também", "outra coisa", "além disso" etc."""
    regras, normalizado = _roteamento(), normalizar(texto)
    interrogacoes = len(re.findall(r"\?+", normalizado))
    return interrogacoes >= regras["minimo_interrogacoes"] or _casa(regras["varias"], normalizado)


def campos_do_texto(texto: str) -> Campos:
    """Benefício, RA e violência sexual recente tirados só do texto (nunca do perfil)."""
    regras, normalizado = _roteamento(), normalizar(texto)
    beneficios = [b for b, padroes in regras["beneficios"].items() if _casa(padroes, normalizado)]
    ras = [ra for ra, padroes in regras["ras"].items() if _casa(padroes, normalizado)]
    violencia_sexual_recente = None
    if _casa(regras["sexual"], normalizado):
        # Sem dizer quando, conta como recente: na dúvida, a saúde vem primeiro.
        violencia_sexual_recente = not _casa(regras["sexual_antiga"], normalizado)
    return Campos(beneficio=_unico(beneficios), ra=_unico(ras), violencia_sexual_recente=violencia_sexual_recente)


def por_regra(texto: str) -> Decisao | None:
    """Agente pela regra de palavras-chave, ou None quando a regra não decide (o LLM escolhe)."""
    if varias_perguntas(texto):
        return None
    regras, normalizado = _roteamento(), normalizar(texto)
    direito = _casa(regras["direito"], normalizado)
    agentes, resto = set(), normalizado
    if _casa(regras["auxilio_aluguel"], normalizado):
        # A norma do auxílio-aluguel (Lei 11.340/2006, art. 23, VI) está no eixo jurídico: a explicação vai
        # para o jurídico, e "tenho direito?" vai para a regra de benefícios. O apelido sai do texto para
        # "maria da penha", "juiz" e "auxílio" dentro dele não contarem como outros agentes.
        agentes.add("beneficios" if direito else "juridico")
        for padrao in regras["auxilio_aluguel"]:
            resto = padrao.sub(" ", resto)
    agentes |= {agente for agente, padroes in regras["agentes"].items() if _casa(padroes, resto)}
    if len(agentes) != 1:
        return None
    agente = agentes.pop()
    tipo = ("direito" if direito else "explicacao") if agente == "beneficios" else None
    return Decisao(agente=agente, tipo=tipo, campos=campos_do_texto(texto))


# --- Segunda etapa: classificação pelo LLM (tarefas 2.3 e 2.4) ----------------------------------

# Até 3 perguntas são tratadas: uma respondida e até 2 sugeridas. Com mais, `excedeu`.
MAXIMO_PERGUNTAS = 3

INSTRUCOES_CLASSIFICACAO = (
    "Você encaminha mensagens de um serviço de apoio a mulheres em situação de violência doméstica "
    "no Distrito Federal. Não responda à mensagem: só classifique.\n"
    "Separe a mensagem em perguntas, na ordem em que foram escritas. Reescreva cada uma para ser "
    "entendida sozinha, trocando pronomes pelo assunto (\"onde eu peço ela?\" vira \"Onde peço medida "
    "protetiva?\"), sem acrescentar fatos. Uma mensagem com uma pergunta só gera uma pergunta.\n"
    "Para cada pergunta, escolha um agente desta lista fechada:\n"
    "- juridico: leis, direitos, crimes, medida protetiva, processo, guarda, divórcio, Lei Maria da Penha. "
    "Inclui explicar o auxílio-aluguel da Lei Maria da Penha (\"aluguel da Maria da Penha\", "
    "\"aluguel do juiz\").\n"
    "- beneficios: benefícios sociais (Bolsa Família, BPC, Aluguel Social do DF, Cartão Gás, Prato Cheio "
    "e outros). Use tipo \"direito\" quando a pessoa quer saber se tem direito ou pode receber, e tipo "
    "\"explicacao\" quando quer saber o que é, como funciona ou quem pode receber.\n"
    "- triagem: a pessoa quer saber se corre perigo ou qual o nível de risco.\n"
    "- rede: onde buscar atendimento (delegacia, CRAS, Defensoria, hospital, Casa da Mulher Brasileira).\n"
    "- fora_do_tema: qualquer outro assunto.\n"
    "Campos tirados só do texto da mensagem, nunca supostos:\n"
    "- beneficio: \"bolsa_familia\", \"bpc\", \"auxilio_aluguel\", \"aluguel_social_df\", \"outro\" "
    "(benefício citado fora desses) ou null.\n"
    "- ra: a Região Administrativa do DF citada, escrita exatamente como um destes valores: "
    + ", ".join(f'"{ra}"' for ra in RAS_DO_SITE)
    + "; ou null.\n"
    "- violencia_sexual_recente: true se a mensagem fala de violência sexual recente ou sem dizer quando; "
    "false se diz que foi há mais tempo; null se não fala de violência sexual.\n"
    "Responda só com JSON, sem texto fora dele, neste formato:\n"
    '{"perguntas": [{"agente": "juridico", "tipo": null, "pergunta": "...", "beneficio": null, '
    '"ra": null, "violencia_sexual_recente": null}]}\n'
    "O campo tipo é null em todos os agentes, menos em beneficios."
)


class PerguntaClassificada(BaseModel):
    """Um item da saída do LLM. Agente ou tipo inválidos invalidam a saída inteira (vai para a reserva)."""

    agente: Agente
    tipo: TipoBeneficio | None = None
    pergunta: str = Field(min_length=1, max_length=2000)
    beneficio: str | None = None
    ra: str | None = None
    violencia_sexual_recente: bool | None = None

    def decisao(self) -> Decisao:
        # Valores fora do contrato nos campos viram nulos (spec conversa: "RA fora da lista do site").
        beneficio = self.beneficio if self.beneficio in typing.get_args(Beneficio) else None
        ra = self.ra if self.ra in RAS_DO_SITE else None
        campos = Campos(beneficio=beneficio, ra=ra, violencia_sexual_recente=self.violencia_sexual_recente)
        return Decisao(agente=self.agente, tipo=self.tipo, campos=campos)


class SaidaClassificacao(BaseModel):
    perguntas: list[PerguntaClassificada] = Field(min_length=1)


class Classificacao(BaseModel):
    """Resultado das duas etapas: quem decidiu, o agente da pergunta respondida e as sugestões."""

    model_config = ConfigDict(extra="forbid")

    decidido_por: DecididoPor
    decisao: Decisao
    # Texto que o agente recebe: o original com uma pergunta; a pergunta reescrita com várias.
    pergunta: str
    outras_perguntas: list[str] = Field(default_factory=list, max_length=MAXIMO_PERGUNTAS - 1)
    excedeu: bool = False


def montar_mensagens_classificacao(texto: str) -> list[dict]:
    return [
        {"role": "system", "content": INSTRUCOES_CLASSIFICACAO},
        {"role": "user", "content": f"Mensagem: {texto}"},
    ]


def _ler_saida(saida: str) -> list[tuple[Decisao, str]] | None:
    """Perguntas da saída do LLM, ou None se ela não seguir o formato (aceita cercas de código em volta)."""
    bloco = re.search(r"\{.*\}", saida, re.S)
    if bloco is None:
        return None
    try:
        lidas = SaidaClassificacao.model_validate_json(bloco[0])
        return [(p.decisao(), p.pergunta.strip()) for p in lidas.perguntas]
    except ValueError:  # JSON quebrado, agente fora da lista, tipo inválido ou tipo fora de benefícios
        return None


def por_llm(texto: str, cliente) -> list[tuple[Decisao, str]] | None:
    """Perguntas classificadas pelo LLM, na ordem escrita, ou None (saída inválida ou LLM indisponível)."""
    try:
        saida = cliente.responder(montar_mensagens_classificacao(texto), temperatura=0)
    except llm.LLMIndisponivel:
        return None
    return _ler_saida(saida)


def classificar(texto: str, cliente) -> Classificacao:
    """Regra, depois LLM, depois reserva no jurídico. A checagem de risco é feita antes, pela rota."""
    if decisao := por_regra(texto):
        return Classificacao(decidido_por="regra", decisao=decisao, pergunta=texto)
    perguntas = por_llm(texto, cliente)
    if perguntas is None:
        # O jurídico já tem a própria recusa (similaridade e citação).
        return Classificacao(
            decidido_por="reserva", decisao=Decisao(agente="juridico", campos=campos_do_texto(texto)), pergunta=texto
        )
    # Ordenação estável: triagem primeiro, depois a ordem em que a usuária escreveu.
    ordenadas = sorted(perguntas, key=lambda item: item[0].agente != "triagem")
    decisao, reescrita = ordenadas[0]
    return Classificacao(
        decidido_por="llm",
        decisao=decisao,
        # Com uma pergunta só, a reescrita não altera o que a usuária escreveu.
        pergunta=texto if len(perguntas) == 1 else reescrita,
        outras_perguntas=[p for _, p in ordenadas[1:MAXIMO_PERGUNTAS]],
        excedeu=len(perguntas) > MAXIMO_PERGUNTAS,
    )


# --- Rota: risco, classificação e resposta no mesmo pedido (tarefas 3.1 a 3.3) ------------------

logger = logging.getLogger("rede_lilas.orquestrador")

# Ponto de troca da explicação de benefícios. s4-rag-beneficios registra aqui uma função
# (pergunta, indice, cliente) -> dict no formato de app.rag.resposta.responder(). Enquanto for None,
# a explicação vai ao jurídico, como antes da S4: cortar o RAG de benefícios não quebra o orquestrador.
explicar_beneficio: Callable[..., dict] | None = None

# Modo "ajudando outra pessoa" (tarefa 3.4): as instruções do jurídico, sem tirar nenhuma regra, mais
# estas linhas. O /juridico nunca usa esta versão, e INSTRUCOES continua igual (tests/test_instrucoes_sem_rag.py).
INSTRUCOES_AJUDANDO = rag.INSTRUCOES + (
    "\n- Quem pergunta está ajudando outra mulher, que é a vítima. Fale da vítima em terceira pessoa "
    "(\"ela\") e fale com quem pergunta em segunda pessoa (\"você\").\n"
    "- Além do que os trechos de lei preveem, inclua em uma ou duas frases, sem citar artigo, como apoiar "
    "sem expor a vítima ao agressor: ouvir sem julgar, não confrontar o agressor, não deixar mensagens "
    "sobre o assunto no celular dela e combinar com ela uma forma segura de contato.\n"
    "- Respeite as decisões da vítima: não oriente quem pergunta a agir no lugar dela sem o consentimento "
    "dela. Se ela estiver em perigo agora, diga para ligar 190 e informar o endereço dela."
)


def _resposta_do_agente(classificacao: Classificacao, indice: Callable, cliente, *, ajudando: bool) -> dict | None:
    """Resposta gerada no servidor, ou None para os agentes que rodam no aparelho (com o perfil)."""
    agente, tipo = classificacao.decisao.agente, classificacao.decisao.tipo
    instrucoes = INSTRUCOES_AJUDANDO if ajudando else rag.INSTRUCOES
    if agente == "fora_do_tema":
        # Recusa padrão: sem índice e sem LLM de resposta.
        return {"resposta": FORA_DO_TEMA, "citacoes": [], "recusada": True}
    if agente == "beneficios" and tipo == "explicacao" and explicar_beneficio is not None:
        return explicar_beneficio(classificacao.pergunta, indice(), cliente)
    if agente == "juridico" or (agente == "beneficios" and tipo == "explicacao"):
        return rag.responder(classificacao.pergunta, indice(), cliente, instrucoes=instrucoes)
    return None  # benefícios ("tenho direito?"), triagem e rede


def orquestrar(pedido: PedidoOrquestrar, *, indice: Callable, cliente) -> dict:
    """Corpo da resposta do POST /orquestrar. `indice` é chamado só se algum agente precisar dele.

    Pode lançar llm.LLMIndisponivel ao gerar a resposta: a rota devolve 503.
    """
    # Risco imediato antes de tudo, por regra, sem LLM (spec triagem-risco).
    sinal = risco.avaliar(pedido.texto)
    comum = {
        "risco_imediato": sinal is not None,
        "categoria_risco": sinal["categoria"] if sinal else None,
        "alerta": risco.ALERTA if sinal else None,
    }
    if sinal and not pedido.alerta_visto:
        # Sem o toque em "Continuar com minha pergunta" (ou página antiga): só o alerta, e o texto
        # nunca chega ao LLM. alerta_visto não é controle de segurança: a proteção principal é o
        # alerta no aparelho, antes do envio (design, "Alerta e Continuar com minha pergunta").
        corpo = RespostaOrquestrar(
            **comum, agente=None, tipo=None, campos=Campos(), resposta=None,
            outras_perguntas=[], excedeu=False, decidido_por=None,
        )  # fmt: skip
        return corpo.model_dump()
    classificacao = classificar(pedido.texto, cliente)
    # Só o rótulo de quem decidiu e o agente: nunca o texto, as perguntas reescritas ou os campos.
    logger.info("roteamento decidido_por=%s agente=%s", classificacao.decidido_por, classificacao.decisao.agente)
    corpo = RespostaOrquestrar(
        **comum,
        agente=classificacao.decisao.agente,
        tipo=classificacao.decisao.tipo,
        campos=classificacao.decisao.campos,
        resposta=_resposta_do_agente(classificacao, indice, cliente, ajudando=pedido.ajudando),
        outras_perguntas=classificacao.outras_perguntas,
        excedeu=classificacao.excedeu,
        decidido_por=classificacao.decidido_por,
    )
    return corpo.model_dump()
