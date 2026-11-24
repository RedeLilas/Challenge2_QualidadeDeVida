# Spec Delta

## ADDED Requirements

### Requirement: Servidor publicado sem log de acesso
O servidor da versão publicada SHALL rodar sem o log de acesso do servidor web, e os logs da aplicação MUST conter só os dados técnicos do middleware (método, rota, status, duração e tipo de erro), sem query string e sem o IP de quem acessa.

#### Scenario: Requisição com query string
- **WHEN** a equipe acessa a URL publicada com uma query string fictícia e envia uma pergunta fictícia
- **THEN** os logs da aplicação na plataforma mostram só a rota, o status e o tempo, sem a query string, sem o IP e sem o texto da pergunta
