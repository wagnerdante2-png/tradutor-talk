# Máquina de estados

Fluxo nominal:

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

Estados excepcionais reservados:

- `RECOVERING_NETWORK`
- `PROVIDER_UNAVAILABLE`
- `AUDIO_DEVICE_LOST`
- `RATE_LIMITED`
- `SESSION_ERROR`

Transições inválidas levantam `InvalidTransitionError`.

Cancelamento de uma operação retorna a sessão a `LISTENING`. Falhas não tratadas entram em `SESSION_ERROR`, preservando a exceção original para diagnóstico.

`reset()` é deliberadamente restrito a `IDLE` ou `LISTENING`; não é uma maneira genérica de furar a máquina de estados.
