from pathlib import Path

import pytest

from app.config import VARIAVEIS, ConfigIncompleta, carregar

COMPLETO = {
    "LLM_BASE_URL": "http://localhost:11434/v1",
    "LLM_MODEL": "modelo-de-teste",
    "LLM_API_KEY": "chave-de-teste",
}


def test_carrega_as_tres_variaveis():
    config = carregar(COMPLETO)
    assert config.base_url == "http://localhost:11434/v1"
    assert config.model == "modelo-de-teste"
    assert config.api_key == "chave-de-teste"


@pytest.mark.parametrize("faltando", VARIAVEIS)
def test_falha_com_mensagem_clara_se_variavel_faltar(faltando):
    env = {k: v for k, v in COMPLETO.items() if k != faltando}
    with pytest.raises(ConfigIncompleta) as erro:
        carregar(env)
    mensagem = str(erro.value)
    assert faltando in mensagem
    assert ".env.example" in mensagem
    # Só a variável ausente é apontada.
    assert all(v not in mensagem for v in VARIAVEIS if v != faltando)


def test_variavel_vazia_conta_como_ausente():
    with pytest.raises(ConfigIncompleta, match="LLM_API_KEY"):
        carregar({**COMPLETO, "LLM_API_KEY": "  "})


def test_lista_todas_as_ausentes_de_uma_vez():
    with pytest.raises(ConfigIncompleta) as erro:
        carregar({})
    assert all(v in str(erro.value) for v in VARIAVEIS)


def test_env_example_tem_as_variaveis_sem_chave_real():
    linhas = (Path(__file__).parents[1] / ".env.example").read_text(encoding="utf-8").splitlines()
    valores = dict(l.split("=", 1) for l in linhas if l.strip() and not l.startswith("#"))
    assert set(VARIAVEIS) <= set(valores)
    # O Ollama ignora a chave; o valor de exemplo não pode parecer uma chave de verdade.
    assert not valores["LLM_API_KEY"].startswith("sk-")
