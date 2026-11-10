# Spec Delta

## MODIFIED Requirements

### Requirement: Perfil opcional e mínimo
O sistema SHALL oferecer um formulário de perfil com apenas: Região Administrativa ou CEP, renda total aproximada da casa, número de pessoas da casa, inscrição no CadÚnico, vínculo com o INSS, número de filhos, existência de medida protetiva, idade e estado civil. O perfil MUST NOT pedir nome, CPF ou documento, e MUST ficar armazenado apenas no aparelho.

#### Scenario: Uso sem perfil
- **WHEN** a usuária nunca preenche o perfil
- **THEN** a conversa e a triagem continuam disponíveis, e Benefícios e Onde buscar ajuda pedem o formulário antes de abrir

#### Scenario: Perfil não sai do aparelho
- **WHEN** a usuária salva o perfil
- **THEN** os dados ficam só no armazenamento local do navegador, não são gravados no servidor e não são enviados ao LLM

#### Scenario: Perfil depois de fechar o aplicativo
- **WHEN** a usuária salva o perfil, fecha a PWA e a abre de novo sem ter acionado a saída rápida ou apagado os dados
- **THEN** o perfil continua disponível, e nenhuma conversa anterior aparece

#### Scenario: Prefiro não informar
- **WHEN** a usuária marca "prefiro não informar" em um campo
- **THEN** o formulário é aceito como preenchido, e nenhum valor é inventado para esse campo

### Requirement: Saída rápida
O sistema SHALL exibir em todas as telas um botão de saída rápida que, com um toque, substitui a página por um site neutro e apaga a conversa em andamento e o perfil guardado.

#### Scenario: Agressor se aproxima
- **WHEN** a usuária toca em "sair"
- **THEN** a página é substituída por um site neutro, voltar no navegador não reabre a conversa e o perfil é removido do aparelho

### Requirement: Apagar dados
O sistema SHALL permitir apagar o perfil e qualquer dado local com uma única ação, sem remover o que mantém a interface e o alerta de 190 funcionando sem internet.

#### Scenario: Apagar tudo
- **WHEN** a usuária aciona "apagar meus dados"
- **THEN** o perfil e qualquer dado local da aplicação são removidos do aparelho

#### Scenario: Alerta depois de apagar
- **WHEN** a usuária apaga os dados e fica sem internet
- **THEN** a interface carrega e o alerta de 190 continua funcionando

## ADDED Requirements

### Requirement: Funções que exigem o formulário
Benefícios e Onde buscar ajuda SHALL exigir o formulário de perfil preenchido antes de abrir. A conversa, a triagem, o alerta de 190 e a saída rápida MUST funcionar sem o formulário, e os telefones 190 e Ligue 180 MUST ficar visíveis no formulário e nas telas bloqueadas.

#### Scenario: Benefícios sem formulário
- **WHEN** a usuária abre Benefícios sem ter preenchido o formulário
- **THEN** o sistema mostra o formulário, com 190 e Ligue 180 visíveis

#### Scenario: Triagem sem formulário
- **WHEN** a usuária abre a triagem sem ter preenchido o formulário
- **THEN** a triagem começa normalmente

#### Scenario: Risco imediato durante o formulário
- **WHEN** a usuária está no formulário e toca em ligar para o 190
- **THEN** a ligação é iniciada sem exigir o preenchimento
