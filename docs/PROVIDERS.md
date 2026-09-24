# Contratos de providers

## STTProvider

Recebe bytes de áudio e dica opcional de idioma. Retorna texto, idioma detectado e confiança opcional.

## TranslationProvider

Recebe texto, idiomas de origem/destino, snapshot de contexto e glossário. Retorna texto traduzido.

## TTSProvider

Recebe texto e idioma. Retorna bytes de áudio e metadados mínimos.

## Regra arquitetural

SDKs externos deverão existir somente dentro de `providers/<fornecedor>/`. O restante do produto não deve importar SDK de provedor diretamente.

## Adapter mock

O adapter atual interpreta os bytes como UTF-8, traduz um conjunto determinístico de frases e devolve bytes fictícios de áudio. Ele não tenta simular fidelidade de IA: serve para validar controle de fluxo sem custo ou rede.

## Próximos adapters

- provider real de STT;
- provider real de tradução;
- provider real de TTS;
- rota realtime speech-to-speech opcional;
- providers locais futuros.
