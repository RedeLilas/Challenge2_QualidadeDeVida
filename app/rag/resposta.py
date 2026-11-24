"""Resposta jurídica com citação: recuperação no eixo jurídico, prompt, LLM e verificação de citação.

A verificação extrai do texto do LLM cada referência a artigo ("art. 7º", "artigo 5", "arts. 18 e 22")
e a norma mais próxima no texto ("Lei 11.340/2006", "Lei Maria da Penha", "Código Penal"). A resposta
só é exibida se tiver ao menos uma citação e todas estiverem entre os trechos recuperados; senão,
o sistema recusa (spec orientacao-juridica: "Citação conferida" e "Recusa sem fundamentação").
"""
from dataclasses import dataclass
import re
import unicodedata

K = 5
EIXOS = {"juridico"}
EIXOS_BENEFICIOS = {"beneficios", "df"}
# Abaixo desta similaridade (cosseno, e5-base) com o trecho mais parecido, recusa sem chamar o LLM.
# Recalibrado em 15/11, com a base ampliada e só as perguntas de desenvolvimento: menor pergunta do
# tema 0,826; extras fora do tema de 0,796 a 0,831. As faixas se sobrepõem, então o limite fica
# abaixo do tema, e as extras que passam dependem da recusa por falta de citação
# (openspec/changes/s3-base-legal-ampliada/design.md).
LIMITE_SIMILARIDADE = 0.81
# Calibrado em 17/11 só com avaliacao/conjuntos/s4/desenvolvimento_beneficios.yaml (após expansão de "bpc"):
# 22 perguntas do tema de 0,8175 (bd-013) a 0,8959 (bd-018); 8 extras quase do tema de 0,8123 (bd-x04)
# a 0,8629 (bd-x08). Em 0,815 nenhuma pergunta do tema é recusada, bd-x04 é barrada pelo limite e as
# outras 7 extras dependem da recusa por verificação de citação (openspec/changes/archive/2026-11-24-s4-rag-beneficios/design.md).
LIMITE_BENEFICIOS = 0.815
# Siglas leigas ausentes do texto das normas de benefícios (s4-rag-beneficios, tarefa 3.3).
# A Lei 8.742/1993 escreve "benefício de prestação continuada" por extenso e nunca traz a sigla "BPC".
# Aplicadas só ao texto da busca no índice; a pergunta enviada ao LLM continua a original.
SIGLAS_BENEFICIOS = {
    r"\bbpc\b": "benefício de prestação continuada (bpc)",
}
# Normas do eixo jurídico. Uma referência a outra norma nunca é aceita.
LEIS_JURIDICAS = ("Lei 11.340/2006", "Lei 14.149/2021", "Código Penal", "Código Civil", "Código de Processo Civil")
# A Lei 14.713/2023 alterou o art. 1.584 do Código Civil e incluiu o art. 699-A no CPC: é apelido dos dois.
APELIDOS = {
    "Lei 11.340/2006": ["maria da penha"],
    "Código Penal": ["codigo penal", r"2\.?848"],
    "Código Civil": [r"10\.?406", r"14\.?713"],
    "Código de Processo Civil": [r"\bcpc\b", r"13\.?105", r"14\.?713"],
}
# 11 normas dos eixos beneficios e df (s4-rag-beneficios).
LEIS_BENEFICIOS = (
    "Lei 14.601/2023",
    "Lei 8.742/1993 (LOAS)",
    "Lei Distrital 6.623/2020",
    "Decreto Distrital 45.989/2024",
    "Portaria SMDF 49/2026",
    "Lei Distrital 6.938/2021",
    "Decreto Distrital 42.376/2021",
    "Lei Distrital 7.009/2021",
    "Decreto Distrital 42.873/2021",
    "Lei Distrital 5.165/2013",
    "Decreto Distrital 35.191/2014",
)
# Apelidos sem acento, com ponto e "/ano" opcionais e "Distrital"/"SMDF" opcionais.
# Nomes de programa compartilhados entre lei e decreto ("cartão gás", "prato cheio") apontam só para a lei.
APELIDOS_BENEFICIOS = {
    "Lei 14.601/2023": [
        r"\blei\s+(?:n[º°o.]*\s*)?14\.?601(?:/2023)?\b",
        r"\b14\.?601(?:/2023)?\b",
        r"\bbolsa\s+familia\b",
    ],
    "Lei 8.742/1993 (LOAS)": [
        r"\blei\s+(?:n[º°o.]*\s*)?8\.?742(?:/1993)?\b",
        r"\b8\.?742(?:/1993)?\b",
        r"\bloas\b",
    ],
    "Lei Distrital 6.623/2020": [
        r"\blei\s+(?:distrital\s+)?(?:n[º°o.]*\s*)?6\.?623(?:/2020)?\b",
    ],
    "Decreto Distrital 45.989/2024": [
        r"\bdecreto\s+(?:distrital\s+)?(?:n[º°o.]*\s*)?45\.?989(?:/2024)?\b",
    ],
    "Portaria SMDF 49/2026": [
        r"\bportaria\s+(?:smdf\s+)?(?:n[º°o.]*\s*)?49(?:/2026)?\b",
    ],
    "Lei Distrital 6.938/2021": [
        r"\blei\s+(?:distrital\s+)?(?:n[º°o.]*\s*)?6\.?938(?:/2021)?\b",
        r"\bcartao\s+gas\b",
    ],
    "Decreto Distrital 42.376/2021": [
        r"\bdecreto\s+(?:distrital\s+)?(?:n[º°o.]*\s*)?42\.?376(?:/2021)?\b",
    ],
    "Lei Distrital 7.009/2021": [
        r"\blei\s+(?:distrital\s+)?(?:n[º°o.]*\s*)?7\.?009(?:/2021)?\b",
        r"\bprato\s+cheio\b",
    ],
    "Decreto Distrital 42.873/2021": [
        r"\bdecreto\s+(?:distrital\s+)?(?:n[º°o.]*\s*)?42\.?873(?:/2021)?\b",
    ],
    "Lei Distrital 5.165/2013": [
        r"\blei\s+(?:distrital\s+)?(?:n[º°o.]*\s*)?5\.?165(?:/2013)?\b",
    ],
    "Decreto Distrital 35.191/2014": [
        r"\bdecreto\s+(?:distrital\s+)?(?:n[º°o.]*\s*)?35\.?191(?:/2014)?\b",
    ],
}
_TODOS_APELIDOS = {**APELIDOS, **APELIDOS_BENEFICIOS}


