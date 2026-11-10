# Spec Delta

## Purpose

Permitir que a usuária converse em linguagem natural (texto e, opcionalmente, áudio e foto) e que cada pergunta seja encaminhada ao agente certo: jurídico, benefícios, triagem ou rede de atendimento. Origem: RF08, RF09.

## ADDED Requirements

### Requirement: Perguntas sugeridas
O sistema SHALL oferecer perguntas sugeridas no início e após cada resposta, para quem não sabe por onde começar.

#### Scenario: Primeiro acesso
- **WHEN** a usuária abre a conversa
- **THEN** o sistema mostra sugestões como "O que ele faz comigo é crime?" e "Tenho direito a algum auxílio?"

### Requirement: Encaminhamento ao agente certo
Um orquestrador SHALL encaminhar cada mensagem ao agente adequado (jurídico, benefícios, triagem ou rede de atendimento), e a verificação de risco imediato MUST ocorrer antes do encaminhamento.

#### Scenario: Pergunta sobre benefício
- **WHEN** a usuária pergunta "tenho direito a bolsa família?"
- **THEN** a mensagem é tratada pelo agente de benefícios

#### Scenario: Mensagem com risco e pergunta
- **WHEN** a mensagem contém uma pergunta jurídica e um sinal de risco imediato
- **THEN** o alerta de 190 é exibido antes da resposta do agente jurídico

### Requirement: Modo de ajuda a outra pessoa
O sistema SHALL oferecer o modo "estou ajudando outra pessoa", que adapta a linguagem para a terceira pessoa e orienta como apoiar e encaminhar a vítima.

#### Scenario: Amiga pedindo ajuda
- **WHEN** a usuária ativa o modo de ajuda e pergunta o que pode fazer pela amiga
- **THEN** as respostas falam da vítima em terceira pessoa e incluem como apoiar sem expô-la ao agressor

### Requirement: Pergunta por áudio
O sistema SHALL aceitar perguntas por áudio, transcrevê-las e tratá-las como texto, sem guardar o arquivo de áudio. Prioridade: desejável (primeiro item a ser cortado se faltar tempo).

#### Scenario: Pergunta falada
- **WHEN** a usuária grava "ele pode tirar meus filhos de mim?"
- **THEN** o sistema transcreve, responde como se fosse texto e descarta o áudio

### Requirement: Leitura de documento fotografado
O sistema SHALL aceitar a foto de um documento (por exemplo, um boletim de ocorrência ou uma decisão de medida protetiva), extrair o texto e explicá-lo, sem guardar a imagem. Prioridade: desejável.

#### Scenario: Foto de decisão judicial
- **WHEN** a usuária envia a foto de uma decisão de medida protetiva
- **THEN** o sistema explica em linguagem simples o que a decisão determina e descarta a imagem
