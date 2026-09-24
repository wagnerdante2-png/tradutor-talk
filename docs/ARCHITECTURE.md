# Arquitetura

## Objetivo

Manter o núcleo de sessão independente de hardware, UI e fornecedor.

```text
UI / cliente
    ↓
SessionController
    ↓
StateMachine
    ↓
STTProvider → TranslationProvider → TTSProvider
    ↓                ↓
Audio             Context + Glossary
```

## Decisões

1. **Half-duplex primeiro.** Apenas uma utterance é processada por vez. Isso elimina sobreposição enquanto o núcleo amadurece.
2. **Providers por contrato.** O core conhece Protocols, não SDKs específicos.
3. **Sem persistência de áudio.** O `SessionController` recebe bytes, extrai a transcrição e não anexa áudio ao objeto `Utterance`.
4. **Contexto limitado.** Somente os últimos N turnos ficam em memória.
5. **Timeout e cancelamento.** Toda chamada de provider passa pelo mesmo mecanismo.
6. **Observabilidade.** Cada utterance mede STT, tradução, TTS e latência total.
7. **Mocks determinísticos.** A fundação pode ser validada sem internet, credenciais ou custo.
8. **I/O adiado.** Microfone, alto-falante e API real começam somente em M1+.

## Pacotes

- `core/`: estados, modelos e orquestração;
- `providers/`: contratos e adapters;
- `audio/`: buffers e contratos de dispositivos/VAD;
- `translation/`: contexto, idiomas e glossário;
- `infrastructure/`: configuração e logging;
- `app/`: composição e ponto de entrada.

## Limite de M0

M0 não acessa microfone real e não chama API externa. O objetivo é estabilizar contratos e orquestração antes de introduzir I/O imprevisível.
