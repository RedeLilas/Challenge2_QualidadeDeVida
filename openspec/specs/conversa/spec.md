# conversa Specification

## Purpose
Permitir que a usuária converse em linguagem natural (texto e, opcionalmente, áudio e foto) e que cada pergunta seja encaminhada ao agente certo: jurídico, benefícios, triagem ou rede de atendimento. Origem: RF08, RF09.

## Requirements

### Requirement: Perguntas sugeridas
O sistema SHALL oferecer perguntas sugeridas no início e após cada resposta, para quem não sabe por onde começar.

#### Scenario: Primeiro acesso
- **WHEN** a usuária abre a conversa
- **THEN** o sistema mostra sugestões como "O que ele faz comigo é crime?" e "Tenho direito a algum auxílio?"

### Requirement: Encaminhamento ao agente certo
Um orquestrador SHALL encaminhar cada mensagem a um agente de uma lista fechada: jurídico, benefícios, triagem, rede de atendimento ou fora do tema. A verificação de risco imediato MUST ocorrer antes do encaminhamento. Dentro de benefícios, "tenho direito?" vai para a regra no aparelho, e "o que é / como funciona?" vai para a explicação com citação. Explicações sobre o auxílio-aluguel da Lei Maria da Penha vão para o jurídico.

#### Scenario: Pergunta sobre benefício
- **WHEN** a usuária pergunta "tenho direito a bolsa família?"
- **THEN** a mensagem é tratada pelo agente de benefícios, com a regra avaliada no aparelho

#### Scenario: Mensagem com risco e pergunta
- **WHEN** a mensagem contém uma pergunta jurídica e um sinal de risco imediato
- **THEN** o alerta de 190 é exibido primeiro, com o botão "Continuar com minha pergunta", e nada é enviado ao servidor
- **AND** se ela tocar no botão, a resposta do agente jurídico aparece abaixo do alerta de 190, que continua visível

#### Scenario: Pergunta de explicação sobre benefício
- **WHEN** a usuária pergunta "como funciona o cartão gás?"
- **THEN** a mensagem é tratada como explicação de benefício, e nenhuma regra de elegibilidade é avaliada

#### Scenario: Explicação sobre o auxílio-aluguel
- **WHEN** a usuária pergunta "como funciona o aluguel da maria da penha?"
- **THEN** a mensagem é tratada pelo agente jurídico

#### Scenario: Direito ao auxílio-aluguel
- **WHEN** a usuária pergunta "tenho direito ao auxílio-aluguel?"
- **THEN** a mensagem é tratada pela regra de benefícios, que responde "depende de decisão judicial"

### Requirement: Modo de ajuda a outra pessoa
O sistema SHALL oferecer o modo "estou ajudando outra pessoa", que adapta a linguagem para a terceira pessoa e orienta como apoiar e encaminhar a vítima.

#### Scenario: Amiga pedindo ajuda
- **WHEN** a usuária ativa o modo de ajuda e pergunta o que pode fazer pela amiga
- **THEN** as respostas falam da vítima em terceira pessoa e incluem como apoiar sem expô-la ao agressor

#### Scenario: Só a indicação do modo é enviada
- **WHEN** o modo de ajuda está ativo e uma mensagem é enviada ao servidor
- **THEN** a requisição leva apenas o texto e a indicação do modo, sem perfil e sem dados da vítima

#### Scenario: Textos dos agentes do aparelho
- **WHEN** o modo de ajuda está ativo e a resposta vem de benefícios, triagem ou rede
- **THEN** o texto fixo exibido fala da pessoa ajudada em terceira pessoa

#### Scenario: Desativar o modo
- **WHEN** a usuária desativa o modo de ajuda
- **THEN** as mensagens seguintes voltam a ser enviadas sem a indicação do modo, e as respostas falam com ela em segunda pessoa

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

