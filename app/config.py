"""Configuração lida de variáveis de ambiente. Segredos nunca ficam no código nem no repositório."""
import math
import os
from collections.abc import Mapping
from dataclasses import dataclass, field

VARIAVEIS = ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY")
# Segundos de espera pelo LLM. A tela (web/app.js) espera um pouco mais, para receber
# a mensagem de indisponibilidade do servidor em vez de desistir antes.
TIMEOUT_PADRAO = 30.0
# Valores de LLM_THINKING, enviados ao DeepSeek como extra_body={"thinking": {"type": <valor>}}.
# Sem a variável, nada é enviado e o modelo local (Ollama) segue igual.
RACIOCINIO_VALIDOS = ("disabled", "enabled")


class ConfigIncompleta(RuntimeError):
    """Falta uma variável de ambiente obrigatória ou ela tem um valor inválido."""


@dataclass(frozen=True)
class Config:
    base_url: str
    model: str
    # A chave não aparece se a config for impressa ou cair num log.
    api_key: str = field(repr=False)
    timeout: float = TIMEOUT_PADRAO
    thinking: str | None = None


def carregar(env: Mapping[str, str] | None = None) -> Config:
    """Lê LLM_BASE_URL, LLM_MODEL, LLM_API_KEY, LLM_TIMEOUT e LLM_THINKING (opcionais); falha apontando o problema."""
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
        thinking=_raciocinio(env.get("LLM_THINKING")),
    )


def _raciocinio(valor: str | None) -> str | None:
    if valor is None or not valor.strip():
        return None
    valor = valor.strip().lower()
    if valor not in RACIOCINIO_VALIDOS:
        raise ConfigIncompleta(
            f"LLM_THINKING deve ser {' ou '.join(RACIOCINIO_VALIDOS)}, ou ficar sem valor para não enviar o parâmetro."
        )
    return valor


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
