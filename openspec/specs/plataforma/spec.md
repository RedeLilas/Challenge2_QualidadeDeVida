# plataforma Specification

## Purpose
Garantir a base técnica comum: trocar o provedor de LLM (local nos testes, DeepSeek em produção) sem mudar código, manter segredos fora do repositório e publicar a aplicação continuamente desde a S2.

## Requirements

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

### Requirement: Segredos fora do repositório
Chaves de API e demais segredos SHALL ser lidos de variáveis de ambiente e MUST NOT ser versionados.

#### Scenario: Verificação do repositório
- **WHEN** o repositório é inspecionado
- **THEN** não há chaves de API em nenhum arquivo versionado, e existe um `.env.example` sem valores reais

### Requirement: Implantação contínua
A aplicação SHALL estar publicada em uma URL de teste a partir da S5, a partir de um único container, e cada mudança concluída a partir da S5 MUST estar publicada antes de ser arquivada.

#### Scenario: Mudança concluída
- **WHEN** uma mudança é arquivada a partir da S5
- **THEN** a versão com essa mudança está acessível na URL de teste

#### Scenario: Mudança concluída antes da S5
- **WHEN** uma mudança é arquivada antes da S5
- **THEN** o arquivamento não depende de publicação

### Requirement: Decisão de privacidade do provedor registrada
O uso de um provedor de LLM em produção SHALL ser precedido de uma decisão registrada no design sobre transferência internacional de dados (LGPD, art. 33), incluindo como o texto é tratado antes do envio.

#### Scenario: Ativar o DeepSeek em produção
- **WHEN** a equipe configura o DeepSeek no ambiente publicado
- **THEN** existe um design arquivado com a decisão de privacidade correspondente
