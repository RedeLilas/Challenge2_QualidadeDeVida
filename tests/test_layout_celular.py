"""Layout no celular num navegador de verdade (#152): saída rápida sempre inteira e chat dentro da tela.

Marca `navegador`: fica fora da suíte padrão, porque precisa do Chromium do Playwright.
Uma vez por máquina: `uv run playwright install chromium`. Depois: `uv run pytest -m navegador`.
O app sobe num servidor local sem os modelos (sem lifespan): só a interface é medida.
"""
import socket
import threading
import time

import pytest
import uvicorn

from app.main import app

pytestmark = pytest.mark.navegador

# Larguras de celular: iPhone SE 1ª geração, Android de entrada, iPhone SE/8, iPhone 13 a 15, iPhone Pro Max.
TELAS = [(320, 568), (360, 740), (375, 667), (390, 844), (430, 932)]
ALTURA_DO_CABECALHO = 66

MEDIR = """() => {
  const caixa = (seletor) => {
    const b = document.querySelector(seletor).getBoundingClientRect();
    return { esquerda: b.left, direita: b.right, topo: b.top, base: b.bottom, altura: b.height };
  };
  const aberta = !document.getElementById("chat-window").hidden;
  return {
    largura: innerWidth,
    sair: caixa("#sair"), apagar: caixa("#apagar-dados"), t180: caixa('a[href="tel:180"]'), t190: caixa('a[href="tel:190"]'),
    menu: caixa("#abrir-menu"), gatilho: caixa("#chat-trigger"),
    janela: aberta ? caixa("#chat-window") : null, titulo: aberta ? caixa(".chat-head-info strong") : null,
    digitar: aberta ? caixa("#envio") : null, microfone: aberta ? caixa("#microfone") : null,
    nomeApagar: document.getElementById("apagar-dados").innerText.trim() || document.getElementById("apagar-dados").textContent.trim(),
  };
}"""


@pytest.fixture(scope="module")
def endereco():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta = s.getsockname()[1]
    servidor = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=porta, lifespan="off", log_level="warning"))
    thread = threading.Thread(target=servidor.run, daemon=True)
    thread.start()
    for _ in range(100):
        if servidor.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{porta}/"
    servidor.should_exit = True
    thread.join(5)


@pytest.fixture(scope="module")
def navegador():
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        try:
            chromium = p.chromium.launch()
        except Exception as erro:  # navegador não instalado nesta máquina
            pytest.skip(f"Chromium do Playwright indisponível ({type(erro).__name__}): rode `uv run playwright install chromium`")
        yield chromium
        chromium.close()


def abrir(navegador, endereco, largura, altura):
    contexto = navegador.new_context(
        viewport={"width": largura, "height": altura}, is_mobile=True, has_touch=True, service_workers="block"
    )
    pagina = contexto.new_page()
    pagina.goto(endereco)
    pagina.wait_for_load_state("networkidle")
    return contexto, pagina


def dentro_da_tela(caixa, largura):
    return caixa["esquerda"] >= 0 and caixa["direita"] <= largura


@pytest.mark.parametrize("largura, altura", TELAS, ids=[f"{l}px" for l, _ in TELAS])
def test_saida_rapida_e_telefones_inteiros_no_cabecalho(navegador, endereco, largura, altura):
    contexto, pagina = abrir(navegador, endereco, largura, altura)
    m = pagina.evaluate(MEDIR)
    contexto.close()
    for nome in ("sair", "apagar", "t180", "t190", "menu"):
        assert dentro_da_tela(m[nome], largura), f"{nome} passa da borda em {largura}px: {m[nome]}"
        assert m[nome]["base"] <= ALTURA_DO_CABECALHO, f"{nome} sai do cabeçalho em {largura}px"
    # Um botão grande o bastante para tocar (WCAG 2.5.8: alvo de pelo menos 24 px).
    assert m["sair"]["altura"] >= 24 and m["sair"]["direita"] - m["sair"]["esquerda"] >= 44
    # "Apagar meus dados" pode virar só ícone, mas o nome acessível continua.
    assert "Apagar meus dados" in m["nomeApagar"]


@pytest.mark.parametrize("largura, altura", TELAS, ids=[f"{l}px" for l, _ in TELAS])
def test_chat_aberto_dentro_da_tela_sem_o_botao_por_cima(navegador, endereco, largura, altura):
    contexto, pagina = abrir(navegador, endereco, largura, altura)
    pagina.click("#chat-trigger")
    pagina.wait_for_timeout(400)
    m = pagina.evaluate(MEDIR)
    contexto.close()
    janela = m["janela"]
    assert janela is not None
    assert dentro_da_tela(janela, largura), janela
    assert janela["topo"] >= ALTURA_DO_CABECALHO, "a janela do chat cobre o cabeçalho (e a saída rápida)"
    assert janela["base"] <= m["gatilho"]["topo"], "o botão flutuante fica por cima do chat aberto"
    assert m["titulo"]["altura"] <= 24, "o título do chat quebra em várias linhas"
    assert janela["topo"] <= m["digitar"]["topo"] and m["digitar"]["base"] <= janela["base"]
    assert dentro_da_tela(m["digitar"], largura)


@pytest.mark.parametrize("largura, altura", TELAS, ids=[f"{l}px" for l, _ in TELAS])
def test_campos_com_16px_para_o_iphone_nao_dar_zoom(navegador, endereco, largura, altura):
    # Abaixo de 16 px, o Safari do iPhone dá zoom ao tocar no campo e o chat fica cortado (#160).
    contexto, pagina = abrir(navegador, endereco, largura, altura)
    pagina.click("#chat-trigger")
    tamanhos = pagina.evaluate(
        """() => ["#texto", "#filtro-ra", "#filtro-tipo", "#filtro-cep"].map((seletor) => [
          seletor, parseFloat(getComputedStyle(document.querySelector(seletor)).fontSize),
        ])"""
    )
    viewport = pagina.get_attribute('meta[name="viewport"]', "content")
    contexto.close()
    for seletor, tamanho in tamanhos:
        assert tamanho >= 16, f"{seletor} com {tamanho}px em {largura}px"
    # Zoom continua livre para quem precisa ampliar (WCAG 1.4.4).
    assert "maximum-scale" not in viewport and "user-scalable" not in viewport
