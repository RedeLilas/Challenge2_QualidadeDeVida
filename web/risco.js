// Risco imediato na PWA: mesmas regras (regras/risco_imediato.json) e mesma normalização do
// servidor (app/risco.py). Roda antes de qualquer envio e sem internet.
// tests/test_risco_js.py compara este arquivo com o Python em todas as frases da suíte.
"use strict";

var Risco = (function () {
  // Minúsculas, sem acentos e com espaços colapsados.
  function normalizar(texto) {
    return String(texto)
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .toLowerCase()
      .replace(/\s+/g, " ")
      .trim();
  }

  function compilar(dados) {
    return dados.regras.map(function (regra) {
      return { id: regra.id, categoria: regra.categoria, padrao: new RegExp(regra.padrao) };
    });
  }

  // A primeira regra que dispara ({ id, categoria }), ou null.
  function avaliar(regras, texto) {
    var normalizado = normalizar(texto);
    for (var i = 0; i < regras.length; i++) {
      if (regras[i].padrao.test(normalizado)) {
        return { id: regras[i].id, categoria: regras[i].categoria };
      }
    }
    return null;
  }

  return { normalizar: normalizar, compilar: compilar, avaliar: avaliar };
})();
