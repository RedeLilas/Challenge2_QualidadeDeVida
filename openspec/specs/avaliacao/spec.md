# avaliacao Specification

## Purpose
Medir objetivamente a qualidade da Rede Lilás sem entrevistas nem dados reais: casos fictícios com gabarito e fonte, correção por um único LLM externo, sem revisão humana das notas e com controles (respostas erradas de propósito e trechos comprobatórios), e teste de usabilidade com colegas. Origem: seção 8 (métricas de sucesso) das definições da Semana 1; método da correção alterado na S3 (decisões de 09/11 e 12/11).

## Requirements

### Requirement: Conjunto de casos fictícios com fonte
A equipe SHALL manter um conjunto versionado de casos fictícios, cada um com a pergunta, a resposta esperada e a norma/artigo que a sustenta. O conjunto MUST NOT conter relatos reais de vítimas.

#### Scenario: Caso sem fonte
- **WHEN** um caso é adicionado sem a norma ou o artigo que sustenta a resposta esperada
- **THEN** a validação do conjunto falha

### Requirement: Metas de qualidade
O relatório de avaliação SHALL medir e comparar com as metas:

| Métrica | Meta |
| :--- | :--- |
| Precisão jurídica | ≥ 90% corretas |
| Fidelidade às fontes | 100% com citação; ≤ 5% de afirmações sem suporte |
| Acurácia de elegibilidade | ≥ 90% de concordância com o gabarito |
| Sensibilidade para risco alto | 100% (nenhum falso negativo), verificada por regra |
| Tempo até o 190 | ≤ 2 s |
| Usabilidade (SUS) | ≥ 70 |

#### Scenario: Meta não atingida
- **WHEN** uma métrica fica abaixo da meta
- **THEN** o relatório registra o valor obtido, a causa provável e a ação tomada ou o motivo para não agir

### Requirement: Comparação LLM x RAG
A avaliação SHALL comparar, com o mesmo conjunto de perguntas e o mesmo modelo de produção, as respostas do LLM sem RAG e com RAG.

#### Scenario: Relatório da S3
- **WHEN** a comparação é executada
- **THEN** o relatório mostra precisão e fidelidade às fontes das duas versões lado a lado

### Requirement: Usabilidade com colegas
O teste de usabilidade SHALL ser feito com colegas do curso, seguindo roteiros com casos fictícios e o questionário SUS anônimo, e MUST NOT pedir relatos pessoais.

#### Scenario: Sessão de teste
- **WHEN** uma colega participa do teste
- **THEN** ela segue um roteiro fictício, responde o SUS sem se identificar e nenhum relato pessoal é coletado

### Requirement: Limitação declarada
O relatório final SHALL declarar que a solução não foi validada por especialistas da rede de atendimento nem por usuárias reais.

#### Scenario: Relatório final
- **WHEN** o relatório final é entregue
- **THEN** ele contém uma seção de limitações com essa declaração

### Requirement: Correção por LLM externo sem revisão humana das notas
As respostas SHALL ser corrigidas por um único LLM externo, de outra empresa que não a do modelo avaliado, sem acesso ao repositório e com busca na web e memória desligadas. O relatório MUST declarar "avaliação feita por LLM, sem verificação humana das notas".

#### Scenario: Relatório da correção
- **WHEN** o relatório comparativo é entregue
- **THEN** ele traz a declaração exigida, o modelo corretor e a data de cada envio

### Requirement: Composição do conjunto oficial
O conjunto oficial SHALL ter 30 perguntas dentro do tema: formas de violência e quem a lei protege 5; medidas protetivas e descumprimento 7; polícia, processo e Defensoria 4; "isso é crime?" 9; guarda 2; auxílio-aluguel, Fonar e trabalho 3. Cada uma MUST ter resposta esperada, pontos obrigatórios, normas aceitas e fonte.

#### Scenario: Pergunta sem pontos obrigatórios
- **WHEN** uma pergunta do conjunto oficial não tem pontos obrigatórios, normas aceitas ou fonte
- **THEN** a validação do conjunto falha

### Requirement: Formato dos conjuntos de avaliação
Os conjuntos SHALL ser arquivos YAML UTF-8 versionados em `avaliacao/conjuntos/desenvolvimento.yaml` e `avaliacao/conjuntos/oficial.yaml`, ambos com raiz `versao: 1`, `perguntas` e `extras`. O conjunto de desenvolvimento MUST ter 15 perguntas do tema e 10 extras; o oficial MUST ter 30 perguntas do tema e 10 extras. As extras SHALL usar a categoria `fora_do_tema` e não exigem gabarito.

