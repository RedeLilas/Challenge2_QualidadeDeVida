# Spec Delta

## Purpose

Indicar onde a usuária pode buscar atendimento no Distrito Federal (rede de proteção e serviços de saúde), com a origem e a data dos dados. Amplia o RF06, que cobria só os estabelecimentos do CNES.

## ADDED Requirements

### Requirement: Busca por Região Administrativa ou CEP
O sistema SHALL listar os serviços mais próximos a partir da Região Administrativa ou do CEP informado, com nome, endereço, telefone e horário de funcionamento.

#### Scenario: Busca por RA
- **WHEN** a usuária informa que mora em Ceilândia
- **THEN** o sistema lista primeiro os serviços localizados em Ceilândia e depois os mais próximos em outras RAs

#### Scenario: Busca por CEP
- **WHEN** a usuária informa um CEP do DF
- **THEN** o sistema ordena os serviços pela distância aproximada até esse CEP

### Requirement: Rede de proteção e rede de saúde
A base SHALL incluir a lista curada da rede de proteção do DF (Casa da Mulher Brasileira, CEAMs, DEAMs, Defensoria Pública, entre outros) e os estabelecimentos do CNES do DF com atendimento a vítimas de violência sexual.

#### Scenario: Violência sexual recente
- **WHEN** a usuária relata violência sexual ocorrida nas últimas 72 horas
- **THEN** o sistema prioriza os serviços de saúde de referência e explica que o atendimento rápido permite profilaxias que dependem do tempo

#### Scenario: Busca por delegacia
- **WHEN** a usuária pergunta onde registrar ocorrência
- **THEN** o sistema lista as DEAMs e informa a possibilidade de registro em qualquer delegacia

### Requirement: Origem e atualidade do dado
Cada serviço exibido SHALL mostrar a fonte e a data de verificação (ou a competência do CNES), e o sistema MUST orientar a confirmar por telefone antes de se deslocar.

#### Scenario: Exibição de um serviço
- **WHEN** um serviço aparece na lista
- **THEN** ele mostra a fonte, a data de verificação e a recomendação de confirmar por telefone

### Requirement: Usuária fora do DF
Quando a localização informada estiver fora do DF, o sistema SHALL informar que o mapa de serviços cobre só o DF e indicar o Ligue 180, mantendo disponíveis a orientação jurídica e a triagem.

#### Scenario: CEP de outro estado
- **WHEN** a usuária informa um CEP de Goiânia
- **THEN** o sistema explica que a lista de serviços cobre só o DF, indica o Ligue 180 e continua respondendo perguntas jurídicas
