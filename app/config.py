"""Configuração lida de variáveis de ambiente. Segredos nunca ficam no código nem no repositório."""
import os
from collections.abc import Mapping
from dataclasses import dataclass, field

VARIAVEIS = ("LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY")


class ConfigIncompleta(RuntimeError):
    """Falta uma variável de ambiente obrigatória."""


@dataclass(frozen=True)
class Config:
    base_url: str
    model: str
    # A chave não aparece se a config for impressa ou cair num log.
    api_key: str = field(repr=False)


def carregar(env: Mapping[str, str] | None = None) -> Config:
    """Lê LLM_BASE_URL, LLM_MODEL e LLM_API_KEY; falha apontando as que faltam."""
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
    )
