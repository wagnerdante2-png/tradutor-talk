# Codespaces Lab — teste sem instalação local

## Objetivo

Executar o núcleo do Tradutor Talk dentro de um GitHub Codespace e usar somente o navegador do notebook como dispositivo de entrada/saída.

Nada do runtime Python precisa ser instalado no notebook corporativo.

## Arquitetura

~~~text
NOTEBOOK
Chrome
  | microfone
  v
HTTPS / porta privada do Codespace
  |
  v
CODESPACE
SessionController
  -> gpt-transcribe
  -> gpt-5.6-luna
  -> gpt-4o-mini-tts
  |
  v
HTTPS
  |
  v
Chrome
  -> fone/alto-falante
~~~

O modo web é um adaptador de I/O. O core e os providers usados pelo desktop permanecem os mesmos.

## 1. Criar o Codespace

No repositório:

~~~text
Code
-> Codespaces
-> Create codespace on main
~~~

O devcontainer fixa Python 3.12 e executa automaticamente:

~~~text
python -m pip install -e '.[dev,web]'
~~~

A instalação acontece dentro do ambiente Linux remoto.

## 2. Servidor

O devcontainer inicia o laboratório automaticamente quando o Codespace sobe.

Se a porta 8000 não aparecer ou se você reiniciar o servidor manualmente, use:

~~~text
python -m tradutor_talk.web
~~~

Alternativa:

~~~text
tradutor-talk-web
~~~

O log da inicialização automática fica em:

~~~text
/tmp/tradutor-talk-web.log
~~~

## 3. Abrir a porta

O Codespaces deve detectar a porta 8000 automaticamente.

Na guia PORTS/PORTAS:

- porta: 8000;
- visibilidade: Private/Privada;
- abra no navegador.

Não é necessário tornar a porta pública.

## 4. API key

Há duas formas.

### Opção A — somente nesta página/sessão

Se o backend não encontrar OPENAI_API_KEY, a interface exibe um campo de chave.

A chave é enviada ao backend do Codespace e colocada apenas na memória do processo atual. O Tradutor Talk não grava a chave em arquivo.

### Opção B — terminal/Codespaces secret

Configure OPENAI_API_KEY no ambiente do Codespace antes de iniciar o servidor.

Nesse caso o campo não aparece.

## 5. Primeiro teste

Mantenha:

~~~text
Você: Português (Brasil)
Interlocutor: English (US)
~~~

Fluxo:

1. clique em Interlocutor fala;
2. permita o microfone no Chrome;
3. fale uma frase em inglês;
4. clique em Parar e traduzir;
5. aguarde a tradução em português;
6. escute o WAV retornado;
7. clique em Você fala;
8. fale em português;
9. pare;
10. escute o inglês.

## Estados

O navegador não ignora a máquina de estados existente.

Quando o backend termina o TTS:

~~~text
SYNTHESIZING -> PLAYING
~~~

Ele só retorna para:

~~~text
LISTENING
~~~

quando o navegador informa que a reprodução acabou.

Se o Chrome bloquear autoplay, use o controle de áudio manualmente. O turno é fechado quando o evento ended ocorrer.

## Métricas exibidas

- STT ms;
- tradução ms;
- TTS ms;
- processamento total;
- texto original;
- texto traduzido;
- número de turnos mantidos em contexto.

## Limites do laboratório V0

- início/fim do turno é manual;
- apenas PT-BR ⇄ EN está no gate principal;
- áudio remoto de Teams/Meet/WhatsApp ainda não é capturado diretamente;
- a saída traduzida ainda não é injetada como microfone virtual;
- streaming contínuo ainda não está ativo.

Esses pontos são deliberados. O objetivo do laboratório é validar primeiro o ciclo real browser -> Codespace -> OpenAI -> browser.

## Próximo passo após o primeiro teste

Com as latências reais registradas, decidir:

1. VAD no browser;
2. streaming de transcrição;
3. TTS em streaming;
4. rota speech-to-speech/realtime;
5. integração com áudio remoto de chamadas.

A arquitetura desktop permanece disponível para o futuro equipamento próprio.
