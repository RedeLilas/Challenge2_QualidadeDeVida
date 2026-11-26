import pytest


@pytest.fixture(scope="session")
def indice_real():
    """O índice de todas as normas, montado na hora com o modelo de verdade, uma vez por execução.

    Montar leva cerca de 30 s na CPU; compartilhar evita pagar isso em cada arquivo de teste.
    """
    # Import tardio: rodar só os testes que não usam o índice não carrega o torch.
    from app.rag.indice import Indice, carregar_trechos

    return Indice(carregar_trechos())
