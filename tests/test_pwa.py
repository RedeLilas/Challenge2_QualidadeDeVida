"""PWA servida pelo FastAPI, rota de mensagem, perfil local, benefícios e rede de proteção (s2 e s3)."""
import json
import logging
import re
from pathlib import Path

import pytest
import quickjs
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
        "/conversa.js",
        "/rede.js",
        "/risco.js",
        "/audio.js",
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
        '"/conversa.js"',
        '"/risco.js"',
        '"/regras/beneficios.json"',
        '"/regras/triagem_fonar.json"',
        '"/regras/risco_imediato.json"',
        '"/rede-protecao"',
        '"/rede.js"',
        '"/cep-ra"',
        '"/audio.js"',
    ):
        assert item in sw.text


def test_interface_permite_armazenamento_apenas_em_perfil_js():
    # s3-frontend-e-perfil (tarefa 2.2) e s4-orquestrador-agentes (tarefa 4.7): verifica todos os scripts de web/
    scripts = {p.name: p.read_text(encoding="utf-8") for p in sorted((RAIZ / "web").glob("*.js"))}
    assert "perfil.js" in scripts and "app.js" in scripts and "beneficios.js" in scripts and "conversa.js" in scripts
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


def test_audio_js_nao_guarda_o_audio_no_aparelho():
    # s5-entrada-audio, tarefa 3.1: o áudio fica só na memória da aba.
    codigo = re.sub(r"//[^\n]*", "", (RAIZ / "web" / "audio.js").read_text(encoding="utf-8"))
    for proibido in ("localStorage", "sessionStorage", "indexedDB", "caches", "document.cookie", "createObjectURL", "download"):
        assert proibido not in codigo, proibido
    # Só fala com o servidor da própria aplicação, sem cache.
    assert re.findall(r'"(/[a-z]+)"', codigo) == ["/transcrever"]
    assert 'cache: "no-store"' in codigo


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

    # pagehide apaga apenas a conversa em memória (incluindo sugestões, texto em espera e modo ajudando),
    # mantendo o perfil salvo no navegador (s4-orquestrador-agentes, tarefas 4.5 e 4.6)
    assert 'window.addEventListener("pagehide", apagarConversa);' in codigo
    bloco_apagar_conversa = re.search(r"function apagarConversa\(\)\s*\{(.*?)\n\}", codigo, re.S).group(1)
    assert 'textoAguardandoAlerta = "";' in bloco_apagar_conversa
    assert "sugestoesConversa = [];" in bloco_apagar_conversa
    assert "modoAjudando = false;" in bloco_apagar_conversa
    assert "lista.replaceChildren()" in bloco_apagar_conversa

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
    # s4-orquestrador-agentes, tarefas 4.4 e 4.6: toda mensagem do chat vai para /orquestrar via Conversa.montarPedido.
    codigo = cliente.get("/app.js").text
    html = cliente.get("/").text
    assert 'const ROTA = "/orquestrar";' in codigo
    assert "Conversa.montarPedido(semCep.texto, {" in codigo
    assert "body: JSON.stringify(corpoPedido)" in codigo
    assert "texto verificado em" in codigo
    # Botão do modo "ajudando outra pessoa" com aria-pressed e estado apenas em memória
    assert 'id="modo-ajudando"' in html and 'aria-pressed="false"' in html
    assert "modoAjudando" not in (RAIZ / "web" / "perfil.js").read_text(encoding="utf-8")
    # Sem link para sites (a página da lei ficaria no histórico do navegador); só tel:190 e tel:180.
    assert "planalto" not in codigo
    assert set(re.findall(r'\.href = "([^"]*)"', codigo)) == {"tel:190", "tel:180"}


def test_alerta_de_190_na_tela_antes_do_envio_e_offline(cliente):
    # s2-alerta-risco-190 (tarefas 2.2 e 2.3) e s4-orquestrador-agentes (tarefa 4.4).
    html = cliente.get("/").text
    assert html.index('src="/risco.js"') < html.index('src="/app.js"')
    assert html.index('src="/conversa.js"') < html.index('src="/app.js"')
    codigo = cliente.get("/app.js").text
    # A checagem local vem antes do aviso de "sem internet" e do envio ao servidor.
    assert codigo.index("Risco.avaliar(regrasDeRisco, texto)") < codigo.index("if (!navigator.onLine)")
    assert codigo.index("Risco.avaliar(regrasDeRisco, texto)") < codigo.index("await fetch(ROTA")
    # O envio após o alerta só acontece pelo botão "Continuar com minha pergunta" com alertaVisto: true
    assert 'btnContinuar.textContent = "Continuar com minha pergunta";' in codigo
    assert "await enviar(pendente, { alertaVisto: true });" in codigo
    assert "dados.risco_imediato" in codigo  # o servidor também pode mandar o alerta
    sw = cliente.get("/sw.js").text
    assert '"/risco.js"' in sw and '"/regras/risco_imediato.json"' in sw and '"/conversa.js"' in sw
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
        "/conversa.js",
        "/rede.js",
        "/risco.js",
        "/audio.js",
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


