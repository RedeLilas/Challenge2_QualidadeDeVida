# Spec Delta

## Purpose

Proteger a usuária diante de um agressor que pode ter acesso ao celular e tratar os dados conforme a LGPD: coletar o mínimo, guardar só no aparelho e permitir apagar tudo. Origem: RF01, RF07, RNF02, RNF04.

## ADDED Requirements

### Requirement: Perfil opcional e mínimo
O sistema SHALL oferecer um perfil opcional com apenas: Região Administrativa ou CEP, faixa de renda, inscrição no CadÚnico, vínculo com o INSS, número de filhos e existência de medida protetiva. O perfil MUST NOT pedir nome, CPF ou documento, e MUST ficar armazenado apenas no aparelho.

#### Scenario: Uso sem perfil
- **WHEN** a usuária nunca preenche o perfil
- **THEN** todas as funções continuam disponíveis, com perguntas pontuais quando necessário

#### Scenario: Perfil não sai do aparelho
- **WHEN** a usuária salva o perfil
- **THEN** os dados ficam só no armazenamento local do navegador e não são gravados no servidor

### Requirement: Saída rápida
O sistema SHALL exibir em todas as telas um botão de saída rápida que, com um toque, substitui a página por um site neutro e apaga a conversa em andamento.

#### Scenario: Agressor se aproxima
- **WHEN** a usuária toca em "sair"
- **THEN** a página é substituída por um site neutro e voltar no navegador não reabre a conversa

### Requirement: Sem histórico persistente
A conversa SHALL existir apenas na memória da aba aberta e MUST NOT ser gravada no aparelho ou no servidor.

#### Scenario: Reabrir o aplicativo
- **WHEN** a usuária fecha e reabre a PWA
- **THEN** nenhuma conversa anterior aparece

### Requirement: Apagar dados
O sistema SHALL permitir apagar o perfil e qualquer dado local com uma única ação.

#### Scenario: Apagar tudo
- **WHEN** a usuária aciona "apagar meus dados"
- **THEN** o perfil e qualquer dado local da aplicação são removidos do aparelho

### Requirement: Aparência discreta
A PWA SHALL usar nome e ícone que não remetam a violência, e MUST NOT enviar notificações.

#### Scenario: Tela inicial do celular
- **WHEN** a PWA está instalada
- **THEN** o nome e o ícone exibidos não mencionam violência, mulher ou denúncia

### Requirement: Dados pessoais fora dos logs
Os logs do servidor SHALL registrar apenas dados técnicos (horário, rota, tempo, erro) e MUST NOT registrar o texto das mensagens nem o perfil.

#### Scenario: Erro no processamento
- **WHEN** ocorre um erro ao responder uma mensagem
- **THEN** o log registra o tipo de erro sem o conteúdo da mensagem

### Requirement: Envio mínimo a serviços externos
O envio de texto a provedores externos (como o LLM em produção) SHALL seguir a decisão de privacidade registrada no design da plataforma, e o sistema MUST NOT enviar o perfil completo a esses provedores.

#### Scenario: Pergunta ao LLM
- **WHEN** o backend chama o LLM de produção
- **THEN** a requisição contém apenas a pergunta (tratada conforme a decisão registrada) e os trechos recuperados, sem o perfil
