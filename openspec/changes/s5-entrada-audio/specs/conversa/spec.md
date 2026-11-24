# Spec Delta

## MODIFIED Requirements

### Requirement: Pergunta por áudio
O sistema SHALL aceitar perguntas por áudio, transcrevê-las no servidor da própria aplicação, sem serviço externo, e tratá-las como texto, sem guardar o arquivo de áudio. A transcrição MUST voltar ao aparelho antes de qualquer envio ao orquestrador. Prioridade: desejável (primeiro item a ser cortado se faltar tempo).

#### Scenario: Pergunta falada
- **WHEN** a usuária grava "ele pode tirar meus filhos de mim?"
- **THEN** o sistema transcreve, responde como se fosse texto e descarta o áudio

#### Scenario: Transcrição sem resposta do LLM
- **WHEN** o servidor recebe um áudio para transcrever
- **THEN** devolve só o texto transcrito, sem buscar trechos de lei e sem chamar o LLM

#### Scenario: Áudio sem fala
- **WHEN** a usuária grava só silêncio ou ruído
- **THEN** o sistema mostra "Não entendi o áudio. Tente de novo ou digite sua pergunta." e nada é enviado ao orquestrador

#### Scenario: Sem internet
- **WHEN** a usuária está sem conexão
- **THEN** o botão de microfone fica indisponível com a orientação de digitar, e o alerta de 190 do texto digitado continua funcionando

### Requirement: Continuar depois do alerta de 190
Quando o alerta de 190 disparar no aparelho, o sistema SHALL mostrar o botão "Continuar com minha pergunta" e MUST NOT enviar o texto ao servidor sem o toque. A única exceção é o áudio, que vai ao servidor da aplicação para ser transcrito antes da regra (exceção registrada em 24/11); a transcrição segue a mesma regra. Pedido sem alerta visto e com sinal de risco MUST receber só o alerta, sem chamar o LLM. Com alerta visto, o servidor MUST seguir para o agente e indicar o risco junto com a resposta.

#### Scenario: Alerta sem toque
- **WHEN** a mensagem tem sinal de risco imediato e a usuária não toca em "Continuar com minha pergunta"
- **THEN** nenhuma requisição com o texto é feita

#### Scenario: Pedido antigo sem alerta visto
- **WHEN** um pedido com sinal de risco chega sem a indicação de alerta visto
- **THEN** o servidor devolve só o alerta de 190, e o texto nunca chega ao LLM

#### Scenario: Pedido depois do toque
- **WHEN** um pedido com sinal de risco chega com a indicação de alerta visto
- **THEN** a resposta traz o agente, a resposta dele e a indicação de risco imediato, e o 190 continua visível acima da resposta

## ADDED Requirements

### Requirement: Alerta de 190 na pergunta por áudio
Quando a transcrição chegar ao aparelho, o sistema SHALL aplicar a mesma regra de risco imediato do texto digitado, antes de mostrar a transcrição para conferência. Com sinal de risco, o alerta de 190 MUST aparecer na hora, com "Continuar com minha pergunta", e a transcrição MUST NOT ir ao orquestrador sem o toque.

#### Scenario: Áudio com sinal de risco
- **WHEN** a usuária grava "ele está aqui na porta com uma faca e disse que vai me matar"
- **THEN** o alerta de 190 aparece com "Continuar com minha pergunta", e nenhum pedido com a transcrição chega ao orquestrador nem ao LLM sem o toque

#### Scenario: Áudio com risco e pergunta
- **WHEN** a usuária grava "ele disse que vai me matar hoje, posso pedir medida protetiva?" e toca em "Continuar com minha pergunta"
- **THEN** a resposta do agente jurídico aparece abaixo do alerta de 190, que continua visível

### Requirement: Transcrição para conferir antes do envio
Sem sinal de risco, o sistema SHALL colocar a transcrição na caixa de texto da conversa, para a usuária conferir, corrigir e enviar, e MUST NOT enviá-la ao orquestrador sem o toque em enviar.

#### Scenario: Conferir e corrigir
- **WHEN** a transcrição chega sem sinal de risco e a usuária corrige uma palavra antes de enviar
- **THEN** o texto corrigido é o que segue para o orquestrador, pelo mesmo caminho do texto digitado

#### Scenario: Desistir da pergunta
- **WHEN** a transcrição está na caixa e a usuária aciona a saída rápida
- **THEN** a caixa é esvaziada junto com a conversa, e nada é enviado

### Requirement: Limites do áudio
O sistema SHALL aceitar áudios de até 30 segundos e até 1 MB. A gravação MUST parar sozinha em 30 segundos, e o servidor MUST recusar áudios maiores com uma mensagem que oriente a gravar de novo, em partes, ou digitar.

#### Scenario: Gravação no limite
- **WHEN** a gravação chega a 30 segundos
- **THEN** ela para sozinha e o áudio é enviado para transcrição

#### Scenario: Áudio acima do limite
- **WHEN** o servidor recebe um áudio com mais de 1 MB ou mais de 35 segundos
- **THEN** recusa sem transcrever e a usuária vê "O áudio pode ter até 30 segundos. Grave de novo, em partes, ou digite sua pergunta."

#### Scenario: Arquivo que não é áudio
- **WHEN** o servidor recebe um arquivo corrompido ou que não é áudio
- **THEN** recusa com uma mensagem para gravar de novo ou digitar, e nenhum arquivo fica no disco

## REMOVED Requirements

### Requirement: Leitura de documento fotografado
**Reason**: decisão da equipe de 24/11: a S5 tem só dois dias de trabalho e fica só com texto e áudio, sem fotos. A mudança `s5-documento-foto` saiu do plano.
**Migration**: nenhuma; a funcionalidade nunca foi implementada. Retomar a leitura de documento exige uma mudança nova, com a decisão de privacidade das imagens registrada no design.
