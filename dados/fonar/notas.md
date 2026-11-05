# Notas sobre o Formulário Nacional de Avaliação de Risco (Fonar)

- **Data de verificação:** `2026-11-05`
- **Fontes oficiais:**
  - **Lei nº 14.149, de 5 de maio de 2021:** https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14149.htm
  - **Portaria Conjunta CNJ/CNMP nº 6, de 25 de julho de 2025** (atualiza o anexo da Resolução Conjunta CNJ/CNMP nº 5/2020): https://atos.cnj.jus.br/atos/detalhar/6324
  - **Anexo Único compilado no CNJ (modelo vigente de 2025):** https://atos.cnj.jus.br/files/compilado190716202508066893a7e440efa.pdf
  - **Portal do Fonar no CNJ:** https://www.cnj.jus.br/programas-e-acoes/violencia-contra-a-mulher/formulario-nacional-de-avaliacao-de-risco/

---

## Critérios de Classificação para Autoaplicação na Rede Lilás

Conforme o `design.md` da mudança `s2-fontes-df` e a spec `triagem-risco`, cada item do modelo vigente do Fonar (Anexo da Portaria Conjunta CNJ/CNMP nº 6/2025, com questões numeradas de **1 a 24** e **8 subitens** na Parte I, além dos itens **1 a 8** da Parte II) é classificado em uma das três categorias abaixo:

1. **`adaptável para autoaplicação`**: Pergunta objetiva sobre fatos concretos vivenciados pela mulher, que pode ser respondida diretamente por ela (ou por pessoa de confiança no modo "ajudando outra pessoa") em linguagem acolhedora, sem exigir jargão técnico.
2. **`adaptável com cuidado`**: Pergunta sobre temas sensíveis (violência sexual, saúde mental, suicídio, filhos ou percepção subjetiva de território/isolamento) que pode compor a triagem **desde que** tenha redação acolhedora, aviso de que a resposta é opcional (regra conservadora: pular não reduz o nível de risco) e acionamento imediato de canais de emergência quando pertinente.
3. **`não adaptável`**: Item que depende de avaliação técnica presencial de profissional capacitado (Parte II do Fonar), consulta a sistemas policiais/judiciais ou coleta de dados identificadores/demográficos incompatíveis com a diretriz de privacidade e ausência de cadastro da Rede Lilás.

---

## Parte I — Identificação das Partes e Questões Objetivas (Blocos I a IV)

### Identificação das Partes e Vínculo (Cabeçalho da Parte I)

| Item | Descrição no modelo vigente do Fonar (2025) | Classificação | Motivo e diretriz para a S3 (`s3-triagem-fonar`) |
| :--- | :--- | :--- | :--- |
| **Identificação da Vítima e do(a) Agressor(a)** | Nome da vítima, nome social, CPF/passaporte, data de nascimento, idade, identidade de gênero, orientação sexual, escolaridade, nacionalidade e dados equivalentes do(a) agressor(a), além de número do BO e processo. | `não adaptável` | Viola os requisitos da Rede Lilás de **ausência de cadastro obrigatório**, **não solicitar CPF/nome** e **ausência de histórico persistente** para segurança da vítima (`privacidade-seguranca`). |
| **Vínculo entre as Partes** | *Vínculo do(a) agressor(a) com a vítima: Relacionamento afetivo (Marido ou Esposo(a) / Companheiro(a) / Namorado(a) / Ex-marido ou ex-esposo(a) / Ex-companheiro(a) / Ex-namorado(a) / Outro); Relacionamento familiar (Pai / Mãe / Padrasto / Madrasta / Irmão(ã) / Filho(a) / Avô ou avó / Tio(a) / Primo(a) / Cunhado(a) / Sobrinho(a) / Enteado(a) / Genro ou nora / Outro); Relacionamento doméstico (Pessoa que reside no mesmo lar / Ex-residente do lar / Cuidador(a) / Empregado(a) doméstico(a) / Outro).* | `adaptável para autoaplicação` | Fato objetivo essencial para verificar o enquadramento na Lei Maria da Penha (art. 5º, I, II e III da Lei 11.340/2006) sem exigir nomes ou documentos. |

