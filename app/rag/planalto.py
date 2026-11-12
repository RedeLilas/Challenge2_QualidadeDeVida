"""Coleta e segmentação de normas do Planalto e do SINJ-DF por dispositivo legal.

O Planalto publica o texto compilado: a redação revogada fica riscada (<strike>)
ao lado da redação atual. Removemos o texto riscado para indexar só o vigente;
o HTML bruto de cada coleta fica guardado em dados/fontes/raw/ para consulta histórica.
"""
import hashlib
import re
import time
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup, UnicodeDammit

# O servidor do Planalto não responde a clientes HTTP/2 sem cabeçalhos de navegador.
# requests usa HTTP/1.1.
CABECALHOS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130 Safari/537.36",
    "Accept": "text/html",
    "Accept-Language": "pt-BR",
}

# "(?!\w)" evita ler "Art. 147 - Ameaçar" como art. 147-A.
# "(?:\.\d{3})?" lê o separador de milhar: "Art. 1.584." é o art. 1.584, não o art. 1.
RE_ARTIGO = re.compile(r"^Art\.\s*(\d+(?:\.\d{3})?)\s*(?:º|°|o\b)?\s*(-\s*[A-Z](?!\w))?\s*\.?\s*")
RE_PARAGRAFO = re.compile(r"^(?:§\s*(\d+)\s*(?:º|°)?\s*(-\s*[A-Z](?!\w))?|(Parágrafo único))\s*[.\-–]?\s*")
RE_INCISO = re.compile(r"^([IVXLC]+)(-[A-Z])?\s*[-–]\s*")
RE_ALINEA = re.compile(r"^([a-z])\)\s*")
RE_DIVISAO = re.compile(r"^(TÍTULO|CAPÍTULO|SEÇÃO|Seção|SUBSEÇÃO|Subseção)\s+([IVXLC]+(?:-[A-Z])?)\b\s*(.*)$")
RE_NOTA = re.compile(
    r"\(\s*((?:Redação dada|Incluíd|Acrescid|Revogad|Vide|Vigência|Renumerad|Regulamento|Produção de efeito)[^()]*)\)",
    re.I,
)
# O Planalto às vezes escreve "(VETADO." sem fechar o parêntese.
RE_VETADO = re.compile(r"\(\s*VETADO\s*\.?\s*\)?", re.I)


@dataclass
class Dispositivo:
    id: str
    tipo: str  # caput | paragrafo | inciso | alinea
    artigo: str
    rotulo: str  # "art. 7º, IV"
    texto: str
    status: str  # vigente | revogado | vetado
    notas: list[str] = field(default_factory=list)
    titulo: str = ""
    capitulo: str = ""
    secao: str = ""
    ancora: str = ""
    contexto: str = ""  # caput e dispositivos-pai, para o texto do embedding

    @property
    def hash(self) -> str:
        return hashlib.sha256(self.texto.encode()).hexdigest()


@dataclass
class ResultadoParse:
    dispositivos: list[Dispositivo]
    ignorados: list[str]  # parágrafos sem padrão reconhecido, para revisão humana
    duplicados: list[str]


def baixar(url: str, tentativas: int = 3) -> bytes:
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = requests.get(url, headers=CABECALHOS, timeout=60)
            resposta.raise_for_status()
            return resposta.content
        except requests.RequestException:
            if tentativa == tentativas:
                raise
            time.sleep(5 * tentativa)
    raise AssertionError("inalcançável")


