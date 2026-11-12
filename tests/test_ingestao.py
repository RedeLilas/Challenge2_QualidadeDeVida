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


def test_artigo_seguido_de_travessao_nao_vira_artigo_com_letra():
    # Código Penal: "Art. 147 - Ameaçar" é o art. 147, não o 147-A.
    html = "<p>Art. 147 - Ameaçar alguém.</p><p>§ 1 - Primeiro.</p><p>Art. 147-A. Perseguir alguém.</p>"
    ids = [d.id for d in planalto.parse(html).dispositivos]
    assert ids == ["art147", "art147.par1", "art147-a"]


def test_artigo_com_separador_de_milhar():
    # Código Civil: "Art. 1.584." é o art. 1.584, não o art. 1.
    html = "<p>Art. 1.584. A guarda será atribuída:</p><p>§ 2º Texto fictício do parágrafo.</p>"
    caput, paragrafo = planalto.parse(html).dispositivos
    assert (caput.id, caput.artigo, caput.rotulo) == ("art1584", "1.584", "art. 1.584")
    assert (paragrafo.id, paragrafo.rotulo) == ("art1584.par2", "art. 1.584, § 2º")


def test_artigo_com_letra_sem_ordinal():
    # CPC: "Art. 699-A." é o art. 699-A.
    caput = planalto.parse("<p>Art. 699-A. Texto fictício do artigo.</p>").dispositivos[0]
    assert (caput.id, caput.artigo, caput.rotulo) == ("art699-a", "699-A", "art. 699-A")


def test_artigos_sem_separador_continuam_iguais():
    html = "<p>Art. 1º Primeiro.</p><p>Art. 147 - Ameaçar alguém.</p><p>Art. 1000. Mil, sem ponto.</p>"
    assert [(d.id, d.artigo, d.rotulo) for d in planalto.parse(html).dispositivos] == [
        ("art1", "1", "art. 1º"),
        ("art147", "147", "art. 147"),
        ("art1000", "1000", "art. 1000"),
    ]


def test_vetado_sem_parentese_de_fechamento():
    html = "<p>Art. 1º Exemplo:</p><p>I - (VETADO.</p>"
    assert {d.id: d.status for d in planalto.parse(html).dispositivos}["art1.inc_i"] == "vetado"


def test_hash_do_dispositivo_depende_so_do_texto(dispositivos):
    assert dispositivos["art1"].hash == planalto.hashlib.sha256(b"Art. 1\xc2\xba Esta Lei trata de um exemplo.").hexdigest()


NORMA_FICTICIA = {
    "id": "lei-0-2000",
    "eixo": "juridico",
    "citacao": "Lei 0/2000",
    "urn": "urn:lex:br:federal:lei:2000-01-01;0",
    "url": "https://www.planalto.gov.br/exemplo.htm",
}


def test_trechos_ignoram_revogados_e_vetados(dispositivos):
    trechos = ingestao.trechos(NORMA_FICTICIA, list(dispositivos.values()), "2026-11-03")
    assert [t["artigo"] for t in trechos] == ["1", "2", "4-A"]
    assert "VETADO" not in trechos[1]["texto"]
    assert trechos[0]["id"] == "lei-0-2000:art1"
    assert trechos[0]["citacao"] == "Lei 0/2000, art. 1º"
    assert {t["eixo"] for t in trechos} == {"juridico"}


def test_dispositivo_reconstruido_do_registro_da_coleta(dispositivos):
    original = dispositivos["art2"]
    registro = {**vars(original), "url_fonte": f"{NORMA_FICTICIA['url']}#{original.ancora}"}
    assert ingestao.dispositivo(registro) == original


def test_eixo_invalido_e_rejeitado(tmp_path):
    fontes = tmp_path / "fontes.yaml"
    fontes.write_text("normas:\n  - id: lei-0-2000\n    eixo: penal\n", encoding="utf-8")
    with pytest.raises(ValueError, match="eixo"):
        ingestao.carregar_normas(fontes)


# Testes sobre os arquivos versionados em dados/leis/

ARTIGOS_COM_LETRA = {"10-A", "12-A", "12-B", "12-C", "12-D", "14-A", "16-A", "17-A", "24-A", "38-A", "40-A"}


@pytest.fixture(scope="module")
def todos_os_trechos():
    return carregar_trechos()


@pytest.fixture(scope="module")
def trechos_lei(todos_os_trechos):
    return [t for t in todos_os_trechos if t["norma_id"] == "lei-11340-2006"]


def test_numero_de_artigos(trechos_lei):
    # Se falhar, a lei mudou: revisar o diff de dados/leis/ antes de atualizar o teste.
    esperados = {str(n) for n in range(1, 47)} | ARTIGOS_COM_LETRA
    assert {t["artigo"] for t in trechos_lei} == esperados


def test_sem_texto_revogado(trechos_lei):
    textos = " ".join(t["texto"] for t in trechos_lei)
    assert "auto-estima" not in textos  # redação antiga do art. 7º, II
    assert "autoestima" in textos
    assert "VETADO" not in textos  # inclui o art. 12-B, § 2º, escrito "(VETADO." sem parêntese
    assert "lei-11340-2006:art22.par5" not in {t["id"] for t in trechos_lei}  # art. 22, § 5º revogado


def test_toda_norma_de_fontes_tem_trechos(todos_os_trechos):
    normas = ingestao.carregar_normas()
    assert {t["norma_id"] for t in todos_os_trechos} == {n["id"] for n in normas}


def test_todo_trecho_tem_url_oficial_data_e_citacao(todos_os_trechos):
    normas = {n["id"]: n for n in ingestao.carregar_normas()}
    for t in todos_os_trechos:
        norma = normas[t["norma_id"]]
        assert t["url"].startswith(norma["url"])
        date.fromisoformat(t["data_acesso"])
        assert t["citacao"].startswith(f"{norma['citacao']}, art. ")
        assert t["eixo"] == norma["eixo"]
        assert t["id"].startswith(f"{norma['id']}:")


def test_ids_unicos(todos_os_trechos):
    ids = [t["id"] for t in todos_os_trechos]
    assert len(ids) == len(set(ids))
