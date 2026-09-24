# Codespaces Lab — Gemini Live Translate

## Objetivo

Testar tradução voz→voz quase em tempo real sem instalar Python, drivers ou bibliotecas no notebook corporativo.

## Arquitetura

~~~text
NOTEBOOK CORPORATIVO
Chrome
  | microfone
  | PCM 16 kHz / ~100 ms
  v
Gemini Live Translate
  | áudio traduzido PCM 24 kHz
  v
Chrome / fone

CODESPACE
  usado apenas para:
  - servir a interface
  - guardar GEMINI_API_KEY
  - emitir token efêmero Gemini
~~~

O áudio ao vivo não precisa atravessar o backend do Codespace.

## Modelo

~~~text
gemini-3.5-live-translate-preview
~~~

O modelo faz tradução speech-to-speech de baixa latência e também fornece transcrição do áudio de entrada e da tradução.

## 1. Atualizar o Codespace

No terminal:

~~~text
git pull
~~~

Depois reinicie o servidor:

~~~text
pkill -f "tradutor_talk.web"
nohup python -m tradutor_talk.web >/tmp/tradutor-talk-web.log 2>&1 &
~~~

## 2. Porta 8000

Se a porta privada funcionar, mantenha Private.

Se este navegador corporativo retornar HTTP 401 na porta privada:

- mude temporariamente a porta 8000 para Public;
- use o token do laboratório;
- ao terminar, volte a porta para Private ou pare o Codespace.

## 3. Token do laboratório

~~~text
cat /tmp/tradutor-talk-lab-token
~~~

Cole o valor no primeiro painel da página.

Este token protege os endpoints do backend.

## 4. Gemini API key

Use a GEMINI_API_KEY já utilizada no Ultimecia, caso ainda esteja válida.

Ela é diferente do token do laboratório.

A chave é mantida somente em memória no Codespace e é usada para solicitar um token efêmero restrito ao Live Translate.

Se a chave antiga do Ultimecia for uma chave padrão legada e for rejeitada, crie/migre uma chave atual no Google AI Studio. Em 2026 a API Gemini migrou novas chaves para auth keys e passou a descontinuar chaves padrão.

## 5. Primeiro teste

Configure:

~~~text
VOCÊ: Português (Brasil)
INTERLOCUTOR: English (US)
~~~

### Interlocutor -> você

1. clique em Iniciar tradução ao vivo no cartão Interlocutor fala;
2. permita o microfone;
3. fale em inglês;
4. o texto original deve aparecer incrementalmente;
5. a tradução em português deve aparecer;
6. o áudio em português deve começar a tocar enquanto a fala ainda está em andamento;
7. clique em Parar sessão quando terminar.

### Você -> interlocutor

1. clique no cartão Você fala;
2. fale em português;
3. o alvo será English (US);
4. a voz traduzida em inglês será reproduzida neste laboratório.

Neste estágio ambos os fluxos usam o mesmo microfone e fone do navegador. A injeção direta em Meet/Teams/WhatsApp continua sendo uma etapa posterior do desktop/roteamento virtual.

## 6. Métricas

A interface mostra:

- Conexão: tempo até o WebSocket Live ficar pronto;
- 1º áudio: tempo até chegar o primeiro chunk de voz traduzida;
- Direção;
- modelo;
- transcrição original;
- transcrição traduzida.

## 7. Formatos

Entrada:

~~~text
PCM bruto
16-bit little-endian
mono
16 kHz
blocos ~100 ms
~~~

Saída:

~~~text
PCM bruto
16-bit little-endian
mono
24 kHz
streaming
~~~

## 8. Segurança

A GEMINI_API_KEY não é enviada ao navegador.

O Codespace solicita um token efêmero:

- uso único para abertura da sessão;
- expiração curta;
- restrito ao modelo Live Translate;
- restrito ao idioma-alvo solicitado.

O Chrome usa esse token no endpoint WebSocket constrained da API Live.

## 9. Free tier

O Gemini Developer API oferece free tier para determinados modelos. O Live Translate está listado com entrada e saída gratuitas dentro dos limites do nível gratuito.

O nível gratuito possui rate limits e o conteúdo pode ser usado pelo Google para melhorar produtos, conforme a política atual do free tier.

## 10. Próximas etapas depois do teste

Se o Live Translate funcionar:

1. medir latência real;
2. estabilizar captura/reprodução;
3. adicionar VAD/automação de direção;
4. testar espanhol, japonês e chinês;
5. estudar captura de áudio remoto de chamadas;
6. levar o mesmo provider para o runtime desktop futuro.