@dataclass(frozen=True)
class ConfigVerificacao:
    """Configuração de verificação de citações por agente (s4-rag-beneficios)."""

    leis: tuple[str, ...]
    apelidos: dict[str, list[str]]
    recusar_artigo_sem_norma_em_varias_leis: bool = False


JURIDICO = ConfigVerificacao(
    leis=LEIS_JURIDICAS,
    apelidos=APELIDOS,
    recusar_artigo_sem_norma_em_varias_leis=False,
)
BENEFICIOS = ConfigVerificacao(
    leis=LEIS_BENEFICIOS,
    apelidos=APELIDOS_BENEFICIOS,
    recusar_artigo_sem_norma_em_varias_leis=True,
)
# Distância máxima, em caracteres, entre o artigo e o nome da norma para associar os dois.
DISTANCIA_MAXIMA = 80

RECUSA = (
    "Não consigo responder a essa pergunta com segurança a partir da lei. "
    "Para orientação, ligue 180 (gratuito, 24 horas) ou procure a Defensoria Pública do DF, "
    "que atende de graça."
)

RECUSA_BENEFICIOS = (
    "Não consigo explicar esse benefício com segurança a partir das normas disponíveis. "
    "Para orientação sobre benefícios e inscrição, procure o CRAS (Centro de Referência de Assistência Social) "
    "mais próximo ou ligue 180 (gratuito, 24 horas)."
)

