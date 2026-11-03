import re
from datetime import date

import pytest

from app.rag import ingestao, planalto
from app.rag.indice import carregar_trechos

HTML_FICTICIO = """
<html><body>
<p>LEI Nº 0, DE 1º DE JANEIRO DE 2000</p>
<p>CAPÍTULO I</p>
<p>DAS DISPOSIÇÕES GERAIS</p>
<p><a name="art1"></a>Art. 1º Esta Lei trata de um exemplo.</p>
<p><strike>Art. 2º Redação antiga que foi alterada.</strike></p>
<p><a name="art2"></a>Art. 2º Redação nova. <a href="#">(Redação dada pela Lei nº 1, de 2001)</a></p>
<p>I - primeiro inciso;</p>
<p>a) alínea do primeiro inciso;</p>
<p>II - (VETADO).</p>
<p>Parágrafo único. Parágrafo do artigo 2º.</p>
<p>Art. 3º (Revogado pela Lei nº 2, de 2002)</p>
<p>Art. 4º-A. Descumprir decisão judicial:</p>
<p>Pena - detenção, de 1 (um) a 2 (dois) anos.</p>
</body></html>
"""


@pytest.fixture(scope="module")
def dispositivos():
    return {d.id: d for d in planalto.parse(HTML_FICTICIO).dispositivos}


def test_remove_texto_riscado(dispositivos):
    assert "Redação antiga" not in " ".join(d.texto for d in dispositivos.values())
    assert dispositivos["art2"].texto == "Art. 2º Redação nova."
    assert dispositivos["art2"].notas == ["Redação dada pela Lei nº 1, de 2001"]


def test_hierarquia_e_status(dispositivos):
    assert dispositivos["art2.inc_i.ali_a"].rotulo == "art. 2º, I, a"
    assert dispositivos["art2.par_unico"].rotulo == "art. 2º, parágrafo único"
    assert dispositivos["art2.inc_ii"].status == "vetado"
    assert dispositivos["art3"].status == "revogado"
    assert dispositivos["art1"].capitulo == "Capítulo I - DAS DISPOSIÇÕES GERAIS"


def test_pena_fica_no_artigo(dispositivos):
    assert dispositivos["art4-a"].texto.endswith("Pena - detenção, de 1 (um) a 2 (dois) anos.")


def test_decodifica_utf16_com_byte_sobrando():
    conteudo = HTML_FICTICIO.encode("utf-16") + b"\x00"
    assert "Art. 1º" in planalto.decodificar(conteudo)


def test_trechos_ignoram_revogados_e_vetados(dispositivos):
    trechos = ingestao.trechos(list(dispositivos.values()), "2026-11-03")
    assert [t["artigo"] for t in trechos] == ["1", "2", "4-A"]
    assert "VETADO" not in trechos[1]["texto"]


# Testes sobre o arquivo versionado dados/leis/lei_11340.jsonl

ARTIGOS_COM_LETRA = {"10-A", "12-A", "12-B", "12-C", "12-D", "14-A", "16-A", "17-A", "24-A", "38-A", "40-A"}


@pytest.fixture(scope="module")
def trechos_lei():
    return carregar_trechos()


def test_numero_de_artigos(trechos_lei):
    # Se falhar, a lei mudou: revisar o diff de dados/leis/ antes de atualizar o teste.
    esperados = {str(n) for n in range(1, 47)} | ARTIGOS_COM_LETRA
    assert {t["artigo"] for t in trechos_lei} == esperados


def test_sem_texto_revogado(trechos_lei):
    textos = " ".join(t["texto"] for t in trechos_lei)
    assert "auto-estima" not in textos  # redação antiga do art. 7º, II
    assert "autoestima" in textos
    assert "VETADO" not in textos
    assert "lei_11340-art22.par5" not in {t["id"] for t in trechos_lei}  # art. 22, § 5º revogado


def test_todo_trecho_tem_url_e_data(trechos_lei):
    for t in trechos_lei:
        assert t["url"].startswith(ingestao.LEI["url"])
        date.fromisoformat(t["data_acesso"])
        assert re.match(r"Lei 11\.340/2006, art\. \d+", t["citacao"])
