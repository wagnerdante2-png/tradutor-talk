# Tradutor Talk

Tradutor Talk é um intérprete bidirecional de voz com arquitetura desktop preservada e laboratório remoto via GitHub Codespaces.

## Laboratório atual: Gemini Live Translate

O caminho de teste no notebook corporativo agora usa diretamente:

~~~text
Chrome
  -> microfone PCM 16 kHz
  -> Gemini 3.5 Live Translate
  -> áudio traduzido PCM 24 kHz
  -> fone do navegador
~~~

O modelo usado é:

~~~text
gemini-3.5-live-translate-preview
~~~

Ele é específico para tradução speech-to-speech em tempo real. A direção é definida somente pelo idioma-alvo:

~~~text
Interlocutor fala -> idioma alvo = seu idioma
Você fala         -> idioma alvo = idioma do interlocutor
~~~

O idioma de origem é detectado pelo modelo.

## Por que Gemini no laboratório

A API Gemini possui nível gratuito para modelos compatíveis, incluindo o Live Translate dentro dos limites do free tier. O Ultimecia Code já usa Gemini por chave local e HTTP direto; o Tradutor Talk mantém a mesma filosofia de chave no backend, sem expô-la ao frontend.

A chave principal nunca é enviada ao navegador. O fluxo é:

~~~text
GEMINI_API_KEY
    fica no Codespace
        |
        v
backend pede token efêmero restrito
        |
        v
navegador recebe token de uso curto
        |
        v
WebSocket direto Chrome <-> Gemini Live
~~~

Isso evita o proxy de áudio pelo Codespace e reduz latência.

## Teste via Codespaces

1. Atualize/crie um Codespace no branch main.
2. A porta 8000 inicia automaticamente.
3. Se a porta Private retornar HTTP 401 neste notebook, mude temporariamente para Public.
4. Obtenha o token do laboratório:

~~~text
cat /tmp/tradutor-talk-lab-token
~~~

5. Cole o token na página.
6. Informe uma GEMINI_API_KEY.
7. Se você já possui a chave usada no Ultimecia, pode reutilizá-la desde que ela continue válida.
8. Caso a chave antiga seja rejeitada, gere/migre uma chave de autenticação atual no Google AI Studio.
9. Escolha os idiomas e inicie uma das direções.

Ao terminar, volte a porta para Private ou pare o Codespace.

## Streaming

O navegador envia áudio PCM mono 16-bit a 16 kHz em blocos próximos de 100 ms.

O Gemini retorna áudio PCM mono 16-bit a 24 kHz em streaming. O navegador agenda os blocos de saída para reprodução contínua.

A interface também mostra:

- transcrição da fala original;
- transcrição traduzida;
- tempo de abertura da conexão;
- tempo até o primeiro áudio traduzido;
- direção ativa.

## Arquitetura desktop preservada

Nada disso elimina o caminho desktop futuro:

~~~text
REMOTO -> entrada remota -> engine -> saída local -> VOCÊ
VOCÊ   -> entrada local  -> engine -> saída remota -> INTERLOCUTOR
~~~

O Codespaces Lab é um adaptador temporário de teste. O desktop continuará sendo importante para integração com dispositivos virtuais de áudio e chamadas externas.

## Segurança

Existem três camadas separadas:

~~~text
porta Codespaces
  -> token aleatório do laboratório
      -> GEMINI_API_KEY somente no backend
          -> token efêmero Gemini no navegador
~~~

A página pública não recebe sua GEMINI_API_KEY.

## OpenAI

O core OpenAI desenvolvido anteriormente permanece no repositório como provider alternativo/futuro. Ele não é necessário para o laboratório web atual e ChatGPT Plus não é usado como credencial de API.

## Sem Actions

Nenhum workflow de GitHub Actions é necessário para desenvolver ou executar o laboratório.
