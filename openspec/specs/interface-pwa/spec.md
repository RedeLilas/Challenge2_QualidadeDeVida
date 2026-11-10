# interface-pwa Specification

## Purpose
Garantir que a aplicação seja usável por mulheres com pouca familiaridade digital, em celular básico e conexão lenta, com linguagem simples e acessibilidade. Origem: RNF01, RNF06.

## Requirements

### Requirement: Linguagem simples
Os textos fixos da interface e as respostas SHALL usar linguagem simples, frases curtas e explicar termos jurídicos quando eles aparecerem.

#### Scenario: Termo jurídico na resposta
- **WHEN** uma resposta usa a expressão "medida protetiva de urgência"
- **THEN** a resposta explica o termo em uma frase simples

### Requirement: Acessibilidade
A interface SHALL atender ao WCAG 2.1 nível AA nas telas principais (conversa, perfil, serviços).

#### Scenario: Auditoria automatizada
- **WHEN** a auditoria de acessibilidade é executada nas telas principais
- **THEN** não há violações de nível A ou AA

### Requirement: Tempo de resposta
O sistema SHALL exibir 95% das respostas em até 10 segundos, medidos do envio da mensagem até a exibição da resposta.

#### Scenario: Medição de latência
- **WHEN** o conjunto de perguntas de teste é executado contra o ambiente publicado
- **THEN** o percentil 95 do tempo de resposta é de no máximo 10 segundos

### Requirement: Celular básico e conexão lenta
A PWA SHALL funcionar em celulares Android de entrada e em conexões 3G, e MUST manter a interface e o alerta de 190 disponíveis mesmo sem conexão.

#### Scenario: Sem conexão
- **WHEN** a usuária abre a PWA instalada sem internet
- **THEN** a interface carrega, o alerta de 190 funciona e o sistema avisa que as respostas precisam de conexão

### Requirement: Instalável
A aplicação SHALL ser instalável como PWA (manifest e service worker), com o nome e o ícone discretos definidos em `privacidade-seguranca`.

#### Scenario: Instalação no Android
- **WHEN** a usuária acessa a URL pelo Chrome no Android
- **THEN** o navegador oferece a opção de instalar o aplicativo