def test_rota_cep_ra_sem_parametros(cliente):
    # s4-rede-atendimento, tarefa 3.1: só as faixas do DF; nenhum CEP da usuária entra ou sai.
    resposta = cliente.get("/cep-ra")
    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-cache"
    faixas = resposta.json()
    assert [(f["cep_inicio"], f["cep_fim"]) for f in faixas] == [("70000-000", "72799-999"), ("73000-000", "73699-999")]
    assert all(f["fonte_url"] and f["data_verificacao"] for f in faixas)
    # Um parâmetro na URL é ignorado: a resposta é a mesma e não repete o CEP.
    com_parametro = cliente.get("/cep-ra?cep=72215-110")
    assert com_parametro.json() == faixas and "72215-110" not in com_parametro.text
    from app.main import cep_ra
    import inspect
    assert not inspect.signature(cep_ra).parameters


def test_rede_js_carrega_antes_da_conversa_e_da_tela(cliente):
    # s4-rede-atendimento, tarefa 3.4
    html = cliente.get("/").text
    assert html.index('src="/rede.js"') < html.index('src="/conversa.js"') < html.index('src="/app.js"')


# --- s4-rede-atendimento, tarefas 3.2 e 3.3 (CEP só no aparelho) ---


def _funcao_js(codigo: str, nome: str) -> str:
    inicio = codigo.index(f"function {nome}(")
    return codigo[inicio : codigo.index("\n}\n", inicio) + 3]


def test_tela_onde_buscar_ajuda_usa_rede_e_nao_manda_cep(cliente):
    codigo = cliente.get("/app.js").text
    assert "RA_PROXIMAS" not in codigo
    assert "Rede.ordenar(servicosRedeDF" in codigo
    assert "Rede.cepParaRa(cep, faixasCepDF)" in codigo
    # Os únicos fetch da tela de serviços são GET sem parâmetros; nenhum leva o CEP.
    for chamada in re.findall(r"fetch\(([^)]*)\)", codigo):
        assert "cep" not in chamada.lower() or chamada.strip() == "ROTA_CEP"
    assert 'const ROTA_CEP = "/cep-ra";' in codigo
    html = cliente.get("/").text
    assert 'id="filtro-cep"' in html and 'value="CRAS"' in html


def test_cep_sai_do_texto_antes_do_pedido(cliente):
    codigo = cliente.get("/app.js").text
    corpo = _funcao_js(codigo, "enviar")
    # Risco sobre o texto original, depois o CEP sai, e só então o pedido é montado.
    assert corpo.index("Risco.avaliar(regrasDeRisco, texto)") < corpo.index("tirarCepDoTexto(texto)")
    assert corpo.index("tirarCepDoTexto(texto)") < corpo.index("Conversa.montarPedido(semCep.texto")
    assert "Conversa.montarPedido(texto" not in corpo


@pytest.mark.parametrize("com_rede", [True, False])
def test_corpo_do_pedido_sem_cep(cliente, com_rede):
    contexto = quickjs.Context()
    if com_rede:
        contexto.eval((RAIZ / "web" / "rede.js").read_text(encoding="utf-8"))
    contexto.eval('var faixasCepDF = [{"cep_inicio": "70000-000", "cep_fim": "72799-999"}, {"cep_inicio": "73000-000", "cep_fim": "73699-999"}];')
    contexto.eval(_funcao_js(cliente.get("/app.js").text, "tirarCepDoTexto"))
    for texto, dentro in [
        ("meu cep é 72215-110, onde tem delegacia?", True),
        ("moro no 74000-000", False),
        ("cep 72.215-110", True),
        ("cep 72215110", True),
    ]:
        resultado = json.loads(contexto.eval(f"JSON.stringify(tirarCepDoTexto({json.dumps(texto)}))"))
        assert "[CEP]" in resultado["texto"]
        assert not re.search(r"\d{2}\.?\d{3}-?\d{3}", resultado["texto"])
        assert resultado["dentroDF"] == (dentro if com_rede else None)


def test_cep_de_fora_do_df_responde_no_aparelho(cliente):
    codigo = cliente.get("/app.js").text
    assert "if (semCep.dentroDF === false) adicionar(\"msg--assistente\", TEXTOS.cepForaDoDF);" in codigo
    assert "ligue 180" in codigo.split("cepForaDoDF:")[1].split("\n")[1]


