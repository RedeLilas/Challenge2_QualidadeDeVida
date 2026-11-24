"""web/audio.js no QuickJS (s5-entrada-audio, tarefa 3.1).

Microfone, gravador, temporizadores e fetch são falsos. Os textos são os casos fictícios do design
(A1 e A5/A6); nenhuma voz ou relato real.
"""
import json
from pathlib import Path

import pytest
import quickjs

RAIZ = Path(__file__).resolve().parents[1]

# Casos fictícios do design da s5-entrada-audio.
A1 = "Ele pode tirar meus filhos de mim?"
A5 = "Ele está aqui na porta com uma faca e disse que vai me matar"
A6 = "Ele disse que vai me matar hoje, posso pedir medida protetiva?"

AMBIENTE_FALSO = r"""
var registro = { trilhasParadas: 0, pedidosMicrofone: 0, timeouts: [], intervalos: [], fetches: [], abortados: 0 };
var agoraFalso = 0;

function Trilha() { this.parada = false; }
Trilha.prototype.stop = function () { this.parada = true; registro.trilhasParadas += 1; };

function Fluxo() { this.trilhas = [new Trilha()]; }
Fluxo.prototype.getTracks = function () { return this.trilhas; };

function BlobFalso(partes, opcoes) { this.partes = partes; this.type = opcoes.type; this.size = partes.length; }

function GravadorFalso(fluxo, opcoes) {
  this.fluxo = fluxo;
  this.mimeType = opcoes ? opcoes.mimeType : "audio/webm";
  this.state = "inactive";
  GravadorFalso.ultimo = this;
}
GravadorFalso.aceitos = ["audio/webm;codecs=opus"];
GravadorFalso.isTypeSupported = function (tipo) { return GravadorFalso.aceitos.indexOf(tipo) >= 0; };
GravadorFalso.prototype.start = function () { this.state = "recording"; };
GravadorFalso.prototype.stop = function () {
  this.state = "inactive";
  if (this.ondataavailable) this.ondataavailable({ data: { size: 3, conteudo: "pedaco-ficticio" } });
  if (this.onstop) this.onstop();
};

function ControleFalso() {
  var self = this;
  this.signal = { aborted: false };
  this.abort = function () { self.signal.aborted = true; registro.abortados += 1; };
}

var respostaFalsa = { ok: true, status: 200, corpo: { texto: "texto ficticio" } };
var fetchPendente = null;

function criarAmbiente(opcoes) {
  opcoes = opcoes || {};
  var permissao = opcoes.permissao || "aceita";
  return {
    navigator: {
      onLine: opcoes.offline ? false : true,
      mediaDevices: opcoes.semMicrofone ? undefined : {
        getUserMedia: function () {
          registro.pedidosMicrofone += 1;
          if (permissao === "negada") return Promise.reject(new Error("NotAllowedError"));
          if (permissao === "pendente") {
            return new Promise(function (resolver) { ambientePendente = function () { resolver(new Fluxo()); }; });
          }
          return Promise.resolve(new Fluxo());
        },
      },
    },
    MediaRecorder: opcoes.semGravador ? null : GravadorFalso,
    Blob: BlobFalso,
    AbortController: ControleFalso,
    fetch: function (url, init) {
      registro.fetches.push({ url: url, metodo: init.method, cache: init.cache, tipo: init.headers["Content-Type"], corpo: init.body });
      var resposta = {
        ok: respostaFalsa.ok,
        status: respostaFalsa.status,
        json: function () { return Promise.resolve(respostaFalsa.corpo); },
      };
      if (opcoes.fetchPendente) {
        return new Promise(function (resolver) { fetchPendente = function () { resolver(resposta); }; });
      }
      return Promise.resolve(resposta);
    },
    setTimeout: function (fn, ms) { registro.timeouts.push({ fn: fn, ms: ms, ativo: true }); return registro.timeouts.length - 1; },
    clearTimeout: function (id) { if (registro.timeouts[id]) registro.timeouts[id].ativo = false; },
    setInterval: function (fn, ms) { registro.intervalos.push({ fn: fn, ms: ms, ativo: true }); return registro.intervalos.length - 1; },
    clearInterval: function (id) { if (registro.intervalos[id]) registro.intervalos[id].ativo = false; },
    agora: function () { return agoraFalso; },
  };
}
var ambientePendente = null;
var resultados = { parou: [], erros: [], contagem: [], transcricao: undefined };
function opcoesDeTeste(ambiente) {
  return {
    ambiente: ambiente,
    aoParar: function (blob, tipo) { resultados.parou.push({ tipo: tipo, blobTipo: blob.type, partes: blob.partes.length }); },
    aoErro: function (mensagem) { resultados.erros.push(mensagem); },
    aoContar: function (s) { resultados.contagem.push(s); },
  };
}
"""