AVISO_BENEFICIOS = "Valores e regras podem mudar por decreto. Norma consultada em {data}."

INSTRUCOES = (
    "Você orienta mulheres sobre a Lei Maria da Penha e normas relacionadas, com linguagem simples "
    "e frases curtas.\n"
    "- Escreva sempre e somente em português do Brasil, nunca em outro idioma.\n"
    "- Não prometa resultado nem diga que a pessoa tem direito garantido: diga o que a lei prevê "
    "e quem decide (por exemplo, \"o juiz pode conceder\").\n"
    "- Responda usando apenas os trechos de lei enviados junto com a pergunta. Não use conhecimento de fora deles.\n"
    "- Cite a norma e o artigo de cada informação, entre parênteses, no formato do rótulo do trecho, "
    "por exemplo: (Lei 11.340/2006, art. 7º). Cite somente artigos que aparecem nos trechos.\n"
    "- Quando usar um termo jurídico, explique-o em uma frase simples.\n"
    "- Se os trechos não bastarem para responder, diga apenas que não sabe responder com segurança.\n"
    "- Você oferece orientação e não substitui advogada ou defensora; não redija petições.\n"
    "- Se a pessoa estiver em perigo agora, diga para ligar 190."
)

INSTRUCOES_BENEFICIOS = (
    "Você explica benefícios sociais federais e do Distrito Federal para mulheres, com linguagem simples "
    "e frases curtas.\n"
    "- Escreva sempre e somente em português do Brasil, nunca em outro idioma.\n"
    "- Explique apenas o que a norma prevê sobre o benefício (o que é, como funciona e quem pode pedir) "
    "e nunca diga se a pessoa atende aos requisitos ou se vai receber; a concessão depende da análise do órgão responsável.\n"
    "- Indique a tela Benefícios para avaliar o perfil e o CRAS para fazer o pedido.\n"
    "- Responda usando apenas os trechos de norma enviados junto com a pergunta. Não use conhecimento de fora deles.\n"
    "- Cite a norma e o artigo de cada informação, entre parênteses, no formato do rótulo do trecho, "
    "por exemplo: (Lei 8.742/1993 (LOAS), art. 20) ou (Lei Distrital 6.938/2021, art. 1º). "
    "Cite somente artigos que aparecem nos trechos.\n"
    "- Quando usar um termo técnico ou da norma, explique-o em uma frase simples.\n"
    "- Se os trechos não bastarem para explicar, diga apenas que não sabe explicar com segurança.\n"
    "- Responda em no máximo 5 frases curtas. Se o assunto for maior, diga o essencial e indique a tela "
    "Benefícios ou o CRAS para o resto.\n"
    "- Não mencione artigos que aparecem só dentro do texto de outro artigo (por exemplo, \"os critérios "
    "do art. 3º\"): cite apenas os artigos dos rótulos dos trechos.\n"
    "- Se a pessoa estiver em perigo agora, diga para ligar 190."
)

# Versão sem RAG, usada só na comparação LLM x RAG da S3 (scripts de avaliação), nunca na
# aplicação. Muda apenas as frases sobre os trechos: sai a regra de usar só os trechos, e as
# outras duas são adaptadas para fazer sentido sem eles. None remove a frase. Se uma dessas
# frases mudar em INSTRUCOES, tests/test_instrucoes_sem_rag.py falha (a aplicação não é afetada).
_TROCAS_SEM_RAG = {
    "- Responda usando apenas os trechos de lei enviados junto com a pergunta. "
    "Não use conhecimento de fora deles.": None,
    "- Cite a norma e o artigo de cada informação, entre parênteses, no formato do rótulo do trecho, "
    "por exemplo: (Lei 11.340/2006, art. 7º). Cite somente artigos que aparecem nos trechos.":
        "- Cite a norma e o artigo de cada informação, entre parênteses, "
        "por exemplo: (Lei 11.340/2006, art. 7º).",
    "- Se os trechos não bastarem para responder, diga apenas que não sabe responder com segurança.":
        "- Se não tiver certeza da resposta, diga apenas que não sabe responder com segurança.",
}  # fmt: skip
INSTRUCOES_SEM_RAG = "\n".join(
    _TROCAS_SEM_RAG.get(linha, linha)
    for linha in INSTRUCOES.split("\n")
    if _TROCAS_SEM_RAG.get(linha, linha) is not None
)