def decodificar(conteudo: bytes) -> str:
    # O Planalto serve páginas em UTF-16 (com BOM) e em windows-1252.
    # O UTF-16 às vezes vem com um byte a mais no fim, por isso errors="replace".
    if conteudo[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return conteudo.decode("utf-16", errors="replace")
    return UnicodeDammit(conteudo, ["utf-8", "windows-1252"]).unicode_markup


def _limpar(texto: str) -> str:
    texto = texto.replace("\xa0", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    texto = re.sub(r"\s+([,.;:)])", r"\1", texto)
    return re.sub(r"(?<=\w)\.{2}$", ".", texto)


def _ordinal(numero: str) -> str:
    return f"{numero}º" if int(numero.replace(".", "")) < 10 else numero


def _romano_minusculo(romano: str) -> str:
    return romano.lower().replace("-", "_")


def parse(html: str) -> ResultadoParse:
    soup = BeautifulSoup(html, "lxml")
    for riscado in soup.find_all(["strike", "s", "del"]):
        riscado.decompose()
    for riscado in soup.find_all(style=re.compile(r"line-through", re.I)):
        riscado.decompose()

    dispositivos: list[Dispositivo] = []
    ignorados: list[str] = []
    ids_vistos: dict[str, int] = {}
    duplicados: list[str] = []

    divisoes = {"titulo": "", "capitulo": "", "secao": ""}
    divisao_sem_nome: str | None = None
    caput: Dispositivo | None = None
    paragrafo: Dispositivo | None = None
    inciso: Dispositivo | None = None

    def registrar(d: Dispositivo) -> None:
        if d.id in ids_vistos:
            ids_vistos[d.id] += 1
            duplicados.append(d.id)
            d.id = f"{d.id}#{ids_vistos[d.id]}"
        else:
            ids_vistos[d.id] = 1
        d.titulo, d.capitulo, d.secao = divisoes["titulo"], divisoes["capitulo"], divisoes["secao"]
        dispositivos.append(d)

    for p in soup.find_all("p"):
        bruto = _limpar(p.get_text(" "))
        if not bruto:
            continue

        notas = [_limpar(n) for n in RE_NOTA.findall(bruto)]
        vetado = bool(RE_VETADO.search(bruto))
        texto = _limpar(RE_VETADO.sub("", RE_NOTA.sub("", bruto)))
        ancora_tag = p.find("a", attrs={"name": True})
        ancora = ancora_tag["name"] if ancora_tag else ""

        # Parágrafo só com nota (ex.: "(Incluído pela Lei nº ...)") pertence ao dispositivo anterior.
        if not texto and notas and dispositivos:
            dispositivos[-1].notas.extend(notas)
            continue
        if not texto:
            continue

        m = RE_DIVISAO.match(texto)
        if m:
            nivel = {"TÍTULO": "titulo", "CAPÍTULO": "capitulo"}.get(m.group(1).upper(), "secao")
            rotulo = f"{m.group(1).capitalize()} {m.group(2)}"
            divisoes[nivel] = f"{rotulo} - {m.group(3)}" if m.group(3) else rotulo
            if nivel == "titulo":
                divisoes["capitulo"] = divisoes["secao"] = ""
            elif nivel == "capitulo":
                divisoes["secao"] = ""
            divisao_sem_nome = None if m.group(3) else nivel
            continue
        if divisao_sem_nome and not RE_ARTIGO.match(texto):
            divisoes[divisao_sem_nome] += f" - {texto}"
            divisao_sem_nome = None
            continue
        divisao_sem_nome = None

        def status(corpo: str) -> str:
            if vetado:
                return "vetado"
            if not corpo and any(n.lower().startswith("revogad") for n in notas):
                return "revogado"
            return "vigente"

        if m := RE_ARTIGO.match(texto):
            numero = m.group(1) + (m.group(2) or "").replace(" ", "")
            corpo = texto[m.end():]
            caput = Dispositivo(
                # O ponto já separa as partes do id ("art1584.par2"), então sai do número.
                id=f"art{numero.replace('.', '').lower()}",
                tipo="caput",
                artigo=numero,
                rotulo=f"art. {_ordinal(m.group(1))}{(m.group(2) or '').replace(' ', '')}",
                texto=texto,
                status=status(corpo),
                notas=notas,
                ancora=ancora,
            )
            paragrafo = inciso = None
            registrar(caput)
        elif caput and (m := RE_PARAGRAFO.match(texto)):
            if m.group(3):
                sufixo, rotulo = "par_unico", "parágrafo único"
            else:
                letra = (m.group(2) or "").replace(" ", "")
                sufixo, rotulo = f"par{m.group(1)}{letra.lower()}", f"§ {_ordinal(m.group(1))}{letra}"
            paragrafo = Dispositivo(
                id=f"{caput.id}.{sufixo}",
                tipo="paragrafo",
                artigo=caput.artigo,
                rotulo=f"{caput.rotulo}, {rotulo}",
                texto=texto,
                status=status(texto[m.end():]),
                notas=notas,
                ancora=ancora,
                contexto=caput.texto,
            )
            inciso = None
            registrar(paragrafo)
        elif caput and (m := RE_INCISO.match(texto)):
            pai = paragrafo or caput
            romano = m.group(1) + (m.group(2) or "")
            inciso = Dispositivo(
                id=f"{pai.id}.inc_{_romano_minusculo(romano)}",
                tipo="inciso",
                artigo=caput.artigo,
                rotulo=f"{pai.rotulo}, {romano}",
                texto=texto,
                status=status(texto[m.end():]),
                notas=notas,
                ancora=ancora,
                contexto=" ".join(filter(None, [pai.contexto, pai.texto])),
            )
            registrar(inciso)
        elif caput and (m := RE_ALINEA.match(texto)):
            pai = inciso or paragrafo or caput
            registrar(
                Dispositivo(
                    id=f"{pai.id}.ali_{m.group(1)}",
                    tipo="alinea",
                    artigo=caput.artigo,
                    rotulo=f"{pai.rotulo}, {m.group(1)}",
                    texto=texto,
                    status=status(texto[m.end():]),
                    notas=notas,
                    ancora=ancora,
                    contexto=" ".join(filter(None, [pai.contexto, pai.texto])),
                )
            )
        elif texto.startswith("Pena") and caput:
            # Pena de tipo penal fica em parágrafo próprio, mas pertence ao dispositivo anterior.
            dispositivos[-1].texto += f" {texto}"
        else:
            ignorados.append(texto)

    return ResultadoParse(dispositivos, ignorados, duplicados)
