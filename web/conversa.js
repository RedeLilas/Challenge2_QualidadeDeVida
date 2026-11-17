// Módulo puro da conversa (s4-orquestrador-agentes, tarefas 4.1, 4.2, 4.3 e 4.6).
// Monta o pedido do POST /orquestrar (sem perfil e sem histórico) e transforma a resposta
// do servidor em blocos prontos para exibição no navegador.
// Não faz chamadas de rede nem acessa armazenamento do navegador.
"use strict";

var Conversa = (function () {
  var NOMES_BENEFICIOS = {
    bolsa_familia: "Programa Bolsa Família",
    bpc: "Benefício de Prestação Continuada (BPC/LOAS)",
    auxilio_aluguel: "Auxílio-aluguel (Lei Maria da Penha)",
    aluguel_social_df: "Aluguel Social do Distrito Federal",
  };

  var TEXTOS_FIXOS = {
    continuarPergunta: "Continuar com minha pergunta",
    excessoPerguntas:
      "Você enviou mais de 3 perguntas na mesma mensagem. Respondi à primeira e separei até duas sugestões abaixo; por favor, envie as demais separadamente.",
    excessoPerguntasAjudando:
      "Você enviou mais de 3 perguntas na mesma mensagem. Respondi à primeira e separei até duas sugestões abaixo; por favor, envie as demais separadamente.",
    convitePerfil:
      "Para verificar se o seu caso se encaixa nas regras dos benefícios, preencha primeiro o formulário rápido de perfil (leva 1 minuto e fica apenas neste aparelho). Se estiver em perigo agora, ligue 190. Para orientação gratuita 24 horas, ligue 180.",
    convitePerfilAjudando:
      "Para verificar se a situação da pessoa que você está ajudando se encaixa nas regras dos benefícios, preencha o formulário rápido de perfil com os dados aproximados dela (fica apenas neste aparelho e você pode apagar em seguida). Se ela estiver em perigo agora, ligue 190. Para orientação gratuita 24 horas, ligue 180.",
    beneficioOutro:
      "Esta ferramenta avalia automaticamente apenas quatro benefícios: Bolsa Família, BPC/LOAS, Auxílio-aluguel da Lei Maria da Penha e Aluguel Social do DF. Para consultar outros programas (como Cartão Prato Cheio, Cartão Gás ou Benefícios Eventuais), procure o CRAS mais próximo da sua Região Administrativa no DF ou ligue 180 (gratuito, 24 horas).",
    beneficioOutroAjudando:
      "Esta ferramenta avalia automaticamente apenas quatro benefícios: Bolsa Família, BPC/LOAS, Auxílio-aluguel da Lei Maria da Penha e Aluguel Social do DF. Para consultar outros programas para a pessoa que você está ajudando (como Cartão Prato Cheio, Cartão Gás ou Benefícios Eventuais), oriente-a a procurar o CRAS mais próximo da Região Administrativa dela no DF ou ligue 180 (gratuito, 24 horas).",
    ofertaTriagem:
      "Você pode fazer agora a avaliação de risco adaptada do Formulário Nacional de Avaliação de Risco (Fonar). As respostas ficam somente na memória temporária desta página e nunca são enviadas ao servidor. Se estiver em perigo imediato, ligue 190 ou 180 (gratuito, 24 horas).",
    ofertaTriagemAjudando:
      "Você pode responder à avaliação de risco adaptada do Formulário Nacional de Avaliação de Risco (Fonar) pensando na situação da pessoa que está ajudando, ou fazer junto com ela em um momento seguro. As respostas ficam somente na memória temporária desta página e nunca são enviadas ao servidor. Se ela estiver em perigo imediato, ligue 190 e informe o endereço dela, ou ligue 180 (gratuito, 24 horas).",
    introBeneficios:
      "Veja abaixo a análise indicativa com base no perfil preenchido neste aparelho:",
    introBeneficiosAjudando:
      "Veja abaixo a análise indicativa para a pessoa que você está ajudando, com base no perfil preenchido neste aparelho:",
    introRede:
      "Confira os serviços de atendimento verificados no Distrito Federal (confirme o horário por telefone antes de ir, exceto nos plantões 24 horas):",
    introRedeAjudando:
      "Confira os serviços de atendimento no Distrito Federal que podem acolher a pessoa que você está ajudando (confirme o horário por telefone antes de ir, exceto nos plantões 24 horas):",
    saudeViolenciaSexual:
      "Em caso de violência sexual, qualquer hospital público do SUS deve prestar atendimento médico emergencial, integral e multidisciplinar imediato, sem exigir Boletim de Ocorrência (Lei 12.845/2013, arts. 1º e 3º, IV e V). Se ocorreu nas últimas 72 horas, procure imediatamente o pronto-socorro de um hospital público para a medicação preventiva (profilaxia).",
    saudeViolenciaSexualAjudando:
      "Em caso de violência sexual, qualquer hospital público do SUS deve prestar à vítima atendimento médico emergencial, integral e multidisciplinar imediato, sem exigir Boletim de Ocorrência (Lei 12.845/2013, arts. 1º e 3º, IV e V). Se ocorreu nas últimas 72 horas, apoie-a para ir imediatamente ao pronto-socorro de um hospital público para receber a medicação preventiva (profilaxia), respeitando a vontade dela.",
  };

  function dataBrasileira(iso) {
    if (!iso || typeof iso !== "string") return "";
    var partes = iso.trim().split("-");
    if (partes.length === 3 && partes[0].length === 4) {
      return partes[2] + "/" + partes[1] + "/" + partes[0];
    }
    return iso;
  }

  // Monta o corpo do POST /orquestrar garantindo que apenas { texto, alerta_visto, ajudando }
  // existam no objeto retornado (qualquer campo extra como perfil ou historico é descartado).
  function montarPedido(textoOuOpcoes, opcoes) {
    var textoBruto = "";
    var alertaVisto = false;
    var ajudando = false;

    if (textoOuOpcoes && typeof textoOuOpcoes === "object" && !Array.isArray(textoOuOpcoes)) {
      textoBruto = textoOuOpcoes.texto !== undefined ? textoOuOpcoes.texto : "";
      alertaVisto = Boolean(textoOuOpcoes.alerta_visto);
      ajudando = Boolean(textoOuOpcoes.ajudando);
    } else {
      textoBruto = textoOuOpcoes !== undefined && textoOuOpcoes !== null ? String(textoOuOpcoes) : "";
      if (opcoes && typeof opcoes === "object") {
        alertaVisto = Boolean(opcoes.alerta_visto);
        ajudando = Boolean(opcoes.ajudando);
      }
    }

    return {
      texto: String(textoBruto).trim(),
      alerta_visto: alertaVisto,
      ajudando: ajudando,
    };
  }

  function formatarCitacoes(citacoes) {
    if (!Array.isArray(citacoes)) return [];
    var resultado = [];
    for (var i = 0; i < citacoes.length; i++) {
      var c = citacoes[i] || {};
      var dataIso = c.data_acesso || c.data_verificacao || "";
      var dataBr = dataBrasileira(dataIso);
      var rotuloCitacao = c.citacao || (c.lei && c.artigo ? c.lei + ", art. " + c.artigo : "");
      resultado.push({
        lei: c.lei || "",
        artigo: c.artigo || "",
        citacao: rotuloCitacao,
        data_acesso: dataIso,
        data_verificacao: dataIso,
        data_formatada: dataBr,
        texto_fonte: dataBr
          ? rotuloCitacao + " · texto verificado em " + dataBr
          : rotuloCitacao,
      });
    }
    return resultado;
  }

  // Verifica se há um perfil preenchido (aceita tanto o formato bruto das 9 etapas de Perfil
  // quanto um objeto de perfil fictício já estruturado para Beneficios.avaliar nos testes).
  function temPerfilPreenchido(perfil) {
    if (!perfil || typeof perfil !== "object") return false;

    if (typeof Perfil !== "undefined" && typeof Perfil.completo === "function") {
      if (Perfil.completo(perfil)) return true;
    }

    var chavesDiretasAvaliacao = [
      "renda_total",
      "renda_familiar_mensal",
      "renda_familiar",
      "renda_per_capita",
      "numero_pessoas",
      "pessoas_na_casa",
      "moradia_df",
      "mora_no_df",
      "localizacao",
      "idosa",
      "deficiencia",
    ];
    for (var i = 0; i < chavesDiretasAvaliacao.length; i++) {
      var k = chavesDiretasAvaliacao[i];
      if (perfil[k] !== undefined && perfil[k] !== null && String(perfil[k]).trim() !== "") {
        return true;
      }
    }

    var chavesFormulario = [
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
    var preenchidas = 0;
    for (var j = 0; j < chavesFormulario.length; j++) {
      var valor = perfil[chavesFormulario[j]];
      if (valor !== undefined && valor !== null && String(valor).trim() !== "") {
        preenchidas++;
      }
    }
    return preenchidas === chavesFormulario.length;
  }

  // Prepara o objeto de perfil para Beneficios.avaliar(), preservando campos diretos de teste
  // e convertendo campos textuais do formulário quando Perfil.paraAvaliacaoBeneficios estiver disponível.
  function normalizarPerfilParaBeneficios(perfil) {
    if (!perfil || typeof perfil !== "object") return {};

    var base = {};
    if (typeof Perfil !== "undefined" && typeof Perfil.paraAvaliacaoBeneficios === "function") {
      var temChaveBruta =
        typeof perfil.renda === "string" ||
        typeof perfil.pessoas_casa === "string" ||
        typeof perfil.cadunico === "string" ||
        typeof perfil.medida_protetiva === "string" ||
        typeof perfil.idade === "string";
      if (temChaveBruta) {
        base = Perfil.paraAvaliacaoBeneficios(perfil);
      }
    }

    var copia = {};
    var chavesBase = Object.keys(base);
    for (var i = 0; i < chavesBase.length; i++) {
      copia[chavesBase[i]] = base[chavesBase[i]];
    }

    var chavesDiretas = [
      "renda_total",
      "renda_familiar_mensal",
      "renda_familiar",
      "renda_per_capita",
      "numero_pessoas",
      "pessoas_na_casa",
      "pessoas",
      "moradia_df",
      "mora_no_df",
      "no_df",
      "localizacao",
      "uf",
      "cep",
      "idosa",
      "deficiencia",
      "boletim_ocorrencia",
      "acompanhamento_psicossocial",
      "necessidade_moradia",
    ];
    for (var j = 0; j < chavesDiretas.length; j++) {
      var chave = chavesDiretas[j];
      if (perfil[chave] !== undefined) {
        copia[chave] = perfil[chave];
      }
    }
    if (copia.ra === undefined && perfil.ra !== undefined) {
      copia.ra = perfil.ra;
    }
    if (typeof perfil.cadunico === "boolean" || perfil.cadunico === "prefiro_nao_informar") {
      copia.cadunico = perfil.cadunico;
    }
    if (typeof perfil.medida_protetiva === "boolean" || perfil.medida_protetiva === "prefiro_nao_informar") {
      copia.medida_protetiva = perfil.medida_protetiva;
    }
    if (typeof perfil.idade === "number") {
      copia.idade = perfil.idade;
    }

    return copia;
  }

  function encontrarRegra(regras, idBeneficio) {
    var lista = regras && Array.isArray(regras.regras) ? regras.regras : [];
    for (var i = 0; i < lista.length; i++) {
      if (lista[i] && lista[i].id === idBeneficio) {
        return lista[i];
      }
    }
    return null;
  }

  function enriquecerItemBeneficio(regras, item) {
    var regra = encontrarRegra(regras, item.id) || {};
    var fontePrincipal =
      Array.isArray(item.fontes) && item.fontes.length > 0 ? item.fontes[0] : {};
    var norma = fontePrincipal.norma || regra.norma || "";
    var artigo = fontePrincipal.artigo || regra.artigo || "";
    var inicioVigencia = fontePrincipal.inicio_vigencia || regra.inicio_vigencia || "";
    var dataVerificacao = fontePrincipal.data_verificacao || regra.data_verificacao || "";
    var nome = NOMES_BENEFICIOS[item.id] || regra.nome || item.id;

    return {
      id: item.id,
      nome: nome,
      titulo: nome,
      status: item.status,
      situacao: item.rotulo,
      rotulo: item.rotulo,
      motivos: Array.isArray(item.motivos) ? item.motivos.slice() : [],
      falta: Array.isArray(item.falta) ? item.falta.slice() : [],
      o_que_falta: Array.isArray(item.falta) ? item.falta.slice() : [],
      onde_pedir: item.onde_pedir || regra.onde_pedir || "",
      norma: norma,
      artigo: artigo,
      inicio_vigencia: inicioVigencia,
      data_verificacao: dataVerificacao,
      data: dataBrasileira(dataVerificacao) || dataVerificacao,
      fontes: Array.isArray(item.fontes) ? item.fontes.slice() : [],
      aviso: item.aviso || "",
    };
  }

  // Monta o bloco de benefício para perguntas do tipo "tenho direito?" (tarefa 4.2).
  function montarCartaoBeneficio(regras, perfil, beneficioCitado, opcoes) {
    var config = opcoes && typeof opcoes === "object" ? opcoes : {};
    var ajudando = Boolean(config.ajudando);
    var especificas =
      config.especificas && typeof config.especificas === "object" ? config.especificas : {};
    var beneficioId = beneficioCitado || null;

    if (beneficioId === "outro") {
      return {
        tipo: "beneficio_outro",
        agente: "beneficios",
        beneficio: "outro",
        ajudando: ajudando,
        texto: ajudando ? TEXTOS_FIXOS.beneficioOutroAjudando : TEXTOS_FIXOS.beneficioOutro,
        onde_pedir:
          "Procure o CRAS mais próximo da sua Região Administrativa no DF ou ligue 180 (gratuito, 24 horas).",
        telefone_orientacao: "180",
        acao_destino: "benefits",
        rotulo_acao: "Ver os 4 benefícios avaliados no site",
        cartoes: [],
      };
    }

    if (!temPerfilPreenchido(perfil)) {
      return {
        tipo: "convite_perfil",
        agente: "beneficios",
        beneficio: beneficioId,
        ajudando: ajudando,
        texto: ajudando ? TEXTOS_FIXOS.convitePerfilAjudando : TEXTOS_FIXOS.convitePerfil,
        telefone_emergencia: "190",
        telefone_orientacao: "180",
        acao_destino: "screening",
        rotulo_acao: "Preencher formulário de perfil",
        cartoes: [],
      };
    }

    if (typeof Beneficios === "undefined" || !regras) {
      return {
        tipo: "convite_perfil",
        agente: "beneficios",
        beneficio: beneficioId,
        ajudando: ajudando,
        texto: ajudando ? TEXTOS_FIXOS.convitePerfilAjudando : TEXTOS_FIXOS.convitePerfil,
        telefone_emergencia: "190",
        telefone_orientacao: "180",
        acao_destino: "benefits",
        rotulo_acao: "Abrir tela de Benefícios",
        cartoes: [],
      };
    }

    var entradaPerfil = normalizarPerfilParaBeneficios(perfil);
    var avaliados = Beneficios.avaliar(regras, entradaPerfil, especificas);
    if (beneficioId) {
      avaliados = avaliados.filter(function (item) {
        return item.id === beneficioId;
      });
    }

    var cartoes = [];
    var precisaEspecificas = false;
    for (var i = 0; i < avaliados.length; i++) {
      var enriquecido = enriquecerItemBeneficio(regras, avaliados[i]);
      if (enriquecido.status === "faltam_informacoes") {
        precisaEspecificas = true;
      }
      cartoes.push(enriquecido);
    }

    return {
      tipo: "cartao_beneficio",
      agente: "beneficios",
      beneficio: beneficioId,
      ajudando: ajudando,
      texto: ajudando ? TEXTOS_FIXOS.introBeneficiosAjudando : TEXTOS_FIXOS.introBeneficios,
      cartoes: cartoes,
      precisa_especificas: precisaEspecificas,
      acao_destino: "benefits",
      rotulo_acao: precisaEspecificas
        ? "Responder perguntas específicas na tela Benefícios"
        : "Abrir tela completa de Benefícios",
    };
  }

  function formatarDominioFonte(url) {
    if (!url || typeof url !== "string") return "GDF";
    return url.replace(/^https?:\/\/(www\.)?/, "").split("/")[0] || "GDF";
  }

  function raValida(ra) {
    if (!ra || typeof ra !== "string") return null;
    var limpa = ra.trim();
    if (
      !limpa ||
      limpa === "Prefiro não informar" ||
      limpa === "prefiro_nao_informar" ||
      limpa === "Outra RA do DF" ||
      limpa === "Moro fora do Distrito Federal"
    ) {
      return null;
    }
    return limpa;
  }

  function ordenarServicosCurta(servicos, raAlvo, violenciaSexualRecente) {
    var lista = Array.isArray(servicos) ? servicos.slice() : [];
    if (!lista.length) return [];

    if (typeof Rede !== "undefined" && typeof Rede.ordenar === "function") {
      return Rede.ordenar(lista, {
        ra: raAlvo || null,
        violencia_sexual_recente: Boolean(violenciaSexualRecente),
      }).slice(0, 3);
    }

    return lista
      .map(function (servico, indice) {
        var ehSaude =
          violenciaSexualRecente && (servico.tipo === "Saúde" || servico.tipo === "Hospital")
            ? 0
            : 1;
        var ehMesmaRa = raAlvo && servico.ra === raAlvo ? 0 : 1;
        var eh24h = String(servico.horario || "").indexOf("24 horas") !== -1 ? 0 : 1;
        return {
          servico: servico,
          chave: [ehSaude, ehMesmaRa, eh24h, indice],
        };
      })
      .sort(function (a, b) {
        for (var i = 0; i < a.chave.length; i++) {
          if (a.chave[i] !== b.chave[i]) return a.chave[i] - b.chave[i];
        }
        return 0;
      })
      .slice(0, 3)
      .map(function (item) {
        return item.servico;
      });
  }

  function montarBlocoRede(campos, opcoes) {
    var config = opcoes && typeof opcoes === "object" ? opcoes : {};
    var ajudando = Boolean(config.ajudando);
    var perfil = config.perfil && typeof config.perfil === "object" ? config.perfil : {};
    var servicos = Array.isArray(config.servicos) ? config.servicos : [];
    var c = campos && typeof campos === "object" ? campos : {};

    var raCitada = raValida(c.ra);
    var raPerfil = raValida(perfil.ra);
    var raEscolhida = raCitada || raPerfil || null;
    var violenciaSexualRecente = Boolean(c.violencia_sexual_recente);

    var textoSaude = null;
    if (violenciaSexualRecente) {
      if (typeof Rede !== "undefined" && typeof Rede.textoSaude === "function") {
        textoSaude = Rede.textoSaude({ ajudando: ajudando });
      } else {
        textoSaude = ajudando
          ? TEXTOS_FIXOS.saudeViolenciaSexualAjudando
          : TEXTOS_FIXOS.saudeViolenciaSexual;
      }
    }

    var selecionados = ordenarServicosCurta(servicos, raEscolhida, violenciaSexualRecente).map(
      function (s) {
        var dataIso = s.data_verificacao || "";
        var fonteUrl = s.fonte_url || "";
        return {
          nome: s.nome || "",
          tipo: s.tipo || "",
          ra: s.ra || "",
          endereco: s.endereco || "",
          cep: s.cep || "",
          telefone: s.telefone || "",
          horario: s.horario || "",
          fonte: formatarDominioFonte(fonteUrl),
          fonte_url: fonteUrl,
          data_verificacao: dataIso,
          data_formatada: dataBrasileira(dataIso),
          recomendacao: "Confirme por telefone antes de ir",
        };
      }
    );

    return {
      tipo: "rede_atendimento",
      agente: "rede",
      ajudando: ajudando,
      ra: raEscolhida,
      violencia_sexual_recente: violenciaSexualRecente,
      texto: ajudando ? TEXTOS_FIXOS.introRedeAjudando : TEXTOS_FIXOS.introRede,
      texto_saude: textoSaude,
      servicos: selecionados,
      acao_destino: "places",
      rotulo_acao: "Ver lista completa de locais de atendimento",
    };
  }

  // Transforma a resposta do POST /orquestrar em uma lista ordenada de blocos de interface.
  function paraBlocos(respostaServidor, opcoes) {
    var config = opcoes && typeof opcoes === "object" ? opcoes : {};
    var ajudando = Boolean(config.ajudando);
    var blocos = [];

    if (!respostaServidor || typeof respostaServidor !== "object") {
      return blocos;
    }

    // Resposta 503 de indisponibilidade do LLM
    if (typeof respostaServidor.erro === "string" && respostaServidor.erro.trim()) {
      blocos.push({
        tipo: "erro",
        texto: respostaServidor.erro,
        telefone_orientacao: "180",
      });
      return blocos;
    }

    var riscoImediato = Boolean(respostaServidor.risco_imediato);
    var agente = respostaServidor.agente || null;

    // Sem alerta_visto: o servidor devolveu apenas o alerta de 190
    if (riscoImediato && agente === null) {
      blocos.push({
        tipo: "alerta_190",
        texto: respostaServidor.alerta || "",
        categoria_risco: respostaServidor.categoria_risco || null,
        telefone_emergencia: "190",
        telefone_orientacao: "180",
        botao_continuar: TEXTOS_FIXOS.continuarPergunta,
      });
      return blocos;
    }

    // Com alerta_visto: mantém a linha de 190 visível acima da resposta do agente
    if (riscoImediato && agente !== null) {
      blocos.push({
        tipo: "linha_190",
        texto: respostaServidor.alerta || "",
        categoria_risco: respostaServidor.categoria_risco || null,
        telefone_emergencia: "190",
        telefone_orientacao: "180",
      });
    }

    var campos =
      respostaServidor.campos && typeof respostaServidor.campos === "object"
        ? respostaServidor.campos
        : { beneficio: null, ra: null, violencia_sexual_recente: null };
    var respAgente =
      respostaServidor.resposta && typeof respostaServidor.resposta === "object"
        ? respostaServidor.resposta
        : null;

    if (agente === "fora_do_tema") {
      blocos.push({
        tipo: "fora_do_tema",
        agente: "fora_do_tema",
        texto: respAgente ? respAgente.resposta : "",
        citacoes: [],
        recusada: true,
        aviso: null,
        telefone_orientacao: "180",
      });
    } else if (agente === "juridico") {
      blocos.push({
        tipo: "resposta_com_fontes",
        agente: "juridico",
        decidido_por: respostaServidor.decidido_por || null,
        texto: respAgente ? respAgente.resposta : "",
        citacoes: respAgente ? formatarCitacoes(respAgente.citacoes) : [],
        recusada: respAgente ? Boolean(respAgente.recusada) : false,
        aviso: respAgente && respAgente.aviso ? respAgente.aviso : null,
      });
    } else if (agente === "beneficios" && respostaServidor.tipo === "explicacao") {
      blocos.push({
        tipo: "explicacao_beneficio",
        agente: "beneficios",
        beneficio: campos.beneficio || null,
        texto: respAgente ? respAgente.resposta : "",
        citacoes: respAgente ? formatarCitacoes(respAgente.citacoes) : [],
        recusada: respAgente ? Boolean(respAgente.recusada) : false,
        aviso: respAgente && respAgente.aviso ? respAgente.aviso : null,
      });
    } else if (agente === "beneficios" && respostaServidor.tipo === "direito") {
      blocos.push(
        montarCartaoBeneficio(config.regrasBeneficios || config.regras, config.perfil, campos.beneficio, {
          ajudando: ajudando,
          especificas: config.especificas,
        })
      );
    } else if (agente === "triagem") {
      blocos.push({
        tipo: "oferta_triagem",
        agente: "triagem",
        ajudando: ajudando,
        titulo: "Avaliação de Risco (Fonar)",
        texto: ajudando ? TEXTOS_FIXOS.ofertaTriagemAjudando : TEXTOS_FIXOS.ofertaTriagem,
        telefone_emergencia: "190",
        telefone_orientacao: "180",
        acao_destino: "fonar",
        rotulo_acao: "Começar avaliação de risco",
      });
    } else if (agente === "rede") {
      blocos.push(
        montarBlocoRede(campos, {
          ajudando: ajudando,
          perfil: config.perfil,
          servicos: config.servicos,
        })
      );
    }

    if (
      Array.isArray(respostaServidor.outras_perguntas) &&
      respostaServidor.outras_perguntas.length > 0
    ) {
      blocos.push({
        tipo: "sugestoes",
        perguntas: respostaServidor.outras_perguntas.slice(0, 2),
      });
    }

    if (respostaServidor.excedeu === true) {
      blocos.push({
        tipo: "excesso",
        texto: ajudando
          ? TEXTOS_FIXOS.excessoPerguntasAjudando
          : TEXTOS_FIXOS.excessoPerguntas,
      });
    }

    return blocos;
  }

  return {
    TEXTOS_FIXOS: TEXTOS_FIXOS,
    NOMES_BENEFICIOS: NOMES_BENEFICIOS,
    dataBrasileira: dataBrasileira,
    montarPedido: montarPedido,
    formatarCitacoes: formatarCitacoes,
    temPerfilPreenchido: temPerfilPreenchido,
    montarCartaoBeneficio: montarCartaoBeneficio,
    cartaoBeneficio: montarCartaoBeneficio,
    avaliarCartaoBeneficio: montarCartaoBeneficio,
    montarBlocoRede: montarBlocoRede,
    paraBlocos: paraBlocos,
    transformarResposta: paraBlocos,
  };
})();
