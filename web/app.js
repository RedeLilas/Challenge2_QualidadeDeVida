// Conversa só em memória: nada vai para localStorage, sessionStorage, cookies ou IndexedDB.
"use strict";

// Site neutro da saída rápida. location.replace() tira esta página do histórico.
const SITE_NEUTRO = "https://www.climatempo.com.br/previsao-do-tempo/cidade/61/brasilia-df";
// Até o orquestrador (S4), toda mensagem é uma pergunta jurídica respondida com citações.
const ROTA = "/juridico";
const REGRAS_DE_RISCO = "/regras/risco_imediato.json";
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

let pedidoAtual = null;
// Regras de risco imediato (regras/risco_imediato.json), guardadas pelo service worker para
// funcionar sem internet. Se não carregarem, o servidor ainda checa cada mensagem.
let regrasDeRisco = null;
fetch(REGRAS_DE_RISCO)
  .then((resposta) => (resposta.ok ? resposta.json() : Promise.reject(resposta.status)))
  .then((dados) => {
    regrasDeRisco = Risco.compilar(dados);
  })
  .catch(() => {});

function sair() {
  apagarConversa();
  window.location.replace(SITE_NEUTRO);
}

function apagarConversa() {
  if (pedidoAtual) pedidoAtual.abort();
  pedidoAtual = null;
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

// Resposta jurídica: o texto e, embaixo, a norma, o artigo e a data em que o texto da lei foi
// verificado. Sem link para o site da lei: abrir a página deixaria "Lei Maria da Penha" no
// histórico do navegador, visível para quem pegar o celular.
function adicionarResposta({ resposta, citacoes = [] }) {
  const item = adicionar("msg--assistente", "");
  const texto = document.createElement("p");
  texto.textContent = resposta;
  item.append(texto);

  if (citacoes.length) {
    const fontes = document.createElement("ul");
    fontes.className = "msg__fontes";
    fontes.setAttribute("aria-label", "Fontes");
    for (const { citacao, data_acesso } of citacoes) {
      const fonte = document.createElement("li");
      fonte.textContent = `${citacao} · texto verificado em ${dataBrasileira(data_acesso)}`;
      fontes.append(fonte);
    }
    item.append(fontes);
  }
  irParaOFim();
}

// "2026-11-03" -> "03/11/2026"
function dataBrasileira(iso) {
  const [ano, mes, dia] = String(iso).split("-");
  return dia && mes && ano ? `${dia}/${mes}/${ano}` : String(iso);
}

// Rola a página até o fim: a última mensagem fica logo acima do campo de envio (que é fixo).
function irParaOFim() {
  window.scrollTo(0, document.documentElement.scrollHeight);
}

// Alerta de 190: aparece na conversa, com o botão de ligar em destaque. Não bloqueia a conversa
// e o botão Sair continua no topo.
function mostrarAlerta() {
  const item = document.createElement("li");
  item.className = "msg msg--alerta msg--nova";
  item.setAttribute("role", "alert");

  const titulo = document.createElement("p");
  titulo.className = "alerta__titulo";
  titulo.textContent = "Você pode estar em perigo agora.";

  const ligar190 = document.createElement("a");
  ligar190.className = "alerta__ligar";
  ligar190.href = "tel:190";
  ligar190.textContent = "Ligar 190";

  const outra = document.createElement("p");
  outra.textContent = "Se a pessoa em perigo for outra, ligue 190 e informe o endereço dela.";

  const ligar180 = document.createElement("a");
  ligar180.className = "alerta__secundario";
  ligar180.href = "tel:180";
  ligar180.textContent = "Ligar 180 para conversar com alguém (gratuito, 24 horas)";

  item.append(titulo, ligar190, outra, ligar180);
  lista.append(item);
  irParaOFim();
  ligar190.focus({ preventScroll: true });
}

async function enviar(texto) {
  // Risco imediato primeiro, no próprio aparelho: funciona sem internet e não espera o servidor.
  if (regrasDeRisco && Risco.avaliar(regrasDeRisco, texto)) {
    mostrarAlerta();
    return true;
  }
  if (!navigator.onLine) {
    adicionar("msg--erro", TEXTOS.semInternet);
    return false;
  }

  const controle = new AbortController();
  pedidoAtual = controle;
  const limite = setTimeout(() => controle.abort("tempo"), TEMPO_LIMITE_MS);
  const pensando = adicionar("msg--pensando", TEXTOS.pensando);

  try {
    const resposta = await fetch(ROTA, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pergunta: texto }),
      cache: "no-store",
      signal: controle.signal,
    });
    const dados = await resposta.json().catch(() => ({}));
    pensando.remove();
    // O servidor checa de novo (protege contra uma versão antiga desta tela).
    if (dados.risco_imediato) {
      mostrarAlerta();
      return true;
    }
    if (!resposta.ok || !dados.resposta) {
      adicionar("msg--erro", dados.erro || TEXTOS.falha);
      return false;
    }
    adicionarResposta(dados);
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
