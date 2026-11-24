# rede-atendimento Specification

## Purpose
Indicar onde a usuária pode buscar atendimento no Distrito Federal (rede de proteção e serviços de saúde), com a origem e a data dos dados. Amplia o RF06, que cobria só os estabelecimentos do CNES.

## Requirements

### Requirement: Busca por Região Administrativa ou CEP
O sistema SHALL listar os serviços mais próximos a partir da Região Administrativa, com nome, endereço, telefone e horário de funcionamento. A RA MUST vir do perfil ou da escolha na lista, e a distância aproximada MUST ser dada pela RA. O CEP informado MUST ser conferido no aparelho só para saber se é do DF, por uma tabela local com as faixas de CEP do DF, com fonte e data, porque a fonte oficial (Busca Faixa de CEP dos Correios) não separa o DF por RA.

#### Scenario: Busca por RA
- **WHEN** a usuária informa que mora em Ceilândia
- **THEN** o sistema lista primeiro os serviços localizados em Ceilândia e depois os mais próximos em outras RAs

#### Scenario: Busca por CEP
- **WHEN** a usuária informa um CEP do DF e o perfil tem a RA
- **THEN** o sistema ordena os serviços pela RA do perfil: primeiro os da mesma RA, depois os das RAs mais próximas

#### Scenario: CEP do DF sem RA
- **WHEN** a usuária informa um CEP do DF e nem o perfil nem a tela têm a RA
- **THEN** o sistema explica que o CEP não indica a RA, pede que ela escolha a RA na lista e mostra os plantões 24 horas primeiro

### Requirement: Rede de proteção e rede de saúde
A base SHALL incluir a lista curada da rede de proteção do DF (Casa da Mulher Brasileira, CEAMs, DEAMs, Defensoria Pública, entre outros), a lista curada de CRAS do DF e os serviços de saúde de referência para pessoas em situação de violência sexual, curados à mão, com o CNES como fonte do endereço e do telefone.

#### Scenario: Violência sexual recente
- **WHEN** a usuária relata violência sexual ocorrida nas últimas 72 horas
- **THEN** o sistema prioriza os serviços de saúde de referência e explica que o atendimento rápido permite profilaxias que dependem do tempo
- **AND** a explicação cita a Lei 12.845/2013 (atendimento imediato e obrigatório nos hospitais do SUS, com profilaxias) e orienta procurar o pronto-socorro de um hospital público

#### Scenario: Violência sexual sem tempo informado
- **WHEN** a mensagem fala de violência sexual sem dizer quando aconteceu
- **THEN** o sistema mostra os serviços de saúde primeiro e explica que, se tiver sido nas últimas 72 horas, o atendimento rápido é importante

#### Scenario: Busca por delegacia
- **WHEN** a usuária pergunta onde registrar ocorrência
- **THEN** o sistema lista as DEAMs e informa a possibilidade de registro em qualquer delegacia

#### Scenario: Busca por CRAS
- **WHEN** a usuária procura o CRAS e informa a RA
- **THEN** o sistema lista primeiro o CRAS da RA dela, ou o da RA mais próxima, com a fonte, a data de verificação e a recomendação de confirmar por telefone

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

### Requirement: CEP só no aparelho
O sistema SHALL conferir se o CEP é do DF só no aparelho, seja ele do perfil, da tela de serviços ou digitado na conversa. Nenhuma requisição MUST conter o CEP da usuária, e o servidor MUST NOT devolver CEP da usuária.

#### Scenario: CEP digitado na conversa
- **WHEN** a usuária escreve "meu cep é 72215-110, onde tem delegacia?"
- **THEN** o texto enviado ao servidor não contém o CEP, e a lista de serviços é ordenada pela RA do perfil, ou pede a RA se o perfil não tiver

#### Scenario: CEP na tela de serviços
- **WHEN** a usuária digita um CEP na tela Onde buscar ajuda
- **THEN** a tela confere se o CEP é do DF sem nenhuma requisição que contenha o CEP

#### Scenario: CEP de fora do DF na conversa
- **WHEN** a usuária escreve um CEP de Goiânia na conversa
- **THEN** o CEP não é enviado, e o sistema explica que a lista de serviços cobre só o DF e indica o Ligue 180

### Requirement: Faixas de CEP do DF
A tabela de faixas de CEP SHALL conter as faixas do DF publicadas pela Busca Faixa de CEP dos Correios (70000-000 a 72799-999 e 73000-000 a 73699-999). Cada faixa MUST registrar a fonte e a data de verificação. CEPs de 72800-000 a 72999-999 MUST NOT ser tratados como do DF.

#### Scenario: Faixas com fonte
- **WHEN** a validação dos dados roda
- **THEN** toda faixa está dentro do DF, tem início menor ou igual ao fim, fonte dos Correios e data

#### Scenario: CEP entre as duas faixas
- **WHEN** a usuária informa o CEP 72800-000
- **THEN** o sistema trata o CEP como de fora do DF

#### Scenario: Faixas sobrepostas
- **WHEN** duas faixas da tabela se sobrepõem
- **THEN** a validação dos dados falha e aponta as duas linhas
