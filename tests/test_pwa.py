"""PWA servida pelo FastAPI, rota de mensagem, perfil local, benefícios e rede de proteção (s2 e s3)."""
import json
import logging
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import llm, main
from app.config import TIMEOUT_PADRAO, ConfigIncompleta
from app.main import app

RAIZ = Path(__file__).resolve().parents[1]
APIS_ARMAZENAMENTO = ("localStorage", "sessionStorage", "indexedDB", "document.cookie")

# Frase fictícia: nunca usar relatos reais em testes.
PERGUNTA = "Pergunta fictícia de teste sobre auxílio"


class LLMFalso:
    def __init__(self, resposta="Resposta fictícia.", erro=None):
        self.resposta, self.erro, self.recebido = resposta, erro, None

    def responder(self, mensagens):
        self.recebido = mensagens
        if self.erro:
            raise self.erro
        return self.resposta


@pytest.fixture
def cliente():
    # As rotas chamam main.cliente_llm() depois da checagem de risco; os testes trocam a função.
    original = main.cliente_llm
    yield TestClient(app)
    main.cliente_llm = original


def usar(llm_falso):
    main.cliente_llm = lambda: llm_falso
    return llm_falso


def _scripts_usam_armazenamento(textos_por_arquivo, permitidos=("perfil.js",)):
    """Retorna os nomes dos scripts fora de `permitidos` que acessam APIs de armazenamento."""
    violacoes = []
    for nome, codigo in textos_por_arquivo.items():
        if nome in permitidos:
            continue
        for api in APIS_ARMAZENAMENTO:
            if f"{api}." in codigo or f"{api}[" in codigo:
                violacoes.append((nome, api))
    return violacoes


def test_raiz_serve_a_tela_de_conversa(cliente):
    resposta = cliente.get("/")
    assert resposta.status_code == 200
    assert "text/html" in resposta.headers["content-type"]
    assert "<title>Anotações</title>" in resposta.text
    assert 'id="sair"' in resposta.text


@pytest.mark.parametrize(
    "caminho",
    [
        "/app.js",
        "/perfil.js",
        "/beneficios.js",
        "/triagem.js",
        "/dados.js",
        "/risco.js",
        "/styles.css",
        "/sw.js",
        "/regras/beneficios.json",
        "/regras/triagem_fonar.json",
        "/regras/risco_imediato.json",
        "/icones/icone-192.png",
        "/icones/icone-512.png",
    ],
)
def test_arquivos_da_interface(cliente, caminho):
    assert cliente.get(caminho).status_code == 200


def test_manifest_discreto_e_instalavel(cliente):
    resposta = cliente.get("/manifest.webmanifest")
    assert resposta.headers["content-type"].startswith("application/manifest+json")
    manifest = json.loads(resposta.text)
    assert manifest["display"] == "standalone"
    assert {"192x192", "512x512"} <= {icone["sizes"] for icone in manifest["icons"]}
    visivel = " ".join([manifest["name"], manifest["short_name"], manifest["description"]]).lower()
    for palavra in ("violência", "mulher", "denúncia", "lilás", "rede"):
        assert palavra not in visivel


def test_service_worker_nao_guarda_a_conversa_e_inclui_novos_arquivos(cliente):
    sw = cliente.get("/sw.js")
    assert sw.headers["cache-control"] == "no-cache"
    assert '"/mensagem"' not in sw.text
    assert 'pedido.method !== "GET"' in sw.text
    for item in (
        '"/app.js"',
        '"/perfil.js"',
        '"/beneficios.js"',
        '"/triagem.js"',
        '"/dados.js"',
        '"/risco.js"',
        '"/regras/beneficios.json"',
        '"/regras/triagem_fonar.json"',
        '"/regras/risco_imediato.json"',
        '"/rede-protecao"',
    ):
        assert item in sw.text


