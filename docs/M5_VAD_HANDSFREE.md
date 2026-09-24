# M5 — VAD local e hands-free

## Objetivo

Remover o botão/Enter do ciclo normal de conversa sem introduzir full-duplex prematuramente.

O modo atual continua half-duplex:

~~~text
OUVIR INTERLOCUTOR
      ↓
detectar início/fim
      ↓
STT → tradução → TTS
      ↓
reproduzir para o usuário
      ↓
OUVIR USUÁRIO
      ↓
detectar início/fim
      ↓
STT → tradução → TTS
      ↓
reproduzir para o interlocutor
~~~

Como o microfone só volta ao estado de escuta depois que a reprodução termina, o TTS não é deliberadamente capturado como nova fala.

## VAD

O VAD é local e não consome API.

Padrão:

- WebRTC VAD;
- PCM16 mono;
- 16 kHz;
- frames de 20 ms;
- agressividade 2.

## Segmentador

A regra de fronteira é independente do microfone e do WebRTC VAD.

Parâmetros padrão:

- pré-roll: 200 ms;
- fala contínua para iniciar: 60 ms;
- silêncio para encerrar: 600 ms;
- timeout aguardando alguém falar: 30 s;
- utterance máxima: 20 s.

O pré-roll evita cortar o início de palavras quando o VAD confirma a fala alguns frames depois.

## Segurança operacional

- timeout sem fala não muda o lado da conversa;
- utterance possui limite máximo;
- overflow de microfone é erro explícito;
- áudio continua apenas em memória;
- nenhuma chamada de IA é feita enquanto só existe silêncio;
- a regra de segmentação possui testes determinísticos sem hardware.

## Execução

~~~bash
pip install -e ".[dev,runtime]"
python -m tradutor_talk.app.handsfree_probe
~~~

Por padrão:

- usuário: pt-BR;
- interlocutor: en-US;
- execução contínua;
- Ctrl+C encerra.

Teste de uma única rodada:

~~~bash
python -m tradutor_talk.app.handsfree_probe --rounds 1
~~~

## Critério de aceite

1. silêncio não dispara API;
2. início normal de frase não é cortado;
3. pequenas pausas no meio da frase não encerram o turno;
4. cerca de 600 ms de silêncio encerram o turno;
5. o TTS termina antes do próximo lado começar a escutar;
6. duas rodadas consecutivas funcionam sem reinício;
7. ruído ambiente comum não dispara repetidamente o VAD;
8. a latência STT + tradução + TTS é registrada.

## Próximo gate

M6 só deve começar depois de medir o M5 real.

Com esses dados decidiremos quais parcelas da latência justificam:

- STT streaming;
- tradução incremental;
- TTS streaming;
- ou rota direta GPT-Realtime-Translate.

A escolha será baseada em medição, não em hipótese.