Cada item MUST ter `id`, `pergunta`, `autor` e `categoria`. Os IDs MUST ser únicos dentro de cada arquivo. Cada item de `perguntas` MUST também ter `resposta_esperada`, `pontos_obrigatorios` (lista não vazia), `normas_aceitas` (lista não vazia) e `fonte`. Cada pergunta do conjunto oficial MUST ainda registrar `conferencia.revisor` e `conferencia.fonte_conferida`; o revisor MUST ser diferente do autor. Todos os enunciados MUST ser fictícios, em linguagem leiga, e passar pela regra de risco imediato.

As categorias MUST usar estas chaves no YAML: `violencia_e_protecao` (formas de violência e quem a lei protege), `medidas_protetivas` (medidas protetivas e descumprimento), `policia_processo_defensoria` (polícia, processo e Defensoria), `crime` ("isso é crime?"), `guarda` (guarda) e `auxilio_fonar_trabalho` (auxílio-aluguel, Fonar e trabalho). Os itens de `extras` MUST usar `fora_do_tema`.

#### Scenario: Campo obrigatório ausente
- **WHEN** um item não contém um campo obrigatório para seu conjunto e tipo
- **THEN** a validação falha e identifica o arquivo e o item

#### Scenario: Gabarito oficial sem segunda pessoa
- **WHEN** um gabarito oficial não registra conferência por uma segunda pessoa
- **THEN** a validação do conjunto oficial falha

#### Scenario: Pergunta extra sem gabarito
- **WHEN** uma extra tem ID, enunciado, autoria e categoria fora do tema, sem campos de gabarito
- **THEN** a validação aceita a extra se os demais limites e regras forem atendidos

#### Scenario: Distribuição diferente da decidida
- **WHEN** a quantidade de perguntas de um tema difere da distribuição
- **THEN** a validação do conjunto falha

### Requirement: Perguntas fora do tema relatadas à parte
A avaliação SHALL incluir 10 perguntas extras fora do tema, lidas pela equipe nas duas versões e relatadas à parte, sem entrar nas metas de precisão e fidelidade.

#### Scenario: Resultado das extras
- **WHEN** o relatório é escrito
- **THEN** as 10 extras aparecem em seção própria e não alteram o resultado das 30 perguntas

### Requirement: Perguntas fictícias sem disparar o alerta
As perguntas SHALL usar linguagem leiga e situações fictícias, e cada uma MUST passar pela checagem de risco imediato antes do congelamento. Quando o alerta disparar, a pergunta MUST ser reescrita de forma impessoal, sem alterar as regras de risco.

#### Scenario: Pergunta dispara o alerta
- **WHEN** uma pergunta do conjunto dispara o alerta de risco imediato
- **THEN** a validação do conjunto falha até a pergunta ser reescrita, e as regras de risco continuam iguais

### Requirement: Autoria das perguntas e gabaritos
As perguntas e os gabaritos SHALL ser escritos pela equipe, sem uso de Claude. A conferência por segunda pessoa está definida no requisito "Formato dos conjuntos de avaliação".

#### Scenario: Registro da autoria
- **WHEN** uma pergunta entra em um conjunto de avaliação
- **THEN** ela traz no campo `autor` a pessoa da equipe que a escreveu

### Requirement: Separação e congelamento do conjunto oficial
As perguntas de desenvolvimento SHALL ficar separadas do conjunto oficial. O conjunto MUST congelar antes da rodada oficial, e qualquer ajuste depois do resultado MUST obrigar a refazer a rodada e declarar o ajuste no relatório.

#### Scenario: Conjunto alterado depois de congelar
- **WHEN** o conjunto oficial difere do registrado no congelamento
- **THEN** a rodada oficial não executa até um novo congelamento, e a nova rodada é declarada no relatório

#### Scenario: Recalibração
- **WHEN** um parâmetro do sistema é ajustado antes da rodada oficial
- **THEN** o ajuste usa só as perguntas de desenvolvimento

### Requirement: Condições iguais entre as versões
As versões com e sem RAG SHALL rodar no mesmo dia, com o mesmo modelo e as mesmas instruções, exceto a regra de usar apenas os trechos. Cada rodada MUST registrar nome do modelo, data e versão do changelog.

#### Scenario: Registro da rodada
- **WHEN** uma rodada termina
- **THEN** o registro traz nome do modelo, data, versão do changelog e as instruções usadas em cada versão

### Requirement: Recusa dentro do tema conta como erro
Na medição de precisão, uma recusa em pergunta dentro do tema SHALL contar como erro. A meta é de 27 acertos em 30.

