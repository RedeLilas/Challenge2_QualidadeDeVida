# Spec Delta

## Purpose

Garantir que nenhuma situação de perigo seja subestimada: detectar risco imediato em qualquer ponto da conversa e levar ao 190, e classificar o nível de urgência com perguntas derivadas do Formulário Nacional de Avaliação de Risco (Fonar). Origem: RF04, RF05, RNF01, RNF05.

## ADDED Requirements

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

### Requirement: Aviso de limite da triagem
O sistema SHALL informar, junto a todo resultado de triagem, que a classificação não substitui a avaliação de um profissional da rede de atendimento.

#### Scenario: Resultado de risco baixo
- **WHEN** a triagem resulta em risco baixo
- **THEN** o sistema mostra o aviso de limite e indica o Ligue 180 e os serviços do DF para avaliação profissional
