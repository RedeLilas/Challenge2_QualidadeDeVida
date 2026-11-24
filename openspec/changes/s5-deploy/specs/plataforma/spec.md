# Spec Delta

## ADDED Requirements

### Requirement: Modelos locais incluídos na publicação
A versão publicada SHALL trazer, desde o build, o modelo de embeddings e o modelo de transcrição, e MUST NOT baixar modelos ao subir ou ao responder.

#### Scenario: Subir sem acesso ao repositório de modelos
- **WHEN** a aplicação publicada sobe com o download de modelos bloqueado (modo offline do Hugging Face)
- **THEN** o índice do RAG e a transcrição ficam prontos, e `/saude`, uma pergunta jurídica e uma transcrição respondem normalmente

### Requirement: Partida a frio medida
O tempo da partida a frio da versão publicada SHALL ser medido e registrado no design: do início do processo até `/saude` responder e até o índice e a transcrição ficarem prontos.

#### Scenario: Registro da medição
- **WHEN** a versão é publicada pela primeira vez na plataforma escolhida
- **THEN** o design registra a data, a plataforma, o plano e os dois tempos medidos

#### Scenario: Pergunta durante a partida a frio
- **WHEN** uma pergunta chega antes de o índice ficar pronto
- **THEN** a pergunta espera o índice ou recebe a mensagem de indisponibilidade com o Ligue 180, e o alerta de 190 continua funcionando no aparelho

### Requirement: Chave do LLM só no ambiente publicado
A chave do LLM de produção SHALL ser configurada só como variável de ambiente secreta da plataforma e MUST NOT aparecer na imagem ou no pacote publicado, no repositório nem nos logs de build.

#### Scenario: Inspeção do pacote publicado
- **WHEN** a equipe procura a chave no pacote publicado (camadas da imagem ou arquivos do build) e nos logs de build
- **THEN** a chave não é encontrada, e a aplicação publicada responde usando a variável de ambiente
