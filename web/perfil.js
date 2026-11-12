// Gerenciador do perfil local da usuária (salvo apenas no localStorage do navegador).
// Nenhum dado do perfil é enviado automaticamente ao servidor; o nome da chave é neutro.
"use strict";

var Perfil = (function () {
  var CHAVE = "anotacoes_preferencias_v1";
  var NAO_INFORMADO = "prefiro_nao_informar";

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

  // Campos obrigatórios na spec de privacidade-seguranca (s3-frontend-e-perfil)
  var CAMPOS_SPEC = [
    "ra",
    "renda",
    "pessoas_casa",
    "cadunico",
    "inss",
    "filhos",
    "medida_protetiva",
    "idade",
    "estado_civil",
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

  function ehNaoInformado(valor) {
    if (valor === null || valor === undefined) return false;
    var limpo = String(valor).trim().toLowerCase();
    return (
      limpo === "prefiro_nao_informar" ||
      limpo === "prefiro não informar" ||
      limpo === "prefiro nao informar"
    );
  }

  function normalizarCampo(valor) {
    if (valor === null || valor === undefined) return "";
    return String(valor).trim();
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
        if (lido[campo] !== undefined && lido[campo] !== null) {
          base[campo] = normalizarCampo(lido[campo]);
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
        if (dados[campo] !== undefined && dados[campo] !== null) {
          limpo[campo] = normalizarCampo(dados[campo]);
        }
      }
      // Se moradia não foi passada mas os 9 campos da spec foram, preenche como não informado
      if (!limpo.moradia && completoSpec(limpo)) {
        limpo.moradia = "Prefiro não informar";
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

  function completoSpec(dados) {
    if (!dados || typeof dados !== "object") return false;
    for (var i = 0; i < CAMPOS_SPEC.length; i++) {
      var valor = dados[CAMPOS_SPEC[i]];
      if (valor === undefined || valor === null || String(valor).trim() === "") {
        return false;
      }
    }
    return true;
  }

  // Considera respondido quando todos os campos obrigatórios têm valor (inclusive "Prefiro não informar").
  function completo(dados) {
    return completoSpec(dados);
  }

  // Conta quantos campos do wizard já foram respondidos (0 a 10).
  function progresso(dados) {
    if (!dados || typeof dados !== "object") return 0;
    var respondidos = 0;
    for (var i = 0; i < CAMPOS.length; i++) {
      var valor = dados[CAMPOS[i]];
      if (valor !== undefined && valor !== null && String(valor).trim() !== "") {
        respondidos++;
      }
    }
    return respondidos;
  }

  // Devolve o valor útil do campo, ou null quando está vazio ou marcado como "Prefiro não informar"
  // (garante o requisito da spec: nenhum valor é inventado quando a usuária prefere não informar).
  function valorUtil(dados, campo) {
    if (!dados || typeof dados !== "object") return null;
    var bruto = dados[campo];
    if (bruto === undefined || bruto === null) return null;
    var texto = String(bruto).trim();
    if (!texto || ehNaoInformado(texto)) return null;
    return texto;
  }

  // Converte o perfil salvo (com rótulos amigáveis ou valores diretos) para o formato numérico/booleano
  // esperado pelo módulo oficial Beneficios.avaliar(REGRAS, entrada, especificas).
  function paraAvaliacaoBeneficios(dados) {
    var p = dados || {};

    // 1. Localização / RA
    var raUtil = valorUtil(p, "ra");
    var localizacao = raUtil ? raUtil : NAO_INFORMADO;
    if (raUtil === "Moro fora do Distrito Federal") {
      localizacao = "fora_df";
    }

    // 2. Renda familiar total aproximada (sem o agressor)
    var rendaBruta = valorUtil(p, "renda");
    var rendaTotal = NAO_INFORMADO;
    if (rendaBruta !== null) {
      var mapaRenda = {
        "Sem renda no momento": 0,
        "Até R$ 218 por mês": 218,
        "Até R$ 600 por mês": 600,
        "De R$ 601 a R$ 1.621 (até 1 salário mínimo)": 1621,
        "De R$ 1.622 a R$ 3.242 (até 2 salários mínimos)": 3242,
        "Acima de 2 salários mínimos": 3500,
      };
      if (mapaRenda[rendaBruta] !== undefined) {
        rendaTotal = mapaRenda[rendaBruta];
      } else {
        var numRenda = Number(String(rendaBruta).replace(",", "."));
        rendaTotal = isFinite(numRenda) ? numRenda : NAO_INFORMADO;
      }
    }

    // 3. Número de pessoas na casa (sem o agressor)
    var pessoasBruto = valorUtil(p, "pessoas_casa");
    var numeroPessoas = NAO_INFORMADO;
    if (pessoasBruto !== null) {
      var matchPessoas = String(pessoasBruto).match(/\d+/);
      if (matchPessoas) {
        numeroPessoas = Number(matchPessoas[0]);
      }
    }

    // 4. CadÚnico
    var cadBruto = valorUtil(p, "cadunico");
    var cadunico = NAO_INFORMADO;
    if (cadBruto !== null) {
      var cadLower = cadBruto.toLowerCase();
      if (cadLower.indexOf("sim") === 0 || cadLower === "true") {
        cadunico = true;
      } else if (cadLower.indexOf("não") === 0 || cadLower.indexOf("nao") === 0 || cadLower === "false") {
        cadunico = false;
      }
    }

    // 5. Idade
    var idadeBruta = valorUtil(p, "idade");
    var idade = NAO_INFORMADO;
    if (idadeBruta !== null) {
      var mapaIdade = {
        "18 a 29 anos": 25,
        "30 a 59 anos": 40,
        "60 a 64 anos": 62,
        "65 anos ou mais": 65,
      };
      if (mapaIdade[idadeBruta] !== undefined) {
        idade = mapaIdade[idadeBruta];
      } else {
        var numIdade = Number(idadeBruta);
        if (isFinite(numIdade) && numIdade > 0) idade = numIdade;
      }
    }

    // 6. Medida protetiva
    var mpuBruta = valorUtil(p, "medida_protetiva");
    var medidaProtetiva = NAO_INFORMADO;
    if (mpuBruta !== null) {
      var mpuLower = mpuBruta.toLowerCase();
      if (mpuLower.indexOf("sim") === 0 || mpuLower === "true") {
        medidaProtetiva = true;
      } else if (
        mpuLower.indexOf("ainda não") === 0 ||
        mpuLower.indexOf("não") === 0 ||
        mpuLower.indexOf("nao") === 0 ||
        mpuLower === "false"
      ) {
        medidaProtetiva = false;
      } else if (mpuLower.indexOf("já pedi") === 0) {
        medidaProtetiva = false;
      }
    }

    return {
      ra: localizacao,
      localizacao: localizacao,
      renda_total: rendaTotal,
      numero_pessoas: numeroPessoas,
      cadunico: cadunico,
      idade: idade,
      medida_protetiva: medidaProtetiva,
    };
  }

  return {
    CHAVE: CHAVE,
    NAO_INFORMADO: NAO_INFORMADO,
    CAMPOS: CAMPOS,
    CAMPOS_SPEC: CAMPOS_SPEC,
    vazio: vazio,
    ehNaoInformado: ehNaoInformado,
    valorUtil: valorUtil,
    ler: ler,
    salvar: salvar,
    apagar: apagar,
    completo: completo,
    progresso: progresso,
    paraAvaliacaoBeneficios: paraAvaliacaoBeneficios,
  };
})();
