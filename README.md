# Tradutor Talk

Tradutor Talk é um intérprete bidirecional de conversação em tempo real, inicialmente para Windows, com foco em robustez, baixa latência, privacidade e arquitetura substituível por provedores.

## Estado atual

A fundação M0 está concluída e o caminho técnico de M1–M5 já está implementado para validação física no Windows.

~~~text
microfone
   ↓
VAD local / segmentação
   ↓
STT
   ↓
tradução com contexto + glossário
   ↓
TTS
   ↓
WAV em memória
   ↓
alto-falante / fone
~~~

Existem dois modos de prova:

1. conversa controlada por Enter;
2. hands-free half-duplex, com detecção local de início e fim de fala.

Importante: M1–M5 ainda precisam ser validados em hardware real com microfone, saída de áudio e credencial de API. Os adapters possuem testes sem rede, mas este repositório não trata teste mock como prova de dispositivo físico.

## Escopo inicial

~~~text
PT-BR ⇄ EN
áudio → STT → tradução → TTS → áudio
~~~

A arquitetura separa captura, reconhecimento, tradução e síntese para permitir diagnóstico, fallback e troca de fornecedor sem reconstruir o produto.

## Princípios

- estados explícitos e determinísticos;
- nenhum áudio persistido por padrão;
- providers substituíveis;
- timeout e cancelamento centralizados;
- contexto de conversa limitado;
- testes com mocks/fakes antes de APIs reais;
- métricas por etapa;
- segredos fora do repositório;
- VAD local sem consumo de API durante silêncio;
- interface de produto somente depois de o núcleo estar estável.

## Marcos

- ✅ M0 — fundação, máquina de estados, modelos, mocks e resiliência.
- 🟡 M1 — captura de microfone + STT implementados; validação física pendente.
- 🟡 M2 — tradução PT-BR ⇄ EN implementada; validação real pendente.
- 🟡 M3 — TTS + reprodução WAV implementados; validação real pendente.
- 🟡 M4 — conversa bidirecional controlada implementada; validação ponta a ponta pendente.
- 🟡 M5 — VAD local + hands-free alternado implementados; validação em ambiente real pendente.
- ⏸ M6 — streaming e otimização de latência; aguarda métricas reais do M5.
- M7 — ES / JA / ZH e autodetecção.
- M8 — contexto e glossário avançado.
- M9 — recuperação e testes de falha sob carga.
- M10 — executável Windows.
- M11+ — full-duplex, rota realtime direta e clientes futuros.

## Instalação

Requer Python 3.12+.

Teste somente do núcleo:

~~~bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
python -m tradutor_talk
~~~

Runtime real:

~~~bash
pip install -e ".[dev,runtime]"
~~~

A variável OPENAI_API_KEY deve existir apenas no ambiente local. Nunca faça commit de uma chave real.

## Provas

Microfone → STT:

~~~bash
python -m tradutor_talk.app.microphone_probe --seconds 3 --language pt-BR
~~~

Conversa bidirecional controlada PT-BR ⇄ EN:

~~~bash
python -m tradutor_talk.app.conversation_probe --seconds 4
~~~

Hands-free half-duplex:

~~~bash
python -m tradutor_talk.app.handsfree_probe --rounds 1
~~~

Para execução hands-free contínua:

~~~bash
python -m tradutor_talk.app.handsfree_probe
~~~

O áudio capturado e o WAV sintetizado são mantidos em memória pelo aplicativo.

## Providers atuais

- STT: gpt-transcribe;
- tradução: gpt-6-luna, reasoning none;
- TTS: gpt-4o-mini-tts;
- voz padrão: marin;
- VAD: WebRTC local, agressividade 2.

Todos são configuráveis em config/default.toml.

## Documentação

- docs/PROJECT_TECHNICAL_V1.md — âncora do projeto;
- docs/ARCHITECTURE.md — decisões e fronteiras;
- docs/STATES.md — máquina de estados;
- docs/PROVIDERS.md — contratos de integração;
- docs/TEST_PLAN.md — estratégia de validação;
- docs/M1_AUDIO_STT.md — teste físico do primeiro caminho de áudio;
- docs/M5_VAD_HANDSFREE.md — arquitetura e gate do modo hands-free.
