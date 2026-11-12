// Controlador principal da interface Rede Lilás:
// - Navegação lateral entre seções (Início, Perfil & Triagem, Benefícios, Direitos, Locais DF e Fonar)
// - Bloqueio amigável dos blocos personalizados até que o perfil esteja respondido (com redirecionamento automático)
// - Botões "Apagar meus dados" e "Saída rápida" em todas as páginas
// - Chat flutuante sempre acessível com detecção imediata de risco (190) e consulta jurídica (/juridico)
"use strict";

// Site neutro da saída rápida. location.replace() tira esta página do histórico.
const SITE_NEUTRO = "https://www.climatempo.com.br/previsao-do-tempo/cidade/61/brasilia-df";
// Até o orquestrador (S4), toda mensagem é uma pergunta jurídica respondida com citações.
const ROTA = "/juridico";
const ROTA_REDE = "/rede-protecao";
const REGRAS_DE_RISCO = "/regras/risco_imediato.json";
const REGRAS_DE_BENEFICIOS = "/regras/beneficios.json";
const REGRAS_DE_TRIAGEM = "/regras/triagem_fonar.json";
// Um pouco acima do LLM_TIMEOUT do servidor (padrão 30 s): o servidor desiste primeiro e
// devolve a mensagem com o Ligue 180. Este limite só vale quando a conexão cai.
const TEMPO_LIMITE_MS = 35000;

const TEXTOS = {
  semInternet: "Sem internet. Sua mensagem não foi enviada ao servidor, mas veja abaixo uma orientação local.",
  falha: "Não consegui responder agora. Tente de novo em alguns instantes. Se precisar falar com alguém, ligue 180 (gratuito, 24 horas).",
  demorou: "A resposta está demorando. Tente de novo em alguns instantes.",
  pensando: "Escrevendo resposta…",
};

// Ícones SVG limpos usados nos botões, menu lateral e cartões
const ICONES = {
  home: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5.5v-6h-5v6H4a1 1 0 0 1-1-1v-9.5Z"/></svg>',
  check: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12 4.5 4.5L19 7"/></svg>',
  benefit: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="6" width="18" height="13" rx="2.5"/><path d="M12 9.5v6M9.5 11.5h3.5a1.5 1.5 0 0 1 0 3h-2a1.5 1.5 0 0 0 0 3H14"/></svg>',
  scale: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v18M5 7h14M5 7l-3 6h6l-3-6Zm14 0-3 6h6l-3-6ZM8 21h8"/></svg>',
  pin: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-5.6-7-11a7 7 0 1 1 14 0c0 5.4-7 11-7 11Z"/><circle cx="12" cy="10" r="2.5"/></svg>',
  shield: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 5 6v6c0 5 3.4 7.9 7 9 3.6-1.1 7-4 7-9V6l-7-3Z"/></svg>',
  lock: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
  trash: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4h8v2m-9 0 1 14h8l1-14"/></svg>',
  phone: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.9v3a2 2 0 0 1-2.2 2A19.8 19.8 0 0 1 3.1 5.2 2 2 0 0 1 5.1 3h3a2 2 0 0 1 2 1.7l.7 3.3a2 2 0 0 1-.6 1.8l-1.5 1.5a16 16 0 0 0 6 6l1.5-1.5a2 2 0 0 1 1.8-.6l3.3.7a2 2 0 0 1 1.7 2Z"/></svg>',
  alert: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 9v4m0 4h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg>',
  exit: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4m7 14 5-5-5-5m5 5H9"/></svg>',
  arrow: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>',
  back: '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5m6-6-6 6 6 6"/></svg>',
  spark: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3 1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3Z"/></svg>',
  chat: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.7 8.7 0 0 1-4-.9L3 20l1.3-4.2A8.3 8.3 0 0 1 3 11.5 8.5 8.5 0 0 1 11.5 3h1A8.5 8.5 0 0 1 21 11.5Z"/></svg>',
  close: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg>',
  menu: '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>',
  chevron: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>',
  info: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4m0-4h.01"/></svg>',
};

function aplicarIcones(raiz = document) {
  raiz.querySelectorAll("[data-icon]").forEach((el) => {
    const nome = el.getAttribute("data-icon");
    if (ICONES[nome]) el.innerHTML = ICONES[nome];
  });
}

// =========================================================================
// ESTADO DA APLICAÇÃO
// =========================================================================
let secaoAtual = "home";
let destinoAposPerfil = "benefits";
let etapaAtualWizard = 0;
let direcaoWizard = "slide-in";
let perfilUsuario = typeof Perfil !== "undefined" ? Perfil.ler() : {};
let servicosRedeDF = [];
let respostasFonar = {};
let ordemRespostasFonar = [];
// Respostas específicas de benefícios (mantidas exclusivamente em memória, nunca salvas nem enviadas)
let respostasEspecificasBeneficios = {};
let regrasDeBeneficios = null;
let regrasDeTriagem = null;

// Elementos do Chat
const lista = document.getElementById("mensagens");
const formulario = document.getElementById("envio");
const campo = document.getElementById("texto");
const botaoEnviar = document.getElementById("enviar");
const aviso = document.getElementById("aviso");
const chatWindow = document.getElementById("chat-window");
const chatTrigger = document.getElementById("chat-trigger");
const chatTriggerIcon = document.getElementById("chat-trigger-icon");

let pedidoAtual = null;
let regrasDeRisco = null;

fetch(REGRAS_DE_RISCO)
  .then((resposta) => (resposta.ok ? resposta.json() : Promise.reject(resposta.status)))
  .then((dados) => {
    regrasDeRisco = Risco.compilar(dados);
  })
  .catch(() => {});

fetch(REGRAS_DE_BENEFICIOS)
  .then((resposta) => (resposta.ok ? resposta.json() : Promise.reject(resposta.status)))
  .then((dados) => {
    regrasDeBeneficios = dados;
    if (secaoAtual === "benefits") renderizarBeneficios();
  })
  .catch(() => {});

fetch(REGRAS_DE_TRIAGEM)
  .then((resposta) => (resposta.ok ? resposta.json() : Promise.reject(resposta.status)))
  .then((dados) => {
    regrasDeTriagem = dados;
    if (secaoAtual === "fonar") renderizarFonar();
  })
  .catch(() => {});

// Carrega os serviços verificados do DF a partir do backend (sem enviar dados da usuária)
fetch(ROTA_REDE)
  .then((r) => (r.ok ? r.json() : Promise.reject(r.status)))
  .then((listaServicos) => {
    if (Array.isArray(listaServicos) && listaServicos.length) {
      servicosRedeDF = listaServicos;
      if (secaoAtual === "places") renderizarLocais();
    }
  })
  .catch(() => {});

