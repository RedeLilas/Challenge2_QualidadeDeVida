# Design

## Context

A especificação exige alerta em até 2 s, sem LLM, em qualquer ponto da conversa e também sem conexão. A PWA é escrita em JS puro e o backend em Python, então as mesmas regras precisam rodar nos dois lados.

## Goals / Non-Goals

**Goals:**
- Zero falso negativo na suíte de risco.
- Uma única fonte de regras, legível por quem não programa.

**Non-Goals:**
- Classificar níveis de risco (isso é a triagem do Fonar, S3).
- Reduzir falsos positivos ao mínimo: um alerta desnecessário custa pouco, um alerta perdido pode custar uma vida.

## Decisions

### Regras em JSON compartilhado

```json
{
  "versao": "2026-11-05",
  "regras": [
    {
      "id": "arma-presente",
      "categoria": "arma",
      "padrao": "\\b(faca|arma|revolver|pistola|facao)\\b.*\\b(aqui|agora|na mao|apontando)\\b",
      "exemplo": "ele esta aqui com uma faca",
      "justificativa": "Arma presente no momento"
    }
  ]
}
```

- Categorias iniciais: arma presente, ameaça de morte iminente, agressão em andamento, cárcere (trancada, impedida de sair), ferimento grave e criança em perigo imediato.
- Os padrões usam só o subconjunto de expressão regular comum a Python (`re`) e JavaScript (sem lookbehind e sem grupos nomeados), para que o mesmo arquivo funcione nos dois lados.
- Os padrões são aplicados sobre o texto normalizado.

### Normalização idêntica
Minúsculas, remoção de acentos (decomposição NFD e remoção de marcas), espaços colapsados. As variações comuns de digitação são tratadas nos padrões (ex.: `matar|matah|mata`).

### Duas camadas
1. **PWA:** verifica antes de enviar e mostra o alerta na hora, mesmo offline. O service worker guarda o JSON em cache.
2. **Backend:** verifica de novo antes de chamar o LLM. Se houver risco, responde só com o alerta e não chama o LLM.

A camada do backend protege contra uma PWA desatualizada; a da PWA garante tempo e funcionamento offline.

Implementação no backend (05/11): a checagem roda nas **duas** rotas de conversa, `/juridico` (que a tela usa desde `s2-rag-juridico`) e `/mensagem`, e vem **antes** de obter o cliente de LLM e o índice. Assim o alerta não depende de o LLM estar configurado (spec `plataforma`, "Provedor indisponível") e não espera a montagem do índice ao subir o servidor (medido: 4 ms logo após o início). Com risco, a rota devolve `{"risco_imediato": true, "categoria", "resposta"}`, com o texto do alerta, e não chama o LLM.

Implementação na PWA (05/11):
- `web/risco.js` repete a normalização e a avaliação do `app/risco.py` e lê o mesmo JSON, servido em `/regras/risco_imediato.json`. O service worker guarda os dois arquivos, então o alerta funciona sem internet. `tests/test_risco_js.py` roda o JavaScript no QuickJS e confere que ele dá o mesmo resultado que o Python em todas as frases da suíte.
- A checagem local vem antes do aviso de "sem internet" e antes do envio. Com risco, a mensagem **não é enviada** ao servidor: o alerta aparece na hora e nada sai do aparelho. Se as regras não tiverem carregado, a mensagem segue e o servidor checa.
- O alerta aparece na própria conversa (não é uma janela por cima): título "Você pode estar em perigo agora.", botão "Ligar 190" (`tel:190`) em destaque e com foco, orientação para informar o endereço quando a vítima é outra pessoa e "Ligar 180" como opção secundária. A conversa continua depois do alerta, e o botão Sair segue visível no topo.
- Verificação manual da tarefa 2.2 (05/11, Chrome no computador, localhost): 5 frases da suíte, uma por categoria e com variações de escrita, mostraram o alerta com "Ligar 190" online e offline, sem enviar a mensagem ao servidor. O primeiro teste falhou porque o navegador reaproveitava o `app.js` antigo (arquivos sem `Cache-Control`); corrigido com `no-cache` no servidor e `cache: "reload"` no service worker.

### Suíte de testes
`tests/casos_risco.yaml`, com cerca de 30 frases fictícias de risco e 30 de não risco, escritas pela equipe. O teste falha se qualquer frase de risco não disparar o alerta. Falsos positivos são contados e reportados, mas não reprovam a suíte.

## Risks / Trade-offs

- **Regras por palavra-chave deixam passar formulações inesperadas**: mitigação com triagem do Fonar na S3, revisão das regras a cada falha encontrada na avaliação e padrões amplos.
- **Muitos falsos positivos irritam a usuária**: o alerta é curto, não bloqueia a conversa e permite continuar depois de exibido.
- **Diferenças entre Python e JS nas regex**: mitigação com o subconjunto comum e um teste que confere se cada padrão compila nos dois formatos (checagem de sintaxe proibida no Python).
