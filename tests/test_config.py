from pathlib import Path

import pytest

from app.config import RACIOCINIO_VALIDOS, TIMEOUT_PADRAO, VARIAVEIS, ConfigIncompleta, carregar

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


def test_tempo_limite_padrao():
    assert carregar(COMPLETO).timeout == TIMEOUT_PADRAO == 30.0


def test_tempo_limite_configuravel():
    assert carregar({**COMPLETO, "LLM_TIMEOUT": "12.5"}).timeout == 12.5


@pytest.mark.parametrize("valor", ["abc", "0", "-5", "nan", "inf"])
def test_tempo_limite_invalido_falha_com_mensagem_clara(valor):
    with pytest.raises(ConfigIncompleta, match="LLM_TIMEOUT"):
        carregar({**COMPLETO, "LLM_TIMEOUT": valor})


def test_raciocinio_ausente_nao_e_enviado():
    assert carregar(COMPLETO).thinking is None


def test_raciocinio_vazio_conta_como_ausente():
    assert carregar({**COMPLETO, "LLM_THINKING": "  "}).thinking is None


@pytest.mark.parametrize("valor", RACIOCINIO_VALIDOS)
def test_raciocinio_definido(valor):
    assert carregar({**COMPLETO, "LLM_THINKING": f" {valor.upper()} "}).thinking == valor


@pytest.mark.parametrize("valor", ["off", "false", "0", "desligado"])
def test_raciocinio_invalido_falha_com_mensagem_clara(valor):
    with pytest.raises(ConfigIncompleta, match="LLM_THINKING"):
        carregar({**COMPLETO, "LLM_THINKING": valor})


def test_env_example_tem_as_variaveis_sem_chave_real():
    linhas = (Path(__file__).parents[1] / ".env.example").read_text(encoding="utf-8").splitlines()
    valores = dict(l.split("=", 1) for l in linhas if l.strip() and not l.startswith("#"))
    assert set(VARIAVEIS) <= set(valores)
    # O Ollama ignora a chave; o valor de exemplo não pode parecer uma chave de verdade.
    assert not valores["LLM_API_KEY"].startswith("sk-")
