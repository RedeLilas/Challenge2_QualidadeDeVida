// Service worker: guarda só a interface para ela abrir sem internet.
// Nunca guarda a conversa: POST /mensagem passa direto para a rede.
const VERSAO = "interface-v8";
const INTERFACE = [
  "/",
  "/index.html",
  "/styles.css",
  "/perfil.js",
  "/dados.js",
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
  // cache: "reload" ignora o cache HTTP do navegador: sem isso, a versão nova do service worker
  // podia guardar um app.js ou um arquivo de regras antigo.
  const pedidos = INTERFACE.map((url) => new Request(url, { cache: "reload" }));
  evento.waitUntil(caches.open(VERSAO).then((cache) => cache.addAll(pedidos)).then(() => self.skipWaiting()));
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
    // no-cache: confere com o servidor em vez de reaproveitar a cópia do cache HTTP.
    const atualizar = fetch(pedido, { cache: "no-cache" }).then((resposta) => {
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