# "(?:\.\d{3})?" lê o separador de milhar: "art. 1.584" é o art. 1.584, não o art. 1.
RE_ARTIGO = re.compile(r"\b(art(?:igo)?s?)\.?\s*(\d+(?:\.\d{3})?(?:-[a-z])?)(?!\d)\s*[º°o]?", re.IGNORECASE)
RE_MAIS_ARTIGOS = re.compile(r"\s*(?:,|\be\b)\s*(\d+(?:\.\d{3})?(?:-[a-z])?)(?!\d)\s*[º°o]?", re.IGNORECASE)
# Aplicado ao texto sem acento: "isso constitui violência" não é a Constituição.
RE_OUTRA_LEI = re.compile(r"\blei\s+(?:n[º°o.]*\s*)?(\d{1,2}\.?\d{3})\b|\bconstituicao\b", re.IGNORECASE)


def rotulo(lei: str, artigo: str) -> str:
    """'Lei 11.340/2006, art. 7º' (ordinal até o 9º, cardinal a partir do 10)."""
    ordinal = "º" if artigo.isdigit() and int(artigo) < 10 else ""
    return f"{lei}, art. {artigo}{ordinal}"


def montar_mensagens(pergunta: str, trechos: list[dict], *, instrucoes: str = INSTRUCOES) -> list[dict]:
    blocos = "\n\n".join(f"[{rotulo(t['lei'], t['artigo'])}]\n{t['texto']}" for t in trechos)
    return [
        {"role": "system", "content": instrucoes},
        {"role": "user", "content": f"Trechos de lei:\n\n{blocos}\n\n{_pergunta(pergunta)}"},
    ]


def montar_mensagens_sem_rag(pergunta: str) -> list[dict]:
    """Mensagens da versão sem RAG da comparação da S3: a mesma pergunta, sem trechos."""
    return [
        {"role": "system", "content": INSTRUCOES_SEM_RAG},
        {"role": "user", "content": _pergunta(pergunta)},
    ]


def _pergunta(pergunta: str) -> str:
    return f"Pergunta: {pergunta}"


def _sem_acento(texto: str) -> str:
    # Mantém o comprimento do texto, para as posições continuarem valendo.
    return "".join(unicodedata.normalize("NFD", c)[0] for c in texto).lower()


def _mencoes_de_leis(
    texto: str, leis: list[str], apelidos: dict[str, list[str]] | None = None
) -> list[tuple[int, int, str]]:
    """(início, fim, lei) de cada menção a uma norma no texto."""
    mapa_apelidos = _TODOS_APELIDOS if apelidos is None else apelidos
    base = _sem_acento(texto)
    mencoes = []
    for lei in leis:
        padroes = list(mapa_apelidos.get(lei, []))
        numero = re.match(r"Lei (\d+)\.(\d+)/\d{4}$", lei)
        padroes.append(rf"{numero[1]}\.?{numero[2]}" if numero else re.escape(_sem_acento(lei)))
        for padrao in padroes:
            mencoes += [(m.start(), m.end(), lei) for m in re.finditer(padrao, base)]
    conhecidas = {(i, f) for i, f, _ in mencoes}
    for m in RE_OUTRA_LEI.finditer(base):
        if not any(i <= m.start(1 if m[1] else 0) < f for i, f in conhecidas):
            mencoes.append((m.start(), m.end(), f"Lei {m[1]}" if m[1] else "Constituição Federal"))
    return mencoes