// =========================================================================
// SAÍDA RÁPIDA E APAGAR DADOS SALVOS
// =========================================================================
function sair() {
  apagarConversa();
  respostasEspecificasBeneficios = {};
  respostasFonar = {};
  ordemRespostasFonar = [];
  if (typeof Perfil !== "undefined") Perfil.apagar();
  window.location.replace(SITE_NEUTRO);
}

function apagarConversa() {
  if (pedidoAtual) pedidoAtual.abort();
  pedidoAtual = null;
  if (campo) campo.value = "";
  if (lista) lista.replaceChildren();
}

function apagarMeusDados() {
  if (typeof Perfil !== "undefined") {
    perfilUsuario = Perfil.apagar();
  }
  respostasEspecificasBeneficios = {};
  respostasFonar = {};
  ordemRespostasFonar = [];
  etapaAtualWizard = 0;
  atualizarStatusPerfilUI();
  if (["benefits", "rights", "places"].includes(secaoAtual)) {
    irParaSecao("home");
  } else if (secaoAtual === "screening") {
    renderizarWizard();
  }
  mostrarToast("Seus dados foram apagados deste navegador com segurança.");
}

function mostrarToast(mensagem) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = mensagem;
  toast.hidden = false;
  clearTimeout(mostrarToast._timer);
  mostrarToast._timer = setTimeout(() => {
    toast.hidden = true;
  }, 3400);
}

document.getElementById("sair").addEventListener("click", sair);
document.getElementById("apagar-dados")?.addEventListener("click", apagarMeusDados);
document.getElementById("apagar-dados-menu")?.addEventListener("click", apagarMeusDados);

document.addEventListener("keydown", (evento) => {
  if (evento.key !== "Escape") return;
  // Se o chat flutuante estiver aberto, Esc fecha apenas o diálogo do chat
  if (chatWindow && !chatWindow.hidden) {
    alternarChat(false);
    return;
  }
  // Se o menu mobile estiver aberto, Esc fecha apenas o menu
  const menuLateral = document.getElementById("sidebar");
  if (menuLateral && menuLateral.classList.contains("sidebar-open")) {
    fecharMenuMobile();
    return;
  }
  // Se o foco estiver dentro de um campo de texto ou seletor, tira o foco sem apagar o perfil
  const ativo = document.activeElement;
  if (ativo && ["INPUT", "TEXTAREA", "SELECT"].includes(ativo.tagName)) {
    ativo.blur();
    return;
  }
  sair();
});
// Se a página fechar normalmente, limpa apenas a conversa em memória (mantendo o perfil salvo no cache local).
window.addEventListener("pagehide", apagarConversa);

// =========================================================================
// NAVEGAÇÃO ENTRE SEÇÕES E CONTROLE DE ACESSO AOS BLOCOS
// =========================================================================
const NOMES_BLOCOS = {
  benefits: "Benefícios e Auxílios Financeiros",
  rights: "Direitos e Leis que Protegem Você",
  places: "Locais de Atendimento no DF",
};

