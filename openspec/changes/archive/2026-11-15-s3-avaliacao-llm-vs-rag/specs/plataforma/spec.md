# Spec Delta

## MODIFIED Requirements

### Requirement: Provedor de LLM configurável
O backend SHALL acessar o LLM por uma interface única compatível com a API da OpenAI, e a troca entre o modelo local e o de produção MUST ser feita apenas por variáveis de ambiente, inclusive o controle do raciocínio do modelo.

#### Scenario: Troca para produção
- **WHEN** as variáveis `LLM_BASE_URL` e `LLM_MODEL` apontam para o DeepSeek
- **THEN** o sistema passa a usar o DeepSeek sem nenhuma alteração de código

#### Scenario: Provedor indisponível
- **WHEN** o provedor de LLM não responde
- **THEN** o sistema informa que não consegue responder agora e indica o Ligue 180, e o alerta de 190 continua funcionando

#### Scenario: Raciocínio desligado
- **WHEN** a variável de controle do raciocínio pede o raciocínio desligado
- **THEN** a chamada ao modelo envia o parâmetro que desliga o raciocínio

#### Scenario: Variável de raciocínio ausente
- **WHEN** a variável de controle do raciocínio não está definida
- **THEN** a chamada ao modelo não envia esse parâmetro, e o modelo local continua funcionando

### Requirement: Implantação contínua
A aplicação SHALL estar publicada em uma URL de teste a partir da S5, a partir de um único container, e cada mudança concluída a partir da S5 MUST estar publicada antes de ser arquivada.

#### Scenario: Mudança concluída
- **WHEN** uma mudança é arquivada a partir da S5
- **THEN** a versão com essa mudança está acessível na URL de teste

#### Scenario: Mudança concluída antes da S5
- **WHEN** uma mudança é arquivada antes da S5
- **THEN** o arquivamento não depende de publicação
