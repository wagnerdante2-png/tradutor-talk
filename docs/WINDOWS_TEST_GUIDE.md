# Guia de teste Windows — caminho mais curto

## Objetivo

Validar o Tradutor Talk em hardware real antes de iniciar streaming/M6.

O projeto oferece dois cenários.

## Modo mesa

Serve para validar rapidamente microfone, VAD, STT, tradução PT-BR ⇄ EN, TTS, reprodução e repetição de rodadas.

Os dois lados usam o mesmo microfone e a mesma saída. Duas pessoas podem falar alternadamente na mesma máquina.

## Modo chamada roteada

Este é o cenário mais próximo do produto final.

~~~text
INTERLOCUTOR / CHAMADA
        |
        v
entrada de áudio remoto / virtual cable
        |
        v
STT -> tradução -> TTS
        |
        v
seu fone


VOCÊ
        |
        v
seu microfone
        |
        v
STT -> tradução -> TTS
        |
        v
saída virtual
        |
        v
microfone selecionado no app de chamada
~~~

O software mantém quatro papéis independentes:

- entrada local;
- entrada remota;
- saída local;
- saída remota.

## Teste mais rápido

No Windows, baixe ou clone o repositório e dê duplo clique em:

~~~text
TESTAR_WINDOWS.bat
~~~

O script:

1. verifica Python 3.12+;
2. cria .venv dentro da pasta;
3. instala as dependências do runtime;
4. executa os testes determinísticos;
5. abre o assistente interativo;
6. pede a chave da API somente se ela não existir no ambiente;
7. não salva a chave.

## Listar dispositivos

~~~bash
python -m tradutor_talk.app.device_probe
~~~

ou, após instalação:

~~~bash
tradutor-talk-devices
~~~

## Linha de comando

Teste de mesa com dispositivos padrão:

~~~bash
python -m tradutor_talk.app.handsfree_probe --rounds 1
~~~

Exemplo de chamada roteada:

~~~bash
python -m tradutor_talk.app.handsfree_probe ^
  --rounds 1 ^
  --local-input-device 1 ^
  --remote-input-device 6 ^
  --local-output-device 4 ^
  --remote-output-device 7
~~~

Os IDs são apenas exemplo. Use os IDs mostrados na sua máquina.

## Dispositivo virtual

Para uma chamada real, o Windows precisa expor uma rota que permita capturar o áudio do interlocutor como entrada e entregar a voz traduzida como um microfone que o aplicativo de chamada enxergue.

O Tradutor Talk não instala nem altera drivers de áudio do sistema automaticamente.

## Gate antes de M6

Durante o teste, observe:

- se o início da frase foi cortado;
- se o VAD encerrou cedo ou tarde;
- STT ms;
- tradução ms;
- TTS ms;
- playback ms;
- total do turno;
- dispositivo usado em cada papel;
- eventual eco;
- falha de API ou áudio.

Com esses dados, M6 deve atacar a parcela real de latência em vez de otimizar por hipótese.
