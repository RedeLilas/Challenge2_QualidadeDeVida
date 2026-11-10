# Spec Delta

## ADDED Requirements

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

### Requirement: Autoria das perguntas e gabaritos
As perguntas e os gabaritos SHALL ser escritos pela equipe, sem uso de Claude. Uma segunda pessoa MUST conferir cada gabarito no texto da lei antes do congelamento.

#### Scenario: Gabarito sem conferência
- **WHEN** uma pergunta não tem o registro de conferência por segunda pessoa
- **THEN** a validação do conjunto falha

### Requirement: Perguntas fictícias sem disparar o alerta
As perguntas SHALL usar linguagem leiga e situações fictícias, e cada uma MUST passar pela checagem de risco imediato antes do congelamento. Quando o alerta disparar, a pergunta MUST ser reescrita de forma impessoal, sem alterar as regras de risco.

#### Scenario: Pergunta dispara o alerta
- **WHEN** uma pergunta do conjunto dispara o alerta de risco imediato
- **THEN** a validação do conjunto falha até a pergunta ser reescrita, e as regras de risco continuam iguais

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

## REMOVED Requirements

### Requirement: Julgamento por LLM juiz com revisão em dupla
**Reason**: Decisão de 09/11: a correção passa a ser feita só por LLM, sem revisão humana das notas.
**Migration**: Usar o requisito "Correção por LLM externo sem revisão humana das notas" e declarar o método no relatório.