#### Scenario: Versão recusa uma pergunta do conjunto oficial
- **WHEN** uma versão recusa responder uma das 30 perguntas
- **THEN** a pergunta conta como errada para essa versão

### Requirement: Correção de precisão
A correção de precisão SHALL receber pergunta, gabarito, pontos obrigatórios e resposta, e marcar cada ponto como presente ou ausente e se algo contradiz o gabarito. A resposta MUST ser certa só com todos os pontos e sem contradição.

#### Scenario: Ponto ausente
- **WHEN** a resposta não traz um dos pontos obrigatórios
- **THEN** a resposta é considerada errada

#### Scenario: Contradição
- **WHEN** a resposta traz todos os pontos, mas contradiz o gabarito
- **THEN** a resposta é considerada errada

### Requirement: Correção de fidelidade
A correção de fidelidade SHALL receber só a resposta e o texto integral dos artigos citados, sem gabarito, e marcar cada afirmação jurídica como com ou sem suporte. Acolhimento e encaminhamento MUST NOT contar. Citações fora da base MUST ser marcadas à parte.

#### Scenario: Citação fora da base
- **WHEN** a resposta cita um artigo que não está na base legal
- **THEN** a citação é marcada à parte, e a meta de até 5% sem suporte vale só para a versão com RAG

#### Scenario: Frase de acolhimento
- **WHEN** a resposta traz uma frase de acolhimento ou indica o Ligue 180
- **THEN** a frase não entra na contagem de afirmações jurídicas

### Requirement: Envios às cegas com controles
A correção SHALL ter quatro envios, com uma conversa de precisão e uma de fidelidade para cada arquivo, cada um com uma versão de cada pergunta. Os códigos MUST ser neutros, a ordem sorteada e o mapa de versões guardado à parte até o fim.

#### Scenario: Conteúdo do envio
- **WHEN** um arquivo é preparado
- **THEN** ele não revela qual versão gerou cada resposta

### Requirement: Respostas erradas de propósito
Cada arquivo SHALL trazer 3 respostas erradas de propósito, uma delas perto do final. Se o corretor aprovar alguma, a correção daquele arquivo MUST NOT ser usada, e a rubrica ou o modelo corretor MUST mudar.

#### Scenario: Corretor aprova uma resposta errada
- **WHEN** o retorno marca como certa uma resposta errada de propósito
- **THEN** o script rejeita aquela correção e o relatório registra o ocorrido

### Requirement: Conferência automática do retorno
O corretor SHALL copiar o trecho que comprova cada marcação. Um script MUST conferir se todas as linhas voltaram e se os trechos existem no texto enviado, e calcular por código a recusa e a presença de citação.

#### Scenario: Linha faltando
- **WHEN** o retorno não traz todas as linhas enviadas
- **THEN** o script aponta os códigos faltantes e a correção não é aceita

#### Scenario: Trecho inexistente
- **WHEN** o trecho copiado pelo corretor não existe no texto enviado
- **THEN** o script aponta a linha e a marcação não é aceita

### Requirement: Guarda do material da correção
Todo o material enviado e recebido SHALL ser guardado com o modelo e a data.

#### Scenario: Auditoria de uma nota
- **WHEN** alguém confere uma nota depois da rodada
- **THEN** o envio, o retorno, o modelo e a data estão disponíveis

### Requirement: Casos fictícios da S4
A equipe SHALL manter, em arquivos próprios em `avaliacao/conjuntos/s4/`, três conjuntos de casos fictícios: elegibilidade (20 a 30 perfis, com a situação esperada por benefício), triagem (respostas ao Fonar, com o nível esperado) e roteamento (cerca de 30 mensagens, com o agente esperado). Os arquivos da S3 MUST NOT ser alterados.

#### Scenario: Conjuntos presentes
- **WHEN** a validação dos conjuntos da S4 roda
- **THEN** ela encontra os três arquivos, e o de elegibilidade tem de 20 a 30 perfis

#### Scenario: Conjuntos da S3 intactos
- **WHEN** os conjuntos da S4 são criados
- **THEN** `avaliacao/conjuntos/desenvolvimento.yaml` e `avaliacao/conjuntos/oficial.yaml` ficam sem alteração

### Requirement: Gabarito com fonte e conferência
Cada caso de elegibilidade e de triagem SHALL citar a norma e o artigo (ou a portaria e o item) de onde vem o gabarito. Todo caso MUST registrar o autor e a conferência por uma pessoa da equipe diferente de quem o escreveu.

#### Scenario: Caso sem fonte
- **WHEN** um caso de elegibilidade ou de triagem não cita a norma e o artigo do gabarito
- **THEN** a validação do conjunto falha e identifica o caso

