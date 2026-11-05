# Notas sobre o Formulário Nacional de Avaliação de Risco (Fonar)

- **Data de verificação:** `2026-11-05`
- **Fontes oficiais:**
  - **Lei nº 14.149, de 5 de maio de 2021:** https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2021/lei/l14149.htm
  - **Portaria Conjunta CNJ/CNMP nº 6, de 25 de julho de 2025** (atualiza o anexo da Resolução Conjunta CNJ/CNMP nº 5/2020): https://mpce.mp.br/wp-content/uploads/2025/10/PORTARIA-CONJUNTA-No-6-DE-25-DE-JULHO-DE-2025-Dispoe-sobre-alteracoes-no-modelo-do-FONAR.pdf
  - **Portal do Fonar no CNJ:** https://www.cnj.jus.br/programas-e-acoes/violencia-contra-a-mulher/formulario-nacional-de-avaliacao-de-risco/

---

## Critérios de Classificação para Autoaplicação na Rede Lilás

Conforme o `design.md` da mudança `s2-fontes-df` e a spec `triagem-risco`, cada item do modelo vigente do Fonar é classificado em uma das três categorias abaixo:

1. **`adaptável para autoaplicação`**: Pergunta objetiva sobre fatos concretos vivenciados pela mulher, que pode ser respondida diretamente por ela (ou por pessoa de confiança no modo "ajudando outra pessoa") em linguagem acolhedora, sem exigir jargão técnico.
2. **`adaptável com cuidado`**: Pergunta sobre temas sensíveis (violência sexual, saúde mental, suicídio, filhos ou percepção subjetiva de letalidade) que pode compor a triagem **desde que** tenha redação simplificada, aviso de que a resposta é opcional (regra conservadora: pular não reduz o nível de risco) e acionamento imediato de canais de emergência quando pertinente.
3. **`não adaptável`**: Item que depende de avaliação técnica presencial de profissional capacitado (Parte II do Fonar), consulta a sistemas policiais/judiciais ou coleta de dados identificadores incompatíveis com a diretriz de privacidade/ausência de cadastro da Rede Lilás.

---

## Parte I — Questões Objetivas (Blocos I a IV)

### Bloco I — Sobre o histórico de violência

| Nº | Pergunta no modelo vigente do Fonar | Classificação | Motivo e diretriz para a S3 (`s3-triagem-fonar`) |
| :--- | :--- | :--- | :--- |
| **1** | *O(A) agressor(a) já ameaçou você ou algum familiar com a finalidade de atingi-la? (Com arma de fogo / Com faca / De outra forma / Não)* | `adaptável para autoaplicação` | Fator crítico de letalidade; pergunta direta sobre fato objetivo. Resposta afirmativa com arma de fogo ou faca deve elevar o risco para **alto** imediatamente. |
| **2** | *O(A) agressor(a) já praticou alguma(s) destas agressões físicas contra você? (Queimadura, enforcamento, sufocamento, estrangulamento, tiro, afogamento, facada, paulada, soco, chute, tapa, empurrão, puxão de cabelo, outra)* | `adaptável para autoaplicação` | Fato concreto; permite separar agressões de altíssima letalidade (enforcamento, sufocamento, estrangulamento, queimadura, facada, tiro → risco **alto**) de outras agressões físicas. |
| **3** | *Você necessitou de atendimento médico e/ou internação após algumas dessas agressões?* | `adaptável para autoaplicação` | Indicador objetivo de gravidade física pregressa; fácil compreensão pela usuária. |
| **4** | *O(A) agressor(a) já obrigou você a ter relações sexuais ou praticar atos sexuais contra a sua vontade?* | `adaptável com cuidado` | Tema altamente sensível e potencialmente revitimizante. Deve permitir pular a pergunta sem reduzir o risco e, se afirmativa (especialmente nas últimas 72h), priorizar orientação da Lei 12.845/2013 (Minuto Seguinte). |
| **5** | *O(A) agressor(a) persegue você, demonstra ciúme excessivo, tenta controlar sua vida e as coisas que você faz (aonde você vai, com quem conversa, o tipo de roupa que usa etc.)?* | `adaptável para autoaplicação` | Descreve comportamentos cotidianos claros de controle e perseguição (*stalking*, art. 147-A do CP e violência psicológica/moral). |
| **6** | *O(A) agressor(a) já teve algum destes comportamentos? (Frases como "se não for minha, não será de mais ninguém"; perturbação, monitoramento ou proibição de visitar familiares/amigos, trabalhar ou estudar; telefonemas/mensagens insistentes; retenção de dinheiro, bens ou documentos)* | `adaptável para autoaplicação` | Excelente para autoaplicação; conecta diretamente a triagem de risco à identificação de violência psicológica e patrimonial (art. 7º, II e IV da Lei 11.340/2006). |
| **7** | *Você já registrou ocorrência policial ou formulou pedido de medida protetiva de urgência envolvendo essa mesma pessoa?* | `adaptável para autoaplicação` | Pergunta objetiva sobre histórico de busca institucional; útil também para orientar os próximos passos na DEAM/Defensoria. |
| **8** | *O(A) agressor(a) já descumpriu medida protetiva anteriormente?* | `adaptável para autoaplicação` | Forte preditor de reincidência grave e crime autônomo (art. 24-A da Lei 11.340/2006). Se afirmativo, eleva o nível de urgência para **alto**. |
| **9** | *As agressões ou ameaças do(a) agressor(a) contra você se tornaram mais frequentes ou mais graves nos últimos meses?* | `adaptável para autoaplicação` | Mede diretamente a escalada da violência de forma simples e compreensível. |

