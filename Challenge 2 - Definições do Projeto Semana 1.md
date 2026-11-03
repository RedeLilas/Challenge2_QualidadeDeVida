# Challenge 2 — Definições do Projeto (Semana 1)

**Data:** 29 de outubro de 2026 (atualizado em 3 de novembro de 2026: escopo DF, validação sem entrevistas e stack; ver `ROADMAP.md` e `openspec/`)  
**Equipe:** Ana Beatriz, Léo Alec, Rafaella Borges, Túlio Celeri e Vítor Gonçalves  
**Big Idea:** Qualidade de Vida — *"Empoderando pessoas com IA para compreender melhor, decidir melhor e viver melhor."*

Nossa solução de IA apoia mulheres em situação ou risco de violência doméstica e de gênero a identificar violações de direitos, reconhecer a gravidade da sua situação por triagem de risco e mapear benefícios sociais e pontos de acolhimento da rede de proteção e de saúde no Distrito Federal. A eficácia será validada pela precisão jurídica e assistencial das orientações, pela ausência de subnotificação de risco grave (alerta imediato para o 190) e pela clareza prática dos encaminhamentos.

---

## 1. Cenário escolhido

Mulheres em situação de violência doméstica e familiar muitas vezes não reconhecem o que vivem como violência, desconhecem os direitos e benefícios que a lei lhes garante e não sabem a qual serviço recorrer nem com que urgência. A decisão costuma ser tomada sozinha, pelo celular e em um momento curto de privacidade, com a informação espalhada entre leis, sites de órgãos públicos e serviços diferentes. Uma orientação errada ou atrasada pode significar subestimar um perigo real ou perder um apoio a que ela tem direito.

- **Domínio:** proteção social e segurança de mulheres em situação de violência doméstica: Lei Maria da Penha, benefícios sociais, rede de proteção e rede de saúde.
- **Abrangência:** Distrito Federal. A orientação jurídica usa a legislação federal (Lei Maria da Penha, Fonar, benefícios federais) e as normas distritais aplicáveis; o mapeamento de serviços cobre apenas a rede do DF, localizada por Região Administrativa ou CEP. Fora do DF, a orientação jurídica e a triagem continuam disponíveis e o sistema indica o Ligue 180.
- **Decisão que a IA vai apoiar:** reconhecer se o que ela vive é violência prevista em lei, entender quais direitos e benefícios provavelmente se aplicam e o que falta para acessá-los, e definir onde e com que urgência buscar atendimento, priorizando o 190 diante de risco imediato.
- **Por que este cenário:** problema de grande escala, com legislação que muda com frequência; há fontes públicas, oficiais e datadas (Lei Maria da Penha, leis dos benefícios, Formulário Nacional de Avaliação de Risco e CNES). Por razões éticas, não haverá testes com vítimas reais, e não haverá entrevistas com profissionais da rede: a validação usará casos fictícios com gabarito escrito pela equipe a partir de fontes oficiais, julgados por um LLM juiz com revisão em dupla de uma amostra, e testes de usabilidade com colegas do curso.

---

## 2. Problema

**Declaração do problema:** mulheres em situação de violência doméstica ou vulnerabilidade precisam de orientação jurídica, acesso a benefícios e atendimento de saúde urgente, mas enfrentam desinformação, burocracia complexa e isolamento, o que leva à omissão de socorro, à perpetuação do ciclo de violência e ao desamparo social.

- **Evidências:** dados do Fórum Brasileiro de Segurança Pública e do Ministério das Mulheres apontam altos índices de violência de gênero e subnotificação, além de barreiras informacionais no acesso a auxílios e medidas protetivas.
- **Como é resolvido hoje:** atendimento telefônico genérico (Ligue 180, 190), busca manual em delegacias e centros de referência (CEAM, DEAM) ou triagens presenciais demoradas, muitas vezes inacessíveis para mulheres isoladas.
- **Fora do escopo:** o sistema não substitui o atendimento policial de emergência (190 em caso de risco iminente) e não realiza petições judiciais. O mapa de serviços não cobre outras unidades da federação.

---

## 3. Mapa de stakeholders

A Rede Lilás serve diretamente à usuária, mas só funciona alinhada à rede de enfrentamento e às fontes oficiais. O agressor entra como stakeholder adverso e orienta as decisões de segurança.

