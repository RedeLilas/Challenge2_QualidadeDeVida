// Pergunta por áudio no navegador (s5-entrada-audio, tarefa 3.1).
// O áudio fica só na memória desta aba: nada vai para armazenamento local, Cache API ou download.
// Vai só ao servidor da própria aplicação (POST /transcrever), que devolve o texto e não guarda nada.
// O nome não é "Audio" para não esconder o construtor Audio do navegador.
// Testes em tests/test_audio_js.py, rodando este arquivo no QuickJS com microfone e gravador falsos.
"use strict";

var Gravacao = (function () {
  var LIMITE_SEGUNDOS = 30;
  var ROTA = "/transcrever";
  // Primeiro formato aceito pelo navegador: opus no Chrome/Android e no Firefox, mp4 (AAC) no Safari/iPhone.
  var FORMATOS = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/mp4"];

  var TEXTOS = {
    limite: "O áudio pode ter até 30 segundos. Grave de novo, em partes, ou digite sua pergunta.",
    vazio: "Não entendi o áudio. Tente de novo ou digite sua pergunta.",
    semInternet: "Para usar o áudio, é preciso internet. Digite sua pergunta.",
    semMicrofone: "Não foi possível usar o microfone. Você pode digitar sua pergunta.",
    falha: "Não consegui transcrever o áudio agora. Tente de novo ou digite sua pergunta.",
  };

  // --- Funções puras (sem DOM, sem rede) ---

  // O primeiro formato aceito, ou "" para o navegador escolher o padrão dele.
  function escolherFormato(aceita) {
    for (var i = 0; i < FORMATOS.length; i++) {
      if (aceita(FORMATOS[i])) return FORMATOS[i];
    }
    return "";
  }

  // Segundos inteiros que faltam para o limite (para a contagem regressiva), nunca negativos.
  function segundosRestantes(inicioMs, agoraMs) {
    var restante = LIMITE_SEGUNDOS - (agoraMs - inicioMs) / 1000;
    return restante <= 0 ? 0 : Math.ceil(restante);
  }

  // O que fazer quando a transcrição chega. A regra de risco roda antes de qualquer outra coisa:
  // com sinal de risco, o alerta de 190 aparece na hora e nada vai ao orquestrador sem o toque em
  // "Continuar com minha pergunta" (exceção à decisão de 17/11 registrada no design).
  // Sem as regras carregadas, o texto vai para a caixa: enviar() e o servidor checam de novo.
  function decidir(regras, texto) {
    var limpo = String(texto == null ? "" : texto).trim();
    if (!limpo) return { acao: "vazio" };
    var risco = regras ? Risco.avaliar(regras, limpo) : null;
    if (risco) return { acao: "alerta", texto: limpo, categoria: risco.categoria };
    return { acao: "caixa", texto: limpo };
  }

  // Mensagem para a tela a partir da resposta do POST /transcrever (status e corpo JSON).
  function mensagemDeErro(status, dados) {
    if (dados && typeof dados.erro === "string" && dados.erro) return dados.erro;
    if (status === 413) return TEXTOS.limite;
    return TEXTOS.falha;
  }

  // O áudio só funciona com microfone, gravador e internet. Sem isso, o botão fica desabilitado.
  function disponivel(ambiente) {
    var nav = ambiente.navigator;
    return Boolean(
      nav && nav.onLine && nav.mediaDevices && typeof nav.mediaDevices.getUserMedia === "function" && ambiente.MediaRecorder
    );
  }

  // --- Gravação (precisa do navegador; o ambiente é passado para os testes usarem falsos) ---

  var estado = null; // { gravador, fluxo, pedacos, tipo, temporizador, contador, descartar }
  var pedidoAtual = null;
  var geracao = 0; // cancelar() muda a geração; resultados de uma geração antiga são ignorados

  function ambienteDoNavegador() {
    return {
      navigator: navigator,
      MediaRecorder: typeof MediaRecorder === "undefined" ? null : MediaRecorder,
      fetch: function (url, opcoes) { return fetch(url, opcoes); },
      AbortController: AbortController,
      Blob: Blob,
      setTimeout: setTimeout,
      clearTimeout: clearTimeout,
      setInterval: setInterval,
      clearInterval: clearInterval,
      agora: function () { return Date.now(); },
    };
  }

  function desligarMicrofone(fluxo) {
    if (!fluxo || typeof fluxo.getTracks !== "function") return;
    fluxo.getTracks().forEach(function (trilha) { trilha.stop(); });
  }

  function limparEstado(ambiente) {
    if (!estado) return;
    ambiente.clearTimeout(estado.temporizador);
    ambiente.clearInterval(estado.contador);
    desligarMicrofone(estado.fluxo);
    estado.pedacos.length = 0;
    estado = null;
  }

  function gravando() {
    return estado !== null;
  }

  // Chamar só dentro do tratador do toque no botão: é aqui que o navegador pede a permissão.
  // opcoes: { aoContar(segundos), aoParar(blob, tipo), aoErro(mensagem), ambiente }
  function iniciar(opcoes) {
    var ambiente = opcoes.ambiente || ambienteDoNavegador();
    if (estado) return Promise.resolve(false);
    if (!disponivel(ambiente)) {
      opcoes.aoErro(ambiente.navigator && !ambiente.navigator.onLine ? TEXTOS.semInternet : TEXTOS.semMicrofone);
      return Promise.resolve(false);
    }
    var minhaGeracao = geracao;
    return ambiente.navigator.mediaDevices.getUserMedia({ audio: true }).then(
      function (fluxo) {
        // A saída rápida pode ter sido tocada enquanto o navegador pedia a permissão.
        if (minhaGeracao !== geracao || estado) {
          desligarMicrofone(fluxo);
          return false;
        }
        var Gravador = ambiente.MediaRecorder;
        var aceita = typeof Gravador.isTypeSupported === "function" ? Gravador.isTypeSupported : function () { return false; };
        var tipo = escolherFormato(aceita);
        var gravador = tipo ? new Gravador(fluxo, { mimeType: tipo }) : new Gravador(fluxo);
        var inicio = ambiente.agora();
        estado = { gravador: gravador, fluxo: fluxo, pedacos: [], tipo: tipo || gravador.mimeType || "", descartar: false };
        var atual = estado;

        gravador.ondataavailable = function (evento) {
          if (evento.data && evento.data.size > 0) atual.pedacos.push(evento.data);
        };
        gravador.onstop = function () {
          var pedacos = atual.pedacos.slice();
          var descartar = atual.descartar;
          if (estado === atual) limparEstado(ambiente);
          if (descartar || !pedacos.length) return;
          opcoes.aoParar(new ambiente.Blob(pedacos, { type: atual.tipo }), atual.tipo);
        };

        // Limite de 30 s: a gravação para sozinha e o áudio segue para a transcrição.
        atual.temporizador = ambiente.setTimeout(parar, LIMITE_SEGUNDOS * 1000);
        atual.contador = ambiente.setInterval(function () {
          if (opcoes.aoContar) opcoes.aoContar(segundosRestantes(inicio, ambiente.agora()));
        }, 1000);
        if (opcoes.aoContar) opcoes.aoContar(LIMITE_SEGUNDOS);
        gravador.start();
        return true;
      },
      function () {
        if (minhaGeracao === geracao) opcoes.aoErro(TEXTOS.semMicrofone);
        return false;
      }
    );
  }

  // Para a gravação e entrega o áudio (por aoParar). O microfone é desligado no onstop.
  function parar() {
    if (!estado) return;
    if (estado.gravador.state !== "inactive") estado.gravador.stop();
  }

  // Envia o áudio ao servidor da aplicação e devolve { ok, texto } ou { ok: false, mensagem }.
  // Devolve null se cancelar() foi chamado antes da resposta: a tela não mostra nada.
  function transcrever(blob, tipo, ambiente) {
    ambiente = ambiente || ambienteDoNavegador();
    var minhaGeracao = geracao;
    var controle = new ambiente.AbortController();
    pedidoAtual = controle;
    return ambiente
      .fetch(ROTA, {
        method: "POST",
        headers: { "Content-Type": tipo || "application/octet-stream" },
        body: blob,
        cache: "no-store",
        signal: controle.signal,
      })
      .then(function (resposta) {
        return resposta.json().catch(function () { return {}; }).then(function (dados) {
          if (minhaGeracao !== geracao) return null;
          if (!resposta.ok) return { ok: false, mensagem: mensagemDeErro(resposta.status, dados) };
          return { ok: true, texto: typeof dados.texto === "string" ? dados.texto : "" };
        });
      })
      .catch(function () {
        if (minhaGeracao !== geracao) return null;
        return { ok: false, mensagem: TEXTOS.falha };
      })
      .then(function (resultado) {
        if (pedidoAtual === controle) pedidoAtual = null;
        return resultado;
      });
  }

  // Saída rápida e apagar conversa: para a gravação sem enviar, desliga o microfone, descarta o
  // áudio e aborta a transcrição em andamento. Uma transcrição que chegue depois é ignorada.
  function cancelar(ambiente) {
    geracao += 1;
    if (pedidoAtual) {
      pedidoAtual.abort();
      pedidoAtual = null;
    }
    if (!estado) return;
    ambiente = ambiente || ambienteDoNavegador();
    estado.descartar = true;
    var gravador = estado.gravador;
    limparEstado(ambiente);
    if (gravador.state !== "inactive") gravador.stop();
  }

  return {
    LIMITE_SEGUNDOS: LIMITE_SEGUNDOS,
    FORMATOS: FORMATOS,
    TEXTOS: TEXTOS,
    escolherFormato: escolherFormato,
    segundosRestantes: segundosRestantes,
    decidir: decidir,
    mensagemDeErro: mensagemDeErro,
    disponivel: disponivel,
    gravando: gravando,
    iniciar: iniciar,
    parar: parar,
    transcrever: transcrever,
    cancelar: cancelar,
  };
})();