def test_interface_permite_armazenamento_apenas_em_perfil_js():
    # s3-frontend-e-perfil, tarefa 2.2: verifica todos os scripts de web/ e permite armazenamento só em web/perfil.js.
    scripts = {p.name: p.read_text(encoding="utf-8") for p in sorted((RAIZ / "web").glob("*.js"))}
    assert "perfil.js" in scripts and "app.js" in scripts and "beneficios.js" in scripts
    assert _scripts_usam_armazenamento(scripts) == []

    # Em perfil.js, somente localStorage é usado (nunca sessionStorage, indexedDB ou cookies)
    codigo_perfil = scripts["perfil.js"]
    # perfil.js usa localStorage por uma variável ("s = storage || localStorage"), sem "localStorage.".
    # Os comentários saem antes da busca, para a menção no cabeçalho não bastar.
    sem_comentarios = re.sub(r"//[^\n]*", "", codigo_perfil)
    assert re.search(r"\blocalStorage\b", sem_comentarios)
    for api_proibida in ("sessionStorage", "indexedDB", "document.cookie"):
        assert f"{api_proibida}." not in codigo_perfil and f"{api_proibida}[" not in codigo_perfil

    # Confirma que a verificação falha caso app.js ou outro script passe a usar armazenamento
    scripts_Simulados = dict(scripts, **{"app.js": scripts["app.js"] + "\nlocalStorage.setItem('x', '1');"})
    assert _scripts_usam_armazenamento(scripts_Simulados) == [("app.js", "localStorage")]


def test_navegacao_secoes_saida_rapida_e_conversa_inicial(cliente):
    # s3-frontend-e-perfil, tarefa 1.1
    html = cliente.get("/").text
    for secao_id in ("sec-home", "sec-screening", "sec-benefits", "sec-rights", "sec-places", "sec-fonar"):
        assert f'id="{secao_id}"' in html

    # O cabeçalho com Saída rápida, Apagar meus dados e 180/190 fica fora das seções (visível em todas as telas)
    pos_header_fim = html.index("</header>")
    pos_main_inicio = html.index("<main")
    trecho_header = html[:pos_header_fim]
    assert pos_header_fim < pos_main_inicio
    assert 'id="sair"' in trecho_header
    assert 'id="apagar-dados"' in trecho_header
    assert 'href="tel:180"' in trecho_header
    assert 'href="tel:190"' in trecho_header

    # A conversa está presente na página inicial pronta para digitar
    assert 'id="conversa"' in html
    assert 'id="envio"' in html
    assert 'id="texto"' in html


def test_saida_rapida_e_apagar_dados_preservam_service_worker(cliente):
    # s3-frontend-e-perfil, tarefas 2.3 e 2.4
    codigo = cliente.get("/app.js").text
    assert "location.replace(SITE_NEUTRO)" in codigo

    # sair() apaga a conversa e o perfil
    # Até a chave que fecha a função no início da linha: "{}" dentro do corpo não encerra o bloco.
    bloco_sair = re.search(r"function sair\(\)\s*\{(.*?)\n\}", codigo, re.S).group(1)
    assert "apagarConversa()" in bloco_sair
    assert "Perfil.apagar()" in bloco_sair

    # pagehide apaga apenas a conversa em memória, mantendo o perfil salvo no navegador
    assert 'window.addEventListener("pagehide", apagarConversa);' in codigo

    # apagarMeusDados() remove apenas o perfil e dados em memória, sem apagar o cache do Service Worker
    bloco_apagar = re.search(r"function apagarMeusDados\(\)\s*\{(.*?)\n\}", codigo, re.S).group(1)
    assert "Perfil.apagar()" in bloco_apagar
    assert "caches.delete" not in codigo


