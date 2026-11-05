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


def test_troca_de_provedor_so_pela_config():
    deepseek = Config(base_url="https://api.deepseek.com", model="deepseek-chat", api_key="chave-de-teste")
    cliente = ClienteLLM(deepseek)
    assert str(cliente._cliente.base_url).rstrip("/") == "https://api.deepseek.com"
    assert cliente.modelo == "deepseek-chat"
