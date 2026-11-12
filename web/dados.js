// Catálogo de dados da interface Rede Lilás:
// 1. Etapas do formulário de perfil (com "Prefiro não informar" em todos os campos)
// 2. Perguntas específicas e metadados de apresentação para os Benefícios Sociais
// 3. Guia de Direitos e Leis (Lei Maria da Penha, Lei 14.550/2023, Lei 14.674/2023, Minuto Seguinte)
"use strict";

var DadosRedeLilas = (function () {
  var RAS_DF = [
    "Plano Piloto",
    "Ceilândia",
    "Taguatinga",
    "Samambaia",
    "Gama",
    "Planaltina",
    "Sobradinho",
    "Brazlândia",
    "Paranoá",
    "Núcleo Bandeirante",
    "Santa Maria",
    "Recanto das Emas",
    "Águas Claras",
    "Guará",
    "São Sebastião",
    "Itapoã",
    "Estrutural (SCIA)",
    "Outra RA do DF",
    "Prefiro não informar",
  ];

  var ETAPAS_PERFIL = [
    {
      campo: "ra",
      aba: "Localização",
      icone: "pin",
      pergunta: "Em qual Região Administrativa (RA) ou CEP você está?",
      ajuda: "Você pode escolher sua Região Administrativa abaixo ou digitar apenas o CEP. Usamos somente para ordenar os locais mais próximos.",
      motivo: "Permite mostrar primeiro as delegacias (DEAM), CEAMs, Defensoria e Juizados da sua região.",
      tipo: "select_E_opcoes",
      opcoes: [
        "Ceilândia",
        "Plano Piloto",
        "Samambaia",
        "Taguatinga",
        "Gama",
        "Planaltina",
        "Sobradinho",
        "Santa Maria",
        "Recanto das Emas",
        "Brazlândia",
        "Paranoá",
        "Núcleo Bandeirante",
        "Outra RA do DF",
        "Moro fora do Distrito Federal",
        "Prefiro não informar",
      ],
    },
    {
      campo: "moradia",
      aba: "Moradia",
      icone: "home",
      pergunta: "Qual é a sua situação atual de moradia?",
      ajuda: "Não pedimos seu endereço completo.",
      motivo: "Ajuda a identificar elegibilidade ao Aluguel Social do DF e ao Auxílio-Aluguel da Lei Maria da Penha.",
      opcoes: [
        "Preciso sair de casa com urgência para me proteger",
        "Já saí do lar por causa da violência e pago aluguel / estou de favor",
        "Moro em imóvel alugado ou cedido sem o agressor",
        "Moro em imóvel próprio em segurança",
        "Prefiro não informar",
      ],
    },
    {
      campo: "renda",
      aba: "Renda da casa",
      icone: "benefit",
      pergunta: "Qual é a renda mensal total aproximada da sua casa (sem o agressor)?",
      ajuda: "Considere a soma dos ganhos da casa como ficará sem o agressor. Lembre-se de atualizar o CadÚnico no CRAS para refletir essa mudança.",
      motivo: "Os programas sociais calculam a renda familiar total ou por pessoa considerando a casa sem o agressor.",
      opcoes: [
        "Sem renda no momento",
        "Até R$ 218 por mês",
        "Até R$ 600 por mês",
        "De R$ 601 a R$ 1.621 (até 1 salário mínimo)",
        "De R$ 1.622 a R$ 3.242 (até 2 salários mínimos)",
        "Acima de 2 salários mínimos",
        "Prefiro não informar",
      ],
    },
    {
      campo: "pessoas_casa",
      aba: "Pessoas na casa",
      icone: "users",
      pergunta: "Quantas pessoas moram na casa (incluindo você e seus filhos)?",
      ajuda: "Esse número serve para calcular a renda por pessoa da família.",
      motivo: "Benefícios como Bolsa Família, BPC/LOAS e Aluguel Social calculam a renda dividida pelo total de moradores.",
      opcoes: [
        "Moro sozinha (1 pessoa)",
        "2 pessoas",
        "3 pessoas",
        "4 pessoas",
        "5 ou mais pessoas",
        "Prefiro não informar",
      ],
    },
    {
      campo: "filhos",
      aba: "Filhos / Dependentes",
      icone: "heart",
      pergunta: "Você tem filhos ou dependentes sob seu cuidado?",
      ajuda: "Inclua crianças, adolescentes ou dependentes com deficiência.",
      motivo: "Ter filhos menores ou dependentes garante prioridade e adicionais em programas como Bolsa Família e Prato Cheio.",
      opcoes: [
        "Sim, crianças de 0 a 6 anos",
        "Sim, filhos de 7 a 17 anos",
        "Sim, filho(a) ou dependente com deficiência",
        "Sim, filhos maiores de 18 anos",
        "Não tenho filhos ou dependentes",
        "Prefiro não informar",
      ],
    },
    {
      campo: "idade",
      aba: "Sua idade",
      icone: "spark",
      pergunta: "Qual é a sua faixa de idade?",
      ajuda: "Informação opcional e anônima.",
      motivo: "Mulheres com 65 anos ou mais podem ter direito ao BPC/LOAS (1 salário mínimo mensal). A condição de deficiência é perguntada separadamente na tela de Benefícios.",
      opcoes: [
        "18 a 29 anos",
        "30 a 59 anos",
        "60 a 64 anos",
        "65 anos ou mais",
        "Prefiro não informar",
      ],
    },
    {
      campo: "estado_civil",
      aba: "Vínculo / Estado civil",
      icone: "scale",
      pergunta: "Qual é o seu estado civil ou situação de convivência?",
      ajuda: "Ajuda a orientar sobre partilha de bens, guarda e medidas protetivas.",
      motivo: "A Lei Maria da Penha protege qualquer relação íntima de afeto, mesmo sem casamento formal ou morando em casas separadas.",
      opcoes: [
        "Casada ou em união estável",
        "Separada recentemente / em processo de separação",
        "Solteira (namoro ou ex-namorado)",
        "Divorciada ou viúva",
        "Prefiro não informar",
      ],
    },
    {
      campo: "cadunico",
      aba: "CadÚnico",
      icone: "check",
      pergunta: "Você já está inscrita no Cadastro Único (CadÚnico)?",
      ajuda: "O CadÚnico é o registro gratuito feito no CRAS para programas sociais.",
      motivo: "Saber se seu CadÚnico está ativo ajuda a indicar se você já pode solicitar o benefício direto ou como atualizar no CRAS.",
      opcoes: [
        "Sim, está atualizado (nos últimos 2 anos)",
        "Sim, mas está desatualizado ou inclui o agressor",
        "Não tenho inscrição no CadÚnico",
        "Não sei se tenho",
        "Prefiro não informar",
      ],
    },
    {
      campo: "inss",
      aba: "Trabalho / INSS",
      icone: "shield",
      pergunta: "Qual é o seu vínculo atual de trabalho ou contribuição ao INSS?",
      ajuda: "A Lei Maria da Penha protege seu emprego caso precise se afastar.",
      motivo: "Trabalhadoras com carteira assinada têm direito a manter o vínculo trabalhista por até 6 meses (art. 9º, § 2º, II da Lei 11.340/2006).",
      opcoes: [
        "Trabalho com carteira assinada (CLT)",
        "Autônoma / MEI / contribuinte do INSS",
        "Trabalho informal (sem contribuição ao INSS)",
        "Desempregada / sem renda própria",
        "Prefiro não informar",
      ],
    },
    {
      campo: "medida_protetiva",
      aba: "Medida Protetiva",
      icone: "scale",
      pergunta: "Você já possui Medida Protetiva de Urgência ou Boletim de Ocorrência?",
      ajuda: "Você pode pedir medida protetiva na DEAM ou na Defensoria apenas com o seu depoimento (Lei 14.550/2023).",
      motivo: "A medida protetiva é um dos documentos que dão acesso ao Aluguel Social do DF e ao Auxílio-Aluguel judicial.",
      opcoes: [
        "Sim, já tenho medida protetiva concedida pelo juiz",
        "Já pedi medida protetiva ou fiz Boletim de Ocorrência",
        "Ainda não fiz BO nem pedi medida protetiva",
        "Prefiro não informar",
      ],
    },
  ];

  var DIREITOS_LEIS = [
    {
      id: "lei-maria-da-penha",
      tag: "Lei 11.340/2006 · arts. 5º e 7º",
      titulo: "As 5 formas de violência doméstica reconhecidas por lei",
      resumo:
        "Você não precisa ter marcas físicas para buscar proteção. A Lei Maria da Penha protege contra violência física, psicológica (humilhação, chantagem, isolamento, perseguição), sexual, patrimonial (reter documentos, dinheiro ou destruir objetos) e moral (calúnia, difamação, injúria).",
      destaque: "Vale para marido, companheiro, namorado, ex-parceiro ou familiares, mesmo que não morem na mesma casa.",
      verificacao: "Texto oficial verificado em 05/11/2026",
    },
    {
      id: "medida-protetiva-imediata",
      tag: "Lei 14.550/2023 · art. 19, §§ 4º a 6º da LMP",
      titulo: "Medida Protetiva concedida a partir do seu depoimento (sem precisar de BO prévio)",
      resumo:
        "Desde a Lei 14.550/2023, as medidas protetivas de urgência são concedidas pelo juiz com base no seu relato perante a autoridade policial ou apresentação de suas alegações escritas (como via Defensoria Pública), independentemente de inquérito policial ou registro prévio de boletim de ocorrência.",
      destaque: "Inclui afastamento imediato do agressor do lar, proibição de aproximação e de contato por mensagens ou redes sociais.",
      verificacao: "Texto oficial verificado em 05/11/2026",
    },
    {
      id: "vinculo-trabalhista",
      tag: "Lei 11.340/2006 · art. 9º, § 2º, II",
      titulo: "Manutenção do emprego por até 6 meses e prioridade de matrícula dos filhos",
      resumo:
        "Quando for necessário o afastamento do local de trabalho para preservar sua integridade física e psicológica, o juiz pode assegurar a manutenção do seu vínculo trabalhista por até 6 meses. Você também tem direito à matrícula dos seus dependentes em escola mais próxima do novo endereço, com sigilo dos dados (art. 9º, §§ 7º e 8º).",
      destaque: "Seus dados escolares e de endereço podem ficar sob sigilo judicial para que o agressor não localize você.",
      verificacao: "Texto oficial verificado em 05/11/2026",
    },
    {
      id: "crimes-stalking-psicologica",
      tag: "Código Penal · arts. 147-A, 147-B e 24-A da LMP",
      titulo: "Perseguição (Stalking), Violência Psicológica e Descumprimento de Medida são crimes",
      resumo:
        "Perseguir alguém reiteradamente (pessoalmente ou pela internet) ameaçando sua liberdade ou privacidade é crime (art. 147-A do Código Penal). Causar dano emocional que prejudique seu pleno desenvolvimento ou vise controlar suas ações também é crime (art. 147-B). E descumprir medida protetiva dá prisão em flagrante (art. 24-A da Lei 11.340/2006).",
      destaque: "Guarde prints de mensagens, áudios e ligações em local seguro (como e-mail de confiança) se puder fazer isso sem risco.",
      verificacao: "Texto oficial verificado em 05/11/2026",
    },
    {
      id: "minuto-seguinte",
      tag: "Lei 12.845/2013 e Lei 14.737/2023",
      titulo: "Atendimento médico imediato no SUS (Lei do Minuto Seguinte) e Direito a Acompanhante",
      resumo:
        "Todo hospital do SUS é obrigado a oferecer atendimento emergencial, integral e multidisciplinar imediato em caso de violência sexual, incluindo medicação preventiva (em até 72h) e apoio psicológico, sem exigir Boletim de Ocorrência para atender você. Além disso, a Lei 14.737/2023 garante seu direito a acompanhante de sua livre escolha em qualquer atendimento de saúde.",
      destaque: "O atendimento de saúde é imediato e gratuito em qualquer hospital público do DF.",
      verificacao: "Texto oficial verificado em 05/11/2026",
    },
  ];

  // Perguntas específicas exibidas na tela de Benefícios (mantidas apenas em memória, nunca salvas no localStorage)
  var PERGUNTAS_ESPECIFICAS_BENEFICIOS = [
    {
      campo: "deficiencia",
      pergunta: "Há pessoa com deficiência na casa (você ou dependente)?",
      detalhe: "Critério do BPC/LOAS (Lei 8.742/1993, art. 20).",
    },
    {
      campo: "boletim_ocorrencia",
      pergunta: "Você já registrou Boletim de Ocorrência (BO)?",
      detalhe: "Critério do Aluguel Social do DF (Lei Distrital 6.623/2020, art. 1º, § 2º).",
    },
    {
      campo: "acompanhamento_psicossocial",
      pergunta: "Está em acompanhamento psicossocial na rede (CEAM, Casa da Mulher Brasileira ou CRAS/CREAS)?",
      detalhe: "Requisito da Portaria SMDF 49/2026 para o Aluguel Social do DF.",
    },
    {
      campo: "necessidade_moradia",
      pergunta: "Precisa sair emergencialmente do lar ou permanecer em imóvel alugado sem recursos próprios?",
      detalhe: "Requisito de vulnerabilidade habitacional (Portaria SMDF 49/2026, art. 5º, IV).",
    },
  ];

  // Metadados complementares de apresentação para os 4 benefícios avaliados por Beneficios.avaliar()
  var DETALHES_BENEFICIOS = {
    aluguel_social_df: {
      titulo: "Aluguel Social do Distrito Federal",
      esfera: "Benefício Distrital (GDF)",
      valor: "R$ 600,00 por mês (por até 6 meses, prorrogável por mais 6 meses)",
      resumo:
        "Auxílio financeiro temporário da Secretaria de Estado da Mulher do DF para mulheres vítimas de violência doméstica que precisam deixar o lar ou manter aluguel sem recursos próprios.",
    },
    auxilio_aluguel: {
      titulo: "Auxílio-aluguel (Lei Maria da Penha)",
      esfera: "Benefício Federal (Medida Protetiva)",
      valor: "Valor fixado pelo Juizado (por até 6 meses)",
      resumo:
        "Medida protetiva de urgência concedida pelo juiz em razão de afastamento do lar, conforme a situação de vulnerabilidade social e econômica.",
    },
    bolsa_familia: {
      titulo: "Programa Bolsa Família",
      esfera: "Benefício Federal",
      valor: "Mínimo de R$ 600,00 por família + adicionais para crianças e gestantes",
      resumo:
        "Transferência direta de renda para famílias com renda mensal por pessoa de até R$ 218,00, considerando a composição da casa sem o agressor.",
    },
    bpc: {
      titulo: "Benefício de Prestação Continuada (BPC/LOAS)",
      esfera: "Benefício Federal (LOAS)",
      valor: "1 salário mínimo por mês (R$ 1.621,00 em 2026 — não exige contribuição ao INSS)",
      resumo:
        "Benefício assistencial de 1 salário mínimo mensal para pessoa com deficiência (de qualquer idade) ou pessoa idosa com 65 anos ou mais com renda familiar por pessoa de até 1/4 do salário mínimo.",
    },
  };

  // Respostas locais para o chat flutuante quando o servidor está sem chave de LLM configurada
  function respostaLocalChat(pergunta) {
    var t = String(pergunta || "").toLowerCase();
    if (t.indexOf("medida protetiva") !== -1 || t.indexOf("boletim") !== -1 || t.indexOf("afastar") !== -1) {
      return {
        resposta:
          "Você pode solicitar Medida Protetiva de Urgência diretamente na DEAM (Asa Sul ou Ceilândia, 24h) ou pela Defensoria Pública do DF (NUDEM). Pela Lei 14.550/2023 (que alterou o art. 19 da Lei Maria da Penha), o juiz pode conceder a medida protetiva a partir do seu depoimento, mesmo sem boletim de ocorrência prévio ou inquérito concluído. As medidas podem incluir o afastamento imediato do agressor do lar e a proibição de aproximação e contato.",
        citacoes: [
          { citacao: "Lei 11.340/2006, arts. 19 e 22", data_acesso: "2026-11-05" },
          { citacao: "Lei 14.550/2023, art. 1º", data_acesso: "2026-11-05" },
        ],
      };
    }
    if (t.indexOf("aluguel") !== -1 || t.indexOf("beneficio") !== -1 || t.indexOf("benefício") !== -1 || t.indexOf("dinheiro") !== -1 || t.indexOf("bolsa") !== -1) {
      return {
        resposta:
          "No Distrito Federal, mulheres em situação de violência doméstica podem ter acesso ao Aluguel Social do DF (R$ 600/mês por até 6 meses, prorrogável, conforme Lei Distrital 6.623/2020 e Portaria SMDF 49/2026) e ao Auxílio-Aluguel judicial previsto na Lei Maria da Penha (art. 23, VI, incluído pela Lei 14.674/2023). Além disso, no CRAS você pode atualizar seu CadÚnico sem o agressor para solicitar o Bolsa Família (Lei 14.601/2023) e o Cartão Prato Cheio.",
        citacoes: [
          { citacao: "Lei 11.340/2006, art. 23, VI (Lei 14.674/2023)", data_acesso: "2026-11-05" },
          { citacao: "Portaria SMDF 49/2026, arts. 4º e 5º", data_acesso: "2026-11-05" },
        ],
      };
    }
    if (t.indexOf("atendimento") !== -1 || t.indexOf("delegacia") !== -1 || t.indexOf("deam") !== -1 || t.indexOf("onde") !== -1) {
      return {
        resposta:
          "Para atendimento 24 horas no DF, você pode procurar a Casa da Mulher Brasileira em Ceilândia (CNM 1, Bloco I, Lote 3 — tel. 3181-1474), a DEAM I na Asa Sul (EQS 204/205 — tel. 3207-6172) ou a DEAM II em Ceilândia (QNM 02 — tel. 3207-7391). Para apoio psicológico, social e jurídico gratuito sem precisar registrar ocorrência policial, procure os CEAMs (102 Sul, Ceilândia ou Planaltina) ou o NUDEM da Defensoria Pública (Disque 129).",
        citacoes: [
          { citacao: "Rede de Proteção do DF · dados verificados", data_acesso: "2026-11-05" },
        ],
      };
    }
    return {
      resposta:
        "A Lei Maria da Penha (Lei 11.340/2006, arts. 5º e 7º) protege mulheres contra violência física, psicológica, sexual, patrimonial e moral no âmbito doméstico, familiar ou em qualquer relação íntima de afeto. Você pode buscar orientação gratuita pelo Ligue 180 (24 horas), na Defensoria Pública do DF (NUDEM) ou explorar os blocos de Benefícios, Direitos e Locais de Atendimento no menu ao lado.",
      citacoes: [
        { citacao: "Lei 11.340/2006, arts. 5º e 7º", data_acesso: "2026-11-05" },
      ],
    };
  }

  return {
    RAS_DF: RAS_DF,
    ETAPAS_PERFIL: ETAPAS_PERFIL,
    PERGUNTAS_ESPECIFICAS_BENEFICIOS: PERGUNTAS_ESPECIFICAS_BENEFICIOS,
    DETALHES_BENEFICIOS: DETALHES_BENEFICIOS,
    DIREITOS_LEIS: DIREITOS_LEIS,
    respostaLocalChat: respostaLocalChat,
  };
})();