---

### Bloco I — Sobre o histórico de violência

| Nº | Pergunta no modelo vigente do Fonar (texto literal de 2025) | Classificação | Motivo e diretriz para a S3 (`s3-triagem-fonar`) |
| :--- | :--- | :--- | :--- |
| **1** | *1. O(A) agressor(a) já ameaçou você ou algum familiar com a finalidade de atingi-la? (Sim, com arma de fogo / Sim, com faca / Sim, de outra forma. Especifique / Não)* | `adaptável para autoaplicação` | Fator crítico de letalidade; pergunta direta sobre fato objetivo. Resposta afirmativa com arma de fogo ou faca deve elevar o risco para **alto** imediatamente. |
| **2** | *2. O(A) agressor(a) já praticou alguma(s) das seguintes formas graves de agressão física contra você? (Queimadura / Enforcamento / Sufocamento / Estrangulamento / Tiro / Afogamento / Facada / Paulada / Outro. Especifique / Nenhuma agressão física)* | `adaptável para autoaplicação` | Fato concreto de altíssima letalidade; qualquer marcação positiva neste item deve classificar o risco como **alto** imediatamente. |
| **2.1** | *2.1. O(A) agressor(a) já praticou alguma(s) destas agressões físicas contra você? (Soco / Chute / Tapa / Empurrão / Puxão de cabelo / Outro. Especifique / Nenhuma agressão física)* | `adaptável para autoaplicação` | Pergunta objetiva sobre agressões físicas; permite identificar violência física mesmo quando não houve emprego de meio letal do item 2. |
| **2.2** | *2.2. Você necessitou de atendimento médico e/ou internação após algumas dessas agressões? (Sim / Não / Prefiro não informar)* | `adaptável para autoaplicação` | Indicador objetivo de gravidade física pregressa; já inclui a opção "Prefiro não informar" no próprio modelo de 2025. |
| **3** | *3. O(A) agressor(a) já obrigou você a ter relações sexuais ou praticar atos sexuais contra a sua vontade? (Sim / Não / Não sei)* | `adaptável com cuidado` | Tema altamente sensível e potencialmente revitimizante. Deve permitir pular a pergunta sem reduzir o risco e, se afirmativa (especialmente nas últimas 72h), priorizar orientação da Lei 12.845/2013 (Minuto Seguinte). |
| **4** | *4. O(A) agressor(a) já teve algum destes comportamentos? (Disse algo parecido com: "se não for minha, não será de mais ninguém" / Perturbou, perseguiu ou vigiou você nos locais que frequenta / Proibiu você de visitar familiares ou amigos / Proibiu você de trabalhar ou estudar / Fez telefonemas, enviou mensagens pelo celular ou e-mails de forma insistente / Impediu você de ter acesso a dinheiro, conta bancária, documentos pessoais ou outros bens / Teve outros comportamentos de ciúme excessivo ou controle / Nenhum comportamento de ciúme excessivo ou controle)* | `adaptável para autoaplicação` | Excelente para autoaplicação; conecta diretamente a triagem de risco à identificação de perseguição (*stalking*, art. 147-A do CP) e de violência psicológica e patrimonial (art. 7º, II e IV da Lei 11.340/2006). |
| **5** | *5. Você já registrou ocorrência policial ou solicitou medida protetiva de urgência contra o(a) agressor(a)? (Sim, registrei ocorrência policial e solicitei medida protetiva de urgência / Sim, registrei apenas ocorrência policial / Sim, solicitei apenas medida protetiva de urgência / Não, nunca registrei ocorrência ou solicitei medida protetiva de urgência)* | `adaptável para autoaplicação` | Pergunta objetiva sobre histórico de busca institucional; útil também para orientar os próximos passos na DEAM, Defensoria ou Juizado. |
| **5.1** | *5.1. O(A) agressor(a) já descumpriu medida protetiva de urgência anteriormente? (Sim / Não / Não sei)* | `adaptável para autoaplicação` | Forte preditor de reincidência grave e crime autônomo (art. 24-A da Lei 11.340/2006). Se afirmativo, eleva o nível de risco para **alto**. |
| **6** | *6. As agressões ou ameaças do(a) agressor(a) se tornaram mais frequentes e/ou mais graves nos últimos 12 meses? (Sim, ficaram mais frequentes e/ou mais graves / Não houve aumento da frequência e intensidade das agressões e/ou ameaças / Não sei)* | `adaptável para autoaplicação` | Mede diretamente a escalada recente da violência de forma simples e compreensível. |

