// Avaliação determinística da triagem de urgência baseada no Fonar (s3-triagem-fonar, tarefas 2.2 e 2.3).
// Função pura executada só no navegador, sem acesso ao DOM, rede ou armazenamento local.
"use strict";

var Triagem = (function () {
  var SINONIMOS_INDETERMINADO = {
    "": true,
    "pular": true,
    "pulou": true,
    "indeterminado": true,
    "nao_sei": true,
    "nao sei": true,
    "não sei": true,
    "prefiro_nao_responder": true,
    "prefiro nao responder": true,
    "prefiro não responder": true,
    "prefiro_nao_informar": true,
    "prefiro nao informar": true,
    "prefiro não informar": true
  };

  function normalizarTexto(valor) {
    return String(valor || "")
      .trim()
      .toLowerCase();
  }

  function resolverOpcaoUnica(pergunta, valor) {
    if (valor === null) {
      return { id: "pular", efeito: "indeterminado", abre_5_1: true };
    }
    var chave = normalizarTexto(valor);
    var opcoes = pergunta.opcoes || [];
    for (var i = 0; i < opcoes.length; i++) {
      var op = opcoes[i];
      if (normalizarTexto(op.id) === chave || normalizarTexto(op.rotulo) === chave) {
        return op;
      }
    }
    if (SINONIMOS_INDETERMINADO[chave]) {
      return {
        id: "pular",
        efeito: pergunta.apenas_abre_subitem ? "nenhum" : "indeterminado",
        abre_5_1: true
      };
    }
    if (chave === "sim" || valor === true) {
      for (var j = 0; j < opcoes.length; j++) {
        if (opcoes[j].efeito === "alto" || opcoes[j].efeito === "atencao" || opcoes[j].abre_5_1 === true) {
          return opcoes[j];
        }
      }
    }
    if (chave === "nao" || chave === "não" || valor === false) {
      for (var k = 0; k < opcoes.length; k++) {
        if (opcoes[k].id === "nao") {
          return opcoes[k];
        }
      }
    }
    return {
      id: "pular",
      efeito: pergunta.apenas_abre_subitem ? "nenhum" : "indeterminado",
      abre_5_1: true
    };
  }

  // Resolve a resposta dada a uma pergunta (aceita opção única ou lista de opções no item 4).
  function resolverResposta(pergunta, valor) {
    if (Array.isArray(valor)) {
      if (valor.length === 0) {
        return {
          id: "pular",
          efeito: pergunta.apenas_abre_subitem ? "nenhum" : "indeterminado",
          abre_5_1: true
        };
      }
      var temAlto = false;
      var temAtencao = false;
      var temIndeterminado = false;
      var abreSubitem = false;
      for (var i = 0; i < valor.length; i++) {
        var op = resolverOpcaoUnica(pergunta, valor[i]);
        if (op.efeito === "alto") temAlto = true;
        if (op.efeito === "atencao") temAtencao = true;
        if (op.efeito === "indeterminado") temIndeterminado = true;
        if (op.abre_5_1 !== false) abreSubitem = true;
      }
      var efeitoFinal = temAlto
        ? "alto"
        : temAtencao
          ? "atencao"
          : temIndeterminado
            ? "indeterminado"
            : "nenhum";
      return { id: "multiplo", efeito: efeitoFinal, abre_5_1: abreSubitem };
    }
    return resolverOpcaoUnica(pergunta, valor);
  }

  // O item 5.1 só deixa de ser perguntado quando a usuária responde no item 5 que nunca
  // registrou ocorrência nem pediu medida protetiva. Se pular ou responder "não sei" no 5,
  // o 5.1 é perguntado.
  function devePerguntar51(pergunta5, respostas) {
    if (!pergunta5 || !respostas || !Object.prototype.hasOwnProperty.call(respostas, "5")) {
      return true;
    }
    if (respostas["5"] === undefined) {
      return true;
    }
    var op5 = resolverResposta(pergunta5, respostas["5"]);
    return op5.abre_5_1 !== false;
  }

  function encontrarPergunta(regras, id) {
    var lista = (regras && regras.perguntas) || [];
    for (var i = 0; i < lista.length; i++) {
      if (lista[i].id === id) {
        return lista[i];
      }
    }
    return null;
  }

  function montarResultado(regras, chaveResultado) {
    var base = regras.resultados[chaveResultado];
    return {
      nivel: base.nivel,
      rotulo: base.rotulo,
      titulo: base.titulo,
      orientacao: base.orientacao,
      como_pedir_medida_protetiva: base.como_pedir_medida_protetiva,
      telefone_emergencia: base.telefone_emergencia,
      telefone_orientacao: base.telefone_orientacao,
      aviso_limite: base.aviso_limite || regras.aviso_limite,
      fonte: regras.fonte
    };
  }

  // Recebe as regras versionadas e o mapa de respostas em memória e devolve o próximo passo
  // ou o resultado final da triagem.
  function avaliar(regras, respostas) {
    var mapa = respostas && typeof respostas === "object" ? respostas : {};
    var perguntas = (regras && regras.perguntas) || [];
    var pergunta5 = encontrarPergunta(regras, "5");

    var temGatilhoIndeterminado = false;
    var temAtencao = false;

    for (var i = 0; i < perguntas.length; i++) {
      var p = perguntas[i];
      if (p.id === "5.1" && !devePerguntar51(pergunta5, mapa)) {
        continue;
      }

      var foiRespondida =
        Object.prototype.hasOwnProperty.call(mapa, p.id) && mapa[p.id] !== undefined;

      if (!foiRespondida) {
        return {
          concluida: false,
          encerrada_antecipadamente: false,
          gatilho_acionado: null,
          proxima_pergunta: p,
          nivel: null,
          resultado: null
        };
      }

      var opcao = resolverResposta(p, mapa[p.id]);

      if (opcao.efeito === "alto") {
        var restamPerguntas = i < perguntas.length - 1;
        return {
          concluida: true,
          encerrada_antecipadamente: restamPerguntas,
          gatilho_acionado: p.id,
          proxima_pergunta: null,
          nivel: "alto",
          resultado: montarResultado(regras, "alto")
        };
      }

      if (p.tipo === "gatilho" && !p.apenas_abre_subitem) {
        if (opcao.efeito === "indeterminado") {
          temGatilhoIndeterminado = true;
        } else if (opcao.efeito === "atencao") {
          temAtencao = true;
        }
      } else if (p.tipo === "atencao") {
        // Em pergunta de atenção, resposta afirmativa, pulo ou "não sei" resulta em "atenção".
        if (opcao.efeito === "atencao" || opcao.efeito === "indeterminado") {
          temAtencao = true;
        }
      }
    }

    var chaveFinal = temGatilhoIndeterminado
      ? "alto_nao_descartado"
      : temAtencao
        ? "atencao"
        : "sem_sinais_graves";

    return {
      concluida: true,
      encerrada_antecipadamente: false,
      gatilho_acionado: null,
      proxima_pergunta: null,
      nivel: chaveFinal,
      resultado: montarResultado(regras, chaveFinal)
    };
  }

  return {
    resolverResposta: resolverResposta,
    devePerguntar51: devePerguntar51,
    avaliar: avaliar
  };
})();

