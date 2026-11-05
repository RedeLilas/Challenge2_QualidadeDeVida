"""Cliente único de LLM pela API compatível com a OpenAI (Ollama nos testes, DeepSeek em produção).

O provedor é escolhido só pelas variáveis de ambiente lidas em app/config.py.

Chamada manual (use apenas perguntas fictícias):
    uv run --env-file .env python -m app.llm "O que é violência patrimonial?"
"""
import sys
from functools import cache

import openai

from app import config

# Falhas do provedor, não do nosso código: viram LLMIndisponivel para a rota responder
# que não consegue agora e indicar o Ligue 180.
ERROS_DO_PROVEDOR = (
    openai.APIConnectionError,  # inclui APITimeoutError
    openai.InternalServerError,
    openai.RateLimitError,
)


class LLMIndisponivel(RuntimeError):
    """O provedor de LLM não respondeu ou devolveu uma resposta vazia."""


class ClienteLLM:
    def __init__(self, cfg: config.Config, cliente: openai.OpenAI | None = None, timeout: float = 60.0):
        self.modelo = cfg.model
        self._cliente = cliente or openai.OpenAI(
            base_url=cfg.base_url, api_key=cfg.api_key, timeout=timeout, max_retries=1
        )

    def responder(self, mensagens: list[dict], temperatura: float = 0.2) -> str:
        try:
            resposta = self._cliente.chat.completions.create(
                model=self.modelo, messages=mensagens, temperature=temperatura
            )
        except ERROS_DO_PROVEDOR as erro:
            raise LLMIndisponivel(type(erro).__name__) from erro

        texto = (resposta.choices[0].message.content or "").strip()
        if not texto:
            raise LLMIndisponivel("resposta vazia")
        return texto


@cache
def cliente() -> ClienteLLM:
    """Instância compartilhada, criada no primeiro uso a partir das variáveis de ambiente."""
    return ClienteLLM(config.carregar())


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]) or "Responda em uma frase: o que é a Lei Maria da Penha?"
    print(f"[{cliente().modelo}]")
    print(cliente().responder([{"role": "user", "content": pergunta}]))