def test_perfil_e_respostas_de_beneficios_nunca_saem_do_aparelho(cliente):
    # s3-frontend-e-perfil (tarefa 2.5) e s3-beneficios (tarefa 3.1)
    for caminho_js in sorted((RAIZ / "web").glob("*.js")):
        if caminho_js.name == "sw.js":
            continue
        codigo = caminho_js.read_text(encoding="utf-8")
        # Nenhuma chamada fetch() pode enviar perfilUsuario, respostasEspecificasBeneficios ou respostasFonar
        for chamada_fetch in re.findall(r"fetch\([^;]+", codigo, re.S):
            assert "perfilUsuario" not in chamada_fetch
            assert "respostasEspecificasBeneficios" not in chamada_fetch
            assert "respostasFonar" not in chamada_fetch
            assert "Perfil." not in chamada_fetch

    # A tela de Benefícios avalia localmente com Beneficios.avaliar e mostra referências legais, aviso e CRAS
    app_js = cliente.get("/app.js").text
    html = cliente.get("/").text
    assert 'src="/beneficios.js"' in html
    assert 'src="/triagem.js"' in html
    assert 'id="benefits-specific-questions"' in html
    assert "Beneficios.avaliar(regrasDeBeneficios, entradaPerfil, especificas)" in app_js
    assert "Triagem.avaliar(regrasDeTriagem, respostasFonar)" in app_js
    assert "ordemRespostasFonar.pop()" in app_js
    assert 'respostasEspecificasBeneficios.acompanhamento_psicossocial || "prefiro_nao_informar"' in app_js
    assert "CRAS mais próximo" in html


def test_bloqueio_de_beneficios_e_locais_sem_perfil_e_liberacao_de_triagem_e_conversa(cliente):
    # s3-frontend-e-perfil, tarefa 3.1
    codigo = cliente.get("/app.js").text
    assert 'const exigePerfil = ["benefits", "rights", "places"].includes(destino);' in codigo
    assert "const estaCompleto = typeof Perfil !== \"undefined\" && Perfil.completo(perfilUsuario);" in codigo
    assert 'if (exigePerfil && !estaCompleto)' in codigo
    assert 'secaoAtual = "screening";' in codigo


def test_rota_rede_protecao_sem_parametros_e_tela_onde_buscar_ajuda(cliente):
    # s3-frontend-e-perfil, tarefa 3.2
    resposta = cliente.get("/rede-protecao")
    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-cache"
    servicos = resposta.json()
    assert isinstance(servicos, list) and len(servicos) >= 20
    campos_esperados = {
        "nome",
        "tipo",
        "endereco",
        "ra",
        "cep",
        "telefone",
        "horario",
        "fonte_url",
        "data_verificacao",
    }
    for s in servicos:
        assert campos_esperados <= set(s.keys())

    # Na tela Onde buscar ajuda, a busca é um GET sem parâmetros e ordena a RA do perfil primeiro
    codigo = cliente.get("/app.js").text
    assert 'const ROTA_REDE = "/rede-protecao";' in codigo
    assert "fetch(ROTA_REDE)" in codigo
    assert "s.fonte_url" in codigo
    assert "s.data_verificacao" in codigo
    assert "Confirme por telefone antes de ir" in codigo
    assert "a.ra === raAlvo ? 0 : 1" in codigo


def test_tela_espera_mais_que_o_servidor(cliente):
    # O servidor desiste primeiro e devolve a mensagem com o Ligue 180; o limite da tela
    # é só a rede de segurança para quando a conexão cai.
    codigo = cliente.get("/app.js").text
    limite_ms = int(re.search(r"const TEMPO_LIMITE_MS = (\d+);", codigo).group(1))
    assert TIMEOUT_PADRAO * 1000 < limite_ms <= TIMEOUT_PADRAO * 1000 + 10_000


def test_mensagem_responde_com_o_llm(cliente):
    falso = usar(LLMFalso("Resposta fictícia."))
    historico = [{"papel": "usuaria", "texto": "Oi"}, {"papel": "assistente", "texto": "Olá"}]
    resposta = cliente.post("/mensagem", json={"texto": PERGUNTA, "historico": historico})

    assert resposta.status_code == 200
    assert resposta.json() == {"resposta": "Resposta fictícia."}
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.headers["referrer-policy"] == "no-referrer"
    papeis = [m["role"] for m in falso.recebido]
    assert papeis == ["system", "user", "assistant", "user"]
    assert falso.recebido[-1]["content"] == PERGUNTA


