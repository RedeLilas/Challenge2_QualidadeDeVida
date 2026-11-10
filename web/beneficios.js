// Avaliação determinística de elegibilidade a benefícios (s3-beneficios, tarefas 2.1 e 2.2).
// Função pura executada só no navegador, sem acesso a rede nem armazenamento local.
"use strict";

var Beneficios = (function () {
  var VALORES_NAO_INFORMADOS = {
    "": true,
    "prefiro_nao_informar": true,
    "prefiro nao informar": true,
    "nao_informado": true,
    "nao sei": true,
    "não sei": true
  };

  function ehNaoInformado(valor) {
    if (valor === null || valor === undefined) {
      return true;
    }
    if (typeof valor === "number") {
      return isNaN(valor);
    }
    if (typeof valor === "string") {
      var limpo = valor.trim().toLowerCase();
      return Boolean(VALORES_NAO_INFORMADOS[limpo]);
    }
    return false;
  }

  function lerNumero(valor) {
    if (ehNaoInformado(valor)) {
      return null;
    }
    if (typeof valor === "number") {
      return isFinite(valor) ? valor : null;
    }
    if (typeof valor === "string") {
      var normalizado = valor.trim().replace(",", ".");
      if (!normalizado) {
        return null;
      }
      var n = Number(normalizado);
      return isFinite(n) ? n : null;
    }
    return null;
  }

  function lerBooleano(valor) {
    if (ehNaoInformado(valor)) {
      return null;
    }
    if (typeof valor === "boolean") {
      return valor;
    }
    if (typeof valor === "string") {
      var limpo = valor.trim().toLowerCase();
      if (limpo === "sim" || limpo === "true" || limpo === "1") {
        return true;
      }
      if (limpo === "nao" || limpo === "não" || limpo === "false" || limpo === "0") {
        return false;
      }
    }
    return null;
  }

  // Interpreta se a usuária mora no Distrito Federal (true, false ou null se não informado).
  function lerMoradiaDF(entrada) {
    var chavesDiretas = ["moradia_df", "mora_no_df", "no_df"];
    for (var i = 0; i < chavesDiretas.length; i++) {
      if (entrada[chavesDiretas[i]] !== undefined) {
        return lerBooleano(entrada[chavesDiretas[i]]);
      }
    }

    var loc =
      entrada.localizacao !== undefined
        ? entrada.localizacao
        : entrada.ra !== undefined
          ? entrada.ra
          : entrada.regiao_administrativa !== undefined
            ? entrada.regiao_administrativa
            : entrada.uf !== undefined
              ? entrada.uf
              : entrada.cep;

    if (ehNaoInformado(loc)) {
      return null;
    }
    if (typeof loc === "boolean") {
      return loc;
    }

    var texto = String(loc).trim().toLowerCase();
    if (
      texto === "fora_df" ||
      texto === "fora do df" ||
      texto === "fora_do_df" ||
      texto === "outro_estado" ||
      texto === "outro estado" ||
      texto === "outro" ||
      texto === "nao" ||
      texto === "não"
    ) {
      return false;
    }

    var digitosCep = texto.replace(/\D/g, "");
    if (digitosCep.length === 8) {
      var prefixo = Number(digitosCep.slice(0, 5));
      return prefixo >= 70000 && prefixo <= 73999;
    }

    if (/^[a-z]{2}$/.test(texto)) {
      return texto === "df";
    }

    return true;
  }

  function primeiroDefinido(obj, chaves) {
    for (var i = 0; i < chaves.length; i++) {
      if (obj[chaves[i]] !== undefined) {
        return obj[chaves[i]];
      }
    }
    return undefined;
  }

  function unificarEntrada(dadosOuPerfil, especificas) {
    var base = {};
    var origens = [];
    if (dadosOuPerfil && typeof dadosOuPerfil === "object") {
      if (dadosOuPerfil.perfil && typeof dadosOuPerfil.perfil === "object") {
        origens.push(dadosOuPerfil.perfil);
      }
      if (dadosOuPerfil.especificas && typeof dadosOuPerfil.especificas === "object") {
        origens.push(dadosOuPerfil.especificas);
      }
      origens.push(dadosOuPerfil);
    }
    if (especificas && typeof especificas === "object") {
      origens.push(especificas);
    }
    for (var i = 0; i < origens.length; i++) {
      var origem = origens[i];
      var chaves = Object.keys(origem);
      for (var j = 0; j < chaves.length; j++) {
        var c = chaves[j];
        if (c !== "perfil" && c !== "especificas" && origem[c] !== undefined) {
          base[c] = origem[c];
        }
      }
    }
    return base;
  }

  // Calcula a renda familiar per capita considerando a casa sem o agressor.
  // Retorna null quando a renda ou o número de pessoas não foi informado ou é inválido (< 1).
  function calcularRendaPerCapita(rendaTotal, numeroPessoas) {
    var renda = lerNumero(rendaTotal);
    var pessoas = lerNumero(numeroPessoas);
    if (renda === null || renda < 0) {
      return null;
    }
    if (pessoas === null || pessoas < 1 || Math.floor(pessoas) !== pessoas) {
      return null;
    }
    return renda / pessoas;
  }

  function analisarRenda(entrada, textosGerais) {
    var valorRendaBruto = primeiroDefinido(entrada, ["renda_total", "rendaTotal", "renda_familiar", "renda"]);
    var valorPessoasBruto = primeiroDefinido(entrada, [
      "numero_pessoas",
      "numeroPessoas",
      "pessoas",
      "pessoas_na_casa"
    ]);

    var rendaInformada = !ehNaoInformado(valorRendaBruto);
    var pessoasInformadas = !ehNaoInformado(valorPessoasBruto);
    var renda = lerNumero(valorRendaBruto);
    var pessoas = lerNumero(valorPessoasBruto);

    var rendaValida = renda !== null && renda >= 0;
    var pessoasValidas = pessoas !== null && pessoas >= 1 && Math.floor(pessoas) === pessoas;
    var perCapita = rendaValida && pessoasValidas ? renda / pessoas : null;

    return {
      rendaTotal: rendaValida ? renda : null,
      numeroPessoas: pessoasValidas ? pessoas : null,
      rendaPerCapita: perCapita,
      rendaInformada: rendaInformada,
      pessoasInformadas: pessoasInformadas,
      rendaValida: rendaValida,
      pessoasValidas: pessoasValidas,
      motivoInvalido: !pessoasValidas
        ? textosGerais.motivo_pessoas_invalido
        : !rendaValida
          ? textosGerais.motivo_renda_nao_informada
          : null
    };
  }

  function montarFontes(regra, regrasDados, incluirNormaBoletim) {
    var fontes = [
      {
        norma: regra.norma,
        artigo: regra.artigo,
        inicio_vigencia: regra.inicio_vigencia,
        data_verificacao: regra.data_verificacao
      }
    ];
    if (incluirNormaBoletim && regra.norma_boletim) {
      fontes.push({
        norma: regra.norma_boletim.norma,
        artigo: regra.norma_boletim.artigo,
        inicio_vigencia: regra.norma_boletim.inicio_vigencia,
        data_verificacao: regra.norma_boletim.data_verificacao
      });
    }
    if (regra.usa_salario_minimo && regrasDados && regrasDados.salario_minimo) {
      var sm = regrasDados.salario_minimo;
      fontes.push({
        norma: sm.norma,
        artigo: sm.artigo,
        inicio_vigencia: sm.inicio_vigencia,
        data_verificacao: sm.data_verificacao
      });
    }
    return fontes;
  }

  function avaliarBolsaFamilia(regra, regrasDados, entrada, infoRenda) {
    var rotulos = regrasDados.rotulos_status;
    var t = regra.textos;
    var fontes = montarFontes(regra, regrasDados, false);
    var cadunico = lerBooleano(primeiroDefinido(entrada, ["cadunico", "inscrita_cadunico", "possui_cadunico"]));

    if (infoRenda.rendaPerCapita === null) {
      var faltaInfo = [];
      if (!infoRenda.rendaValida) {
        faltaInfo.push(t.falta_renda);
      }
      if (!infoRenda.pessoasValidas) {
        faltaInfo.push(t.falta_pessoas);
      }
      return {
        id: regra.id,
        status: "faltam_informacoes",
        rotulo: rotulos.faltam_informacoes,
        motivos: [infoRenda.motivoInvalido],
        falta: faltaInfo,
        onde_pedir: regra.onde_pedir,
        fontes: fontes,
        aviso: t.aviso
      };
    }

    var limite = regra.requisitos.renda_per_capita_max;
    if (infoRenda.rendaPerCapita > limite) {
      return {
        id: regra.id,
        status: "nao_aplicavel",
        rotulo: rotulos.nao_aplicavel,
        motivos: [t.motivo_renda_acima],
        falta: [],
        onde_pedir: regra.onde_pedir,
        fontes: fontes,
        aviso: t.aviso
      };
    }

    var motivos = [t.motivo_renda_atendida];
    var falta = [];
    if (cadunico === true) {
      motivos.push(t.motivo_cadunico_atendido);
      falta.push(t.falta_atualizar_cadunico);
    } else {
      falta.push(t.falta_cadunico);
    }

    return {
      id: regra.id,
      status: "provavel",
      rotulo: rotulos.provavel,
      motivos: motivos,
      falta: falta,
      onde_pedir: regra.onde_pedir,
      fontes: fontes,
      aviso: t.aviso
    };
  }

  function avaliarBpc(regra, regrasDados, entrada, infoRenda) {
    var rotulos = regrasDados.rotulos_status;
    var t = regra.textos;
    var fontes = montarFontes(regra, regrasDados, false);
    var salarioMinimo = regrasDados.salario_minimo.valor;
    var limiteRenda = salarioMinimo * regra.requisitos.renda_per_capita_fracao_sm;

    var idade = lerNumero(primeiroDefinido(entrada, ["idade"]));
    var deficiencia = lerBooleano(
      primeiroDefinido(entrada, ["deficiencia", "pessoa_com_deficiencia", "possui_deficiencia"])
    );
    var cadunico = lerBooleano(primeiroDefinido(entrada, ["cadunico", "inscrita_cadunico", "possui_cadunico"]));

    var atendeIdade = idade !== null && idade >= regra.requisitos.idade_minima;
    var atendeDeficiencia = deficiencia === true;
    var publicoAtendido = atendeDeficiencia || atendeIdade;
    var publicoDescartado = deficiencia === false && idade !== null && idade < regra.requisitos.idade_minima;
    var rendaAcima = infoRenda.rendaPerCapita !== null && infoRenda.rendaPerCapita > limiteRenda;

    if (publicoDescartado || rendaAcima) {
      var motivosNaoAplicavel = [];
      if (publicoDescartado) {
        motivosNaoAplicavel.push(t.motivo_sem_deficiencia_nem_idade);
      }
      if (rendaAcima) {
        motivosNaoAplicavel.push(t.motivo_renda_acima);
      }
      return {
        id: regra.id,
        status: "nao_aplicavel",
        rotulo: rotulos.nao_aplicavel,
        motivos: motivosNaoAplicavel,
        falta: [],
        onde_pedir: regra.onde_pedir,
        fontes: fontes,
        aviso: t.aviso_idade
      };
    }

    if (!publicoAtendido || infoRenda.rendaPerCapita === null) {
      var faltaInfo = [];
      var motivosFalta = [];
      if (!publicoAtendido) {
        faltaInfo.push(t.falta_idade_ou_deficiencia);
        motivosFalta.push(t.falta_idade_ou_deficiencia);
      }
      if (!infoRenda.rendaValida) {
        faltaInfo.push(t.falta_renda);
      }
      if (!infoRenda.pessoasValidas) {
        faltaInfo.push(t.falta_pessoas);
      }
      if (infoRenda.motivoInvalido) {
        motivosFalta.push(infoRenda.motivoInvalido);
      }
      return {
        id: regra.id,
        status: "faltam_informacoes",
        rotulo: rotulos.faltam_informacoes,
        motivos: motivosFalta,
        falta: faltaInfo,
        onde_pedir: regra.onde_pedir,
        fontes: fontes,
        aviso: atendeDeficiencia ? t.aviso_deficiencia : t.aviso_idade
      };
    }

    var motivos = [];
    if (atendeDeficiencia) {
      motivos.push(t.motivo_deficiencia);
    }
    if (atendeIdade) {
      motivos.push(t.motivo_idade);
    }
    motivos.push(t.motivo_renda_atendida);

    var falta = [];
    if (atendeDeficiencia) {
      falta.push(t.falta_avaliacao_deficiencia);
    }
    if (cadunico === true) {
      falta.push(t.falta_atualizar_cadunico);
    } else {
      falta.push(t.falta_cadunico);
    }

    return {
      id: regra.id,
      status: "provavel",
      rotulo: rotulos.provavel,
      motivos: motivos,
      falta: falta,
      onde_pedir: regra.onde_pedir,
      fontes: fontes,
      aviso: atendeDeficiencia ? t.aviso_deficiencia : t.aviso_idade
    };
  }

  function avaliarAuxilioAluguel(regra, regrasDados, entrada) {
    var rotulos = regrasDados.rotulos_status;
    var t = regra.textos;
    var fontes = montarFontes(regra, regrasDados, false);
    var medida = lerBooleano(
      primeiroDefinido(entrada, ["medida_protetiva", "possui_medida_protetiva", "tem_medida_protetiva"])
    );

    var falta = [];
    if (medida !== true) {
      falta.push(t.falta_medida_protetiva);
    }
    falta.push(t.falta_pedido_juiz);

    return {
      id: regra.id,
      status: "depende_decisao_judicial",
      rotulo: rotulos.depende_decisao_judicial,
      motivos: [t.motivo_judicial],
      falta: falta,
      onde_pedir: regra.onde_pedir,
      fontes: fontes,
      aviso: t.aviso
    };
  }

  function avaliarAluguelSocialDf(regra, regrasDados, entrada, infoRenda) {
    var rotulos = regrasDados.rotulos_status;
    var t = regra.textos;
    var salarioMinimo = regrasDados.salario_minimo.valor;
    var limitePerCapita = salarioMinimo * regra.requisitos.renda_per_capita_fracao_sm;
    var limiteFamiliar = salarioMinimo * regra.requisitos.renda_familiar_multiplo_sm;

    var moradiaDf = lerMoradiaDF(entrada);
    var necessidadeMoradia = lerBooleano(
      primeiroDefinido(entrada, [
        "necessidade_moradia",
        "precisa_moradia",
        "saida_emergencial",
        "permanecer_imovel_alugado"
      ])
    );
    var acompanhamento = lerBooleano(
      primeiroDefinido(entrada, ["acompanhamento_psicossocial", "acompanhamento", "em_acompanhamento"])
    );
    var medida = lerBooleano(
      primeiroDefinido(entrada, ["medida_protetiva", "possui_medida_protetiva", "tem_medida_protetiva"])
    );
    var boletim = lerBooleano(
      primeiroDefinido(entrada, ["boletim_ocorrencia", "boletim", "possui_boletim", "tem_boletim"])
    );

    var usaBoletim = medida !== true && boletim === true;
    var fontes = montarFontes(regra, regrasDados, true);

    var rendaCalculavel = infoRenda.rendaPerCapita !== null && infoRenda.rendaTotal !== null;
    var rendaAtendida =
      rendaCalculavel &&
      (infoRenda.rendaPerCapita <= limitePerCapita || infoRenda.rendaTotal <= limiteFamiliar);
    var rendaAcima = rendaCalculavel && !rendaAtendida;

    // 1. Requisitos estruturais não atendidos -> "Não aplicável"
    if (moradiaDf === false || necessidadeMoradia === false || rendaAcima) {
      var motivosNao = [];
      if (moradiaDf === false) {
        motivosNao.push(t.motivo_fora_df);
      }
      if (necessidadeMoradia === false) {
        motivosNao.push(t.motivo_sem_necessidade_moradia);
      }
      if (rendaAcima) {
        motivosNao.push(t.motivo_renda_acima);
      }
      return {
        id: regra.id,
        status: "nao_aplicavel",
        rotulo: rotulos.nao_aplicavel,
        motivos: motivosNao,
        falta: [],
        onde_pedir: regra.onde_pedir,
        fontes: fontes,
        aviso: t.aviso_padrao
      };
    }

    // 2. Sem medida protetiva e sem boletim de ocorrência -> "Não aplicável por enquanto"
    if (medida === false && boletim === false) {
      var faltaPorEnquanto = [t.falta_medida_ou_boletim];
      if (acompanhamento !== true) {
        faltaPorEnquanto.push(t.falta_acompanhamento);
      }
      return {
        id: regra.id,
        status: "nao_aplicavel",
        rotulo: rotulos.nao_aplicavel_por_enquanto,
        motivos: [t.motivo_sem_medida_nem_boletim],
        falta: faltaPorEnquanto,
        onde_pedir: regra.onde_pedir,
        fontes: fontes,
        aviso: t.aviso_padrao
      };
    }

    // 3. Faltam informações essenciais
    var faltaMedidaOuBoletimInfo = medida !== true && boletim !== true;
    if (
      moradiaDf === null ||
      !rendaCalculavel ||
      necessidadeMoradia === null ||
      acompanhamento === null ||
      faltaMedidaOuBoletimInfo
    ) {
      var faltaInfo = [];
      var motivosInfo = [];
      if (moradiaDf === null) {
        faltaInfo.push(t.falta_localizacao);
      }
      if (!infoRenda.rendaValida) {
        faltaInfo.push(t.falta_renda);
      }
      if (!infoRenda.pessoasValidas) {
        faltaInfo.push(t.falta_pessoas);
      }
      if (infoRenda.motivoInvalido) {
        motivosInfo.push(infoRenda.motivoInvalido);
      }
      if (necessidadeMoradia === null) {
        faltaInfo.push(t.falta_necessidade_moradia);
      }
      if (acompanhamento === null) {
        faltaInfo.push(t.falta_info_acompanhamento);
      }
      if (faltaMedidaOuBoletimInfo) {
        faltaInfo.push(t.falta_info_medida_ou_boletim);
      }
      if (motivosInfo.length === 0) {
        motivosInfo = faltaInfo.slice();
      }
      return {
        id: regra.id,
        status: "faltam_informacoes",
        rotulo: rotulos.faltam_informacoes,
        motivos: motivosInfo,
        falta: faltaInfo,
        onde_pedir: regra.onde_pedir,
        fontes: fontes,
        aviso: t.aviso_padrao
      };
    }

    // 4. Sem acompanhamento psicossocial no momento -> "Não aplicável por enquanto"
    if (acompanhamento === false) {
      return {
        id: regra.id,
        status: "nao_aplicavel",
        rotulo: rotulos.nao_aplicavel_por_enquanto,
        motivos: [t.falta_acompanhamento],
        falta: [t.falta_acompanhamento],
        onde_pedir: regra.onde_pedir,
        fontes: fontes,
        aviso: usaBoletim ? t.aviso_boletim : t.aviso_padrao
      };
    }

    // 5. Todos os requisitos atendidos (com medida protetiva ou só com boletim)
    var motivos = [
      t.motivo_moradia_df,
      t.motivo_renda_atendida,
      t.motivo_necessidade_moradia,
      t.motivo_acompanhamento,
      medida === true ? t.motivo_medida_protetiva : t.motivo_boletim
    ];

    return {
      id: regra.id,
      status: "provavel",
      rotulo: rotulos.provavel,
      motivos: motivos,
      falta: [t.falta_atualizar_cadunico],
      onde_pedir: regra.onde_pedir,
      fontes: fontes,
      aviso: usaBoletim ? t.aviso_boletim : t.aviso_padrao
    };
  }

  function avaliarRegra(regra, regrasDados, entrada, infoRenda) {
    if (regra.id === "bolsa_familia") {
      return avaliarBolsaFamilia(regra, regrasDados, entrada, infoRenda);
    }
    if (regra.id === "bpc") {
      return avaliarBpc(regra, regrasDados, entrada, infoRenda);
    }
    if (regra.id === "auxilio_aluguel") {
      return avaliarAuxilioAluguel(regra, regrasDados, entrada);
    }
    if (regra.id === "aluguel_social_df") {
      return avaliarAluguelSocialDf(regra, regrasDados, entrada, infoRenda);
    }
    return null;
  }

  function avaliar(regrasDados, dadosOuPerfil, especificas) {
    var entrada = unificarEntrada(dadosOuPerfil, especificas);
    var infoRenda = analisarRenda(entrada, regrasDados.textos_gerais);
    var resultados = [];
    for (var i = 0; i < regrasDados.regras.length; i++) {
      var res = avaliarRegra(regrasDados.regras[i], regrasDados, entrada, infoRenda);
      if (res) {
        resultados.push(res);
      }
    }
    return resultados;
  }

  function avaliarBeneficio(regrasDados, idBeneficio, dadosOuPerfil, especificas) {
    var todos = avaliar(regrasDados, dadosOuPerfil, especificas);
    for (var i = 0; i < todos.length; i++) {
      if (todos[i].id === idBeneficio) {
        return todos[i];
      }
    }
    return null;
  }

  return {
    calcularRendaPerCapita: calcularRendaPerCapita,
    avaliar: avaliar,
    avaliarBeneficio: avaliarBeneficio
  };
})();