---

### Bloco II — Sobre o(a) agressor(a)

| Nº | Pergunta no modelo vigente do Fonar | Classificação | Motivo e diretriz para a S3 (`s3-triagem-fonar`) |
| :--- | :--- | :--- | :--- |
| **10** | *O(A) agressor(a) faz uso abusivo de álcool ou de drogas ou de medicamentos?* | `adaptável para autoaplicação` | Fator de risco objetivo observado pela vítima no convívio diário (com opção "Não sei"). |
| **11** | *O(A) agressor(a) tem alguma doença mental comprovada por avaliação médica?* | `adaptável com cuidado` | A usuária frequentemente desconhece diagnóstico médico formal; na adaptação, deve incluir a opção "Não sei" e não depender de comprovação clínica. |
| **12** | *O(A) agressor(a) já tentou suicídio ou falou em suicidar-se?* | `adaptável com cuidado` | Indicador documentado de risco de feminicídio seguido de suicídio. Exige linguagem cuidadosa e opção "Não sei". |
| **13** | *O(A) agressor(a) está com dificuldades financeiras, está desempregado ou tem dificuldade de se manter no emprego?* | `adaptável para autoaplicação` | Fator situacional objetivo de estresse e escalada de risco doméstico. |
| **14** | *O(A) agressor(a) tem acesso a arma de fogo?* | `adaptável para autoaplicação` | Um dos preditores mais fortes de letalidade no Fonar. Resposta "Sim" deve acionar classificação conservadora de risco **alto**. |
| **15** | *O(A) agressor(a) já ameaçou ou agrediu seus filhos, outros familiares, amigos, colegas de trabalho, outras pessoas ou animais?* | `adaptável para autoaplicação` | Pergunta objetiva que identifica padrão generalizado de violência e intimidação indireta. |

---

### Bloco III — Sobre você (a vítima)

