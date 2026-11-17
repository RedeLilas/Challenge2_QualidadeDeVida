"""Garante que a medição da S4 detecta regressões nas regras de risco alto."""

from scripts import medir_s4


def test_medicao_real_atinge_metas():
    resultado = medir_s4.medir()
    assert resultado["elegibilidade"]["acuracia"] == 1.0
    assert resultado["elegibilidade"]["pares"] == 80
    assert resultado["elegibilidade"]["acertos"] == 80
    assert resultado["elegibilidade"]["divergencias"] == []
    assert resultado["risco_alto"]["sensibilidade"] == 1
    assert not resultado["risco_alto"]["falsos_negativos"]


def test_falso_negativo_da_triagem_reprova():
    triagem = medir_s4._contexto("triagem.js", "triagem_fonar.json")
    triagem.eval('Triagem.avaliar = function () { return {nivel: "atencao"}; };')
    risco = medir_s4._contexto("risco.js", "risco_imediato.json", "Risco.compilar")
    resultado = medir_s4.medir_risco(
        {"casos": [{"id": "alto-1", "respostas": {}, "nivel_esperado": "alto"}]},
        {"risco": [], "nao_risco": []}, triagem, risco,
    )
    assert resultado["sensibilidade"] == 0
    assert resultado["falsos_negativos"] == [
        {"origem": "triagem", "caso": "alto-1", "obtido": "atencao"}
    ]


def test_alerta_ausente_reprova():
    triagem = medir_s4._contexto("triagem.js", "triagem_fonar.json")
    risco = medir_s4._contexto("risco.js", "risco_imediato.json", "Risco.compilar")
    risco.eval("REGRAS = [];")
    resultado = medir_s4.medir_risco(
        {"casos": []}, {"risco": [{"frase": "ele está aqui em casa com uma faca"}], "nao_risco": []},
        triagem, risco,
    )
    assert resultado["sensibilidade"] == 0
    assert resultado["falsos_negativos"] == [
        {"origem": "risco_imediato", "caso": 1, "frase": "ele está aqui em casa com uma faca"}
    ]
