# Projeto Técnico V1 — Tradutor Talk

## Missão

Construir um intérprete bidirecional de conversação em tempo real. O usuário fala PT-BR e o interlocutor fala outro idioma; o sistema converte cada direção para o idioma oposto e reproduz a tradução em áudio.

## Arquitetura de referência

```text
Áudio
  ↓
VAD / segmentação
  ↓
STT
  ↓
texto original
  ↓
tradução com contexto + glossário
  ↓
texto traduzido
  ↓
TTS
  ↓
áudio traduzido
```

O fluxo existe duas vezes, uma para cada direção.

## Decisão central

O produto não dependerá de uma única API speech-to-speech. STT, tradução e TTS possuem contratos independentes. Uma rota realtime direta poderá ser adicionada mais tarde como otimização, não como fundação obrigatória.

## Produto inicial

- Windows 10/11;
- Python 3.12+;
- half-duplex inteligente;
- PT-BR ⇄ EN;
- processamento online quando providers reais entrarem;
- sem gravação persistente por padrão;
- sem banco de dados;
- sem autenticação no MVP.

## Critérios de robustez

1. falha de provider não deve corromper estado;
2. toda etapa externa possui timeout;
3. operação corrente pode ser cancelada;
4. contexto é limitado;
5. utterances possuem identificador único;
6. latência é medida por etapa;
7. fila de conversa não deve crescer indefinidamente;
8. SDKs externos ficam isolados em adapters;
9. segredos nunca entram no repositório;
10. comportamento principal é testável sem internet.

## Estados

```text
IDLE
→ LISTENING
→ SPEECH_DETECTED
→ CAPTURING
→ END_OF_TURN
→ TRANSCRIBING
→ TRANSLATING
→ SYNTHESIZING
→ PLAYING
→ COOLDOWN
→ LISTENING
```

Estados de exceção são reservados para rede, indisponibilidade de provider, dispositivo de áudio, rate limit e erro de sessão.

## Estratégia de entrega

M0 estabiliza a arquitetura sem hardware ou API. M1 introduz apenas áudio real e STT. Tradução e TTS reais entram depois, um componente por vez.

Essa sequência é deliberada: o objetivo é avançar rápido sem transformar problemas de áudio, rede, IA e interface em um único defeito impossível de diagnosticar.

## Fora do escopo inicial

Login, cadastro, banco, servidor próprio, mobile, clonagem de voz, AR, avatars, reuniões multiusuário, tradução de vídeo, armazenamento em nuvem e painel administrativo.