---

### Bloco II — Sobre o(a) agressor(a)

| Nº | Pergunta no modelo vigente do Fonar (texto literal de 2025) | Classificação | Motivo e diretriz para a S3 (`s3-triagem-fonar`) |
| :--- | :--- | :--- | :--- |
| **7** | *7. O(A) agressor(a) faz uso abusivo de álcool ou de drogas ou de medicamentos? (Sim: Álcool / Drogas / Medicamentos / Não faz uso das substâncias listadas / Não sei)* | `adaptável para autoaplicação` | Fator de risco objetivo observado pela vítima no convívio diário, com opção "Não sei". |
| **8** | *8. O(A) agressor(a) tem alguma doença mental comprovada por avaliação médica? (Sim, e faz uso de medicação / Sim, e não faz uso de medicação / Não / Não sei)* | `adaptável com cuidado` | A usuária frequentemente desconhece diagnóstico médico formal; na adaptação, deve preservar a opção "Não sei" e não exigir comprovação clínica. |
| **9** | *9. O(A) agressor(a) já tentou suicídio ou falou em suicidar-se? (Sim, já tentou suicídio / Sim, já falou em suicidar-se, mas nunca tentou / Não, nunca tentou nem falou sobre suicídio / Não sei)* | `adaptável com cuidado` | Indicador documentado de risco de feminicídio seguido de suicídio. Exige linguagem cuidadosa e opção "Não sei". |
| **10** | *10. O(A) agressor(a) está desempregado(a) ou tem dificuldades financeiras? (Sim / Não / Não sei)* | `adaptável para autoaplicação` | Fator situacional objetivo de estresse e escalada de risco doméstico. |
| **11** | *11. O(A) agressor(a) tem fácil acesso a arma de fogo? (Sim / Não / Não sei / Prefiro não informar)* | `adaptável para autoaplicação` | Um dos preditores mais fortes de letalidade no Fonar. Resposta "Sim" deve acionar classificação conservadora de risco **alto**. |
| **12** | *12. O(A) agressor(a) já ameaçou ou agrediu seus(suas) filhos(as), outros familiares, outras parceiras íntimas, amigos(as), colegas de trabalho, pessoas desconhecidas ou animais de estimação? (Sim: Filhos(as) / Outros familiares / Animais de estimação / Outras parceiras íntimas / Outras pessoas / Não / Não sei)* | `adaptável para autoaplicação` | Pergunta objetiva que identifica padrão generalizado de violência e intimidação indireta. |
| **12.1** | *12.1. Você tem conhecimento de registro de ocorrência policial e/ou medida protetiva de urgência contra ele/ela por essas violências? (Sim / Não)* | `adaptável para autoaplicação` | Pergunta objetiva complementar ao item 12 sobre reincidência contra terceiros ou outras parceiras. |

---

### Bloco III — Sobre você