| Stakeholder | Papel e expectativa | Influência | Interesse | Como envolver |
| :--- | :--- | :--- | :--- | :--- |
| **Mulheres em situação de violência (usuária primária)** | Tomam a decisão; querem reconhecer a violência, saber direitos, onde ser atendidas e com que urgência, sem se expor | Alta | Alto | Representadas pelas personas e por casos fictícios; teste de usabilidade (SUS) com colegas do curso, sem relatos pessoais |
| **Pessoas de confiança (usuária secundária)** | Muitas vezes buscam informação primeiro; querem saber como apoiar e encaminhar | Média | Alto | Teste de usabilidade com colegas; modo "estou ajudando outra pessoa" |
| **Agressor (adverso)** | Pode controlar o celular e reagir se descobrir a busca por ajuda | Alta | Alto | Não é envolvido: saída rápida, sem histórico, nome discreto |
| **Especialistas (advogadas, psicólogas, assistentes sociais, UnB)** | Esperam orientação fiel à lei e ao formulário de risco, sem substituir o atendimento profissional | Alta | Alto | Não envolvidos diretamente (sem entrevistas): o conhecimento vem de fontes oficiais citadas; gabarito escrito pela equipe e julgado por LLM juiz com revisão em dupla |
| **Rede de assistência e benefícios (Casa da Mulher Brasileira, CEAM, CRAS/CREAS, CadÚnico, INSS)** | Acolhem e concedem benefícios; querem mulheres informadas e sem falsas expectativas | Alta | Alto | Pesquisa documental das regras de elegibilidade e dos serviços do DF; aviso de que a concessão depende do órgão |
| **Segurança e justiça (190, DEAM, Defensoria, MP, juizados)** | Recebem denúncias e concedem medidas protetivas; querem encaminhamentos corretos | Alta | Médio | Pesquisa documental (PCDF, Defensoria Pública do DF, TJDFT, MPDFT) para a lista curada de serviços |
| **Saúde (SUS, estabelecimentos do CNES)** | Atendem violência sexual; querem encaminhamento ao serviço certo | Média | Médio | Mostrar a competência do dado e conferir uma amostra |
| **Regulação de privacidade (LGPD/ANPD)** | Exige minimização de dados e controle pela titular | Alta | Baixo | Perfil sem nome ou documento, local e apagável |
| **Professores / avaliadores** | Esperam problema bem entendido, decisões justificadas e métricas objetivas | Alta | Alto | Entregas semanais e feedback |

**Leitura do mapa:** gerenciar de perto usuárias, agressor (como ameaça) e avaliadores; representar especialistas e rede de assistência pelas fontes oficiais, já que não haverá entrevistas; manter satisfeitos LGPD e rede de segurança e justiça.

---

## 4. Personas

| Atributo | Persona 1 (primária): Juliana | Persona 2 (secundária): Camila |
| :--- | :--- | :--- |
| **Perfil e contexto** | 32 anos, diarista sem carteira assinada, mãe de 2 filhos. O companheiro controla seu dinheiro e ameaça que ela "ficará sem nada e sem os filhos" se sair de casa | 24 anos, estudante universitária e atendente de telemarketing. Mora com o namorado há 1 ano: ciúme excessivo, conferência de mensagens, empurrões ocasionais |
| **Objetivos e decisão** | "Devo sair de casa agora? Tenho direito a auxílio financeiro e onde posso buscar ajuda?" | "O que ele faz comigo é crime? Como estabeleço limites legais e a quem recorrer?" |
| **Dores** | Medo de ficar sem renda; desconhece as leis; vergonha de se expor no balcão de um órgão público | Acha que suas queixas "são exagero"; medo de represálias; sem dinheiro para advogado |
| **Tecnologia** | Baixa a média: WhatsApp, busca por voz, celular compartilhado com os filhos | Alta: usa redes sociais e navegador no smartphone |
| **Citação** | *"Eu não saio de casa porque não tenho para onde levar meus filhos e acho que vou passar fome."* | *"Ele nunca me bateu no rosto, só quebrou minhas coisas e me humilhou... isso conta como agressão?"* |
| **Como a solução ajuda** | Orienta sobre CadÚnico/Bolsa Família, auxílio-aluguel (Lei 14.674/2023), serviços da rede de proteção e de saúde do DF e medidas protetivas, sem exigir CPF | Classifica as violências psicológica e patrimonial (art. 7º da Lei Maria da Penha), aplica a triagem de risco e alerta para a escalada do perigo |

