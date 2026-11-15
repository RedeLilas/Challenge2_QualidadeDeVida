# triagem-risco Specification

## Purpose
Garantir que nenhuma situação de perigo seja subestimada: detectar risco imediato em qualquer ponto da conversa e levar ao 190, e classificar o nível de urgência com perguntas derivadas do Formulário Nacional de Avaliação de Risco (Fonar). Origem: RF04, RF05, RNF01, RNF05.

## Requirements

### Requirement: Alerta de risco imediato
O sistema SHALL detectar sinais de risco imediato em qualquer mensagem, em qualquer etapa da conversa, e exibir a orientação de ligar 190 antes de qualquer outra resposta. A detecção MUST ser feita por regra determinística, sem chamar o LLM.

#### Scenario: Ameaça com arma no momento
- **WHEN** a usuária escreve "ele está aqui em casa com uma faca"
- **THEN** o sistema exibe o botão "Ligar 190" em até 2 segundos
- **AND** nenhuma resposta gerada pelo LLM é exibida antes do alerta

#### Scenario: Risco no meio de outra conversa
- **WHEN** a usuária está consultando benefícios e escreve "ele disse que vai me matar hoje"
- **THEN** o sistema interrompe o fluxo de benefícios e exibe o alerta de 190 primeiro

#### Scenario: Pessoa de confiança relatando risco de outra
- **WHEN** a usuária está no modo "estou ajudando outra pessoa" e relata que a vítima está trancada em casa com o agressor armado
- **THEN** o sistema orienta ligar 190 informando o endereço da vítima

#### Scenario: Alerta sem conexão
- **WHEN** a usuária está sem internet e escreve uma frase de risco imediato
- **THEN** a PWA exibe o alerta de 190 usando as regras locais

### Requirement: Regras de risco auditáveis
As regras de risco imediato SHALL ficar em um arquivo versionado, legível pela equipe, compartilhado entre a PWA e o backend. A suíte de testes MUST conter frases fictícias de risco e de não risco, e MUST falhar diante de qualquer falso negativo.

#### Scenario: Falso negativo na suíte
- **WHEN** uma frase marcada como risco imediato na suíte de testes não dispara o alerta
- **THEN** a suíte falha e a mudança não pode ser concluída

#### Scenario: Variações de escrita
- **WHEN** a frase de risco é escrita sem acentos, em maiúsculas ou com erros de digitação comuns ("vai me matah")
- **THEN** a regra dispara da mesma forma

### Requirement: Triagem de urgência baseada no Fonar
O sistema SHALL oferecer uma triagem com perguntas derivadas do modelo vigente do Fonar (Lei 14.149/2021 e Portaria Conjunta CNJ/CNMP nº 6/2025), adaptadas para autoaplicação, que resultam em um nível de urgência. As regras de classificação MUST ser determinísticas e conservadoras: na dúvida, o nível mais alto.

#### Scenario: Respostas indicam risco alto
- **WHEN** a usuária responde que o agressor tem acesso a arma de fogo e já ameaçou matá-la
- **THEN** o sistema classifica o risco como alto, orienta ligar 190 e explica como pedir medida protetiva

#### Scenario: Usuária interrompe a triagem
- **WHEN** a usuária abandona a triagem no meio ou aciona a saída rápida
- **THEN** nenhuma resposta da triagem fica salva no aparelho ou no servidor

#### Scenario: Pergunta não respondida
- **WHEN** a usuária pula uma pergunta que poderia elevar o nível de risco
- **THEN** o sistema não reduz o nível por causa da ausência de resposta

#### Scenario: Pulo em pergunta de atenção
- **WHEN** a usuária não aciona nenhum gatilho alto e pula ou responde "não sei" em uma pergunta de atenção
- **THEN** o resultado é, no mínimo, "atenção", e nunca "sem sinais graves"

### Requirement: Aviso de limite em todo resultado da triagem
O sistema SHALL informar, junto a todo resultado de triagem, que a classificação não substitui a avaliação de um profissional da rede de atendimento.

#### Scenario: Resultado sem sinais graves
- **WHEN** a triagem resulta em "sem sinais graves"
- **THEN** o sistema mostra o aviso de limite e indica o Ligue 180 e os serviços do DF para avaliação profissional, sem usar a expressão "risco baixo"

### Requirement: Níveis da triagem sem pontuação
A triagem SHALL classificar sem pontuação. Alto: ameaça com arma ou faca (item 1), agressão grave (2), medida descumprida (5.1) ou acesso a arma (11). Atenção: ameaça de outra forma (1) ou resposta afirmativa nos itens 3, 4, 6, 9, 12, 13, 15 ou 22. Sem sinais graves: nenhum dos anteriores.

#### Scenario: Gatilho de arma
- **WHEN** a usuária responde que o agressor já a ameaçou com faca
- **THEN** o resultado é alto

#### Scenario: Sinal de atenção
- **WHEN** nenhum gatilho alto é acionado e a usuária responde que mora com o agressor
- **THEN** o resultado é atenção

#### Scenario: Nenhum sinal
- **WHEN** a usuária responde negativamente a todas as perguntas
- **THEN** o resultado é "sem sinais graves"

### Requirement: Risco alto não descartado
Quando a usuária pular ou responder "não sei" em um dos quatro gatilhos, e nenhum gatilho alto for confirmado, o sistema SHALL mostrar "não foi possível descartar risco alto", com as orientações do nível alto.

#### Scenario: "Não sei" sobre acesso a arma
- **WHEN** a usuária responde "não sei" sobre o acesso do agressor a arma de fogo
- **THEN** o resultado é "não foi possível descartar risco alto", com as orientações do nível alto

### Requirement: Ordem e limite das perguntas
A triagem SHALL ter no máximo 13 perguntas, com os gatilhos primeiro, e MUST encerrar no primeiro gatilho alto confirmado. A numeração dos itens MUST seguir `dados/fonar/notas.md`.

#### Scenario: Encerramento no primeiro gatilho
- **WHEN** a usuária confirma agressão grave no segundo gatilho
- **THEN** a triagem encerra e mostra o resultado alto sem fazer as demais perguntas

### Requirement: Triagem só no navegador e sem LLM
A triagem SHALL rodar só no navegador, com regras em arquivo versionado e texto fixo. As respostas MUST ficar só em memória e MUST NOT ser enviadas ao servidor ou ao LLM.

#### Scenario: Triagem sem conexão
- **WHEN** a usuária abre a triagem sem internet
- **THEN** a triagem funciona até o resultado

#### Scenario: Nada enviado
- **WHEN** a usuária conclui a triagem
- **THEN** nenhuma requisição contém as respostas, e nenhuma resposta é gravada no aparelho