function irParaSecao(destino) {
  const exigePerfil = ["benefits", "rights", "places"].includes(destino);
  const estaCompleto = typeof Perfil !== "undefined" && Perfil.completo(perfilUsuario);

  // Se o bloco exige o formulário e ele ainda não foi respondido, leva primeiro ao formulário
  // e guarda qual bloco ela queria abrir para redirecionar assim que concluir!
  if (exigePerfil && !estaCompleto) {
    destinoAposPerfil = destino;
    const primeiraPendente = DadosRedeLilas.ETAPAS_PERFIL.findIndex(
      (etapa) => !perfilUsuario[etapa.campo]
    );
    etapaAtualWizard = primeiraPendente >= 0 ? primeiraPendente : 0;
    secaoAtual = "screening";
  } else {
    secaoAtual = destino;
  }

  fecharMenuMobile();

  // Mostra apenas a seção ativa
  const secoes = ["home", "screening", "benefits", "rights", "places", "fonar"];
  for (const id of secoes) {
    const el = document.getElementById(`sec-${id}`);
    if (el) {
      el.hidden = id !== secaoAtual;
      if (id === secaoAtual) {
        el.classList.remove("page-enter");
        void el.offsetWidth;
        el.classList.add("page-enter");
      }
    }
  }

  // Atualiza item ativo na sidebar
  document.querySelectorAll(".nav-item[data-nav]").forEach((btn) => {
    btn.classList.toggle("active", btn.getAttribute("data-nav") === secaoAtual);
  });

  if (secaoAtual === "screening") renderizarWizard();
  if (secaoAtual === "benefits") renderizarBeneficios();
  if (secaoAtual === "rights") renderizarDireitos();
  if (secaoAtual === "places") renderizarLocais();
  if (secaoAtual === "fonar") renderizarFonar();

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function atualizarStatusPerfilUI() {
  if (typeof Perfil === "undefined" || typeof DadosRedeLilas === "undefined") return;
  const respondidos = Perfil.progresso(perfilUsuario);
  const total = DadosRedeLilas.ETAPAS_PERFIL.length;
  const completo = Perfil.completo(perfilUsuario);

  const badgeMenu = document.getElementById("nav-badge-perfil");
  if (badgeMenu) {
    badgeMenu.textContent = completo ? "Pronto" : `${respondidos}/${total}`;
    badgeMenu.classList.toggle("done", completo);
  }

  // Atualiza os badges e CTAs dos 3 blocos personalizados na home
  ["benefits", "rights", "places"].forEach((bloco) => {
    const statusBadge = document.querySelector(`[data-card-status="${bloco}"]`);
    const ctaText = document.querySelector(`[data-card-cta="${bloco}"]`);
    if (statusBadge) {
      statusBadge.textContent = completo ? "Personalizado para você" : "Requer perfil rápido";
      statusBadge.classList.toggle("card-badge--ready", completo);
    }
    if (ctaText) {
      const mapas = {
        benefits: completo ? "Ver meus benefícios compatíveis" : "Responder perfil e ver benefícios",
        rights: completo ? "Ver direitos e leis aplicáveis" : "Responder perfil e ver direitos",
        places: completo ? `Ver locais em ${perfilUsuario.ra || "minha região"}` : "Responder perfil e ver locais",
      };
      ctaText.textContent = mapas[bloco];
    }
  });

  // Atualiza o banner de perfil na Home
  const banner = document.getElementById("profile-banner");
  const bannerTitle = document.getElementById("banner-title");
  const bannerBadge = document.getElementById("banner-badge");
  const bannerDesc = document.getElementById("banner-desc");
  const bannerBtnTexto = document.getElementById("banner-btn-texto");
  const heroBtnTexto = document.getElementById("btn-hero-triagem-texto");

  if (banner) banner.classList.toggle("completed", completo);
  if (completo) {
    if (bannerTitle) bannerTitle.textContent = "Seu perfil está salvo neste navegador";
    if (bannerBadge) bannerBadge.textContent = `${total}/${total} respondidas`;
    if (bannerDesc) {
      bannerDesc.textContent = `Região: ${perfilUsuario.ra} · Renda: ${perfilUsuario.renda}. Todos os blocos abaixo já estão liberados para você sem precisar responder de novo.`;
    }
    if (bannerBtnTexto) bannerBtnTexto.textContent = "Atualizar minhas respostas";
    if (heroBtnTexto) heroBtnTexto.textContent = "Ver meus benefícios e direitos";
  } else {
    if (bannerTitle) bannerTitle.textContent = "Personalize sua experiência sem cadastro";
    if (bannerBadge) bannerBadge.textContent = respondidos > 0 ? `${respondidos}/${total} preenchidas` : "Leva 1 minuto";
    if (bannerDesc) {
      bannerDesc.textContent =
        "Responda o formulário rápido uma única vez para liberar as respostas personalizadas nos blocos abaixo. Fica salvo apenas neste navegador e você pode apagar quando quiser.";
    }
    if (bannerBtnTexto) bannerBtnTexto.textContent = respondidos > 0 ? "Continuar meu perfil" : "Preencher meu perfil";
    if (heroBtnTexto) heroBtnTexto.textContent = "Responder perfil rápido";
  }
}

// =========================================================================
// WIZARD DE PERFIL (COM ANIMAÇÕES SLIDE-IN / SLIDE-BACK DO FIGMA CODE)
// =========================================================================
function renderizarWizard() {
  const etapas = DadosRedeLilas.ETAPAS_PERFIL;
  const etapa = etapas[etapaAtualWizard];
  if (!etapa) return;

  const avisoDestino = document.getElementById("wizard-destination-notice");
  if (avisoDestino) {
    const completo = Perfil.completo(perfilUsuario);
    if (!completo && NOMES_BLOCOS[destinoAposPerfil]) {
      avisoDestino.hidden = false;
      avisoDestino.textContent = `Complete as perguntas abaixo uma única vez para abrir: ${NOMES_BLOCOS[destinoAposPerfil]}.`;
    } else {
      avisoDestino.hidden = true;
    }
  }

  document.getElementById("wizard-counter").textContent = `Etapa ${etapaAtualWizard + 1} de ${etapas.length}`;
  document.getElementById("wizard-progress-fill").style.width = `${((etapaAtualWizard + 1) / etapas.length) * 100}%`;
  document.getElementById("wizard-why-text").textContent = etapa.motivo;

  // Renderiza as abas superiores
  const tabsEl = document.getElementById("wizard-step-tabs");
  tabsEl.replaceChildren();
  etapas.forEach((item, idx) => {
    const respondida = Boolean(perfilUsuario[item.campo]);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.setAttribute("role", "tab");
    btn.setAttribute("aria-selected", String(idx === etapaAtualWizard));
    btn.className = `step-tab ${idx === etapaAtualWizard ? "active" : ""} ${respondida ? "done" : ""}`;
    btn.innerHTML = `<span class="step-tab-num">${idx + 1}</span><span>${item.aba}</span>`;
    btn.addEventListener("click", () => {
      direcaoWizard = idx >= etapaAtualWizard ? "slide-in" : "slide-back";
      etapaAtualWizard = idx;
      renderizarWizard();
    });
    tabsEl.append(btn);
  });

  // Renderiza o painel da pergunta com animação de transição
  const painel = document.getElementById("wizard-question-panel");
  painel.className = `question-panel ${direcaoWizard}`;
  painel.replaceChildren();

  const titulo = document.createElement("h2");
  titulo.textContent = etapa.pergunta;
  const sub = document.createElement("p");
  sub.textContent = etapa.ajuda;

  const gradeOpcoes = document.createElement("div");
  gradeOpcoes.className = "option-list";
  gradeOpcoes.setAttribute("role", "group");
  gradeOpcoes.setAttribute("aria-label", etapa.pergunta);

  const valorAtual = perfilUsuario[etapa.campo] || "";

  etapa.opcoes.forEach((opcao) => {
    const botaoOpcao = document.createElement("button");
    botaoOpcao.type = "button";
    const selecionado = valorAtual === opcao;
    botaoOpcao.className = `option ${selecionado ? "selected" : ""}`;
    botaoOpcao.setAttribute("aria-pressed", String(selecionado));
    botaoOpcao.innerHTML = `<span class="radio-dot"></span><span>${opcao}</span>`;
    botaoOpcao.addEventListener("click", () => {
      selecionarOpcaoPerfil(etapa.campo, opcao);
    });
    gradeOpcoes.append(botaoOpcao);
  });

  painel.append(titulo, sub, gradeOpcoes);

  // Na etapa 1 (ra), também permite informar o CEP diretamente (conforme spec de privacidade-seguranca)
  if (etapa.campo === "ra") {
    const cepBox = document.createElement("div");
    cepBox.style.cssText = "margin-top: 14px; padding-top: 12px; border-top: 1px solid #ece4f8; display: flex; flex-wrap: wrap; align-items: center; gap: 10px;";
    const cepAtual = /^\d{5}-?\d{3}$/.test(valorAtual) ? valorAtual : "";
    cepBox.innerHTML = `
      <label for="wizard-cep-input" style="font-size: 13px; font-weight: 700; color: #4a3d60;">Ou digite seu CEP (opcional):</label>
      <input id="wizard-cep-input" type="text" inputmode="numeric" maxlength="9" placeholder="Ex.: 72215-110" value="${cepAtual}" style="padding: 8px 12px; border-radius: 10px; border: 1px solid #d5c7ec; font-size: 14px; width: 150px;">
      <button type="button" class="secondary-button" id="wizard-cep-btn" style="padding: 8px 14px; font-size: 12.5px;">Usar CEP</button>
    `;
    painel.append(cepBox);

    const inputCep = cepBox.querySelector("#wizard-cep-input");
    const btnCep = cepBox.querySelector("#wizard-cep-btn");
    const aplicarCep = () => {
      const limpo = String(inputCep.value || "").replace(/\D/g, "");
      if (limpo.length === 8) {
        const formatado = `${limpo.slice(0, 5)}-${limpo.slice(5)}`;
        selecionarOpcaoPerfil("ra", formatado);
      } else {
        mostrarToast("Digite um CEP válido com 8 números (ex.: 72215-110).");
      }
    };
    btnCep?.addEventListener("click", aplicarCep);
    inputCep?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        aplicarCep();
      }
    });
  }

  const btnAnterior = document.getElementById("wizard-prev-btn");
  btnAnterior.disabled = etapaAtualWizard === 0;
  btnAnterior.style.opacity = etapaAtualWizard === 0 ? "0.45" : "1";

  const btnProximoTexto = document.getElementById("wizard-next-text");
  btnProximoTexto.textContent =
    etapaAtualWizard === etapas.length - 1 ? "Concluir e abrir orientações" : "Próxima pergunta";
}

