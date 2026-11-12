"""Arquivos enviados ao corretor (s3-avaliacao-llm-vs-rag, tarefa 3.3). Tudo fictício."""
import json
import re

import pytest
import yaml

from scripts.envios import ARQUIVO_ERRADAS, ErroEnvio, preparar
from scripts.rodada import rodar
from test_rodada import AGORA, IndiceFalso, LLMFalso, pastas  # noqa: F401  (pastas é fixture)

ERRADAS = {
    "versao": 1,
    "erradas": [
        {"id": "errada-1", "pergunta_id": "q-001", "autor": "Pessoa A",
         "resposta": "Isso nunca é violência (Lei 11.340/2006, art. 7º).", "erro": "contradiz o art. 7º"},
        {"id": "errada-2", "pergunta_id": "q-002", "autor": "Pessoa A",
         "resposta": "A medida vale para sempre (Lei 11.340/2006, art. 99).", "erro": "artigo inexistente"},
        {"id": "errada-3", "pergunta_id": "q-003", "autor": "Pessoa B",
         "resposta": "Só a polícia pode pedir (Lei 11.340/2006, art. 7º).", "erro": "falta o ponto obrigatório"},
    ],
}  # fmt: skip


def dispositivo(artigo, tipo, texto):
    return {"citacao": f"Lei 11.340/2006, art. {artigo}º", "artigo": artigo, "tipo": tipo, "texto": texto}


@pytest.fixture
def rodada(pastas, tmp_path):  # noqa: F811
    conjuntos, rodadas = pastas
    (conjuntos / ARQUIVO_ERRADAS).write_text(yaml.safe_dump(ERRADAS, allow_unicode=True), encoding="utf-8")
    norma = tmp_path / "dispositivos" / "lei-11340-2006"
    norma.mkdir(parents=True)
    antigo = [dispositivo("7", "caput", "Art. 7º Texto antigo.")]
    atual = [dispositivo("7", "caput", "Art. 7º São formas fictícias:"), dispositivo("7", "inciso", "I - inciso fictício;")]
    for nome, registros in (("2026-11-03.jsonl", antigo), ("2026-11-10.jsonl", atual)):
        (norma / nome).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in registros), encoding="utf-8")
    pasta = rodar("desenvolvimento", cliente=LLMFalso(), indice=IndiceFalso(), changelog="fictício",
                  pasta_conjuntos=conjuntos, pasta_rodadas=rodadas, agora=lambda: AGORA)  # fmt: skip
    return pasta, conjuntos, tmp_path / "dispositivos"


def preparar_(rodada, semente=7):
    pasta, conjuntos, dispositivos = rodada
    return preparar(pasta, semente=semente, pasta_conjuntos=conjuntos, pasta_dispositivos=dispositivos)


def ler(caminho):
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def codigos(texto):
    return re.findall(r"^=== (\w+) ===$", texto, re.MULTILINE)


def test_gera_os_quatro_envios_e_o_mapa_separado(rodada):
    envios = preparar_(rodada)
    assert sorted(p.name for p in envios.glob("*.txt")) == [
        "A-fidelidade.txt", "A-precisao.txt", "B-fidelidade.txt", "B-precisao.txt"
    ]  # fmt: skip
    mapa = ler(rodada[0] / "mapa.yaml")
    assert not (envios / "mapa.yaml").exists()
    assert mapa["semente"] == 7

    # 15 perguntas do tema (as extras não vão ao corretor) e 3 erradas por arquivo.
    for arquivo in "AB":
        itens = mapa["arquivos"][arquivo]
        assert [i["codigo"] for i in itens] == [f"{arquivo}{n:02d}" for n in range(1, 19)]
        assert sum(i["versao"] == "errada" for i in itens) == 3
        texto = (envios / f"{arquivo}-precisao.txt").read_text(encoding="utf-8")
        assert codigos(texto) == [i["codigo"] for i in itens]
        assert codigos((envios / f"{arquivo}-fidelidade.txt").read_text(encoding="utf-8")) == codigos(texto)


def test_cada_pergunta_tem_uma_versao_em_cada_arquivo(rodada):
    preparar_(rodada)
    arquivos = ler(rodada[0] / "mapa.yaml")["arquivos"]
    versoes = {
        arquivo: {i["id"]: i["versao"] for i in arquivos[arquivo] if i["versao"] != "errada"} for arquivo in "AB"
    }
    assert versoes["A"].keys() == versoes["B"].keys() and len(versoes["A"]) == 15
    assert all({versoes["A"][q], versoes["B"][q]} == {"rag", "sem_rag"} for q in versoes["A"])


def test_arquivos_nao_indicam_a_versao(rodada):
    envios = preparar_(rodada)
    for caminho in [*envios.glob("*.txt"), envios / "conteudo.yaml"]:
        texto = caminho.read_text(encoding="utf-8").lower()
        for proibido in ("rag", "versao", "versão", "errada", "q-0", "extra"):
            assert proibido not in texto, (caminho.name, proibido)