---

## 5. Requisitos

### Funcionais

| ID | Requisito (justificativa) | Prioridade |
| :--- | :--- | :--- |
| **RF01** | Perfil opcional sem nome ou documento: Região Administrativa ou CEP, renda, CadÚnico, INSS, filhos, medida protetiva (personaliza com o mínimo de dados) | Essencial |
| **RF02** | Orientador jurídico: RAG sobre a Lei Maria da Penha, citando o artigo (respostas verificáveis, menos alucinação) | Essencial |
| **RF03** | Agente de benefícios: regras de elegibilidade que classificam cada benefício como provável, dependente de decisão judicial ou não aplicável, com o que falta e onde pedir (regras auditáveis) | Essencial |
| **RF04** | Agente de triagem: perguntas do Formulário Nacional de Avaliação de Risco que definem o nível de urgência (instrumento oficial) | Essencial |
| **RF05** | Detectar risco imediato em qualquer ponto e orientar o 190 antes de qualquer outra resposta (risco central do projeto) | Essencial |
| **RF06** | Agente de rede de atendimento: serviços do DF mais próximos por RA ou CEP, incluindo a rede de proteção (Casa da Mulher Brasileira, CEAMs, DEAMs, Defensoria) e os estabelecimentos do CNES com atenção à violência sexual, com a fonte e a data do dado | Essencial |
| **RF07** | Saída rápida e opção de apagar perfil e conversa (segurança diante do agressor) | Essencial |
| **RF08** | Chat com perguntas sugeridas e orquestrador que encaminha cada pergunta ao agente certo (sistema multiagentes, semana 4) | Importante |
| **RF09** | Perguntas por áudio e leitura de documentos fotografados, sem armazenar a imagem (multimodalidade, semana 5) | Desejável |

### Não funcionais

| ID | Categoria | Requisito (mensurável) | Prioridade |
| :--- | :--- | :--- | :--- |
| **RNF01** | Desempenho | Orientação de risco imediato em até 2 s, por regra; demais respostas em até 10 s em 95% dos casos | Essencial |
| **RNF02** | Privacidade (LGPD) | Sem nome ou CPF; perfil só no dispositivo e apagável; nenhum dado usado para treinar modelos | Essencial |
| **RNF03** | Rastreabilidade | 100% das respostas jurídicas e de benefícios com fonte e data; até 5% de afirmações sem suporte | Essencial |
| **RNF04** | Segurança da usuária | Nome e ícone discretos, sem notificações nem histórico visível, saída em 1 toque | Essencial |
| **RNF05** | Transparência | Diferenciar direito provável de confirmado; avisar que a triagem não substitui avaliação profissional | Essencial |
| **RNF06** | Acessibilidade e atualização | Linguagem simples, celular básico e conexão lenta (WCAG 2.1 AA); base legal revisada mensalmente | Importante |

---

## 6. Riscos e limitações

| Risco | Categoria | Probab. | Impacto | Mitigação |
| :--- | :--- | :--- | :--- | :--- |
| **Respostas incorretas ou alucinadas sobre direitos e violência** | Técnico | Média | Alto | RAG restrito a textos legais do Planalto; cita lei, artigo e data; não responde sem trecho que sustente a resposta |
| **Regras de benefícios desatualizadas após mudança de norma** | Técnico | Alta | Alto | Cada regra guarda norma e vigência; revisão mensal; exibir data da última verificação |
| **Triagem subestimar um perigo real** | Técnico | Média | Alto | Regras auditáveis e conservadoras: resposta de risco alto leva ao 190; testes com casos de risco |
| **Dados do CNES desatualizados ou sem coordenadas** | Técnico | Média | Médio | Competência mais recente com mês e ano; geocodificar por CEP (CNEFE); orientar a confirmar por telefone |
| **Viés de acesso: linguagem difícil ou cobertura desigual entre regiões** | Ético | Média | Alto | Linguagem simples e testes com perfis variados; sem serviço na Região Administrativa, indicar o mais próximo no DF; fora do DF, indicar o Ligue 180 |
| **Falsa expectativa sobre benefícios** | Ético | Média | Médio | Separar "provável" de "confirmado"; listar requisitos que faltam; aviso de que a concessão depende do órgão |
| **Ausência de validação por especialistas e usuárias reais** | Metodológico | Alta | Alto | Gabarito sempre com norma e artigo; LLM juiz com revisão em dupla de 20%; limitação declarada no relatório final |
| **Transferência internacional de dados ao usar o DeepSeek em produção (LGPD, art. 33)** | Ético/Legal | Alta | Alto | Decisão registrada até 06/11: anonimizar antes do envio, usar pesos abertos em outro provedor ou declarar o risco e usar só casos fictícios |

