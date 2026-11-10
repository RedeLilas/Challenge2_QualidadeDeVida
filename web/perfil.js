// Gerenciador do perfil local da usuária (salvo apenas no localStorage do navegador).
// Nenhum dado do perfil é enviado automaticamente ao servidor; o nome da chave é neutro.
"use strict";

var Perfil = (function () {
  var CHAVE = "anotacoes_preferencias_v1";

  var CAMPOS = [
    "ra",
    "moradia",
    "renda",
    "pessoas_casa",
    "filhos",
    "idade",
    "estado_civil",
    "cadunico",
    "inss",
    "medida_protetiva",
  ];

  function vazio() {
    return {
      ra: "",
      moradia: "",
      renda: "",
      pessoas_casa: "",
      filhos: "",
      idade: "",
      estado_civil: "",
      cadunico: "",
      inss: "",
      medida_protetiva: "",
    };
  }

  function ler(storage) {
    var s = storage || (typeof localStorage !== "undefined" ? localStorage : null);
    if (!s) return vazio();
    try {
      var bruto = s.getItem(CHAVE);
      if (!bruto) return vazio();
      var lido = JSON.parse(bruto);
      if (!lido || typeof lido !== "object") return vazio();
      var base = vazio();
      for (var i = 0; i < CAMPOS.length; i++) {
        var campo = CAMPOS[i];
        if (typeof lido[campo] === "string") {
          base[campo] = lido[campo];
        }
      }
      return base;
    } catch (_e) {
      return vazio();
    }
  }

  function salvar(dados, storage) {
    var s = storage || (typeof localStorage !== "undefined" ? localStorage : null);
    var limpo = vazio();
    if (dados && typeof dados === "object") {
      for (var i = 0; i < CAMPOS.length; i++) {
        var campo = CAMPOS[i];
        if (typeof dados[campo] === "string") {
          limpo[campo] = dados[campo];
        }
      }
    }
    if (s) {
      try {
        s.setItem(CHAVE, JSON.stringify(limpo));
      } catch (_e) {}
    }
    return limpo;
  }

  // Apaga somente a chave do perfil no localStorage (não mexe no cache do Service Worker).
  function apagar(storage) {
    var s = storage || (typeof localStorage !== "undefined" ? localStorage : null);
    if (s) {
      try {
        s.removeItem(CHAVE);
      } catch (_e) {}
    }
    return vazio();
  }

  // Considera respondido quando todos os 10 campos têm valor (inclusive "Prefiro não informar").
  function completo(dados) {
    if (!dados || typeof dados !== "object") return false;
    for (var i = 0; i < CAMPOS.length; i++) {
      var valor = dados[CAMPOS[i]];
      if (typeof valor !== "string" || valor.trim() === "") {
        return false;
      }
    }
    return true;
  }

  // Conta quantos campos já foram respondidos (0 a 10).
  function progresso(dados) {
    if (!dados || typeof dados !== "object") return 0;
    var respondidos = 0;
    for (var i = 0; i < CAMPOS.length; i++) {
      var valor = dados[CAMPOS[i]];
      if (typeof valor === "string" && valor.trim() !== "") {
        respondidos++;
      }
    }
    return respondidos;
  }

  return {
    CHAVE: CHAVE,
    CAMPOS: CAMPOS,
    vazio: vazio,
    ler: ler,
    salvar: salvar,
    apagar: apagar,
    completo: completo,
    progresso: progresso,
  };
})();