function selecionarOpcaoPerfil(campo, valor) {
  perfilUsuario[campo] = valor;
  perfilUsuario = Perfil.salvar(perfilUsuario);
  atualizarStatusPerfilUI();
  renderizarWizard();
}

function avancarWizard() {
  const etapas = DadosRedeLilas.ETAPAS_PERFIL;
  const etapa = etapas[etapaAtualWizard];
  // Se a usuária clicar em "Próxima pergunta" sem marcar nada, registra "Prefiro não informar" para não travá-la
  if (!perfilUsuario[etapa.campo]) {
    perfilUsuario[etapa.campo] = "Prefiro não informar";
    perfilUsuario = Perfil.salvar(perfilUsuario);
    atualizarStatusPerfilUI();
  }

  if (etapaAtualWizard < etapas.length - 1) {
    direcaoWizard = "slide-in";
    etapaAtualWizard++;
    renderizarWizard();
  } else {
    mostrarToast("Perfil salvo no navegador! Mostrando suas orientações personalizadas.");
    irParaSecao(destinoAposPerfil || "benefits");
  }
}

document.getElementById("wizard-prev-btn")?.addEventListener("click", () => {
  if (etapaAtualWizard > 0) {
    direcaoWizard = "slide-back";
    etapaAtualWizard--;
    renderizarWizard();
  }
});

document.getElementById("wizard-skip-btn")?.addEventListener("click", () => {
  const etapa = DadosRedeLilas.ETAPAS_PERFIL[etapaAtualWizard];
  if (etapa) {
    selecionarOpcaoPerfil(etapa.campo, "Prefiro não informar");
    avancarWizard();
  }
});

document.getElementById("wizard-next-btn")?.addEventListener("click", avancarWizard);

// =========================================================================
// RENDERIZAÇÃO DOS BLOCOS PERSONALIZADOS
// =========================================================================
function criarChipsResumoPerfil(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.replaceChildren();
  const itens = [
    { rotulo: "RA", valor: perfilUsuario.ra },
    { rotulo: "Moradia", valor: perfilUsuario.moradia },
    { rotulo: "Renda", valor: perfilUsuario.renda },
    { rotulo: "Dependentes", valor: perfilUsuario.filhos },
    { rotulo: "CadÚnico", valor: perfilUsuario.cadunico },
    { rotulo: "Medida Protetiva", valor: perfilUsuario.medida_protetiva },
  ];
  for (const item of itens) {
    if (!item.valor) continue;
    const chip = document.createElement("span");
    chip.className = "profile-chip";
    chip.textContent = `${item.rotulo}: ${item.valor}`;
    container.append(chip);
  }
}

function obterEspecificasBeneficios() {
  const moradiaBruta = perfilUsuario.moradia || "";
  let necessidadePadrao = "prefiro_nao_informar";
  if (
    moradiaBruta.startsWith("Preciso sair") ||
    moradiaBruta.startsWith("Já saí") ||
    moradiaBruta.startsWith("Moro em imóvel alugado")
  ) {
    necessidadePadrao = "sim";
  } else if (moradiaBruta.startsWith("Moro em imóvel próprio")) {
    necessidadePadrao = "nao";
  }

  // Só assume "sim" para deficiência se ela já informou dependente com deficiência no perfil;
  // caso contrário permanece "prefiro_nao_informar" até que ela responda a pergunta específica.
  let deficienciaPadrao = "prefiro_nao_informar";
  if (perfilUsuario.filhos === "Sim, filho(a) ou dependente com deficiência") {
    deficienciaPadrao = "sim";
  }

  // Pela Lei 14.550/2023 é possível pedir/ter medida protetiva sem BO prévio.
  // Só marcamos "nao" quando ela declarou que não fez BO nem pediu medida; nos demais casos
  // fica "prefiro_nao_informar" até que ela confirme na pergunta específica de BO.
  let boletimPadrao = "prefiro_nao_informar";
  if (perfilUsuario.medida_protetiva === "Ainda não fiz BO nem pedi medida protetiva") {
    boletimPadrao = "nao";
  }

  return {
    deficiencia: respostasEspecificasBeneficios.deficiencia || deficienciaPadrao,
    boletim_ocorrencia: respostasEspecificasBeneficios.boletim_ocorrencia || boletimPadrao,
    acompanhamento_psicossocial:
      respostasEspecificasBeneficios.acompanhamento_psicossocial || "prefiro_nao_informar",
    necessidade_moradia:
      respostasEspecificasBeneficios.necessidade_moradia || necessidadePadrao,
  };
}

function renderizarPerguntasEspecificasBeneficios() {
  const box = document.getElementById("benefits-specific-questions");
  if (!box || typeof DadosRedeLilas === "undefined") return;
  box.replaceChildren();

  const cabecalho = document.createElement("div");
  cabecalho.className = "specific-questions-head";
  cabecalho.innerHTML = `
    <div>
      <span class="specific-kicker">PERGUNTAS ESPECÍFICAS DESTA CONSULTA (APENAS EM MEMÓRIA)</span>
      <h2>Ajuste os detalhes da sua situação atual</h2>
      <p>Estas 4 respostas complementam a análise dos benefícios e nunca são salvas no aparelho nem enviadas ao servidor.</p>
    </div>
  `;

  const grade = document.createElement("div");
  grade.className = "specific-questions-grid";

  const atuais = obterEspecificasBeneficios();
  const opcoes = [
    { valor: "sim", rotulo: "Sim" },
    { valor: "nao", rotulo: "Não" },
    { valor: "prefiro_nao_informar", rotulo: "Prefiro não informar" },
  ];

  (DadosRedeLilas.PERGUNTAS_ESPECIFICAS_BENEFICIOS || []).forEach((item) => {
    const linha = document.createElement("div");
    linha.className = "specific-question-item";

    const textoDiv = document.createElement("div");
    textoDiv.className = "specific-question-copy";
    textoDiv.innerHTML = `
      <strong>${item.pergunta}</strong>
      <small>${item.detalhe}</small>
    `;

    const botoesDiv = document.createElement("div");
    botoesDiv.className = "specific-question-pills";
    botoesDiv.setAttribute("role", "group");
    botoesDiv.setAttribute("aria-label", item.pergunta);

    const selecionado = atuais[item.campo] || "prefiro_nao_informar";
    opcoes.forEach((op) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = `specific-pill ${selecionado === op.valor ? "active" : ""}`;
      btn.textContent = op.rotulo;
      btn.setAttribute("aria-pressed", String(selecionado === op.valor));
      btn.addEventListener("click", () => {
        respostasEspecificasBeneficios[item.campo] = op.valor;
        renderizarBeneficios();
      });
      botoesDiv.append(btn);
    });

    linha.append(textoDiv, botoesDiv);
    grade.append(linha);
  });

  box.append(cabecalho, grade);
}