| Nº | Pergunta no modelo vigente do Fonar (texto literal de 2025) | Classificação | Motivo e diretriz para a S3 (`s3-triagem-fonar`) |
| :--- | :--- | :--- | :--- |
| **13** | *13. Você terminou, tentou ou manifestou intenção de terminar com o(a) agressor(a) recentemente? (Sim, terminei recentemente / Sim, tentei terminar, mas ainda estou na relação / Sim, manifestei intenção de terminar / Não)* | `adaptável para autoaplicação` | Momento crítico de maior letalidade (ruptura ou tentativa de ruptura do relacionamento); pergunta direta e essencial para a triagem. |
| **14** | *14. Você tem filhos? (Sim, de outro relacionamento. Quantos? / Sim, com o(a) agressor(a). Quantos? / Não possuo filhos)* | `adaptável para autoaplicação` | Pergunta objetiva que serve simultaneamente à triagem de risco e à elegibilidade para benefícios sociais. |
| **14.1** | *14.1. Qual a faixa etária de seus filhos? Se tiver mais de um filho, pode assinalar mais de uma opção: (0 a 11 anos / 12 a 17 anos / A partir de 18 anos)* | `adaptável para autoaplicação` | Fato objetivo essencial para avaliar vulnerabilidade de dependentes e adicionais do Bolsa Família (Lei 14.601/2023). |
| **14.2** | *14.2. Algum de seus filhos é pessoa com deficiência? (Sim. Quantos / Não)* | `adaptável para autoaplicação` | Fato objetivo relevante para priorização protetiva e elegibilidade ao BPC/LOAS (Lei 8.742/1993). |
| **14.3** | *14.3. Estão vivendo algum conflito com relação à guarda dos filhos, visitas ou pagamento de pensão pelo(a) agressor(a)? (Sim / Não / Não sei)* | `adaptável para autoaplicação` | Fato objetivo que indica ponto de contato forçado com o agressor e necessidade de atendimento pela Defensoria Pública. |
| **14.4** | *14.4. Seu(s) filho(s) já presenciaram ato(s) de violência do(a) agressor(a) contra você? (Sim / Não / Não sei)* | `adaptável com cuidado` | Pergunta sensível que pode gerar sentimento de culpa ou receio na mãe; exige tom acolhedor e esclarecimento de que visa apenas proteger a família. |
| **15** | *15. Você sofreu algum tipo de violência durante a gravidez ou até 18 meses após o parto? (Sim, estou grávida atualmente e sofro violência / Sim, tive filho(a) nos últimos 18 meses e sofro violência atualmente / Sim, sofri violência durante a gravidez ou nos 18 meses após o parto, mas não atualmente / Não sofri violência nesses períodos)* | `adaptável para autoaplicação` | Unifica no modelo de 2025 a verificação de gestação/puerpério atual e violência nesse período, relevante tanto para agravamento de risco quanto para benefícios. |
| **16** | *16. Se você está em um novo relacionamento, percebeu que as ameaças ou agressões físicas aumentaram em razão disso? (Sim / Não / Não se aplica)* | `adaptável para autoaplicação` | Pergunta objetiva sobre escalada motivada por ciúme ou posse pós-separação. |
| **17** | *17. Você se sente isolada de amigos, familiares, pessoas da comunidade ou trabalho? (Sim / Não / Não sei)* | `adaptável com cuidado` | Pergunta incluída no modelo de 2025 que mede isolamento social e falta de rede de apoio; requer acolhimento sem julgamento. |
| **18** | *18. Você possui alguma deficiência ou doença degenerativa que acarreta condição limitante ou de vulnerabilidade física ou mental? (Sim: Deficiência física / Deficiência visual / Deficiência auditiva / Deficiência intelectual / Doença degenerativa. Qual? / Outra. Especifique / Não / Prefiro não informar)* | `adaptável para autoaplicação` | Fato objetivo relevante para agravamento de risco (CP, art. 129, § 13; Lei 11.340/2006) e para elegibilidade ao BPC/LOAS. |
| **19** | *19. Com qual cor/raça você se identifica? (Preta (Negra) / Parda (Negra) / Indígena / Branca / Amarela / Prefiro não informar)* | `não adaptável` | No Fonar oficial, tem finalidade estatística e epidemiológica. Na Rede Lilás, não altera a regra determinística de risco imediato e é omitida para minimizar perguntas em momento de crise (princípio da minimização — LGPD, art. 6º, III). |

---

### Bloco IV — Outras informações importantes