@pytest.mark.parametrize("semente", range(20))
def test_uma_resposta_errada_fica_perto_do_final(rodada, semente):
    rodada[0].joinpath("mapa.yaml").unlink(missing_ok=True)
    for arquivo in rodada[0].glob("envios/*"):
        arquivo.unlink()
    preparar_(rodada, semente)
    for itens in ler(rodada[0] / "mapa.yaml")["arquivos"].values():
        posicoes = [n for n, i in enumerate(itens) if i["versao"] == "errada"]
        assert max(posicoes) >= len(itens) - 3


def test_mesma_semente_gera_os_mesmos_arquivos(rodada, tmp_path):
    primeiro = {p.name: p.read_text(encoding="utf-8") for p in preparar_(rodada).iterdir()}
    mapa = (rodada[0] / "mapa.yaml").read_text(encoding="utf-8")
    (rodada[0] / "mapa.yaml").unlink()
    for arquivo in rodada[0].glob("envios/*"):
        arquivo.unlink()
    segundo = {p.name: p.read_text(encoding="utf-8") for p in preparar_(rodada).iterdir()}
    assert primeiro == segundo and mapa == (rodada[0] / "mapa.yaml").read_text(encoding="utf-8")


def test_precisao_leva_gabarito_e_fidelidade_leva_so_os_artigos(rodada):
    envios = preparar_(rodada)
    precisao = (envios / "A-precisao.txt").read_text(encoding="utf-8")
    fidelidade = (envios / "A-fidelidade.txt").read_text(encoding="utf-8")

    assert "GABARITO:\nResposta fictícia para testar a estrutura." in precisao
    assert "PONTOS OBRIGATÓRIOS:\n1. Ponto fictício" in precisao
    assert "GABARITO" not in fidelidade and "Ponto fictício" not in fidelidade
    assert "PERGUNTA" not in fidelidade
    # Texto integral do artigo, da coleta mais recente.
    assert "[Lei 11.340/2006, art. 7º]\nArt. 7º São formas fictícias:\nI - inciso fictício;" in fidelidade
    assert "Texto antigo" not in fidelidade
    # O art. 99 não existe na base: vai para a lista à parte.
    assert "CITAÇÕES FORA DA BASE:\n- Lei 11.340/2006, art. 99" in fidelidade


def test_conteudo_guarda_o_que_foi_enviado_por_codigo(rodada):
    envios = preparar_(rodada)
    conteudo = ler(envios / "conteudo.yaml")
    item = conteudo["A"]["A01"]
    assert set(item) == {"pergunta", "resposta_esperada", "pontos_obrigatorios", "resposta", "artigos", "fora_da_base"}
    assert item["resposta"] in (envios / "A-precisao.txt").read_text(encoding="utf-8")


def test_nao_sobrescreve_envios_existentes(rodada):
    preparar_(rodada)
    with pytest.raises(ErroEnvio, match="já"):
        preparar_(rodada)


def test_recusa_conjunto_alterado_depois_da_rodada(rodada):
    arquivo = rodada[1] / "desenvolvimento.yaml"
    arquivo.write_text(arquivo.read_text(encoding="utf-8") + "\n# ajuste\n", encoding="utf-8")
    with pytest.raises(ErroEnvio, match="mudou"):
        preparar_(rodada)


@pytest.mark.parametrize(
    "mudar, mensagem",
    [
        (lambda d: d["erradas"].pop(), "3 respostas erradas"),
        (lambda d: d["erradas"][0].update(pergunta_id="q-999"), "q-999"),
        (lambda d: d["erradas"][0].update(resposta=" "), "resposta"),
    ],
    ids=["faltando", "pergunta-inexistente", "resposta-vazia"],
)
def test_recusa_erradas_invalidas(rodada, mudar, mensagem):
    dados = yaml.safe_load(yaml.safe_dump(ERRADAS))
    mudar(dados)
    (rodada[1] / ARQUIVO_ERRADAS).write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ErroEnvio, match=mensagem):
        preparar_(rodada)
    assert not (rodada[0] / "mapa.yaml").exists()


# --- Artigos da base citados na resposta (texto que vai ao corretor de fidelidade) ---------

BASE_GUARDA = {
    ("Código Civil", "1.584"): "Art. 1.584. Texto fictício do Código Civil.",
    ("Código de Processo Civil", "699-A"): "Art. 699-A. Texto fictício do CPC.",
    ("Lei 11.340/2006", "7"): "Art. 7º Texto fictício da Lei Maria da Penha.",
}


@pytest.mark.parametrize(
    "resposta, rotulo",
    [
        ("O juiz considera a violência (Código Civil, art. 1584).", "Código Civil, art. 1.584"),
        ("O art. 699-A, incluído pela Lei 14.713/2023, manda o juiz perguntar.", "Código de Processo Civil, art. 699-A"),
    ],
    ids=["sem-ponto", "so-lei-14713"],
)
def test_citado_da_base_leva_o_texto_integral(resposta, rotulo):
    from scripts.envios import _citados

    artigos, fora = _citados(resposta, BASE_GUARDA)
    assert list(artigos) == [rotulo] and fora == []


def test_citado_por_lei_14713_fora_da_base_tem_rotulo_legivel():
    from scripts.envios import _citados

    artigos, fora = _citados("O art. 7º, incluído pela Lei 14.713/2023, diz isso.", BASE_GUARDA)
    assert artigos == {} and fora == ["Código Civil ou Código de Processo Civil, art. 7º"]