# --- s5-entrada-audio, tarefa 3.2 (botão de microfone na conversa) ---

# Casos fictícios do design da s5-entrada-audio.
AUDIO_A1 = "Ele pode tirar meus filhos de mim?"
AUDIO_A5 = "Ele está aqui na porta com uma faca e disse que vai me matar"


def test_audio_js_carrega_depois_do_risco_e_antes_da_tela(cliente):
    html = cliente.get("/").text
    assert html.index('src="/risco.js"') < html.index('src="/audio.js"') < html.index('src="/app.js"')
    botao = re.search(r'<button[^>]*id="microfone"[^>]*>', html).group(0)
    # Não envia o formulário e começa escondido até o app.js conferir o suporte do navegador.
    assert 'type="button"' in botao and "hidden" in botao and 'aria-pressed="false"' in botao


def test_microfone_so_e_pedido_no_toque(cliente):
    codigo = cliente.get("/app.js").text
    # O app.js nunca chama o microfone direto: só pelo Gravacao.iniciar, uma vez, dentro do toque.
    assert "getUserMedia" not in codigo
    assert codigo.count("Gravacao.iniciar(") == 1
    tratador = codigo[codigo.index('botaoMicrofone?.addEventListener("click"') :]
    tratador = tratador[: tratador.index("\n});\n")]
    assert "Gravacao.iniciar(" in tratador


def test_saida_rapida_e_apagar_conversa_cancelam_a_gravacao(cliente):
    codigo = cliente.get("/app.js").text
    sair = _funcao_js(codigo, "sair")
    assert "Gravacao.cancelar()" in sair
    assert sair.index("Gravacao.cancelar()") < sair.index("location.replace")
    assert "Gravacao.cancelar()" in _funcao_js(codigo, "apagarConversa")


