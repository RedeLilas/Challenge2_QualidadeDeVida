// Service worker: guarda só a interface para ela abrir sem internet.
// Nunca guarda a conversa: POST /mensagem passa direto para a rede.
const VERSAO = "interface-v4";
const INTERFACE = [
  "/",
  "/index.html",
  "/styles.css",
  "/app.js",
  "/risco.js",
  // Regras do alerta de 190: o alerta precisa funcionar sem internet.
  "/regras/risco_imediato.json",
  "/manifest.webmanifest",
  "/icones/icone.svg",
  "/icones/icone-192.png",
  "/icones/icone-512.png",
];

self.addEventListener("install", (evento) => {
  evento.waitUntil(caches.open(VERSAO).then((cache) => cache.addAll(INTERFACE)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (evento) => {
  evento.waitUntil(
    caches
      .keys()
      .then((nomes) => Promise.all(nomes.filter((nome) => nome !== VERSAO).map((nome) => caches.delete(nome))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (evento) => {
  const pedido = evento.request;
  const url = new URL(pedido.url);
  if (pedido.method !== "GET" || url.origin !== self.location.origin) return;

  // Abrir o app: tenta a rede (versão nova) e cai para a interface guardada.
  if (pedido.mode === "navigate") {
    evento.respondWith(
      fetch(pedido)
        .then((resposta) => {
          if (resposta.ok && (url.pathname === "/" || url.pathname === "/index.html")) {
            const copia = resposta.clone();
            caches.open(VERSAO).then((cache) => cache.put("/", copia));
          }
          return resposta;
        })
        .catch(() => caches.match("/"))
    );
    return;
  }

  // Interface: responde do cache na hora e atualiza a cópia guardada em segundo plano.
  if (INTERFACE.includes(url.pathname)) {
    const atualizar = fetch(pedido).then((resposta) => {
      if (resposta.ok) {
        const copia = resposta.clone();
        caches.open(VERSAO).then((cache) => cache.put(pedido, copia));
      }
      return resposta;
    });
    evento.respondWith(caches.match(pedido).then((guardado) => guardado || atualizar));
    evento.waitUntil(atualizar.catch(() => {}));
  }
});