function tomDoStatusBeneficio(status, rotulo) {
  if (status === "provavel") return "good";
  if (status === "depende_decisao_judicial" || status === "faltam_informacoes") return "warm";
  if (rotulo === "Não aplicável por enquanto") return "warm";
  return "neutral";
}

function renderizarBeneficios() {
  criarChipsResumoPerfil("benefits-profile-chips");
  renderizarPerguntasEspecificasBeneficios();

  const container = document.getElementById("benefits-list");
  if (!container) return;
  container.replaceChildren();

  // Usa o avaliador determinístico oficial (web/beneficios.js + regras/beneficios.json)
  if (typeof Beneficios !== "undefined" && regrasDeBeneficios) {
    const entradaPerfil =
      typeof Perfil !== "undefined" && Perfil.paraAvaliacaoBeneficios
        ? Perfil.paraAvaliacaoBeneficios(perfilUsuario)
        : perfilUsuario;
    const especificas = obterEspecificasBeneficios();
    const avaliados = Beneficios.avaliar(regrasDeBeneficios, entradaPerfil, especificas);
    const detalhesMapa = (typeof DadosRedeLilas !== "undefined" && DadosRedeLilas.DETALHES_BENEFICIOS) || {};

    // Ordena priorizando Aluguel Social DF e Auxílio-aluguel ou mantendo a relevância
    const ordemPreferida = ["aluguel_social_df", "auxilio_aluguel", "bolsa_familia", "bpc"];
    avaliados.sort((a, b) => ordemPreferida.indexOf(a.id) - ordemPreferida.indexOf(b.id));

    avaliados.forEach((item, idx) => {
      const infoExtra = detalhesMapa[item.id] || {};
      const titulo = infoExtra.titulo || item.id;
      const esfera = infoExtra.esfera || "Benefício Social";
      const valorRef = infoExtra.valor || "";
      const resumo = infoExtra.resumo || item.aviso || "";
      const tom = tomDoStatusBeneficio(item.status, item.rotulo);

      const card = document.createElement("article");
      card.className = `recommendation ${idx === 0 ? "rec-open" : ""}`;

      const head = document.createElement("button");
      head.type = "button";
      head.className = "rec-head";
      head.innerHTML = `
        <span class="rec-symbol">${ICONES.benefit}</span>
        <div>
          <div class="rec-meta">
            <span class="status ${tom}">${item.rotulo}</span>
            <span>${esfera}</span>
            ${valorRef ? `<span>· ${valorRef}</span>` : ""}
          </div>
          <h2>${titulo}</h2>
          <p>${resumo}</p>
        </div>
        <span class="rec-chevron">${ICONES.chevron}</span>
      `;

      const body = document.createElement("div");
      body.className = "rec-body";
      body.hidden = idx !== 0;

      const motivosHtml = (item.motivos || [])
        .map((m, i) => `<li><span class="rec-step-num">${i + 1}</span><p class="rec-step-text">${m}</p></li>`)
        .join("");

      const faltaHtml = (item.falta || [])
        .map((f, i) => `<li><span class="rec-step-num">${i + 1}</span><p class="rec-step-text">${f}</p></li>`)
        .join("");

      const fontesTexto = (item.fontes || [])
        .map(
          (f) =>
            `${f.norma}, ${f.artigo} (vigência: ${dataBrasileira(f.inicio_vigencia)} · verificado em ${dataBrasileira(f.data_verificacao)})`
        )
        .join(" · ");

      body.innerHTML = `
        <h3>Análise dos critérios para o seu perfil</h3>
        <ul>${motivosHtml}</ul>
        ${
          faltaHtml
            ? `<h3>O que falta ou próximos passos</h3><ol>${faltaHtml}</ol>`
            : ""
        }
        <div class="where">
          <strong>Onde solicitar:</strong> ${item.onde_pedir}<br>
          <strong>Aviso importante:</strong> ${item.aviso}<br>
          <small>Referência legal: ${fontesTexto}</small>
        </div>
      `;

      head.addEventListener("click", () => {
        const aberto = card.classList.toggle("rec-open");
        body.hidden = !aberto;
      });

      card.append(head, body);
      container.append(card);
    });
  }
}