---

## 7. Premissas

- As usuárias têm acesso a um celular com internet por alguns minutos com privacidade. **Validar com:** não validável sem usuárias reais; a PWA é leve e funciona com conexão lenta, e a premissa é declarada como limitação.
- Parte das usuárias aceita informar dados básicos se forem anônimos e opcionais. **Validar com:** não validável sem usuárias reais; mitigação: todas as funções funcionam sem perfil.
- Os critérios dos benefícios podem ser escritos como regras a partir do texto legal. **Validar com:** modelagem de 3 benefícios federais e 1 distrital, testada com casos fictícios e gabarito da equipe (semana 3).
- O Formulário Nacional de Avaliação de Risco pode ser adaptado com segurança para autoaplicação. **Validar com:** classificação de cada pergunta do modelo vigente do Fonar quanto à adaptabilidade (semana 2) e regras conservadoras: na dúvida, o nível mais alto.
- RAG reduz erros em relação ao LLM puro nas perguntas jurídicas. **Validar com:** comparação LLM x RAG (semana 3).

---

## 8. Métricas de sucesso

| Métrica | Como medir (linha de base) | Meta | Quando |
| :--- | :--- | :--- | :--- |
| **Precisão jurídica** | 50 perguntas de teste com gabarito e fonte escritos pela equipe, julgadas por LLM juiz com revisão em dupla de 20% (linha de base: LLM sem RAG) | ≥ 90% corretas | Semana 3 |
| **Fidelidade às fontes** | Respostas com norma e data corretas; afirmações sem suporte (LLM sem RAG) | 100% citadas; ≤ 5% sem suporte | Semana 3 |
| **Acurácia de elegibilidade** | Concordância com o gabarito da equipe (com norma e artigo) em casos fictícios | ≥ 90% | Semana 4 |
| **Sensibilidade para risco alto** | Casos fictícios de risco alto ou imediato classificados como tal | 100% (nenhum falso negativo) | Semana 4 |
| **Tempo até o 190** | Tempo entre o sinal de risco imediato e a orientação exibida | ≤ 2 s | Semana 6 |
| **Usabilidade** | System Usability Scale aplicada a colegas do curso com roteiros de casos fictícios | Escala ≥ 70 | Semana 7 |

---

## 9. Guiding questions

- **Usuárias:** quem são e como agrupá-las em personas? Estão dispostas a informar dados sobre a violência? Chat com perguntas sugeridas ou fluxo guiado?
- **Dados:** quais dados jurídicos, de saúde e do CadÚnico são necessários? Os documentos são bem estruturados para RAG e regras? Como mantê-los atualizados?
- **Tecnologia:** como personalizar a conversa com o perfil sem guardar dados além do necessário? Como o orquestrador escolhe o agente? Como tornar a plataforma multimodal com segurança?
- **Avaliação:** quais métricas usar para as respostas do chatbot e quem monta e julga o gabarito?
- **Ética e segurança:** como proteger a usuária se o agressor tiver acesso ao celular? Como tratar os dados segundo a LGPD? Quando parar de orientar e mandar acionar o 190?

---

## 10. Essential Question da equipe

> **Como podemos usar IA generativa e sistemas baseados em regras para empoderar mulheres em situação de vulnerabilidade a identificar violações de direitos, reconhecer níveis de risco e acessar com segurança a rede de proteção e os benefícios sociais a que têm direito?**

**Por que esta pergunta:** ela parte da Big Idea (qualidade de vida e viver melhor) e ataca a raiz do problema: a assimetria de informação e a dependência financeira e emocional que impedem mulheres de romper o ciclo da violência. Ao unir inteligência jurídica (compreender) com suporte socioeconômico e avaliação de risco estruturada (decidir), a solução cria uma ponte segura entre a vítima e as políticas públicas existentes.