def extrair_referencias(
    texto: str, leis: list[str], apelidos: dict[str, list[str]] | None = None
) -> list[tuple[str | tuple[str, ...] | None, str]]:
    """(lei, artigo) citados no texto, na ordem; lei é None quando nenhuma norma aparece perto.

    Quando a menção mais próxima vale para mais de uma norma (a Lei 14.713/2023), lei é a tupla delas.
    """
    mencoes = _mencoes_de_leis(texto, leis, apelidos=apelidos)
    referencias = []
    for m in RE_ARTIGO.finditer(texto):
        artigos, fim = [m[2]], m.end()
        if m[1].lower().endswith("s"):  # "arts." e "artigos" podem trazer uma lista
            while mais := RE_MAIS_ARTIGOS.match(texto, fim):
                artigos.append(mais[1])
                fim = mais.end()

        def distancia(mencao):
            inicio, termino, _ = mencao
            return m.start() - termino if termino <= m.start() else max(inicio - fim, 0)

        proximas = [(distancia(x), x[2]) for x in mencoes if distancia(x) <= DISTANCIA_MAXIMA]
        lei = None
        if proximas:
            menor = min(d for d, _ in proximas)
            empatadas = sorted({nome for d, nome in proximas if d == menor})
            lei = empatadas[0] if len(empatadas) == 1 else tuple(empatadas)
        referencias += [(lei, artigo.upper()) for artigo in artigos]
    return referencias


def verificar_citacoes(
    texto: str, recuperados: list[dict], verificacao: ConfigVerificacao = JURIDICO
) -> list[dict] | None:
    """Citações da resposta, se todas estiverem entre os trechos recuperados; senão None."""
    leis = sorted(set(verificacao.leis) | {t["lei"] for t in recuperados})
    referencias = extrair_referencias(texto, leis, apelidos=verificacao.apelidos)
    if not referencias:
        return None

    def sem_ponto(artigo: str) -> str:
        # O LLM pode escrever "art. 1584" para o art. 1.584.
        return artigo.replace(".", "").upper()

    aceita_sem_lei = not (
        verificacao.recusar_artigo_sem_norma_em_varias_leis and len({t["lei"] for t in recuperados}) > 1
    )

    def da_lei(lei, t: dict) -> bool:
        return (lei is None and aceita_sem_lei) or t["lei"] == lei or (isinstance(lei, tuple) and t["lei"] in lei)

    citacoes = {}
    for lei, artigo in referencias:
        trecho = next(
            (t for t in recuperados if sem_ponto(t["artigo"]) == sem_ponto(artigo) and da_lei(lei, t)), None
        )
        if trecho is None:
            return None
        chave = (trecho["lei"], trecho["artigo"])
        citacoes.setdefault(
            chave,
            {
                "lei": trecho["lei"],
                "artigo": trecho["artigo"],
                "citacao": rotulo(trecho["lei"], trecho["artigo"]),
                "url": trecho["url"],
                "data_acesso": trecho["data_acesso"],
            },
        )
    return list(citacoes.values())


# Palavras frequentes que distinguem o português do inglês e do espanhol num texto em alfabeto latino.
MARCAS_PORTUGUES = {"não", "você", "é", "são", "uma", "para", "pela", "pelo", "com", "os", "as", "da", "do",
                    "das", "dos", "ao", "em", "no", "na", "pode", "que", "ele", "ela", "seu", "sua"}  # fmt: skip
MARCAS_OUTRAS = {"the", "and", "you", "is", "are", "of", "to", "can", "with", "your", "that", "he", "she",
                 "el", "y", "usted", "puede", "del", "los", "las", "ley", "si", "su"}  # fmt: skip
ORDINAIS = set("ºª")  # "1º" e "1ª": letras para o Unicode, mas não são de outro alfabeto


