"""Conferência do retorno do corretor e métricas (s3-avaliacao-llm-vs-rag, tarefa 3.4). Tudo fictício."""
import json

import pytest
import yaml

from app.rag.resposta import RECUSA
from scripts.conferir import ErroConferencia, conferir
from scripts.envios import ARQUIVO_ERRADAS, preparar
from scripts.rodada import rodar
from test_envios import ERRADAS, dispositivo
from test_rodada import AGORA, RESPOSTA_CITADA, IndiceFalso, pastas  # noqa: F401  (pastas é fixture)

ARQUIVOS = ("A-precisao", "A-fidelidade", "B-precisao", "B-fidelidade")


class LLMRecusaPrimeira:
    """Na versão com RAG, a pergunta q-001 recebe uma resposta sem citação, que o sistema recusa."""

    modelo = "modelo-de-teste"

    def responder(self, mensagens):
        com_trechos = "Trechos de lei" in mensagens[-1]["content"]
        if com_trechos and "fictícia 1 " in mensagens[-1]["content"]:
            return "Resposta sem nenhuma citação."
        return RESPOSTA_CITADA


@pytest.fixture
def rodada(pastas, tmp_path):  # noqa: F811
    conjuntos, rodadas = pastas
    (conjuntos / ARQUIVO_ERRADAS).write_text(yaml.safe_dump(ERRADAS, allow_unicode=True), encoding="utf-8")
    norma = tmp_path / "dispositivos" / "lei-11340-2006"
    norma.mkdir(parents=True)
    registros = [dispositivo("7", "caput", "Art. 7º São formas fictícias de violência:")]
    (norma / "2026-11-10.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in registros),
                                            encoding="utf-8")  # fmt: skip
    pasta = rodar("desenvolvimento", cliente=LLMRecusaPrimeira(), indice=IndiceFalso(), changelog="fictício",
                  pasta_conjuntos=conjuntos, pasta_rodadas=rodadas, agora=lambda: AGORA)  # fmt: skip
    preparar(pasta, semente=3, pasta_conjuntos=conjuntos, pasta_dispositivos=tmp_path / "dispositivos")
    return pasta


def ler(caminho):
    return yaml.safe_load(caminho.read_text(encoding="utf-8"))


def versoes(rodada):
    return {i["codigo"]: i["versao"] for itens in ler(rodada / "mapa.yaml")["arquivos"].values() for i in itens}


def retorno_correto(rodada, nome):
    """O retorno de um corretor atento: aprova as respostas reais e reprova as erradas de propósito."""
    arquivo, tipo = nome.split("-")
    conteudo, versao = ler(rodada / "envios" / "conteudo.yaml")[arquivo], versoes(rodada)
    itens = []
    for codigo, item in conteudo.items():
        errada = versao[codigo] == "errada"
        if tipo == "precisao":
            pontos = [{"numero": n, "presente": not errada, "trecho": "" if errada else item["resposta"][:12]}
                      for n in range(1, len(item["pontos_obrigatorios"]) + 1)]  # fmt: skip
            itens.append({"codigo": codigo, "pontos": pontos, "contradiz": False, "trecho_contradicao": ""})
        else:
            artigo = next(iter(item["artigos"].values()), "")
            afirmacao = {"afirmacao": item["resposta"][:20], "suporte": "nao" if errada else "sim",
                         "trecho_artigo": "" if errada else artigo[:15]}  # fmt: skip
            itens.append({"codigo": codigo, "afirmacoes": [afirmacao]})
    return itens


def gravar_retornos(rodada, mudar=None):
    pasta = rodada / "retornos"
    pasta.mkdir(exist_ok=True)
    registro = {}
    for nome in ARQUIVOS:
        itens = retorno_correto(rodada, nome)
        if mudar:
            itens = mudar(nome, itens) or itens
        # Como o corretor costuma devolver: JSON dentro de um bloco de código.
        (pasta / f"{nome}.json").write_text("```json\n" + json.dumps(itens, ensure_ascii=False) + "\n```",
                                            encoding="utf-8")  # fmt: skip
        registro[nome] = {"modelo": "corretor-ficticio", "data": "2026-11-12"}
    (pasta / "registro.yaml").write_text(yaml.safe_dump(registro), encoding="utf-8")