@pytest.fixture
def js():
    contexto = quickjs.Context()
    contexto.eval((RAIZ / "web" / "risco.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "audio.js").read_text(encoding="utf-8"))
    regras = (RAIZ / "regras" / "risco_imediato.json").read_text(encoding="utf-8")
    contexto.eval(f"var REGRAS = Risco.compilar({regras});")
    contexto.eval(AMBIENTE_FALSO)
    return contexto


def chamar(js, expressao):
    return json.loads(js.eval(f"JSON.stringify({expressao})"))


def rodar_promessas(js):
    while js.execute_pending_job():
        pass


# --- Funções puras ---


@pytest.mark.parametrize(
    "aceitos, esperado",
    [
        (["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4"], "audio/webm;codecs=opus"),  # Chrome/Android
        (["audio/ogg;codecs=opus"], "audio/ogg;codecs=opus"),
        (["audio/mp4"], "audio/mp4"),  # Safari/iPhone
        ([], ""),  # o navegador escolhe o padrão dele
    ],
)
def test_escolha_do_formato(js, aceitos, esperado):
    assert chamar(js, f"Gravacao.escolherFormato(function (t) {{ return {json.dumps(aceitos)}.indexOf(t) >= 0; }})") == esperado


@pytest.mark.parametrize(
    "decorrido_ms, esperado",
    [(0, 30), (500, 30), (1000, 29), (29_001, 1), (30_000, 0), (45_000, 0)],
)
def test_contagem_regressiva_ate_o_limite(js, decorrido_ms, esperado):
    assert chamar(js, "Gravacao.LIMITE_SEGUNDOS") == 30
    assert chamar(js, f"Gravacao.segundosRestantes(1000, {1000 + decorrido_ms})") == esperado


@pytest.mark.parametrize("texto", [A5, A6])
def test_transcricao_com_risco_mostra_o_alerta(js, texto):
    decisao = chamar(js, f"Gravacao.decidir(REGRAS, {json.dumps(texto)})")
    assert decisao["acao"] == "alerta"
    assert decisao["texto"] == texto
    assert decisao["categoria"] in {"arma", "ameaca_morte"}


def test_transcricao_sem_risco_vai_para_a_caixa(js):
    assert chamar(js, f"Gravacao.decidir(REGRAS, {json.dumps('  ' + A1 + ' ')})") == {"acao": "caixa", "texto": A1}


@pytest.mark.parametrize("texto", ["", "   ", None])
def test_transcricao_vazia(js, texto):
    assert chamar(js, f"Gravacao.decidir(REGRAS, {json.dumps(texto)})") == {"acao": "vazio"}


def test_sem_regras_carregadas_o_texto_vai_para_a_caixa(js):
    # enviar() roda a regra de novo antes do envio, e o /orquestrar também checa o risco.
    assert chamar(js, f"Gravacao.decidir(null, {json.dumps(A5)})") == {"acao": "caixa", "texto": A5}


def test_mensagens_de_erro_da_transcricao(js):
    assert chamar(js, 'Gravacao.mensagemDeErro(503, {erro: "Mensagem do servidor."})') == "Mensagem do servidor."
    assert chamar(js, "Gravacao.mensagemDeErro(413, {})") == chamar(js, "Gravacao.TEXTOS.limite")
    assert "30 segundos" in chamar(js, "Gravacao.TEXTOS.limite")
    assert chamar(js, "Gravacao.mensagemDeErro(500, null)") == chamar(js, "Gravacao.TEXTOS.falha")


@pytest.mark.parametrize(
    "opcoes, esperado",
    [("{}", True), ("{offline: true}", False), ("{semMicrofone: true}", False), ("{semGravador: true}", False)],
)
def test_disponivel_so_com_microfone_gravador_e_internet(js, opcoes, esperado):
    assert chamar(js, f"Gravacao.disponivel(criarAmbiente({opcoes}))") is esperado


@pytest.mark.parametrize(
    "opcoes, esperado",
    [("{}", True), ("{offline: true}", True), ("{semMicrofone: true}", False), ("{semGravador: true}", False)],
)
def test_suportado_nao_depende_da_internet(js, opcoes, esperado):
    # Sem internet o botão aparece desabilitado; sem microfone ou gravador, ele nem aparece.
    assert chamar(js, f"Gravacao.suportado(criarAmbiente({opcoes}))") is esperado


# --- Gravação ---


def iniciar(js, opcoes="{}"):
    js.eval(f"var amb = criarAmbiente({opcoes}); var inicio = Gravacao.iniciar(opcoesDeTeste(amb));")
    rodar_promessas(js)


def test_gravar_e_parar_entrega_o_audio_e_desliga_o_microfone(js):
    iniciar(js)
    assert chamar(js, "Gravacao.gravando()") is True
    assert chamar(js, "registro.pedidosMicrofone") == 1
    assert chamar(js, "GravadorFalso.ultimo.mimeType") == "audio/webm;codecs=opus"
    assert chamar(js, "resultados.contagem") == [30]
    js.eval("Gravacao.parar();")
    assert chamar(js, "resultados.parou") == [{"tipo": "audio/webm;codecs=opus", "blobTipo": "audio/webm;codecs=opus", "partes": 1}]
    assert chamar(js, "registro.trilhasParadas") == 1
    assert chamar(js, "Gravacao.gravando()") is False
    assert chamar(js, "registro.timeouts.every(function (t) { return !t.ativo; })") is True
    assert chamar(js, "registro.intervalos.every(function (t) { return !t.ativo; })") is True


def test_gravacao_para_sozinha_no_limite(js):
    iniciar(js)
    assert chamar(js, "registro.timeouts.map(function (t) { return t.ms; })") == [30_000]
    js.eval("agoraFalso = 12000; registro.intervalos[0].fn();")
    assert chamar(js, "resultados.contagem") == [30, 18]
    js.eval("registro.timeouts[0].fn();")
    assert len(chamar(js, "resultados.parou")) == 1
    assert chamar(js, "registro.trilhasParadas") == 1


def test_cancelar_durante_a_gravacao_descarta_o_audio(js):
    iniciar(js)
    js.eval("Gravacao.cancelar(amb);")
    assert chamar(js, "resultados.parou") == []
    assert chamar(js, "registro.trilhasParadas") == 1
    assert chamar(js, "Gravacao.gravando()") is False
    assert chamar(js, "GravadorFalso.ultimo.state") == "inactive"
    assert chamar(js, "registro.timeouts.every(function (t) { return !t.ativo; })") is True


def test_cancelar_enquanto_o_navegador_pede_a_permissao(js):
    iniciar(js, "{permissao: 'pendente'}")
    js.eval("Gravacao.cancelar(amb); ambientePendente();")
    rodar_promessas(js)
    assert chamar(js, "Gravacao.gravando()") is False
    assert chamar(js, "registro.trilhasParadas") == 1  # o microfone recém-liberado é desligado na hora
    assert chamar(js, "resultados.parou") == []


def test_permissao_negada(js):
    iniciar(js, "{permissao: 'negada'}")
    assert chamar(js, "resultados.erros") == [chamar(js, "Gravacao.TEXTOS.semMicrofone")]
    assert chamar(js, "Gravacao.gravando()") is False


def test_sem_internet_nao_pede_o_microfone(js):
    iniciar(js, "{offline: true}")
    assert chamar(js, "resultados.erros") == [chamar(js, "Gravacao.TEXTOS.semInternet")]
    assert chamar(js, "registro.pedidosMicrofone") == 0


# --- Transcrição ---


def transcrever(js, opcoes="{}"):
    js.eval(
        f"var amb = criarAmbiente({opcoes});"
        "Gravacao.transcrever(new BlobFalso(['x'], {type: 'audio/mp4'}), 'audio/mp4', amb)"
        ".then(function (r) { resultados.transcricao = r; });"
    )
    rodar_promessas(js)


def test_transcrever_envia_so_ao_servidor_da_aplicacao_sem_cache(js):
    transcrever(js)
    assert chamar(js, "registro.fetches.map(function (f) { return [f.url, f.metodo, f.cache, f.tipo]; })") == [
        ["/transcrever", "POST", "no-store", "audio/mp4"]
    ]
    assert chamar(js, "resultados.transcricao") == {"ok": True, "texto": "texto ficticio"}


def test_transcrever_acima_do_limite(js):
    js.eval("respostaFalsa = {ok: false, status: 413, corpo: {}};")
    transcrever(js)
    assert chamar(js, "resultados.transcricao") == {"ok": False, "mensagem": chamar(js, "Gravacao.TEXTOS.limite")}


def test_cancelar_durante_a_transcricao_ignora_o_texto(js):
    transcrever(js, "{fetchPendente: true}")
    js.eval("Gravacao.cancelar(amb); fetchPendente();")
    rodar_promessas(js)
    assert chamar(js, "registro.abortados") == 1
    assert chamar(js, "resultados.transcricao") is None


# --- Ambiente do navegador de verdade (achado na verificação no Chromium, 24/11) ---

NAVEGADOR_ESTRITO = r"""
// Como no navegador: setTimeout e companhia falham ("Illegal invocation") se chamados como método
// de outro objeto, e MediaRecorder.isTypeSupported também, se chamado solto.
var chamadasEstritas = [];
function exigirGlobal(nome, self) {
  if (self !== undefined && self !== globalThis) throw new TypeError("Illegal invocation: " + nome);
  chamadasEstritas.push(nome);
}
var setTimeout = function (fn, ms) { "use strict"; exigirGlobal("setTimeout", this); return 1; };
var clearTimeout = function () { "use strict"; exigirGlobal("clearTimeout", this); };
var setInterval = function (fn, ms) { "use strict"; exigirGlobal("setInterval", this); return 2; };
var clearInterval = function () { "use strict"; exigirGlobal("clearInterval", this); };
function MediaRecorder(fluxo, opcoes) { this.mimeType = opcoes ? opcoes.mimeType : ""; this.state = "inactive"; }
MediaRecorder.isTypeSupported = function (tipo) {
  "use strict";
  if (this !== MediaRecorder) throw new TypeError("Illegal invocation: isTypeSupported");
  return tipo === "audio/webm;codecs=opus";
};
MediaRecorder.prototype.start = function () { this.state = "recording"; };
MediaRecorder.prototype.stop = function () { this.state = "inactive"; if (this.onstop) this.onstop(); };
var navigator = { onLine: true, mediaDevices: { getUserMedia: function () { return Promise.resolve({ getTracks: function () { return [{ stop: function () {} }]; } }); } } };
function Blob() {}
function AbortController() { this.signal = {}; this.abort = function () {}; }
function fetch() { return new Promise(function () {}); }
var erros = [];
"""


def test_ambiente_do_navegador_respeita_as_regras_de_chamada():
    # Sem ambiente explícito, o módulo usa as funções do navegador: a gravação precisa começar e parar.
    contexto = quickjs.Context()
    contexto.eval(NAVEGADOR_ESTRITO)
    contexto.eval((RAIZ / "web" / "risco.js").read_text(encoding="utf-8"))
    contexto.eval((RAIZ / "web" / "audio.js").read_text(encoding="utf-8"))
    contexto.eval(
        "var contagem = []; Gravacao.iniciar({ aoContar: function (s) { contagem.push(s); },"
        " aoParar: function () {}, aoErro: function (m) { erros.push(m); } })"
        ".catch(function (e) { erros.push(String(e)); });"
    )
    while contexto.execute_pending_job():
        pass
    assert json.loads(contexto.eval("JSON.stringify(erros)")) == []
    assert contexto.eval("Gravacao.gravando()") is True
    assert json.loads(contexto.eval("JSON.stringify(contagem)")) == [30]
    contexto.eval("Gravacao.parar();")
    assert contexto.eval("Gravacao.gravando()") is False
    assert {"setTimeout", "setInterval", "clearTimeout", "clearInterval"} <= set(json.loads(contexto.eval("JSON.stringify(chamadasEstritas)")))
