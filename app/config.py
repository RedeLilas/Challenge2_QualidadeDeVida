"""Configuração lida de variáveis de ambiente. Segredos nunca ficam no código nem no repositório."""
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field

VARIAVEIS = ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY")
# Segundos de espera pelo LLM. A tela (web/app.js) espera um pouco mais, para receber
# a mensagem de indisponibilidade do servidor em vez de desistir antes.
TIMEOUT_PADRAO = 30.0


class ConfigIncompleta(RuntimeError):
    """Falta uma variável de ambiente obrigatória ou ela tem um valor inválido."""


@dataclass(frozen=True)
class Config:
    base_url: str
    model: str
    # A chave não aparece se a config for impressa ou cair num log.
    api_key: str = field(repr=False)
    timeout: float = TIMEOUT_PADRAO


def carregar(env: Mapping[str, str] | None = None) -> Config:
    """Lê LLM_BASE_URL, LLM_MODEL, LLM_API_KEY e LLM_TIMEOUT (opcional); falha apontando o problema."""
    env = os.environ if env is None else env
    valores = {nome: (env.get(nome) or "").strip() for nome in VARIAVEIS}
    faltando = [nome for nome, valor in valores.items() if not valor]
    if faltando:
        raise ConfigIncompleta(
            f"Variável de ambiente não definida: {', '.join(faltando)}. "
            "Copie .env.example para .env, preencha os valores e rode com "
            "`uv run --env-file .env ...`."
        )
    return Config(
        base_url=valores["LLM_BASE_URL"],
        model=valores["LLM_MODEL"],
        api_key=valores["LLM_API_KEY"],
        timeout=_timeout(env.get("LLM_TIMEOUT")),
    )


def _timeout(valor: str | None) -> float:
    if valor is None or not valor.strip():
        return TIMEOUT_PADRAO
    try:
        segundos = float(valor)
    except ValueError:
        segundos = math.nan
    if not math.isfinite(segundos) or segundos <= 0:
        raise ConfigIncompleta(f"LLM_TIMEOUT deve ser um número de segundos maior que zero (padrão: {TIMEOUT_PADRAO:g}).")
    return segundos
