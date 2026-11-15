"""Rubricas do corretor (s3-avaliacao-llm-vs-rag, tarefa 4.1).

O JSON de exemplo de cada rubrica precisa ser lido pelo script de conferência sem nenhuma
marcação inválida; assim a rubrica e o script não divergem.
"""
from pathlib import Path

from scripts.conferir import SUPORTES, _corrigir_fidelidade, _corrigir_precisao, _ler_json

RUBRICAS = Path(__file__).resolve().parents[1] / "avaliacao" / "rubricas"
RESPOSTA = "<cópia da RESPOSTA>"


def test_exemplo_da_rubrica_de_precisao_e_lido_pela_conferencia():
    (item,) = _ler_json(RUBRICAS / "precisao.md")
    invalidas = []
    enviado = {"pontos_obrigatorios": ["ponto 1", "ponto 2"], "resposta": RESPOSTA}

    certa, aprovada = _corrigir_precisao(item, enviado, item["codigo"], invalidas)

    assert invalidas == []
    assert (certa, aprovada) == (False, False)  # o ponto 2 está ausente


def test_exemplo_da_rubrica_de_fidelidade_e_lido_pela_conferencia():
    (item,) = _ler_json(RUBRICAS / "fidelidade.md")
    invalidas = []
    enviado = {"resposta": RESPOSTA, "artigos": {"Lei fictícia, art. 1º": "<cópia do artigo>"}}

    contagem, aprovada = _corrigir_fidelidade(item, enviado, item["codigo"], invalidas)

    assert invalidas == []
    assert contagem == {"sim": 1, "nao": 1, "fora_da_base": 0} and aprovada is False


def test_rubrica_de_fidelidade_cita_todos_os_valores_de_suporte():
    texto = (RUBRICAS / "fidelidade.md").read_text(encoding="utf-8")
    assert all(f'"{suporte}"' in texto for suporte in SUPORTES)