def test_retorno_completo_e_correto_e_aceito(rodada):
    gravar_retornos(rodada)
    resultado = conferir(rodada)

    assert all(resultado["arquivos"][n]["aceito"] for n in ARQUIVOS)
    assert all(resultado["arquivos"][n]["modelo"] == "corretor-ficticio" for n in ARQUIVOS)
    rag, sem_rag = resultado["versoes"]["rag"], resultado["versoes"]["sem_rag"]
    # A recusa da q-001 na versão com RAG conta como erro, mesmo com os pontos marcados.
    assert rag["precisao"] == {"corrigidas": 15, "certas": 14, "recusas": 1, "percentual": round(100 * 14 / 15, 1)}
    assert sem_rag["precisao"] == {"corrigidas": 15, "certas": 15, "recusas": 0, "percentual": 100.0}
    assert rag["citacao"] == {"respostas": 15, "com_citacao": 14, "percentual": round(100 * 14 / 15, 1)}
    assert sem_rag["fidelidade"]["afirmacoes"] == 15 and sem_rag["fidelidade"]["sem_suporte"] == 0
    assert (rodada / "resultado.yaml").is_file()


def test_linha_faltando_rejeita_a_correcao(rodada):
    gravar_retornos(rodada, lambda nome, itens: itens[1:] if nome == "A-precisao" else None)
    resultado = conferir(rodada)["arquivos"]["A-precisao"]
    assert resultado["aceito"] is False
    assert resultado["faltando"] == ["A01"]


def test_trecho_inexistente_aponta_a_linha_e_conta_contra_a_resposta(rodada):
    def inventar(nome, itens):
        if nome == "B-precisao":
            # Uma resposta real e não recusada, para a conta abaixo ficar exata.
            alvo = next(i for i in itens if i["pontos"][0]["presente"] and not RECUSA.startswith(i["pontos"][0]["trecho"]))
            alvo["pontos"][0]["trecho"] = "frase que não está na resposta"
            return itens

    gravar_retornos(rodada, inventar)
    resultado = conferir(rodada)
    arquivo = resultado["arquivos"]["B-precisao"]
    assert len(arquivo["marcacoes_invalidas"]) == 1 and "trecho" in arquivo["marcacoes_invalidas"][0]
    certas = sum(resultado["versoes"][v]["precisao"]["certas"] for v in ("rag", "sem_rag"))
    assert certas == 28  # 30 respostas, menos a recusa e a marcação sem trecho válido


def test_resposta_errada_aprovada_rejeita_a_correcao(rodada):
    errada = next(c for c, v in versoes(rodada).items() if v == "errada" and c.startswith("A"))

    def aprovar(nome, itens):
        if nome == "A-fidelidade":
            item = next(i for i in itens if i["codigo"] == errada)
            item["afirmacoes"] = [{"afirmacao": "Isso nunca", "suporte": "sim", "trecho_artigo": "Art. 7º"}]
            return itens

    gravar_retornos(rodada, aprovar)
    resultado = conferir(rodada)["arquivos"]["A-fidelidade"]
    assert resultado["aceito"] is False
    assert resultado["erradas_aprovadas"] == [errada]


def test_retorno_sem_modelo_e_data_nao_e_aceito(rodada):
    gravar_retornos(rodada)
    registro = rodada / "retornos" / "registro.yaml"
    dados = ler(registro)
    del dados["B-fidelidade"]["data"]
    registro.write_text(yaml.safe_dump(dados), encoding="utf-8")
    resultado = conferir(rodada)["arquivos"]["B-fidelidade"]
    assert resultado["aceito"] is False and "data" in " ".join(resultado["problemas"])


def test_retorno_que_nao_e_json_falha_com_mensagem_clara(rodada):
    gravar_retornos(rodada)
    (rodada / "retornos" / "A-precisao.json").write_text("Aqui está a correção: tudo certo!", encoding="utf-8")
    resultado = conferir(rodada)["arquivos"]["A-precisao"]
    assert resultado["aceito"] is False and "JSON" in " ".join(resultado["problemas"])


def test_sem_retornos_falha(rodada):
    with pytest.raises(ErroConferencia, match="retornos"):
        conferir(rodada)