### Requirement: Decisão por regra antes do LLM
O orquestrador SHALL decidir por uma regra de palavras-chave, versionada, quando ela casar exatamente um agente e a mensagem não tiver sinais de mais de uma pergunta. Nos demais casos, o LLM MUST escolher na lista fechada, com saída JSON validada e temperatura 0. Saída inválida ou LLM indisponível MUST levar ao agente jurídico.

#### Scenario: Regra decide sozinha
- **WHEN** a mensagem "onde fica a delegacia da mulher?" casa só as palavras do agente de rede
- **THEN** o agente de rede é escolhido sem chamar o LLM

#### Scenario: Palavras de dois agentes
- **WHEN** a mensagem casa palavras de mais de um agente
- **THEN** o LLM escolhe o agente

#### Scenario: Sinal de mais de uma pergunta
- **WHEN** a mensagem tem dois ou mais "?" ou expressões como "e também", "outra coisa" ou "além disso"
- **THEN** a regra não decide, e o LLM escolhe o agente

#### Scenario: Saída inválida do LLM
- **WHEN** o LLM devolve um JSON inválido ou um agente fora da lista
- **THEN** a mensagem segue para o agente jurídico

#### Scenario: LLM indisponível na classificação
- **WHEN** o LLM não responde na etapa de classificação
- **THEN** a mensagem segue para o agente jurídico, com a recusa ou o aviso de indisponibilidade dele

### Requirement: Campos tirados do texto
O servidor SHALL devolver ao aparelho só o agente escolhido e os campos tirados do texto da mensagem: benefício citado, Região Administrativa e violência sexual recente. A Região Administrativa MUST ser um dos valores da lista de RAs do site; qualquer outro valor MUST virar nulo.

#### Scenario: RA citada no texto
- **WHEN** a usuária escreve "moro em ceilandia, onde tem delegacia da mulher?"
- **THEN** a resposta do servidor traz a RA "Ceilândia"

#### Scenario: RA fora da lista do site
- **WHEN** o texto cita um lugar que não está na lista de RAs do site
- **THEN** o campo de RA volta nulo

### Requirement: Pedido sem perfil e sem histórico
O pedido de orquestração SHALL levar só o texto da mensagem, a indicação de alerta visto e a indicação do modo de ajuda. O servidor MUST rejeitar pedidos com outros campos, como perfil ou histórico.

#### Scenario: Pedido com campo a mais
- **WHEN** um pedido de orquestração chega com um campo de perfil ou de histórico
- **THEN** o servidor rejeita o pedido sem processar o texto

#### Scenario: Perfil no aparelho
- **WHEN** a usuária com perfil preenchido envia qualquer mensagem pela conversa
- **THEN** nenhuma requisição contém o perfil, as respostas de benefícios ou as respostas da triagem

### Requirement: Várias perguntas na mesma mensagem
Quando a mensagem tiver mais de uma pergunta, o sistema SHALL separá-las e reescrever cada uma de forma independente, resolvendo pronomes, até 3. O sistema MUST responder uma e mostrar as demais como perguntas sugeridas. Com mais de 3, MUST responder uma e pedir para enviar o resto separadamente.

#### Scenario: Duas perguntas
- **WHEN** a usuária escreve "o que é medida protetiva e onde eu peço ela?"
- **THEN** o sistema responde uma das perguntas e mostra a outra, reescrita sem pronome solto, como pergunta sugerida

#### Scenario: Pergunta sugerida tocada
- **WHEN** a usuária toca numa pergunta sugerida que veio da separação
- **THEN** ela é enviada como uma mensagem nova, sem depender da mensagem anterior

#### Scenario: Mais de três perguntas
- **WHEN** a mensagem tem quatro ou mais perguntas
- **THEN** o sistema responde uma, mostra até duas como sugestões e pede para enviar as demais separadamente

### Requirement: Ordem das respostas
Ao responder uma mensagem com mais de uma pergunta, o sistema SHALL seguir esta ordem: alerta de risco imediato, depois triagem, depois a ordem em que a usuária escreveu.