#### Scenario: Conferência pela mesma pessoa
- **WHEN** o revisor de um caso é a mesma pessoa que o escreveu, ou o revisor está vazio
- **THEN** a validação do conjunto falha

### Requirement: Casos de limite na elegibilidade
O conjunto de elegibilidade SHALL incluir casos de limite: renda per capita exatamente no corte, um real acima do corte, "prefiro não informar" num dado necessário e perfil incompleto.

#### Scenario: Cobertura dos limites
- **WHEN** a validação do conjunto de elegibilidade roda
- **THEN** ela confirma que existe ao menos um caso de cada tipo de limite

### Requirement: Roteamento com os pares que confundem
O conjunto de roteamento SHALL incluir os dois tipos de pergunta de benefícios ("tenho direito?" e "o que é?"), o par auxílio-aluguel (jurídico) e Aluguel Social do DF (benefícios), mensagens com mais de uma pergunta e mensagens fora do tema.

#### Scenario: Par do auxílio-aluguel
- **WHEN** o conjunto de roteamento é validado
- **THEN** ele contém "como funciona o aluguel da Maria da Penha?" com o agente jurídico esperado e uma pergunta sobre o Aluguel Social do DF com o agente de benefícios esperado

### Requirement: Medição das metas da S4 por regra
A acurácia de elegibilidade SHALL ser medida rodando a regra de benefícios do aparelho sobre os perfis e comparando cada situação com o gabarito. A sensibilidade para risco alto SHALL ser medida pela triagem e pela suíte de risco imediato. As duas medições MUST rodar sem LLM e sem corretor externo.

#### Scenario: Elegibilidade abaixo da meta
- **WHEN** menos de 90% dos pares perfil e benefício concordam com o gabarito
- **THEN** a medição aponta os casos divergentes e o relatório registra o valor, a causa provável e a ação

#### Scenario: Falso negativo de risco alto
- **WHEN** um caso de triagem com nível esperado alto resulta em nível menor, ou uma frase de risco da suíte não dispara o alerta
- **THEN** a medição falha, e a S4 não é dada como pronta

### Requirement: Relatório da S4
O relatório da S4 SHALL trazer a acurácia de elegibilidade, a sensibilidade para risco alto e, como evidência sem meta, a taxa de acerto do roteamento. Ele MUST identificar a ferramenta usada para redigir cada conjunto, declarar que os casos foram conferidos por uma pessoa da equipe e que não houve corretor externo na S4.

#### Scenario: Relatório entregue
- **WHEN** o relatório da S4 é entregue
- **THEN** ele traz as três medidas, o número de casos, a data, a declaração sobre a autoria e a conferência dos casos, e a ausência de corretor externo

### Requirement: Perguntas de desenvolvimento de benefícios
A equipe SHALL manter um conjunto de desenvolvimento de benefícios em arquivo próprio, separado de `avaliacao/conjuntos/desenvolvimento.yaml`, com perguntas fictícias em linguagem leiga e gabarito com norma e artigo tirados do texto em `dados/leis/`. Cada pergunta MUST registrar o autor e a conferência por outra pessoa da equipe.

#### Scenario: Pergunta sem norma no gabarito
- **WHEN** uma pergunta do conjunto não tem a norma e o artigo do gabarito
- **THEN** a validação do conjunto falha e identifica a pergunta

#### Scenario: Base da S3 intacta
- **WHEN** o conjunto de desenvolvimento de benefícios é criado
- **THEN** `avaliacao/conjuntos/desenvolvimento.yaml` fica sem alteração

### Requirement: Linguagem leiga e extras quase do tema
O conjunto de desenvolvimento de benefícios SHALL ter perguntas com apelidos, frases incompletas e erros de digitação, parte delas sem o nome oficial do programa. MUST ter extras quase do tema (imposto de renda, FGTS, seguro-desemprego, aposentadoria) e a pergunta "como funciona o aluguel da Maria da Penha?", marcada para o eixo jurídico.

#### Scenario: Cobertura da linguagem
- **WHEN** a validação do conjunto roda
- **THEN** ela confirma que há perguntas marcadas como sem o nome oficial, extras quase do tema e a pergunta do aluguel da Maria da Penha

### Requirement: Conjunto de medição separado da calibração
Se o RAG de benefícios for medido depois da S4, o conjunto da medição SHALL ser diferente do usado para calibrar o limite e MUST ser congelado antes da rodada, como na S3.

#### Scenario: Pergunta repetida na medição
- **WHEN** uma pergunta do conjunto de medição de benefícios também está no conjunto de desenvolvimento de benefícios
- **THEN** a validação do conjunto de medição falha