| Nº | Pergunta no modelo vigente do Fonar | Classificação | Motivo e diretriz para a S3 (`s3-triagem-fonar`) |
| :--- | :--- | :--- | :--- |
| **16** | *Você se separou recentemente do(a) agressor(a), tentou ou manifestou intenção de se separar?* | `adaptável para autoaplicação` | Momento crítico de maior letalidade (ruptura do relacionamento); pergunta direta e essencial para a triagem. |
| **17** | *Você tem filhos? (Com o agressor / De outro relacionamento / Faixa etária)* | `adaptável para autoaplicação` | Pergunta objetiva que serve simultaneamente à triagem de risco e à elegibilidade para benefícios (Bolsa Família, Prato Cheio, Aluguel Social). |
| **18** | *Você está vivendo algum conflito com o(a) agressor(a) em relação à guarda dos filhos, visitas ou pagamento de pensão?* | `adaptável para autoaplicação` | Fato objetivo que indica ponto de contato forçado com o agressor e necessidade de orientação da Defensoria Pública. |
| **19** | *Seu(s) filho(s) já presenciou(aram) ato(s) de violência do(a) agressor(a) contra você?* | `adaptável com cuidado` | Pergunta sensível que pode gerar sentimento de culpa ou receio na mãe; exige tom acolhedor e esclarecimento de que visa apenas proteger a família. |
| **20** | *Você sofreu algum tipo de violência durante a gravidez ou nos três meses posteriores ao parto?* | `adaptável para autoaplicação` | Indicador objetivo de vulnerabilidade agravada e recorrência histórica. |
| **21** | *Você está grávida ou teve bebê nos últimos 18 meses?* | `adaptável para autoaplicação` | Fato objetivo que impacta tanto o grau de vulnerabilidade na triagem quanto os adicionais do Bolsa Família e atendimento prioritário. |
| **22** | *Se você está em um novo relacionamento, percebe que as ameaças ou as agressões físicas aumentaram em razão disso?* | `adaptável para autoaplicação` | Pergunta objetiva sobre escalada motivada por ciúme/posse pós-separação. |
| **23** | *Você possui alguma deficiência ou doença degenerativa que acarrete condição limitante ou de vulnerabilidade física ou mental?* | `adaptável para autoaplicação` | Fato objetivo relevante para agravamento de risco (CP, art. 129, § 13; LMP) e para elegibilidade ao BPC/LOAS. |
| **24** | *Com qual cor/raça você se identifica?* | `não adaptável` | No Fonar oficial, tem finalidade estatística e epidemiológica. Na Rede Lilás, não altera a regra determinística de risco imediato e é omitida para minimizar o número de perguntas em momento de crise (princípio da minimização — LGPD, art. 6º, III). |

---

### Bloco IV — Outras informações importantes

| Nº | Pergunta no modelo vigente do Fonar | Classificação | Motivo e diretriz para a S3 (`s3-triagem-fonar`) |
| :--- | :--- | :--- | :--- |
| **25** | *Você considera que mora em bairro, comunidade, área rural ou local de risco de violência?* | `adaptável com cuidado` | Percepção subjetiva de território; na Rede Lilás, é melhor substituída pela indicação opcional da Região Administrativa (RA) ou CEP para localizar a rede de proteção do DF. |
| **26** | *Qual sua situação de moradia? (Própria / Alugada / Cedida / Compartilhada com o agressor)* | `adaptável para autoaplicação` | Essencial tanto para avaliar o risco de coabitação com o agressor quanto para verificar elegibilidade ao Auxílio-Aluguel (Lei 14.674/2023) e ao Aluguel Social do DF (Lei Distrital 6.623/2020). |
| **27** | *Você se considera dependente financeiramente do(a) agressor(a)? / Você quer e aceita abrigamento temporário?* | `adaptável para autoaplicação` | Conecta diretamente o resultado da triagem de risco à avaliação de benefícios socioassistenciais e ao encaminhamento para a Casa da Mulher Brasileira (alojamento de passagem) ou Casa Abrigo. |

---

## Parte II — Avaliação Técnica / Profissional (Bloco de Preenchimento Exclusivo do Profissional)

| Item | Descrição na Parte II do Fonar | Classificação | Motivo |
| :--- | :--- | :--- | :--- |
| **Bloco de Identificação e Assinatura** | Nome completo da vítima, CPF, RG, endereço exato, nome do agressor, número do BO/processo e assinatura | `não adaptável` | Viola os requisitos da Rede Lilás de **ausência de cadastro obrigatório**, **não solicitar CPF/nome** e **ausência de histórico persistente** para segurança da vítima (`privacidade-seguranca`). |
| **Avaliação Semiestruturada do Profissional** | Percepção técnica do(a) policial, psicólogo(a) ou assistente social sobre o estado emocional da vítima, coerência do relato, minimização do risco pela ofendida e histórico criminal do agressor em bases restritas | `não adaptável` | Exige formação técnica presencial e acesso a bancos de dados de segurança pública. Na Rede Lilás, essa limitação é tratada pelo requisito **Aviso de limite da triagem** (`triagem-risco`): todo resultado informa explicitamente que a triagem automática não substitui a avaliação presencial de um profissional da rede de atendimento. |
