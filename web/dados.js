// Catálogo de dados da interface Rede Lilás:
// 1. Etapas do formulário de perfil (com "Prefiro não informar" em todos os campos)
// 2. Perguntas de autoavaliação de risco (baseadas no Fonar — Portaria Conjunta CNJ/CNMP 6/2025)
// 3. Regras de elegibilidade para Benefícios Sociais (3 federais + 1 distrital + complementares)
// 4. Guia de Direitos e Leis (Lei Maria da Penha, Lei 14.550/2023, Lei 14.674/2023, Minuto Seguinte)
// 5. Cópia local dos serviços da rede de proteção do DF (fallback caso esteja offline)
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
      pergunta: "Em qual Região Administrativa (RA) do DF você está?",
      ajuda: "Usamos apenas para ordenar os locais de atendimento mais próximos de você.",
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
        "Prefiro não informar",
      ],
    },
    {
      campo: "moradia",
      aba: "Moradia",
      icone: "home",
      pergunta: "Qual é a sua situação atual de moradia?",
      ajuda: "Não pedimos seu endereço completo.",
      motivo: "Ajuda a identificar direito ao Aluguel Social do DF e ao Auxílio-Aluguel da Lei Maria da Penha.",
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
      pergunta: "Qual é a renda mensal total aproximada da sua casa?",
      ajuda: "Considere a soma dos ganhos das pessoas que moram com você (sem contar a renda do agressor se você pretende sair ou já saiu).",
      motivo: "Os programas sociais usam a renda familiar total ou por pessoa para definir quem tem direito.",
      opcoes: [
        "Sem renda no momento",
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
      pergunta: "Qual é a sua faixa de idade ou condição de saúde?",
      ajuda: "Informação opcional e anônima.",
      motivo: "Mulheres com 65 anos ou mais ou pessoas com deficiência podem ter direito ao BPC/LOAS (1 salário mínimo mensal).",
      opcoes: [
        "18 a 29 anos",
        "30 a 59 anos",
        "60 a 64 anos",
        "65 anos ou mais",
        "Sou pessoa com deficiência (qualquer idade)",
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

  // Autoavaliação baseada no Fonar (Portaria Conjunta CNJ/CNMP nº 6/2025)
  var PERGUNTAS_FONAR = [
    {
      id: "ameaca_arma",
      bloco: "Bloco I — Histórico de Violência (Fonar item 1)",
      pergunta: "O(A) agressor(a) já ameaçou você ou algum familiar com arma de fogo ou faca?",
      pesoAlto: true,
      opcoes: [
        { rotulo: "Sim, com arma de fogo ou faca", risco: "alto" },
        { rotulo: "Sim, ameaçou de outra forma (sem arma)", risco: "medio" },
        { rotulo: "Não", risco: "baixo" },
        { rotulo: "Prefiro não responder", risco: "pular" },
      ],
    },
    {
      id: "agressao_grave",
      bloco: "Bloco I — Agressão Física Grave (Fonar item 2)",
      pergunta: "O(A) agressor(a) já tentou enforcar, sufocar, estrangular, queimar, atirar ou esfaquear você?",
      pesoAlto: true,
      opcoes: [
        { rotulo: "Sim, já praticou uma dessas agressões graves", risco: "alto" },
        { rotulo: "Já praticou tapas, empurrões, socos ou puxões de cabelo (item 2.1)", risco: "medio" },
        { rotulo: "Nenhuma agressão física", risco: "baixo" },
        { rotulo: "Prefiro não responder", risco: "pular" },
      ],
    },
    {
      id: "controle_stalking",
      bloco: "Bloco I — Controle e Perseguição (Fonar item 4)",
      pergunta: "O(A) agressor(a) persegue você, controla seu dinheiro/celular, proíbe visitas ou disse algo como 'se não for minha, não será de mais ninguém'?",
      pesoAlto: false,
      opcoes: [
        { rotulo: "Sim, disse frase de ameaça de morte ou persegue constantemente", risco: "alto" },
        { rotulo: "Sim, tem ciúme excessivo, controla dinheiro ou isola de amigos/família", risco: "medio" },
        { rotulo: "Não apresenta esses comportamentos", risco: "baixo" },
        { rotulo: "Prefiro não responder", risco: "pular" },
      ],
    },
    {
      id: "descumpriu_mpu",
      bloco: "Bloco I — Descumprimento de Medida Protetiva (Fonar item 5.1)",
      pergunta: "O(A) agressor(a) já descumpriu medida protetiva anteriormente ou as ameaças ficaram mais graves nos últimos meses?",
      pesoAlto: true,
      opcoes: [
        { rotulo: "Sim, já descumpriu medida protetiva", risco: "alto" },
        { rotulo: "As agressões ou ameaças ficaram mais frequentes/graves recentemente (item 6)", risco: "medio" },
        { rotulo: "Não", risco: "baixo" },
        { rotulo: "Prefiro não responder", risco: "pular" },
      ],
    },
    {
      id: "acesso_arma_suicidio",
      bloco: "Bloco II — Sobre o(a) Agressor(a) (Fonar itens 7, 9 e 11)",
      pergunta: "O(A) agressor(a) tem acesso fácil a arma de fogo, faz uso abusivo de álcool/drogas ou já ameaçou cometer suicídio?",
      pesoAlto: true,
      opcoes: [
        { rotulo: "Sim, tem acesso a arma de fogo ou já falou em suicídio", risco: "alto" },
        { rotulo: "Faz uso abusivo de álcool, drogas ou está com conflitos graves", risco: "medio" },
        { rotulo: "Não / Não sei", risco: "baixo" },
        { rotulo: "Prefiro não responder", risco: "pular" },
      ],
    },
    {
      id: "separacao_coabitacao",
      bloco: "Blocos III e IV — Ruptura e Moradia (Fonar itens 13, 22 e 24)",
      pergunta: "Você terminou ou tentou terminar a relação recentemente e ainda reside no mesmo imóvel com o(a) agressor(a)?",
      pesoAlto: false,
      opcoes: [
        { rotulo: "Sim, tentei terminar e ainda moramos juntos / preciso de abrigo", risco: "alto" },
        { rotulo: "Terminei recentemente, mas não moramos juntos", risco: "medio" },
        { rotulo: "Não", risco: "baixo" },
        { rotulo: "Prefiro não responder", risco: "pular" },
      ],
    },
  ];

  // Avalia elegibilidade aos benefícios com base no perfil salvo localmente
  function avaliarBeneficios(perfil) {
    var baixaRenda =
      perfil.renda === "Sem renda no momento" ||
      perfil.renda === "Até R$ 600 por mês" ||
      perfil.renda === "De R$ 601 a R$ 1.621 (até 1 salário mínimo)";

    var rendaAteDoisSalarios =
      baixaRenda || perfil.renda === "De R$ 1.622 a R$ 3.242 (até 2 salários mínimos)";

    var precisaMoradia =
      perfil.moradia === "Preciso sair de casa com urgência para me proteger" ||
      perfil.moradia === "Já saí do lar por causa da violência e pago aluguel / estou de favor" ||
      perfil.moradia === "Moro em imóvel alugado ou cedido sem o agressor";

    var temMedidaOuBO =
      perfil.medida_protetiva === "Sim, já tenho medida protetiva concedida pelo juiz" ||
      perfil.medida_protetiva === "Já pedi medida protetiva ou fiz Boletim de Ocorrência";

    var temCriancaPequena = perfil.filhos === "Sim, crianças de 0 a 6 anos";
    var temIdosaOuPcD =
      perfil.idade === "65 anos ou mais" ||
      perfil.idade === "Sou pessoa com deficiência (qualquer idade)" ||
      perfil.filhos === "Sim, filho(a) ou dependente com deficiência";

    return [
      {
        id: "aluguel-social-df",
        esfera: "Benefício Distrital (GDF)",
        titulo: "Aluguel Social para Mulheres Vítimas de Violência no DF",
        valor: "R$ 600,00 por mês (por até 6 meses, prorrogável por mais 6 meses)",
        baseLegal: "Lei Distrital nº 6.623/2020 · Decreto nº 45.989/2024 · Portaria SMDF nº 49/2026 (texto verificado em 05/11/2026)",
        status: rendaAteDoisSalarios && precisaMoradia ? "Alta compatibilidade com seu perfil" : "Pode se aplicar ao seu caso",
        tomStatus: rendaAteDoisSalarios && precisaMoradia ? "good" : "neutral",
        resumo:
          "Auxílio financeiro temporário custeado pela Secretaria da Mulher do DF para mulheres vítimas de violência doméstica que precisam deixar o lar e não possuem imóvel próprio em local seguro.",
        criterios: [
          "Renda familiar por pessoa de até meio salário mínimo OU renda familiar mensal total de até 2 salários mínimos (Portaria SMDF 49/2026, art. 5º, III).",
          "Concessão de Medida Protetiva de Urgência e impossibilidade de retorno ao lar sem risco.",
          "Residir no Distrito Federal (sem outro imóvel próprio seguro no DF).",
          "Atenção: não ter CadÚnico NÃO impede o pedido inicial — a inscrição no CadÚnico pode ser feita durante o acompanhamento (Portaria SMDF 49/2026, art. 15, V).",
        ],
        comoSolicitar: [
          "Se ainda não tiver Medida Protetiva, solicite na DEAM ou na Defensoria Pública (apenas seu depoimento já basta — Lei 14.550/2023).",
          "Procure um CEAM (102 Sul, Ceilândia ou Planaltina), a Casa da Mulher Brasileira de Ceilândia ou o CRAS/CREAS para o relatório multiprofissional.",
          "Leve documento de identificação (se tiver), número do processo/medida protetiva e comprovante ou declaração de residência e renda.",
        ],
        ondeBuscar: "Casa da Mulher Brasileira (Ceilândia), CEAMs da Secretaria da Mulher ou CRAS/CREAS da sua RA.",
      },
      {
        id: "auxilio-aluguel-lmp",
        esfera: "Benefício Federal (Medida Protetiva)",
        titulo: "Auxílio-Aluguel Judicial da Lei Maria da Penha",
        valor: "Valor fixado pelo Juizado (por até 6 meses)",
        baseLegal: "Lei Federal nº 11.340/2006, art. 23, VI (incluído pela Lei nº 14.674/2023 · verificado em 05/11/2026)",
        status: precisaMoradia || temMedidaOuBO ? "Alta compatibilidade com seu perfil" : "Direito previsto na Lei Maria da Penha",
        tomStatus: precisaMoradia || temMedidaOuBO ? "good" : "neutral",
        resumo:
          "O juiz do Juizado de Violência Doméstica pode determinar a concessão de auxílio-aluguel em razão de afastamento do lar, considerando a situação de vulnerabilidade social e econômica da ofendida.",
        criterios: [
          "Estar em situação de violência doméstica e familiar e precisar se afastar do lar do agressor.",
          "Encontrar-se em situação de vulnerabilidade social e econômica (Lei 11.340/2006, art. 23, VI).",
        ],
        comoSolicitar: [
          "Ao registrar a ocorrência na DEAM ou ser atendida pelo NUDEM/Defensoria Pública, peça expressamente a inclusão do pedido de Auxílio-Aluguel (art. 23, VI) nas Medidas Protetivas.",
          "Se você já tem processo de Medida Protetiva, a Defensoria Pública pode pedir ao juiz a inclusão desse benefício a qualquer momento.",
        ],
        ondeBuscar: "Defensoria Pública do DF (NUDEM ou núcleo da sua RA), DEAM ou Juizado de Violência Doméstica.",
      },
      {
        id: "bolsa-familia",
        esfera: "Benefício Federal",
        titulo: "Programa Bolsa Família + Adicionais para Crianças e Gestantes",
        valor: "Mínimo de R$ 600,00 por família + R$ 150 por criança (0 a 6 anos) + R$ 50 (7 a 17 anos / gestantes)",
        baseLegal: "Lei Federal nº 14.601/2023, arts. 1º a 15 (texto verificado em 05/11/2026)",
        status: baixaRenda ? "Alta compatibilidade com seu perfil" : "Verifique a renda por pessoa sem o agressor",
        tomStatus: baixaRenda ? "good" : "warm",
        resumo:
          "Transferência direta de renda para famílias com renda mensal por pessoa de até R$ 218,00. Se você saiu da casa do agressor, você pode retirar o nome dele do seu CadÚnico no CRAS para que a renda dele pare de contar!",
        criterios: [
          "Renda familiar mensal por pessoa (per capita) igual ou inferior a R$ 218,00 (Lei 14.601/2023, art. 5º).",
          "Inscrição atualizada no Cadastro Único (CadÚnico).",
          "Cumprimento das condicionalidades de saúde e educação das crianças (quando houver).",
        ],
        comoSolicitar: [
          "Compareça ao CRAS da sua Região Administrativa para fazer ou atualizar seu CadÚnico em núcleo familiar separado do agressor.",
          "Informe se há crianças de 0 a 6 anos (Benefício Primeira Infância de R$ 150) ou de 7 a 18 anos incompletos (Benefício Variável Familiar de R$ 50).",
        ],
        ondeBuscar: "CRAS (Centro de Referência de Assistência Social) mais próximo da sua Região Administrativa.",
      },
      {
        id: "bpc-loas",
        esfera: "Benefício Federal (LOAS)",
        titulo: "Benefício de Prestação Continuada (BPC / LOAS)",
        valor: "1 salário mínimo por mês (não exige ter contribuído ao INSS)",
        baseLegal: "Lei Federal nº 8.742/1993 (LOAS), art. 20 (texto verificado em 05/11/2026)",
        status: temIdosaOuPcD ? "Alta compatibilidade com seu perfil" : "Para idosas (65+) ou pessoas/filhos com deficiência",
        tomStatus: temIdosaOuPcD ? "good" : "neutral",
        resumo:
          "Garantia de 1 salário mínimo mensal à pessoa com deficiência (de qualquer idade, inclusive filhos) ou à pessoa idosa com 65 anos ou mais que comprove não possuir meios de prover a própria manutenção.",
        criterios: [
          "Ter 65 anos ou mais OU possuir deficiência de longo prazo (física, mental, intelectual ou sensorial) — vale para você ou para seu filho(a).",
          "Renda por pessoa do grupo familiar igual ou inferior a 1/4 do salário mínimo (com possibilidade de flexibilização judicial até 1/2 salário mínimo conforme gastos com saúde).",
          "Estar inscrita no CadÚnico (não precisa nunca ter pago INSS).",
        ],
        comoSolicitar: [
          "Faça ou atualize o CadÚnico no CRAS.",
          "Solicite o BPC pelo aplicativo/site Meu INSS, pelo telefone 135 ou com apoio do CRAS e da Defensoria Pública.",
        ],
        ondeBuscar: "CRAS da sua RA, Meu INSS (telefone 135) e Defensoria Pública do DF.",
      },
      {
        id: "prato-cheio-eventuais",
        esfera: "Complementares no DF",
        titulo: "Cartão Prato Cheio, Cartão Gás e Benefícios Eventuais do DF",
        valor: "R$ 250,00/mês (Prato Cheio) + auxílio gás bimestral + auxílio vulnerabilidade",
        baseLegal: "Lei Distrital nº 7.009/2021 · Decreto nº 42.873/2021 · Lei Distrital nº 5.165/2013 (verificado em 05/11/2026)",
        status: baixaRenda && temCriancaPequena ? "Prioridade para mães solo com crianças de 0 a 6 anos" : "Disponível via CRAS no DF",
        tomStatus: baixaRenda ? "good" : "neutral",
        resumo:
          "O Cartão Prato Cheio concede R$ 250 mensais para alimentação, com prioridade legal para famílias monoparentais chefiadas por mulheres com crianças de 0 a 6 anos (Decreto 42.873/2021, atualizado pelo Decreto 48.095/2025).",
        criterios: [
          "Renda familiar por pessoa de até meio salário mínimo no DF e situação de insegurança alimentar.",
          "Prioridade no atendimento para famílias monoparentais chefiadas por mulheres com crianças de 0 a 6 anos.",
        ],
        comoSolicitar: [
          "Procure o CRAS da sua Região Administrativa e solicite a avaliação de insegurança alimentar no SISC/CadÚnico.",
        ],
        ondeBuscar: "CRAS e CREAS da Secretaria de Desenvolvimento Social (SEDES/DF).",
      },
    ];
  }

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

  // Fallback local caso a usuária esteja sem internet ao abrir a aba de locais
  var REDE_FALLBACK = [
    {
      nome: "Casa da Mulher Brasileira de Ceilândia",
      tipo: "CMB",
      ra: "Ceilândia",
      endereco: "CNM 1, Bloco I, Lote 3, Ceilândia, Brasília - DF",
      cep: "72215-110",
      telefone: "(61) 3181-1474 / (61) 3181-2228 / (61) 3181-2233 / (61) 98312-0763 / (61) 99117-3406",
      horario: "24 horas, todos os dias (inclusive finais de semana e feriados)",
      data_verificacao: "2026-11-05",
    },
    {
      nome: "DEAM I - Delegacia Especial de Atendimento à Mulher I",
      tipo: "DEAM",
      ra: "Plano Piloto",
      endereco: "EQS 204/205, Asa Sul, Brasília - DF",
      cep: "70234-400",
      telefone: "(61) 3207-6172 / (61) 3207-6195 / (61) 3207-6212",
      horario: "24 horas, todos os dias (plantão permanente)",
      data_verificacao: "2026-11-05",
    },
    {
      nome: "DEAM II - Delegacia Especial de Atendimento à Mulher II",
      tipo: "DEAM",
      ra: "Ceilândia",
      endereco: "QNM 02, Área Especial, Conjunto G/H, Ceilândia, Brasília - DF",
      cep: "72210-020",
      telefone: "(61) 3207-7391 / (61) 3207-7408 / (61) 3207-7438 / (61) 3207-7410",
      horario: "24 horas, todos os dias (plantão permanente)",
      data_verificacao: "2026-11-05",
    },
    {
      nome: "CEAM 102 Sul - Centro Especializado de Atendimento à Mulher",
      tipo: "CEAM",
      ra: "Plano Piloto",
      endereco: "Estação do Metrô 102 Sul, Asa Sul, Plano Piloto, Brasília - DF",
      cep: "70330-000",
      telefone: "(61) 3224-0943 / (61) 3181-2245 / (61) 99183-6454",
      horario: "Segunda a sexta-feira, das 8h às 18h",
      data_verificacao: "2026-11-05",
    },
    {
      nome: "NUDEM / NAJ de Defesa das Mulheres - Defensoria Pública do Distrito Federal",
      tipo: "Defensoria",
      ra: "Plano Piloto",
      endereco: "Fórum José Júlio Leal Fagundes, Setor de Múltiplas Atividades Sul (SMAS), Trecho 3, Lotes 4/6, Bloco 4, Brasília - DF",
      cep: "70610-906",
      telefone: "(61) 98272-5123 / (61) 98108-1997 / (61) 2196-4461 / Disque 129",
      horario: "Segunda a sexta-feira, das 13h às 18h (presencial) e das 12h às 19h (remoto)",
      data_verificacao: "2026-11-05",
    },
  ];

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
    PERGUNTAS_FONAR: PERGUNTAS_FONAR,
    DIREITOS_LEIS: DIREITOS_LEIS,
    REDE_FALLBACK: REDE_FALLBACK,
    avaliarBeneficios: avaliarBeneficios,
    respostaLocalChat: respostaLocalChat,
  };
})();
