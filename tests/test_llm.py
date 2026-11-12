from types import SimpleNamespace

import httpx
import openai
import pytest

from app.config import Config
from app.llm import ClienteLLM, LLMIndisponivel

CONFIG = Config(base_url="http://localhost:11434/v1", model="modelo-de-teste", api_key="chave-de-teste")
MENSAGENS = [{"role": "user", "content": "Pergunta fictícia de teste"}]


class OpenAISimulado:
    """Imita client.chat.completions.create do pacote openai."""

    def __init__(self, resposta=None, erro=None):
        self.chamadas = []
        self._resposta, self._erro = resposta, erro
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.chamadas.append(kwargs)
        if self._erro:
            raise self._erro
        mensagem = SimpleNamespace(content=self._resposta)
        return SimpleNamespace(choices=[SimpleNamespace(message=mensagem)])


def test_envia_modelo_e_mensagens_e_devolve_o_texto():
    simulado = OpenAISimulado(resposta="  Resposta do modelo.  ")
    texto = ClienteLLM(CONFIG, cliente=simulado).responder(MENSAGENS)

    assert texto == "Resposta do modelo."
    assert len(simulado.chamadas) == 1
    assert simulado.chamadas[0]["model"] == "modelo-de-teste"
    assert simulado.chamadas[0]["messages"] == MENSAGENS


def test_sem_raciocinio_configurado_nao_envia_extra_body():
    # O parâmetro é do DeepSeek; o modelo local não pode depender dele.
    simulado = OpenAISimulado(resposta="ok")
    ClienteLLM(CONFIG, cliente=simulado).responder(MENSAGENS)
    assert "extra_body" not in simulado.chamadas[0]


@pytest.mark.parametrize("valor", ["disabled", "enabled"])
def test_raciocinio_configurado_vai_no_extra_body(valor):
    simulado = OpenAISimulado(resposta="ok")
    cfg = Config(base_url=CONFIG.base_url, model=CONFIG.model, api_key="x", thinking=valor)
    ClienteLLM(cfg, cliente=simulado).responder(MENSAGENS)
    assert simulado.chamadas[0]["extra_body"] == {"thinking": {"type": valor}}


REQUISICAO = httpx.Request("POST", "http://localhost:11434/v1/chat/completions")


@pytest.mark.parametrize(
    "erro",
    [
        openai.APIConnectionError(request=REQUISICAO),
        openai.APITimeoutError(request=REQUISICAO),
        openai.InternalServerError("erro", response=httpx.Response(503, request=REQUISICAO), body=None),
        openai.RateLimitError("limite", response=httpx.Response(429, request=REQUISICAO), body=None),
    ],
    ids=["sem-conexao", "timeout", "erro-500", "limite"],
)
def test_provedor_fora_do_ar_vira_llm_indisponivel(erro):
    # Quem chama trata LLMIndisponivel (mensagem + Ligue 180) sem conhecer o pacote openai.
    with pytest.raises(LLMIndisponivel):
        ClienteLLM(CONFIG, cliente=OpenAISimulado(erro=erro)).responder(MENSAGENS)


def test_resposta_vazia_vira_llm_indisponivel():
    with pytest.raises(LLMIndisponivel):
        ClienteLLM(CONFIG, cliente=OpenAISimulado(resposta=None)).responder(MENSAGENS)


def test_usa_o_tempo_limite_da_config_e_nao_repete_a_chamada():
    # Repetir uma chamada lenta só dobra a espera; quem decide tentar de novo é a usuária.
    cliente = ClienteLLM(Config(base_url=CONFIG.base_url, model=CONFIG.model, api_key="x", timeout=12.0))
    assert cliente._cliente.timeout == 12.0
    assert cliente._cliente.max_retries == 0


def test_troca_de_provedor_so_pela_config():
    deepseek = Config(base_url="https://api.deepseek.com", model="deepseek-flash", api_key="chave-de-teste")
    cliente = ClienteLLM(deepseek)
    assert str(cliente._cliente.base_url).rstrip("/") == "https://api.deepseek.com"
    assert cliente.modelo == "deepseek-flash"
