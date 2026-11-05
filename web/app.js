// Conversa só em memória: nada vai para localStorage, sessionStorage, cookies ou IndexedDB.
"use strict";

// Site neutro da saída rápida. location.replace() tira esta página do histórico.
const SITE_NEUTRO = "https://www.climatempo.com.br/previsao-do-tempo/cidade/61/brasilia-df";
const MAX_HISTORICO = 20;
// Um pouco acima do LLM_TIMEOUT do servidor (padrão 30 s): o servidor desiste primeiro e
// devolve a mensagem com o Ligue 180. Este limite só vale quando a conexão cai.
const TEMPO_LIMITE_MS = 35000;

const TEXTOS = {
  semInternet: "Sem internet. Sua mensagem não foi enviada. Tente de novo quando tiver conexão.",
  falha: "Não consegui responder agora. Tente de novo em alguns instantes. Se precisar falar com alguém, ligue 180 (gratuito, 24 horas).",
  demorou: "A resposta está demorando. Tente de novo em alguns instantes.",
  pensando: "Escrevendo resposta…",
};

const lista = document.getElementById("mensagens");
const formulario = document.getElementById("envio");
const campo = document.getElementById("texto");
const botaoEnviar = document.getElementById("enviar");
const aviso = document.getElementById("aviso");

// Turnos já respondidos: { papel: "usuaria" | "assistente", texto }.
let conversa = [];
let pedidoAtual = null;

function sair() {
  apagarConversa();
  window.location.replace(SITE_NEUTRO);
}

function apagarConversa() {
  if (pedidoAtual) pedidoAtual.abort();
  pedidoAtual = null;
  conversa = [];
  campo.value = "";
  lista.replaceChildren();
}

document.getElementById("sair").addEventListener("click", sair);
document.addEventListener("keydown", (evento) => {
  if (evento.key === "Escape") sair();
});
// Se a página sair por outro caminho, a conversa não volta pelo cache do botão voltar.
window.addEventListener("pagehide", apagarConversa);

function adicionar(classe, texto) {
  const item = document.createElement("li");
  item.className = `msg ${classe} msg--nova`;
  item.textContent = texto;
  lista.append(item);
  irParaOFim();
  return item;
}

// Rola a página até o fim: a última mensagem fica logo acima do campo de envio (que é fixo).
function irParaOFim() {
  window.scrollTo(0, document.documentElement.scrollHeight);
}

async function enviar(texto) {
  if (!navigator.onLine) {
    adicionar("msg--erro", TEXTOS.semInternet);
    return false;
  }

  const controle = new AbortController();
  pedidoAtual = controle;
  const limite = setTimeout(() => controle.abort("tempo"), TEMPO_LIMITE_MS);
  const pensando = adicionar("msg--pensando", TEXTOS.pensando);

  try {
    const resposta = await fetch("/mensagem", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ texto, historico: conversa.slice(-MAX_HISTORICO) }),
      cache: "no-store",
      signal: controle.signal,
    });
    const dados = await resposta.json().catch(() => ({}));
    pensando.remove();
    if (!resposta.ok || !dados.resposta) {
      adicionar("msg--erro", dados.erro || TEXTOS.falha);
      return false;
    }
    conversa.push({ papel: "usuaria", texto }, { papel: "assistente", texto: dados.resposta });
    adicionar("msg--assistente", dados.resposta);
    return true;
  } catch (erro) {
    pensando.remove();
    // Saída rápida no meio do pedido: não mostra nada.
    if (pedidoAtual !== controle) return false;
    const porTempo = controle.signal.aborted && controle.signal.reason === "tempo";
    adicionar("msg--erro", porTempo ? TEXTOS.demorou : navigator.onLine ? TEXTOS.falha : TEXTOS.semInternet);
    return false;
  } finally {
    clearTimeout(limite);
    if (pedidoAtual === controle) pedidoAtual = null;
  }
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const texto = campo.value.trim();
  if (!texto || pedidoAtual) return;

  adicionar("msg--usuaria", texto);
  campo.value = "";
  ajustarAltura();
  botaoEnviar.disabled = true;
  await enviar(texto);
  botaoEnviar.disabled = false;
});

// Enter envia; Shift+Enter quebra a linha.
campo.addEventListener("keydown", (evento) => {
  if (evento.key === "Enter" && !evento.shiftKey && !evento.isComposing) {
    evento.preventDefault();
    formulario.requestSubmit();
  }
});

function ajustarAltura() {
  const noFim = window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 24;
  campo.style.height = "auto";
  campo.style.height = `${campo.scrollHeight + 2}px`;
  // O campo crescendo não pode esconder a última mensagem.
  if (noFim) irParaOFim();
}
campo.addEventListener("input", ajustarAltura);

function atualizarConexao() {
  aviso.hidden = navigator.onLine;
}
window.addEventListener("online", atualizarConexao);
window.addEventListener("offline", atualizarConexao);
atualizarConexao();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
  });
}