def test_llm_indisponivel_indica_o_180(cliente):
    usar(LLMFalso(erro=llm.LLMIndisponivel("APITimeoutError")))
    resposta = cliente.post("/mensagem", json={"texto": PERGUNTA})
    assert resposta.status_code == 503
    assert "180" in resposta.json()["erro"]


def test_sem_configuracao_responde_indisponivel(cliente):
    def sem_config():
        raise ConfigIncompleta("Variável de ambiente não definida: LLM_MODEL")

    main.cliente_llm = sem_config
    resposta = cliente.post("/mensagem", json={"texto": PERGUNTA})
    assert resposta.status_code == 503
    assert "LLM_MODEL" not in resposta.text


@pytest.mark.parametrize(
    "corpo",
    [{"texto": ""}, {"texto": "x" * 2001}, {"texto": "oi", "historico": [{"papel": "sistema", "texto": "x"}]}],
)
def test_mensagem_invalida(cliente, corpo):
    usar(LLMFalso())
    assert cliente.post("/mensagem", json=corpo).status_code == 422


def test_texto_da_mensagem_nao_vai_para_o_log(cliente, caplog):
    usar(LLMFalso())
    with caplog.at_level(logging.DEBUG):
        cliente.post("/mensagem", json={"texto": PERGUNTA})
    log = "\n".join(r.getMessage() for r in caplog.records if not r.name.startswith(("httpx", "httpcore")))
    assert "POST /mensagem 200" in log
    assert "auxílio" not in log


def test_tela_usa_a_rota_juridica_e_mostra_fontes_sem_link(cliente):
    # s2-rag-juridico, tarefa 2.4: toda mensagem vai para /juridico (decisão de 05/11, até a S4).
    codigo = cliente.get("/app.js").text
    assert 'const ROTA = "/juridico";' in codigo
    assert "JSON.stringify({ pergunta: texto })" in codigo
    assert "texto verificado em" in codigo
    # Sem link para sites (a página da lei ficaria no histórico do navegador); só tel:190 e tel:180.
    assert "planalto" not in codigo
    assert set(re.findall(r'\.href = "([^"]*)"', codigo)) == {"tel:190", "tel:180"}


def test_alerta_de_190_na_tela_antes_do_envio_e_offline(cliente):
    # s2-alerta-risco-190, tarefas 2.2 e 2.3. A paridade com o servidor está em test_risco_js.py.
    html = cliente.get("/").text
    assert html.index('src="/risco.js"') < html.index('src="/app.js"')
    codigo = cliente.get("/app.js").text
    # A checagem local vem antes do aviso de "sem internet" e do envio ao servidor.
    assert codigo.index("Risco.avaliar(regrasDeRisco, texto)") < codigo.index("if (!navigator.onLine)")
    assert codigo.index("Risco.avaliar(regrasDeRisco, texto)") < codigo.index("await fetch(ROTA")
    assert "dados.risco_imediato" in codigo  # o servidor também pode mandar o alerta
    sw = cliente.get("/sw.js").text
    assert '"/risco.js"' in sw and '"/regras/risco_imediato.json"' in sw
    regras = cliente.get("/regras/risco_imediato.json")
    assert regras.status_code == 200 and regras.json()["regras"]


@pytest.mark.parametrize(
    "caminho",
    [
        "/",
        "/app.js",
        "/perfil.js",
        "/beneficios.js",
        "/triagem.js",
        "/dados.js",
        "/risco.js",
        "/styles.css",
        "/regras/beneficios.json",
        "/regras/triagem_fonar.json",
        "/regras/risco_imediato.json",
    ],
)
def test_arquivos_da_tela_sempre_conferidos_com_o_servidor(cliente, caminho):
    # Sem Cache-Control, o navegador reaproveitava o app.js antigo depois de uma atualização (05/11).
    assert cliente.get(caminho).headers["cache-control"] == "no-cache"


def test_service_worker_ignora_o_cache_http_ao_atualizar(cliente):
    sw = cliente.get("/sw.js").text
    assert 'new Request(url, { cache: "reload" })' in sw
    assert 'fetch(pedido, { cache: "no-cache" })' in sw