---

## Referências

- BRASIL. **Lei nº 11.340, de 7 de agosto de 2006.** Cria mecanismos para coibir a violência doméstica e familiar contra a mulher (Lei Maria da Penha). Brasília, DF: Presidência da República, 2006. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm. Acesso em: 29 out. 2026.
- BRASIL. **Lei nº 13.709, de 14 de agosto de 2018.** Lei Geral de Proteção de Dados Pessoais (LGPD). Brasília, DF: Presidência da República, 2018. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm. Acesso em: 29 out. 2026.
- BRASIL. **Lei nº 14.149, de 5 de maio de 2021.** Institui o Formulário Nacional de Avaliação de Risco, a ser aplicado à mulher vítima de violência doméstica e familiar. Brasília, DF: Presidência da República, 2021. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14149.htm. Acesso em: 29 out. 2026.
- BRASIL. **Lei nº 14.601, de 19 de junho de 2023.** Institui o Programa Bolsa Família. Brasília, DF: Presidência da República, 2023. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2023/lei/l14601.htm. Acesso em: 29 out. 2026.
- BRASIL. **Lei nº 14.674, de 14 de setembro de 2023.** Altera a Lei nº 11.340/2006 para dispor sobre auxílio-aluguel a ser concedido pelo juiz em decorrência de situação de vulnerabilidade social e econômica da ofendida afastada do lar. Brasília, DF: Câmara dos Deputados, 2023. Disponível em: https://www2.camara.leg.br/legin/fed/lei/2023/lei-14674-14-setembro-2023-794705-norma-pl.html. Acesso em: 29 out. 2026.
- BRASIL. Ministério da Saúde. **Cadastro Nacional de Estabelecimentos de Saúde (CNES).** Brasília, DF: DATASUS. Disponível em: https://cnes.datasus.gov.br/. Acesso em: 29 out. 2026.
- BRASIL. Ministério da Saúde. **Como acessar o Cadastro Nacional de Estabelecimentos de Saúde.** Brasília, DF: Ministério da Saúde. Disponível em: https://www.gov.br/saude/pt-br/acesso-a-informacao/faq/estabelecimentos-de-saude/como-acessar-o-cadastro-nacional. Acesso em: 29 out. 2026.
- BROOKE, J. SUS: a "quick and dirty" usability scale. In: JORDAN, P. W. et al. (ed.). **Usability evaluation in industry.** London: Taylor & Francis, 1996. p. 189-194.
- CONSELHO NACIONAL DE JUSTIÇA; CONSELHO NACIONAL DO MINISTÉRIO PÚBLICO. **Portaria Conjunta nº 6, de 25 de julho de 2025.** Dispõe sobre alterações no modelo do Formulário Nacional de Avaliação de Risco (Fonar), anexo à Resolução Conjunta CNJ/CNMP nº 5/2020. Brasília, DF, 2025. Disponível em: https://mpce.mp.br/wp-content/uploads/2025/10/PORTARIA-CONJUNTA-No-6-DE-25-DE-JULHO-DE-2025-Dispoe-sobre-alteracoes-no-modelo-do-FONAR.pdf. Acesso em: 29 out. 2026.
- FÓRUM BRASILEIRO DE SEGURANÇA PÚBLICA. **20º Anuário Brasileiro de Segurança Pública: 2026.** São Paulo: FBSP, 2026. Disponível em: https://publicacoes.forumseguranca.org.br/items/bb542342-3cf8-47a5-a51d-a0eb911914b9. Acesso em: 29 out. 2026.
- INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA (IBGE). **Cadastro Nacional de Endereços para Fins Estatísticos (CNEFE).** Rio de Janeiro: IBGE. Disponível em: https://www.ibge.gov.br/. Acesso em: 29 out. 2026.
- LEWIS, P. et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. In: **Advances in Neural Information Processing Systems 33 (NeurIPS 2020).** 2020. Disponível em: https://arxiv.org/abs/2005.11401. Acesso em: 29 out. 2026.
- W3C. **Web Content Accessibility Guidelines (WCAG) 2.1.** 2018. Disponível em: https://www.w3.org/TR/WCAG21/. Acesso em: 29 out. 2026.