function renderizarDireitos() {
  criarChipsResumoPerfil("rights-profile-chips");

  const callout = document.getElementById("rights-personalized-callout");
  if (callout) {
    const notas = [];
    if (perfilUsuario.medida_protetiva === "Ainda não fiz BO nem pedi medida protetiva") {
      notas.push(
        "<strong>Para o seu momento:</strong> Você informou que ainda não possui medida protetiva. Pela <strong>Lei 14.550/2023</strong>, você pode pedir Medida Protetiva de Urgência com base apenas no seu depoimento na DEAM ou na Defensoria Pública, sem depender de inquérito ou provas prévias."
      );
    }
    if (
      perfilUsuario.estado_civil === "Casada ou em união estável" ||
      perfilUsuario.estado_civil === "Separada recentemente / em processo de separação"
    ) {
      notas.push(
        "<strong>Patrimônio, moradia e união:</strong> Mesmo em casamento ou união estável, sair do lar para se proteger não configura abandono de lar nem perda de direitos sobre os bens ou a guarda dos filhos (Lei 11.340/2006, arts. 22 a 24). O Juizado também pode determinar a restituição de bens e documentos retidos pelo agressor."
      );
    }
    if (perfilUsuario.inss === "Trabalho com carteira assinada (CLT)") {
      notas.push(
        "<strong>Proteção do seu trabalho:</strong> Como você trabalha com carteira assinada, o <strong>art. 9º, § 2º, II da Lei Maria da Penha</strong> assegura a manutenção do seu vínculo trabalhista por até 6 meses caso precise se afastar por segurança."
      );
    }
    if (perfilUsuario.filhos && perfilUsuario.filhos.startsWith("Sim")) {
      notas.push(
        "<strong>Proteção dos seus filhos:</strong> Você tem prioridade de matrícula ou transferência dos seus filhos em escola próxima ao novo endereço, com sigilo total dos dados (Lei 11.340/2006, art. 9º, § 7º)."
      );
    }
    callout.innerHTML =
      notas.join("<br><br>") ||
      "<strong>Seus direitos estão protegidos:</strong> Confira abaixo os principais artigos da Lei Maria da Penha e do Código Penal explicados em linguagem simples.";
  }

  const container = document.getElementById("rights-list");
  if (!container) return;
  container.replaceChildren();

  DadosRedeLilas.DIREITOS_LEIS.forEach((lei, idx) => {
    const card = document.createElement("article");
    card.className = `recommendation ${idx < 2 ? "rec-open" : ""}`;

    const head = document.createElement("button");
    head.type = "button";
    head.className = "rec-head";
    head.innerHTML = `
      <span class="rec-symbol">${ICONES.scale}</span>
      <div>
        <div class="rec-meta">
          <span class="status neutral">${lei.tag}</span>
          <span>${lei.verificacao}</span>
        </div>
        <h2>${lei.titulo}</h2>
        <p>${lei.destaque}</p>
      </div>
      <span class="rec-chevron">${ICONES.chevron}</span>
    `;

    const body = document.createElement("div");
    body.className = "rec-body";
    body.hidden = idx >= 2;
    body.innerHTML = `
      <p style="font-size: 13.5px; line-height: 1.65; color: #362e47;">${lei.resumo}</p>
      <div class="where">
        <strong>Referência legal conferida:</strong> ${lei.tag} · ${lei.verificacao}
      </div>
    `;

    head.addEventListener("click", () => {
      const aberto = card.classList.toggle("rec-open");
      body.hidden = !aberto;
    });

    card.append(head, body);
    container.append(card);
  });
}

const RA_PROXIMAS = {
  Samambaia: ["Recanto das Emas", "Ceilândia"],
  Taguatinga: ["Ceilândia", "Recanto das Emas"],
  "Águas Claras": ["Núcleo Bandeirante", "Ceilândia"],
  Guará: ["Núcleo Bandeirante", "Plano Piloto"],
  "São Sebastião": ["Paranoá", "Plano Piloto"],
  Itapoã: ["Paranoá", "Sobradinho"],
  "Estrutural (SCIA)": ["Plano Piloto", "Ceilândia"],
};

function formatarFonteUrl(url) {
  if (!url) return "GDF";
  return String(url)
    .replace(/^https?:\/\/(www\.)?/, "")
    .split("/")[0];
}

function renderizarLocais() {
  const selectRa = document.getElementById("filtro-ra");
  const selectTipo = document.getElementById("filtro-tipo");
  const avisoRa = document.getElementById("places-ra-notice");
  const container = document.getElementById("places-list");
  if (!container || !selectRa || !selectTipo) return;

  // Popula o filtro de RA
  if (!selectRa.options.length) {
    const opTodas = document.createElement("option");
    opTodas.value = "todas";
    opTodas.textContent = "Todas as Regiões Administrativas (mostrar todas as unidades)";
    selectRa.append(opTodas);
    DadosRedeLilas.RAS_DF.forEach((ra) => {
      if (ra === "Prefiro não informar" || ra === "Outra RA do DF" || ra === "Moro fora do Distrito Federal") return;
      const op = document.createElement("option");
      op.value = ra;
      op.textContent = ra;
      selectRa.append(op);
    });
  }

  // Se a usuária ainda não mexeu manualmente no select, seleciona a RA do perfil dela (se existir no select)
  if (!selectRa.dataset.escolhidoManual) {
    const raPerfil = perfilUsuario.ra;
    const existeNoSelect = Array.from(selectRa.options).some((op) => op.value === raPerfil);
    selectRa.value = existeNoSelect ? raPerfil : "todas";
  }

  const tipoFiltro = selectTipo.value || "todos";
  const raAlvo =
    selectRa.value !== "todas"
      ? selectRa.value
      : perfilUsuario.ra && perfilUsuario.ra !== "Prefiro não informar"
      ? perfilUsuario.ra
      : "";

  const rasVizinhas = (raAlvo && RA_PROXIMAS[raAlvo]) || [];
  const temUnidadeDiretaNaRa = Boolean(raAlvo && servicosRedeDF.some((s) => s.ra === raAlvo));

  // Quando a usuária escolhe uma RA específica no filtro, mostramos:
  // 1) As unidades daquela RA (ou das RAs vizinhas de referência, se a RA escolhida não tiver sede própria)
  // 2) As unidades de plantão 24 horas do DF (para que emergência 24h esteja sempre visível)
  const filtrados = servicosRedeDF
    .filter((s) => (tipoFiltro === "todos" ? true : s.tipo === tipoFiltro))
    .filter((s) => {
      if (selectRa.value === "todas" || !raAlvo) return true;
      const eh24h = String(s.horario).includes("24 horas");
      if (temUnidadeDiretaNaRa) {
        return s.ra === raAlvo || eh24h;
      }
      return rasVizinhas.includes(s.ra) || eh24h;
    })
    .slice()
    .sort((a, b) => {
      const aMatch = raAlvo && a.ra === raAlvo ? 0 : 1;
      const bMatch = raAlvo && b.ra === raAlvo ? 0 : 1;
      if (aMatch !== bMatch) return aMatch - bMatch;

      const idxVizinhaA = rasVizinhas.indexOf(a.ra);
      const idxVizinhaB = rasVizinhas.indexOf(b.ra);
      const aVizinha = idxVizinhaA !== -1 ? idxVizinhaA : 99;
      const bVizinha = idxVizinhaB !== -1 ? idxVizinhaB : 99;
      if (aVizinha !== bVizinha) return aVizinha - bVizinha;

      const a24 = String(a.horario).includes("24 horas") ? 0 : 1;
      const b24 = String(b.horario).includes("24 horas") ? 0 : 1;
      return a24 - b24;
    });

  if (avisoRa) {
    if (selectRa.value !== "todas" && raAlvo) {
      avisoRa.hidden = false;
      if (temUnidadeDiretaNaRa) {
        const qtdNaRa = servicosRedeDF.filter((s) => s.ra === raAlvo).length;
        avisoRa.innerHTML = `<strong>Região selecionada: ${raAlvo}</strong> — Exibindo no topo as <strong>${qtdNaRa} unidade(s) localizadas em ${raAlvo}</strong>, seguidas pelos plantões 24 horas do DF. Para ver todas as 21 unidades do DF, selecione <em>"Todas as Regiões Administrativas"</em> acima.`;
      } else {
        avisoRa.innerHTML = `<strong>Região selecionada: ${raAlvo}</strong> — Não há sede física própria em ${raAlvo} nesta lista. Exibindo abaixo as <strong>unidades mais próximas que atendem moradoras de ${raAlvo} (${rasVizinhas.join(" e ")})</strong> e os plantões 24 horas do DF.`;
      }
    } else {
      avisoRa.hidden = true;
    }
  }

  container.replaceChildren();
  filtrados.forEach((s) => {
    const ehMinhaRa = raAlvo && s.ra === raAlvo;
    const ehVizinhaReferencia = !temUnidadeDiretaNaRa && raAlvo && rasVizinhas.includes(s.ra);
    const eh24h = String(s.horario).includes("24 horas");
    const card = document.createElement("article");
    card.className = `place-card ${ehMinhaRa || ehVizinhaReferencia ? "match-ra" : ""}`;

    let badgeRa = `<span class="status neutral">${s.ra}</span>`;
    if (ehMinhaRa) {
      badgeRa = `<span class="status good">Na sua Região Administrativa (${s.ra})</span>`;
    } else if (ehVizinhaReferencia) {
      badgeRa = `<span class="status good">Mais próxima de ${raAlvo} (${s.ra})</span>`;
    }

    card.innerHTML = `
      <div class="place-badges">
        ${badgeRa}
        ${eh24h ? '<span class="status warm">Plantão 24 horas</span>' : `<span class="status neutral">${s.tipo}</span>`}
      </div>
      <h2>${s.nome}</h2>
      <p class="place-meta">
        <strong>Endereço:</strong> ${s.endereco} · CEP ${s.cep}<br>
        <strong>Horário:</strong> ${s.horario}<br>
        <strong>Telefones:</strong> ${s.telefone}
      </p>
      <div class="place-phone">
        <span>Fonte: ${formatarFonteUrl(s.fonte_url)} · verificado em ${dataBrasileira(s.data_verificacao)}</span>
        <strong>Confirme por telefone antes de ir</strong>
      </div>
    `;
    container.append(card);
  });
}

