# Spec Delta

## ADDED Requirements

### Requirement: Navegação entre as funções
A PWA SHALL oferecer acesso a Conversa, Triagem, Perfil, Benefícios e Onde buscar ajuda em uma única página. A tela inicial MUST continuar sendo a conversa, pronta para digitar.

#### Scenario: Abrir o aplicativo
- **WHEN** a usuária abre a PWA
- **THEN** a conversa aparece primeiro e as outras funções ficam acessíveis pela navegação

#### Scenario: Saída rápida em cada tela
- **WHEN** a usuária navega para qualquer função
- **THEN** o botão de saída rápida continua visível

#### Scenario: Navegação sem conexão
- **WHEN** a usuária está sem internet e navega entre as funções
- **THEN** as telas carregam, e as que precisam de conexão avisam disso
