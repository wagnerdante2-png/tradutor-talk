# Contratos de providers

## STTProvider

Recebe bytes de áudio e dica opcional de idioma. Retorna texto, idioma detectado e confiança opcional.

Implementação atual:

- `OpenAISTTProvider`;
- modelo padrão `gpt-transcribe`;
- WAV recebido em memória;
- SDK carregado somente quando necessário.

## TranslationProvider

Recebe texto, idiomas de origem/destino, snapshot de contexto e glossário. Retorna texto traduzido.

Implementação atual:

- `OpenAITranslationProvider`;
- Responses API;
- modelo padrão `gpt-6-luna`;
- reasoning padrão `none`;
- `store=False`;
- contexto limitado a até oito turnos passados;
- conteúdo ouvido serializado como JSON e explicitamente tratado como dados, não como instruções.

## TTSProvider

Recebe texto e idioma. Retorna bytes de áudio e metadados mínimos.

Implementação atual:

- `OpenAITTSProvider`;
- modelo padrão `gpt-4o-mini-tts`;
- voz padrão `marin`;
- saída WAV;
- áudio devolvido ao core como bytes, sem persistência em disco.

## Regra arquitetural

SDKs externos devem existir somente dentro de `providers/<fornecedor>/`. O restante do produto não deve importar SDK de provedor diretamente.

Trocar STT, tradutor ou TTS não pode exigir alteração da máquina de estados ou dos modelos de domínio.

## Adapters mock

Os mocks interpretam bytes como UTF-8, traduzem um conjunto determinístico de frases e devolvem bytes fictícios de áudio. Eles servem para validar controle de fluxo sem custo, credencial ou rede.

Os testes dos providers reais usam clients fake e verificam o contrato sem disparar requisições externas.

## Próximas rotas

- streaming de transcrição;
- TTS streaming;
- `GPT-Realtime-Translate` como rota direta opcional;
- providers locais/offline;
- fallback automático entre providers após a política de recuperação estar consolidada.