document.getElementById("filtro-ra")?.addEventListener("change", (e) => {
  e.target.dataset.escolhidoManual = "1";
  renderizarLocais();
});
document.getElementById("filtro-tipo")?.addEventListener("change", renderizarLocais);

// =========================================================================
// AUTOAVALIAÇÃO DE RISCO (FONAR — web/triagem.js + regras/triagem_fonar.json)
// =========================================================================
function renderizarFonar() {
  const container = document.getElementById("fonar-questions");
  const box = document.getElementById("fonar-result-box");
  if (!container || !box) return;
  container.replaceChildren();

  // Usa o avaliador oficial de triagem determinística (s3-triagem-fonar)
  if (typeof Triagem !== "undefined" && regrasDeTriagem) {
    const avaliacao = Triagem.avaliar(regrasDeTriagem, respostasFonar);
    const idsRespondidos = ordemRespostasFonar.filter((k) => respostasFonar[k] !== undefined);

    if (!avaliacao.concluida && avaliacao.proxima_pergunta) {
      const p = avaliacao.proxima_pergunta;
      const card = document.createElement("div");
      card.className = "fonar-card slide-in";

      const cabecalho = document.createElement("div");
      cabecalho.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; gap:10px; flex-wrap:wrap;">
          <span class="fonar-kicker">${p.bloco} · Item ${p.numero} do Fonar</span>
          <span class="badge">${idsRespondidos.length + 1} de até ${(regrasDeTriagem.perguntas || []).length} perguntas</span>
        </div>
        <h2>${p.enunciado}</h2>
        ${
          p.aviso_cuidado
            ? `<p style="margin-top:6px; font-size:13px; color:#6b43a8; font-weight:600;">${p.aviso_cuidado}</p>`
            : ""
        }
      `;

      const opcoesDiv = document.createElement("div");
      opcoesDiv.className = "fonar-options";

      (p.opcoes || []).forEach((op) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = `option ${respostasFonar[p.id] === op.id ? "selected" : ""}`;
        btn.innerHTML = `<span class="radio-dot"></span><span>${op.rotulo}</span>`;
        btn.addEventListener("click", () => {
          if (!ordemRespostasFonar.includes(p.id)) {
            ordemRespostasFonar.push(p.id);
          }
          respostasFonar[p.id] = op.id;
          renderizarFonar();
        });
        opcoesDiv.append(btn);
      });

      card.append(cabecalho, opcoesDiv);

      if (idsRespondidos.length > 0) {
        const acoes = document.createElement("div");
        acoes.style.cssText = "display:flex; justify-content:space-between; margin-top:16px; padding-top:12px; border-top:1px solid #eee6f9;";
        const btnVoltar = document.createElement("button");
        btnVoltar.type = "button";
        btnVoltar.className = "secondary-button";
        btnVoltar.textContent = "Voltar à pergunta anterior";
        btnVoltar.addEventListener("click", () => {
          const ultimaChave = ordemRespostasFonar.pop();
          if (ultimaChave !== undefined) {
            delete respostasFonar[ultimaChave];
          }
          renderizarFonar();
        });

        const btnLimpar = document.createElement("button");
        btnLimpar.type = "button";
        btnLimpar.className = "ghost-button";
        btnLimpar.textContent = "Reiniciar triagem";
        btnLimpar.addEventListener("click", () => {
          respostasFonar = {};
          ordemRespostasFonar = [];
          renderizarFonar();
        });

        acoes.append(btnVoltar, btnLimpar);
        card.append(acoes);
      }

      container.append(card);

      box.className = "fonar-result";
      box.innerHTML = `
        <h2>Responda ou pule a pergunta acima para avançar na triagem</h2>
        <p style="margin-top:6px; font-size:13.5px; color:#5e5470;">
          Suas respostas ficam apenas na memória temporária da página, nunca são gravadas no aparelho nem enviadas ao servidor.
          Se um fator de risco alto for confirmado, a triagem exibe a orientação de emergência imediatamente.
        </p>
      `;
      return;
    }

    if (avaliacao.concluida && avaliacao.resultado) {
      const r = avaliacao.resultado;
      const ehAlto = avaliacao.nivel === "alto" || avaliacao.nivel === "alto_nao_descartado";
      const ehAtencao = avaliacao.nivel === "atencao";

      box.className = `fonar-result ${ehAlto ? "risco-alto" : ehAtencao ? "risco-medio" : ""}`;
      const tomBadge = ehAlto || ehAtencao ? "warm" : "good";

      box.innerHTML = `
        <span class="status ${tomBadge}">${r.rotulo}</span>
        <h2 style="margin-top:10px; font-size:20px;">${r.titulo}</h2>
        <p style="margin-top:8px; font-size:14px; line-height:1.65;">${r.orientacao}</p>
        ${
          r.como_pedir_medida_protetiva
            ? `<p style="margin-top:10px; font-size:13.5px; line-height:1.6;"><strong>Como pedir medida protetiva:</strong> ${r.como_pedir_medida_protetiva}</p>`
            : ""
        }
        <p style="margin-top:10px; font-size:13px; color:#554a68;">
          <strong>Aviso de limite:</strong> ${r.aviso_limite}
        </p>
        <div style="display:flex; flex-wrap:wrap; gap:10px; margin-top:16px;">
          <a href="tel:190" class="quick-exit">Ligar ${r.telefone_emergencia || "190"} (Emergência Policial)</a>
          <a href="tel:180" class="emergency-call">${r.telefone_orientacao || "Ligue 180 (gratuito, 24 horas)"}</a>
          <button type="button" class="secondary-button" id="fonar-ir-locais">Ver DEAMs 24h e Casa da Mulher Brasileira</button>
          <button type="button" class="ghost-button" id="fonar-reiniciar">Refazer avaliação de risco</button>
        </div>
      `;

      document.getElementById("fonar-ir-locais")?.addEventListener("click", () => irParaSecao("places"));
      document.getElementById("fonar-reiniciar")?.addEventListener("click", () => {
        respostasFonar = {};
        ordemRespostasFonar = [];
        renderizarFonar();
      });
    }
  }
}

// =========================================================================
// CHAT FLUTUANTE (DESIGN FIGMA + ALERTA 190 LOCAL + /JURIDICO)
// =========================================================================
function alternarChat(forcarEstado) {
  if (!chatWindow || !chatTrigger) return;
  const abrir = typeof forcarEstado === "boolean" ? forcarEstado : chatWindow.hidden;
  chatWindow.hidden = !abrir;
  chatTrigger.setAttribute("aria-expanded", String(abrir));
  if (chatTriggerIcon) {
    chatTriggerIcon.innerHTML = abrir ? ICONES.close : ICONES.chat;
  }
  if (abrir && campo) {
    campo.focus();
  }
}

chatTrigger?.addEventListener("click", () => alternarChat());
document.getElementById("chat-close")?.addEventListener("click", () => alternarChat(false));

document.querySelectorAll("[data-quick-msg]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const pergunta = btn.getAttribute("data-quick-msg");
    if (!pergunta) return;
    alternarChat(true);
    campo.value = pergunta;
    formulario.requestSubmit();
  });
});

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

function irParaOFim() {
  if (lista) {
    lista.scrollTop = lista.scrollHeight;
  }
}

// Alerta de 190: aparece na conversa, com o botão de ligar em destaque.
function mostrarAlerta() {
  alternarChat(true);
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
    if (typeof DadosRedeLilas !== "undefined") {
      adicionarResposta(DadosRedeLilas.respostaLocalChat(texto));
    }
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
      // Se o ambiente local estiver sem chave de LLM configurada (503), mostra o aviso + orientação local fundamentada
      adicionar("msg--erro", dados.erro || TEXTOS.falha);
      if (resposta.status === 503 && typeof DadosRedeLilas !== "undefined") {
        adicionarResposta(DadosRedeLilas.respostaLocalChat(texto));
      }
      return false;
    }
    adicionarResposta(dados);
    return true;
  } catch (_erro) {
    pensando.remove();
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
  campo.style.height = "auto";
  campo.style.height = `${campo.scrollHeight + 2}px`;
}
campo.addEventListener("input", ajustarAltura);

function atualizarConexao() {
  aviso.hidden = navigator.onLine;
}
window.addEventListener("online", atualizarConexao);
window.addEventListener("offline", atualizarConexao);
atualizarConexao();

// =========================================================================
// MENU MOBILE E EVENTOS GERAIS DA INTERFACE
// =========================================================================
const sidebarEl = document.getElementById("sidebar");
const backdropEl = document.getElementById("sidebar-backdrop");

function abrirMenuMobile() {
  sidebarEl?.classList.add("sidebar-open");
  if (backdropEl) backdropEl.hidden = false;
}

function fecharMenuMobile() {
  sidebarEl?.classList.remove("sidebar-open");
  if (backdropEl) backdropEl.hidden = true;
}

document.getElementById("abrir-menu")?.addEventListener("click", abrirMenuMobile);
backdropEl?.addEventListener("click", fecharMenuMobile);

document.querySelectorAll("[data-nav]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const destino = btn.getAttribute("data-nav");
    if (destino === "screening") destinoAposPerfil = "benefits";
    if (destino) irParaSecao(destino);
  });
});

document.querySelectorAll("[data-block]").forEach((card) => {
  card.addEventListener("click", () => {
    const bloco = card.getAttribute("data-block");
    if (bloco) irParaSecao(bloco);
  });
});

document.querySelectorAll("[data-edit-profile]").forEach((btn) => {
  btn.addEventListener("click", () => {
    destinoAposPerfil = btn.getAttribute("data-edit-profile") || "benefits";
    etapaAtualWizard = 0;
    secaoAtual = "screening";
    irParaSecao("screening");
  });
});

document.getElementById("btn-hero-triagem")?.addEventListener("click", () => {
  const completo = typeof Perfil !== "undefined" && Perfil.completo(perfilUsuario);
  destinoAposPerfil = "benefits";
  irParaSecao(completo ? "benefits" : "screening");
});

document.getElementById("banner-btn-acao")?.addEventListener("click", () => {
  destinoAposPerfil = "benefits";
  secaoAtual = "screening";
  document.querySelectorAll(".page-section").forEach((s) => (s.hidden = s.id !== "sec-screening"));
  renderizarWizard();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

// Inicialização
aplicarIcones();
atualizarStatusPerfilUI();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("/sw.js")
      .then((reg) => {
        reg.update();
        reg.addEventListener("updatefound", () => {
          const novo = reg.installing;
          if (!novo) return;
          novo.addEventListener("statechange", () => {
            if (novo.state === "activated" && navigator.serviceWorker.controller) {
              window.location.reload();
            }
          });
        });
      })
      .catch(() => {});
  });
}