#### Scenario: Triagem antes de benefício
- **WHEN** a mensagem pergunta primeiro sobre um benefício e depois se ela corre perigo
- **THEN** a resposta mostrada é a da triagem, e a de benefícios fica como pergunta sugerida

#### Scenario: Ordem escrita
- **WHEN** a mensagem tem uma pergunta jurídica seguida de uma de rede, sem triagem
- **THEN** a resposta mostrada é a jurídica, e a de rede fica como pergunta sugerida

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

### Requirement: Fora do tema
Quando o orquestrador escolher "fora do tema", o sistema SHALL responder com a recusa padrão, que indica o Ligue 180 e a Defensoria Pública do DF, sem buscar trechos de lei e sem gerar texto com o LLM.

#### Scenario: Pergunta sobre outro assunto
- **WHEN** a usuária pergunta "qual a previsão do tempo amanhã?"
- **THEN** o sistema mostra a recusa padrão com o Ligue 180 e a Defensoria Pública do DF

### Requirement: Sem memória entre perguntas
Cada mensagem SHALL ser respondida sem as anteriores. As perguntas sugeridas que vierem da separação MUST ficar só na memória da página e MUST ser apagadas ao fechar a página e na saída rápida.

#### Scenario: Pergunta depois de outra
- **WHEN** a usuária envia uma segunda mensagem
- **THEN** o pedido não contém a primeira mensagem nem a resposta dela

#### Scenario: Saída rápida com sugestões na tela
- **WHEN** há perguntas sugeridas da separação na tela e a usuária aciona a saída rápida
- **THEN** as sugestões são apagadas junto com a conversa

### Requirement: Cartão de benefícios na conversa
Quando a pergunta for "tenho direito?", o sistema SHALL avaliar a regra no aparelho, com o perfil, e mostrar na conversa um cartão no formato comum de resultado: situação, motivos, o que falta, onde pedir, norma, artigo, data de verificação e aviso de que a concessão depende do órgão. Sem perfil, MUST convidar ao formulário.

#### Scenario: Benefício citado com perfil
- **WHEN** a usuária com perfil preenchido pergunta "tenho direito ao BPC?"
- **THEN** a conversa mostra o cartão do BPC com a situação, a norma, o artigo e a data de verificação

#### Scenario: Sem benefício citado
- **WHEN** a usuária com perfil preenchido pergunta "tenho direito a algum auxílio?"
- **THEN** a conversa mostra os cartões de todos os benefícios avaliados

#### Scenario: Sem perfil
- **WHEN** a usuária sem perfil pergunta se tem direito a um benefício
- **THEN** a conversa convida a preencher o formulário, com 190 e Ligue 180 visíveis, e nada é enviado

### Requirement: Triagem e rede pela conversa
Quando o orquestrador escolher triagem, a conversa SHALL oferecer a avaliação de risco no aparelho. Quando escolher rede, SHALL mostrar serviços do DF ordenados pela RA do texto ou do perfil e levar à lista completa.

#### Scenario: Pergunta de risco
- **WHEN** a usuária pergunta "será que eu corro perigo?"
- **THEN** a conversa oferece começar a avaliação de risco, e nenhuma resposta da triagem é enviada

#### Scenario: Pergunta de serviço com RA
- **WHEN** a usuária pergunta onde buscar ajuda e cita Ceilândia
- **THEN** a conversa mostra primeiro os serviços de Ceilândia, com fonte, data de verificação e a recomendação de confirmar por telefone

### Requirement: Registro do roteamento sem texto
Cada decisão do orquestrador SHALL ser registrada no log só com quem decidiu (regra, LLM ou reserva) e o agente escolhido. O registro MUST NOT conter o texto da mensagem, as perguntas reescritas ou os campos tirados do texto.

#### Scenario: Mensagem roteada
- **WHEN** uma mensagem é roteada
- **THEN** o log tem uma linha com quem decidiu e o agente, e nenhum trecho do texto

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
