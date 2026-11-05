"""Testes automatizados para os dados levantados em s2-fontes-df."""

from scripts.validar_dados import (
    validar_fonar,
    validar_normas,
    validar_rede_protecao,
    validar_tudo,
)


def test_rede_protecao_df_valida():
    assert validar_rede_protecao() == []


def test_normas_csv_valido():
    assert validar_normas() == []


def test_fonar_notas_valido():
    assert validar_fonar() == []


def test_validar_tudo_sem_erros():
    assert validar_tudo() == []