def em_portugues(texto: str) -> bool:
    """Falso se houver letras de outro alfabeto (ex.: chinês) ou se o texto parecer inglês ou espanhol."""
    if any(c.isalpha() and c not in ORDINAIS and not unicodedata.name(c, "").startswith("LATIN") for c in texto):
        return False
    palavras = re.findall(r"[^\W\d_]+", texto.lower())
    portugues = sum(p in MARCAS_PORTUGUES for p in palavras)
    outras = sum(p in MARCAS_OUTRAS for p in palavras)
    # Textos curtos têm poucas marcas; só decide pelas palavras quando há o bastante para comparar.
    return outras < 3 or portugues > outras


def _normalizar_data(data: str) -> tuple[str, str]:
    """Devolve (AAAA-MM-DD, DD/MM/AAAA) para ordenar datas e exibir no aviso."""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", data):
        ano, mes, dia = data.split("-")
        return data, f"{dia}/{mes}/{ano}"
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", data):
        dia, mes, ano = data.split("/")
        return f"{ano}-{mes}-{dia}", data
    return data, data


def aviso_beneficios(citacoes: list[dict]) -> str | None:
    """Aviso fixo com a data da coleta mais antiga entre as normas citadas (DD/MM/AAAA)."""
    datas = [_normalizar_data(c["data_acesso"]) for c in citacoes if c.get("data_acesso")]
    if not datas:
        return None
    _, mais_antiga = min(datas, key=lambda par: par[0])
    return AVISO_BENEFICIOS.format(data=mais_antiga)


def expandir_siglas_beneficios(pergunta: str) -> str:
    """Expande siglas ausentes do texto das normas de benefícios só para a busca no índice."""
    texto = pergunta
    for padrao, expansao in SIGLAS_BENEFICIOS.items():
        texto = re.sub(padrao, expansao, texto, flags=re.IGNORECASE)
    return texto


def responder(
    pergunta: str,
    indice,
    cliente,
    *,
    eixos: set[str] = EIXOS,
    instrucoes: str = INSTRUCOES,
    limite: float = LIMITE_SIMILARIDADE,
    verificacao: ConfigVerificacao = JURIDICO,
    recusa: str = RECUSA,
    incluir_aviso: bool = False,
    pergunta_busca: str | None = None,
) -> dict:
    """Recupera os trechos, pergunta ao LLM e só devolve a resposta em português e com as citações conferidas."""
    extra_recusa = {"aviso": None} if incluir_aviso else {}
    consulta = pergunta if pergunta_busca is None else pergunta_busca
    resultados = indice.buscar(consulta, k=K, eixos=eixos)
    if not resultados or resultados[0][1] < limite:
        # A base não sustenta a resposta: recusa sem gastar uma chamada ao LLM.
        return {"resposta": recusa, "citacoes": [], "recusada": True, **extra_recusa}
    recuperados = [t for t, _ in resultados]
    texto = cliente.responder(montar_mensagens(pergunta, recuperados, instrucoes=instrucoes))
    citacoes = verificar_citacoes(texto, recuperados, verificacao=verificacao) if em_portugues(texto) else None
    if citacoes is None:
        return {"resposta": recusa, "citacoes": [], "recusada": True, **extra_recusa}
    extra_ok = {"aviso": aviso_beneficios(citacoes)} if incluir_aviso else {}
    return {"resposta": texto, "citacoes": citacoes, "recusada": False, **extra_ok}


def explicar_beneficio(
    pergunta: str,
    indice,
    cliente,
    *,
    limite: float = LIMITE_BENEFICIOS,
) -> dict:
    """Explica um benefício usando os eixos beneficios e df, instruções próprias, recusa e aviso de data."""
    return responder(
        pergunta,
        indice,
        cliente,
        eixos=EIXOS_BENEFICIOS,
        instrucoes=INSTRUCOES_BENEFICIOS,
        limite=limite,
        verificacao=BENEFICIOS,
        recusa=RECUSA_BENEFICIOS,
        incluir_aviso=True,
        pergunta_busca=expandir_siglas_beneficios(pergunta),
    )


responder_beneficios = explicar_beneficio