def _tela_falsa(cliente):
    """QuickJS com risco.js, audio.js e as funções da tela que recebem a transcrição, com espiões."""
    contexto = quickjs.Context()
    contexto.eval((RAIZ / "web" / "risco.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "audio.js").read_text(encoding="utf-8"))
    regras = (RAIZ / "regras" / "risco_imediato.json").read_text(encoding="utf-8")
    contexto.eval(
        f"var regrasDeRisco = Risco.compilar({regras});"
        """
        var chamadas = { fetch: 0, enviar: 0, alertas: [], mensagens: [], removidas: 0 };
        function fetch() { chamadas.fetch += 1; return Promise.resolve({}); }
        function enviar() { chamadas.enviar += 1; return Promise.resolve(true); }
        function mostrarAlerta(opcoes) { chamadas.alertas.push({ comContinuar: !!opcoes.comContinuar, pendente: textoAguardandoAlerta }); }
        function adicionar(classe, texto) {
          chamadas.mensagens.push([classe, texto]);
          return { remove: function () { chamadas.removidas += 1; } };
        }
        function ajustarAltura() {}
        function alternarChat() {}
        function atualizarBotaoMicrofone() {}
        var textoAguardandoAlerta = "";
        var campo = { value: "", focus: function () {} };
        var botaoEnviar = { disabled: false };
        var TEXTOS = { transcrevendo: "Transcrevendo o áudio…" };
        """
    )
    codigo = cliente.get("/app.js").text
    contexto.eval(_funcao_js(codigo, "tratarTranscricao"))
    # _funcao_js corta a partir de "function": o "async" da declaração volta aqui.
    assert "async function receberAudio(" in codigo
    contexto.eval("async " + _funcao_js(codigo, "receberAudio"))
    return contexto


def _estado(contexto):
    return json.loads(contexto.eval("JSON.stringify({c: chamadas, campo: campo.value, pendente: textoAguardandoAlerta})"))


def test_transcricao_com_risco_mostra_o_190_sem_enviar(cliente):
    tela = _tela_falsa(cliente)
    assert tela.eval(f"tratarTranscricao({json.dumps(AUDIO_A5)})") == "alerta"
    estado = _estado(tela)
    assert estado["c"]["alertas"] == [{"comContinuar": True, "pendente": AUDIO_A5}]
    # Nenhuma requisição com o texto antes do toque em "Continuar com minha pergunta".
    assert estado["c"]["fetch"] == 0 and estado["c"]["enviar"] == 0
    assert estado["campo"] == ""


def test_transcricao_sem_risco_vai_para_a_caixa(cliente):
    tela = _tela_falsa(cliente)
    assert tela.eval(f"tratarTranscricao({json.dumps(AUDIO_A1)})") == "caixa"
    estado = _estado(tela)
    assert estado["campo"] == AUDIO_A1
    assert estado["c"]["alertas"] == [] and estado["c"]["fetch"] == 0 and estado["c"]["enviar"] == 0


def test_transcricao_vazia_mostra_nao_entendi(cliente):
    tela = _tela_falsa(cliente)
    assert tela.eval('tratarTranscricao("  ")') == "vazio"
    mensagens = _estado(tela)["c"]["mensagens"]
    assert mensagens == [["msg--erro", "Não entendi o áudio. Tente de novo ou digite sua pergunta."]]


def _receber(tela, resultado_js):
    tela.eval(f"Gravacao.transcrever = function () {{ return Promise.resolve({resultado_js}); }};")
    tela.eval("receberAudio({}, 'audio/webm');")
    while tela.execute_pending_job():
        pass
    return _estado(tela)


def test_audio_com_risco_de_ponta_a_ponta_na_tela(cliente):
    estado = _receber(_tela_falsa(cliente), json.dumps({"ok": True, "texto": AUDIO_A5}))
    assert estado["c"]["alertas"] == [{"comContinuar": True, "pendente": AUDIO_A5}]
    assert estado["c"]["removidas"] == 1  # o "Transcrevendo o áudio…" some
    assert estado["c"]["fetch"] == 0 and estado["c"]["enviar"] == 0


def test_transcricao_cancelada_nao_mostra_nada(cliente):
    # Saída rápida ou "apagar conversa" durante a transcrição: Gravacao.transcrever devolve null.
    estado = _receber(_tela_falsa(cliente), "null")
    assert estado["c"]["mensagens"] == [["msg--pensando", "Transcrevendo o áudio…"]]
    assert estado["c"]["removidas"] == 1
    assert estado["c"]["alertas"] == [] and estado["campo"] == ""


def test_erro_da_transcricao_mostra_a_mensagem_do_servidor(cliente):
    estado = _receber(_tela_falsa(cliente), json.dumps({"ok": False, "mensagem": "O áudio pode ter até 30 segundos."}))
    assert estado["c"]["mensagens"][-1] == ["msg--erro", "O áudio pode ter até 30 segundos."]
    assert estado["campo"] == ""


def test_botao_do_microfone_sem_internet(cliente):
    codigo = cliente.get("/app.js").text
    atualizar = _funcao_js(codigo, "atualizarBotaoMicrofone")
    assert "Gravacao.suportado(" in atualizar and "botaoMicrofone.hidden = true" in atualizar
    assert "botaoMicrofone.disabled = !gravando && !navigator.onLine" in atualizar
    assert "atualizarBotaoMicrofone()" in _funcao_js(codigo, "atualizarConexao")


_DOM_FALSO = r"""
var pedidosDeMicrofone = 0;
function qualquer() {
  return new Proxy(function () {}, {
    get: function (_alvo, chave) {
      if (chave === Symbol.toPrimitive) return function () { return ""; };
      if (chave === Symbol.iterator) return function* () {};
      if (chave === "length") return 0;
      if (chave === "then") return undefined;
      return qualquer();
    },
    set: function () { return true; },
    apply: function () { return qualquer(); },
    construct: function () { return qualquer(); },
    has: function () { return true; },
  });
}
var document = qualquer();
var window = qualquer();
var location = qualquer();
var navigator = {
  onLine: true,
  serviceWorker: qualquer(),
  mediaDevices: { getUserMedia: function () { pedidosDeMicrofone += 1; return new Promise(function () {}); } },
};
var localStorage = { getItem: function () { return null; }, setItem: function () {}, removeItem: function () {} };
function fetch() { return new Promise(function () {}); }
function setTimeout() { return 0; }
function clearTimeout() {}
function setInterval() { return 0; }
function clearInterval() {}
"""


def test_scripts_da_pagina_carregam_sem_erro_e_sem_pedir_o_microfone(cliente):
    # Roda todos os scripts na ordem do index.html, com um DOM falso que aceita qualquer chamada.
    # Pega erros que só aparecem na carga (ex.: usar um const antes da declaração), que quebrariam a tela.
    html = cliente.get("/").text
    scripts = re.findall(r'<script src="/([a-z]+\.js)"', html)
    assert scripts[-1] == "app.js" and "audio.js" in scripts
    contexto = quickjs.Context()
    contexto.eval(_DOM_FALSO)
    for nome in scripts:
        contexto.eval((RAIZ / "web" / nome).read_text(encoding="utf-8"))
    assert contexto.eval("pedidosDeMicrofone") == 0
    assert contexto.eval("Gravacao.gravando()") is False