| Nº | Pergunta no modelo vigente do Fonar (texto literal de 2025) | Classificação | Motivo e diretriz para a S3 (`s3-triagem-fonar`) |
| :--- | :--- | :--- | :--- |
| **20** | *20. Você considera que mora em bairro, comunidade, área rural, território indígena ou outro local de maior risco de violência? (Sim, área rural / Sim, território indígena / Sim, área urbana / Não / Não sei)* | `adaptável com cuidado` | Percepção subjetiva de território; na Rede Lilás, é complementada pela indicação opcional da Região Administrativa (RA) ou CEP para localizar a rede de proteção do DF. |
| **21** | *21. Qual a sua situação de moradia? (Própria / Alugada / Cedida ou "de favor". Por quem?)* | `adaptável para autoaplicação` | Essencial para verificar vulnerabilidade habitacional e elegibilidade ao Auxílio-Aluguel federal (Lei 14.674/2023) e ao Aluguel Social do DF (Lei Distrital 6.623/2020 e Portaria SMDF 49/2026). |
| **22** | *22. Atualmente, você reside no mesmo imóvel com o(a) agressor(a)? (Sim / Não)* | `adaptável para autoaplicação` | Pergunta direta e decisiva para avaliar risco imediato de coabitação e necessidade de afastamento do lar ou saída emergencial. |
| **23** | *23. Você se considera financeiramente dependente do(a) agressor(a)? (Sim, totalmente / Sim, parcialmente / Não dependo financeiramente / Prefiro não informar)* | `adaptável para autoaplicação` | Conecta diretamente o resultado da triagem de risco à avaliação de benefícios socioassistenciais (Bolsa Família, BPC/LOAS, Auxílio-Aluguel e Aluguel Social do DF). |
| **24** | *24. Você quer e aceita abrigamento temporário? (Sim, quero e aceito o abrigamento temporário / Não desejo o abrigamento temporário)* | `adaptável para autoaplicação` | Orienta o encaminhamento imediato para a Casa da Mulher Brasileira de Ceilândia (alojamento de passagem) ou acesso sigiloso à Casa Abrigo via rede especializada. |

---

## Parte II — Avaliação de Risco Semiestruturada Complementar (Itens 1 a 8 — Preenchimento Exclusivo do Profissional)

| Item | Descrição na Parte II do Fonar (modelo vigente de 2025) | Classificação | Motivo |
| :--- | :--- | :--- | :--- |
| **Declaração de Veracidade e Assinaturas (final da Parte I) e Cabeçalho da Parte II** | Assinatura da vítima, registro de modalidade de preenchimento pelo profissional, assinatura do profissional e repetição dos campos de identificação (nome, CPF, processo, vara, comarca). | `não adaptável` | Incompatível com a autoaplicação anônima e sem cadastro da Rede Lilás (`privacidade-seguranca`). |
| **Itens 1 a 8 da Avaliação de Risco Semiestruturada Complementar** | **1.** Percepção de risco por parte da vítima (*Durante o atendimento, a vítima demonstra percepção de risco sobre sua situação?*); **2.** Contexto atual e risco de novas violências; **3.** Sobre a saúde física, mental e estado emocional da vítima; **4.** Sobre o histórico de violência e sobre o(a) agressor(a); **5.** Descreva outros fatores de risco; **6.** Descreva fatores de proteção verificados no caso concreto; **7.** Orientações, encaminhamentos e outras medidas voltadas para a vítima, o(a) agressor(a) e/ou familiares; **8.** Adesão aos encaminhamentos (*A vítima manifestou interesse em aderir aos encaminhamentos?*) e identificação do profissional. | `não adaptável` | Exige entrevista clínica/técnica presencial por profissional com experiência em saúde mental e avaliação de risco. Na Rede Lilás, essa limitação é tratada pelo requisito **Aviso de limite da triagem** (`triagem-risco`): todo resultado informa explicitamente que a triagem automática não substitui a avaliação presencial de um profissional da rede de atendimento. |
