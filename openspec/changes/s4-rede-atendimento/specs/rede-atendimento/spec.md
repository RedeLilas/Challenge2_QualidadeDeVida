# Spec Delta

## MODIFIED Requirements

### Requirement: Busca por Região Administrativa ou CEP
O sistema SHALL listar os serviços mais próximos a partir da Região Administrativa ou do CEP informado, com nome, endereço, telefone e horário de funcionamento. O CEP MUST ser convertido em RA no aparelho, por uma tabela local de faixas de CEP do DF com fonte e data, e a distância aproximada MUST ser dada pela RA.

#### Scenario: Busca por RA
- **WHEN** a usuária informa que mora em Ceilândia
- **THEN** o sistema lista primeiro os serviços localizados em Ceilândia e depois os mais próximos em outras RAs

#### Scenario: Busca por CEP
- **WHEN** a usuária informa um CEP do DF
- **THEN** o sistema mostra a RA desse CEP e ordena os serviços pela RA: primeiro os da mesma RA, depois os das RAs mais próximas

#### Scenario: RA que o site não lista
- **WHEN** o CEP informado pertence a uma RA fora da lista do site, como Sol Nascente/Pôr do Sol
- **THEN** o sistema mostra o nome real da RA e ordena os serviços como se fosse a RA da lista mais próxima, registrada na tabela

#### Scenario: CEP do DF sem faixa na tabela
- **WHEN** o CEP está na faixa do DF, mas em nenhuma faixa da tabela
- **THEN** o sistema avisa que não reconheceu a região, pede a RA e mostra os plantões 24 horas primeiro

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
- **WHEN** a usuária procura o CRAS e informa a RA ou o CEP
- **THEN** o sistema lista primeiro o CRAS da RA dela, ou o da RA mais próxima, com a fonte, a data de verificação e a recomendação de confirmar por telefone

## ADDED Requirements

### Requirement: CEP só no aparelho
O sistema SHALL converter o CEP em RA só no aparelho, seja ele do perfil, da tela de serviços ou digitado na conversa. Nenhuma requisição MUST conter o CEP da usuária, e o servidor MUST NOT devolver CEP da usuária.

#### Scenario: CEP digitado na conversa
- **WHEN** a usuária escreve "meu cep é 72215-110, onde tem delegacia?"
- **THEN** o texto enviado ao servidor não contém o CEP, e a lista de serviços é ordenada pela RA desse CEP

#### Scenario: CEP na tela de serviços
- **WHEN** a usuária digita um CEP na tela Onde buscar ajuda
- **THEN** a lista é reordenada sem nenhuma requisição que contenha o CEP

#### Scenario: CEP de fora do DF na conversa
- **WHEN** a usuária escreve um CEP de Goiânia na conversa
- **THEN** o CEP não é enviado, e o sistema explica que a lista de serviços cobre só o DF e indica o Ligue 180

### Requirement: Tabela de CEP com as 35 RAs
A tabela de faixas de CEP SHALL cobrir as 35 Regiões Administrativas do DF. Cada faixa MUST registrar a RA real, a RA da lista do site usada para ordenar, a fonte e a data de verificação.

#### Scenario: Cobertura das RAs
- **WHEN** a validação dos dados roda
- **THEN** cada uma das 35 RAs oficiais tem ao menos uma faixa, e toda faixa tem RA real, RA para ordenar, fonte e data

#### Scenario: Faixas sobrepostas
- **WHEN** duas faixas da tabela se sobrepõem
- **THEN** a validação dos dados falha e aponta as duas linhas
