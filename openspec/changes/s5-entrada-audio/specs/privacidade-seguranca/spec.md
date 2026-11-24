# Spec Delta

## ADDED Requirements

### Requirement: Áudio nunca guardado
O áudio da usuária SHALL ser processado só no servidor da própria aplicação e MUST NOT ser enviado a serviço externo nem gravado em disco, banco ou cache, inclusive quando a transcrição falhar. A resposta com a transcrição MUST usar `Cache-Control: no-store`.

#### Scenario: Transcrição concluída
- **WHEN** o servidor transcreve um áudio
- **THEN** nenhum arquivo novo fica no disco do servidor, e a resposta traz `Cache-Control: no-store`

#### Scenario: Transcrição com falha
- **WHEN** a transcrição falha por arquivo corrompido, limite excedido ou erro do modelo
- **THEN** nenhum arquivo novo fica no disco do servidor, e o erro devolvido não contém o áudio nem trecho da fala

#### Scenario: Nenhum serviço externo
- **WHEN** um áudio é transcrito com o modelo já carregado
- **THEN** o servidor não abre conexão com nenhum serviço externo

### Requirement: Áudio e transcrição fora dos logs
Os logs do servidor SHALL registrar da transcrição só dados técnicos (rota, status, tempo, tipo de erro) e MUST NOT registrar o áudio, a transcrição nem trechos dela, inclusive nos logs das bibliotecas de transcrição.

#### Scenario: Log de uma transcrição
- **WHEN** um áudio fictício é transcrito com sucesso e outro falha
- **THEN** os logs capturados não contêm nenhuma palavra da transcrição nem bytes do áudio

### Requirement: Microfone só no toque
O sistema SHALL pedir a permissão do microfone só quando a usuária tocar no botão de gravar, MUST manter o áudio só na memória da aba e MUST NOT salvá-lo no aparelho (armazenamento local, cache ou arquivo baixado). Ao fim do envio, o microfone MUST ser desligado e o áudio descartado da memória.

#### Scenario: Abrir a conversa
- **WHEN** a usuária abre a conversa sem tocar no microfone
- **THEN** o navegador não pede a permissão do microfone

#### Scenario: Depois de enviar
- **WHEN** a gravação termina e o áudio é enviado
- **THEN** o indicador de microfone do navegador se apaga, e nada do áudio fica no armazenamento do aparelho

### Requirement: Saída rápida durante a gravação
A saída rápida SHALL interromper uma gravação ou transcrição em andamento, desligar o microfone e descartar o áudio antes de substituir a página.

#### Scenario: Agressor se aproxima durante a gravação
- **WHEN** a usuária toca em "sair" enquanto grava
- **THEN** a gravação para, o microfone é desligado, nada é enviado ao servidor e a página é substituída pelo site neutro

#### Scenario: Saída durante a transcrição
- **WHEN** a usuária toca em "sair" enquanto o áudio está sendo transcrito
- **THEN** o pedido é cancelado e a transcrição, se chegar, não é exibida
