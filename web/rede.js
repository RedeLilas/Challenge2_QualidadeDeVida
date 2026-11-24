// Rede de atendimento no navegador (s4-rede-atendimento, tarefas 2.1 e 2.2).
// Funções puras: sem DOM, sem rede e sem armazenamento. O CEP nunca sai do aparelho.
// Usado pela tela Onde buscar ajuda (web/app.js) e pela conversa (web/conversa.js).
// Testes em tests/test_rede_js.py, rodando este arquivo no QuickJS.
"use strict";

var Rede = (function () {
  // Vizinhas das 17 RAs do site, da maior fronteira para a menor. Conferidas na camada oficial
  // "Limite das Regiões Administrativas do DF em 2019" do IPEDF (LC 958/2019) em 17/11/2026,
  // no mapa agrupado em que cada RA fora do site entra na sua RA_ORDENACAO.
  // Tabela e método em openspec/changes/archive/2026-11-24-s4-rede-atendimento/design.md.
  var VIZINHAS = {
    "Plano Piloto": ["Sobradinho", "São Sebastião", "Guará", "Brazlândia", "Núcleo Bandeirante", "Paranoá", "Taguatinga", "Itapoã", "Estrutural (SCIA)"],
    "Ceilândia": ["Samambaia", "Brazlândia", "Taguatinga"],
    "Taguatinga": ["Águas Claras", "Ceilândia", "Samambaia", "Brazlândia", "Plano Piloto", "Estrutural (SCIA)", "Guará", "Núcleo Bandeirante", "Recanto das Emas"],
    "Samambaia": ["Ceilândia", "Recanto das Emas", "Taguatinga"],
    "Gama": ["Recanto das Emas", "Santa Maria", "Núcleo Bandeirante"],
    "Planaltina": ["Sobradinho", "Paranoá", "Itapoã"],
    "Sobradinho": ["Planaltina", "Plano Piloto", "Itapoã", "Brazlândia"],
    "Brazlândia": ["Plano Piloto", "Ceilândia", "Sobradinho", "Taguatinga"],
    "Paranoá": ["São Sebastião", "Planaltina", "Itapoã", "Plano Piloto"],
    "Núcleo Bandeirante": ["Plano Piloto", "Recanto das Emas", "Águas Claras", "Guará", "Santa Maria", "São Sebastião", "Gama", "Taguatinga"],
    "Santa Maria": ["Núcleo Bandeirante", "São Sebastião", "Gama"],
    "Recanto das Emas": ["Gama", "Samambaia", "Núcleo Bandeirante", "Taguatinga"],
    "Águas Claras": ["Núcleo Bandeirante", "Taguatinga", "Guará"],
    "Guará": ["Plano Piloto", "Núcleo Bandeirante", "Estrutural (SCIA)", "Taguatinga", "Águas Claras"],
    "São Sebastião": ["Paranoá", "Plano Piloto", "Santa Maria", "Núcleo Bandeirante"],
    "Itapoã": ["Sobradinho", "Paranoá", "Plano Piloto", "Planaltina"],
    "Estrutural (SCIA)": ["Taguatinga", "Guará", "Plano Piloto"],
  };

  // RA oficial fora da lista do site -> RA do site usada para ordenar (conferida no mesmo mapa).
  // Os serviços guardam a RA oficial (ex.: um CRAS no Sol Nascente), e a usuária escolhe uma RA do site.
  var RA_ORDENACAO = {
    "Sol Nascente/Pôr do Sol": "Ceilândia",
    "Vicente Pires": "Taguatinga",
    "Arniqueira": "Águas Claras",
    "Cruzeiro": "Plano Piloto",
    "Sudoeste/Octogonal": "Plano Piloto",
    "Lago Sul": "Plano Piloto",
    "Lago Norte": "Plano Piloto",
    "Varjão": "Plano Piloto",
    "Candangolândia": "Núcleo Bandeirante",
    "Park Way": "Núcleo Bandeirante",
    "Riacho Fundo": "Núcleo Bandeirante",
    "Riacho Fundo II": "Recanto das Emas",
    "Água Quente": "Recanto das Emas",
    "SIA": "Guará",
    "Sobradinho II": "Sobradinho",
    "Fercal": "Sobradinho",
    "Jardim Botânico": "São Sebastião",
    "Arapoanga": "Planaltina",
    // Mesmo lugar, nomes diferentes: a lista oficial escreve "SCIA/Estrutural", e o site, "Estrutural (SCIA)".
    "SCIA/Estrutural": "Estrutural (SCIA)",
  };

  // Lei 12.845/2013, arts. 1º e 3º (IV, V e § 1º). O prazo de 72 horas aguarda a fonte do
  // Ministério da Saúde (tarefa 4.2); sem ela, a frase com o número sai, como diz o design.
  var TEXTO_SAUDE =
    "Depois de uma violência sexual, você tem direito a atendimento imediato, de graça, em qualquer hospital público do SUS " +
    "(Lei 12.845/2013, arts. 1º e 3º, § 1º). Esse atendimento inclui remédios para evitar gravidez e infecções sexualmente " +
    "transmissíveis (Lei 12.845/2013, art. 3º, IV e V). Se foi nas últimas 72 horas, vá o quanto antes ao pronto-socorro " +
    "de um hospital público, porque esses remédios dependem do tempo.";
  var TEXTO_SAUDE_AJUDANDO =
    "Depois de uma violência sexual, a pessoa que você está ajudando tem direito a atendimento imediato, de graça, em qualquer hospital público do SUS " +
    "(Lei 12.845/2013, arts. 1º e 3º, § 1º). Esse atendimento inclui remédios para evitar gravidez e infecções sexualmente " +
    "transmissíveis (Lei 12.845/2013, art. 3º, IV e V). Se foi nas últimas 72 horas, apoie-a para ir o quanto antes " +
    "ao pronto-socorro de um hospital público, se ela quiser, porque esses remédios dependem do tempo.";

  // 00000-000, 00.000-000 ou 8 dígitos seguidos, sem fazer parte de um número maior.
  // Sem lookbehind: o Safari antes do iOS 16.4 não lê essa sintaxe e o arquivo inteiro falharia.
  var PADRAO_CEP = /(^|[^\d.])(\d{2}\.?\d{3}-?\d{3})(?![\d-])/g;

  function digitosCep(valor) {
    var digitos = String(valor == null ? "" : valor).replace(/[.\-\s]/g, "");
    return /^\d{8}$/.test(digitos) ? Number(digitos) : null;
  }

  // { dentroDF: true | false | null }. null quando o texto não é um CEP ou não há tabela:
  // nesse caso a tela pede a RA, em vez de dizer que a pessoa está fora do DF.
  // As faixas vêm de dados/cep_ra_df.csv (GET /cep-ra). O nome ficou do plano anterior: não devolve RA.
  function cepParaRa(cep, tabela) {
    var numero = digitosCep(cep);
    if (numero === null || !Array.isArray(tabela) || !tabela.length) return { dentroDF: null };
    for (var i = 0; i < tabela.length; i++) {
      var inicio = digitosCep(tabela[i].cep_inicio);
      var fim = digitosCep(tabela[i].cep_fim);
      if (inicio !== null && fim !== null && numero >= inicio && numero <= fim) return { dentroDF: true };
    }
    return { dentroDF: false };
  }

  // Troca todo CEP do texto por [CEP]. dentroDF é o do primeiro CEP, ou null se não houver CEP.
  // Um número de 8 dígitos que não é CEP também sai: tirar a mais é o lado seguro.
  function tirarCep(texto, tabela) {
    var original = String(texto == null ? "" : texto);
    var primeiro = null;
    var limpo = original.replace(PADRAO_CEP, function (_achado, antes, cep) {
      if (primeiro === null) primeiro = cep;
      return antes + "[CEP]";
    });
    return { texto: limpo, dentroDF: primeiro === null ? null : cepParaRa(primeiro, tabela).dentroDF };
  }

  function raDoSite(ra) {
    if (!ra) return null;
    if (Object.prototype.hasOwnProperty.call(VIZINHAS, ra)) return ra;
    if (Object.prototype.hasOwnProperty.call(RA_ORDENACAO, ra)) return RA_ORDENACAO[ra];
    return null; // "Outra RA do DF", "Prefiro não informar", vazio ou desconhecida
  }

  function eh24h(servico) {
    return String(servico.horario || "").indexOf("24 horas") !== -1;
  }

  // Ordena sem mudar a lista recebida. Ordem: saúde (só com violência sexual recente), mesma RA
  // (a própria antes das que ordenam como ela), vizinhas da maior fronteira para a menor, o resto.
  // Em cada grupo, os plantões 24 horas vêm primeiro; depois, a ordem original.
  // opcoes: { ra, violencia_sexual_recente (ou violenciaSexualRecente), tipo }. Com tipo, só esse tipo.
  function ordenar(servicos, opcoes) {
    var o = opcoes || {};
    var ra = raDoSite(o.ra);
    var sexualRecente = Boolean(
      o.violencia_sexual_recente !== undefined ? o.violencia_sexual_recente : o.violenciaSexualRecente
    );
    var vizinhas = ra ? VIZINHAS[ra] : [];
    var lista = (Array.isArray(servicos) ? servicos : []).filter(function (s) {
      return s && (!o.tipo || s.tipo === o.tipo);
    });

    function grupoRa(servico) {
      if (!ra) return 0;
      if (servico.ra === ra) return 0;
      var doSite = raDoSite(servico.ra);
      if (doSite === ra) return 1;
      var posicao = vizinhas.indexOf(doSite);
      return posicao === -1 ? 1000 : 2 + posicao;
    }

    return lista
      .map(function (servico, indice) {
        return {
          servico: servico,
          chave: [
            sexualRecente && servico.tipo === "Saúde" ? 0 : 1,
            grupoRa(servico),
            eh24h(servico) ? 0 : 1,
            indice,
          ],
        };
      })
      .sort(function (a, b) {
        for (var i = 0; i < a.chave.length; i++) {
          if (a.chave[i] !== b.chave[i]) return a.chave[i] - b.chave[i];
        }
        return 0;
      })
      .map(function (item) {
        return item.servico;
      });
  }

  // Aceita textoSaude(true) e textoSaude({ ajudando: true }), como chama web/conversa.js.
  function textoSaude(opcoes) {
    var ajudando = opcoes && typeof opcoes === "object" ? opcoes.ajudando : opcoes;
    return ajudando ? TEXTO_SAUDE_AJUDANDO : TEXTO_SAUDE;
  }

  return {
    VIZINHAS: VIZINHAS,
    RA_ORDENACAO: RA_ORDENACAO,
    cepParaRa: cepParaRa,
    tirarCep: tirarCep,
    ordenar: ordenar,
    textoSaude: textoSaude,
  };
})();
