"""Conjuntos de avaliação fictícios e válidos, usados pelos testes do validador e da rodada."""

from scripts.validar_conjuntos import DISTRIBUICAO_OFICIAL


def _pergunta(numero: int, categoria: str, *, conferir: bool) -> dict:
    item = {
        "id": f"q-{numero:03d}",
        "categoria": categoria,
        "pergunta": f"Pergunta fictícia {numero} sobre uma situação passada e hipotética?",
        "autor": "Pessoa A",
        "resposta_esperada": "Resposta fictícia para testar a estrutura.",
        "pontos_obrigatorios": ["Ponto fictício"],
        "normas_aceitas": ["Norma fictícia"],
        "fonte": "Referência fictícia ao texto legal",
    }
    if conferir:
        item["conferencia"] = {
            "revisor": "Pessoa B",
            "fonte_conferida": "Referência fictícia conferida",
        }
    return item


def dados_ficticios(tipo: str) -> dict:
    categorias = (
        [categoria for categoria, total in DISTRIBUICAO_OFICIAL.items() for _ in range(total)]
        if tipo == "oficial"
        else list(DISTRIBUICAO_OFICIAL) * 2 + list(DISTRIBUICAO_OFICIAL)[:3]
    )
    return {
        "versao": 1,
        "perguntas": [
            _pergunta(i, categoria, conferir=tipo == "oficial")
            for i, categoria in enumerate(categorias, start=1)
        ],
        "extras": [
            {
                "id": f"extra-{i:03d}",
                "categoria": "fora_do_tema",
                "pergunta": f"Pergunta extra fictícia {i}?",
                "autor": "Pessoa A",
            }
            for i in range(1, 11)
        ],
    }
