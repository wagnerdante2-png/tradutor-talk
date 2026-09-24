# Tradutor Talk

Tradutor Talk é um intérprete bidirecional de conversação em tempo real, inicialmente para Windows, com foco em robustez, baixa latência, privacidade e arquitetura substituível por provedores.

## Estado atual

A fundação M0 está concluída e o caminho técnico de M1–M5 está implementado para validação física no Windows.

~~~text
áudio
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
saída selecionada
~~~

O projeto separa as duas rotas físicas:

~~~text
REMOTO -> entrada remota -> tradução -> saída local -> VOCÊ
VOCÊ   -> entrada local  -> tradução -> saída remota -> INTERLOCUTOR
~~~

## Teste mais rápido no Windows

Dê duplo clique em:

~~~text
TESTAR_WINDOWS.bat
~~~

Ele cria um ambiente virtual local, instala as dependências, roda os testes determinísticos e abre o assistente de teste real.

O assistente oferece:

1. Modo mesa — mesmo microfone e mesmo fone nos dois sentidos, ideal para provar o motor rapidamente;
2. Modo chamada roteada — microfone local, entrada remota, fone local e saída virtual remota independentes.

A variável OPENAI_API_KEY pode ser informada temporariamente pelo assistente e não é salva pelo Tradutor Talk.

Guia completo: docs/WINDOWS_TEST_GUIDE.md.

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
- half-duplex permanece fechado até o playback terminar;
- interface de produto somente depois de o núcleo estar estável.

## Marcos

- ✅ M0 — fundação, máquina de estados, modelos, mocks e resiliência.
- 🟡 M1 — captura de microfone + STT implementados; validação física pendente.
- 🟡 M2 — tradução PT-BR ⇄ EN implementada; validação real pendente.
- 🟡 M3 — TTS + reprodução WAV implementados; validação real pendente.
- 🟡 M4 — conversa bidirecional controlada implementada; validação ponta a ponta pendente.
- 🟡 M5 — VAD local + hands-free + roteamento direcional implementados; validação em ambiente real pendente.
- ⏸ M6 — streaming e otimização de latência; aguarda métricas reais do M5.
- M7 — ES / JA / ZH e autodetecção.
- M8 — contexto e glossário avançado.
- M9 — recuperação e testes de falha sob carga.
- M10 — executável Windows.
- M11+ — full-duplex, rota realtime direta e clientes futuros.

## Instalação manual

Requer Python 3.12+.

~~~bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev,runtime]"
pytest
~~~

## Comandos de teste

Listar dispositivos:

~~~bash
python -m tradutor_talk.app.device_probe
~~~

Microfone -> STT:

~~~bash
python -m tradutor_talk.app.microphone_probe --seconds 3 --language pt-BR
~~~

Conversa bidirecional controlada:

~~~bash
python -m tradutor_talk.app.conversation_probe --seconds 4
~~~

Hands-free, uma rodada, dispositivos padrão:

~~~bash
python -m tradutor_talk.app.handsfree_probe --rounds 1
~~~

Assistente Windows:

~~~bash
python -m tradutor_talk.app.windows_test
~~~

## Providers atuais

- STT: gpt-transcribe;
- tradução: gpt-5.6-luna, reasoning none;
- TTS: gpt-4o-mini-tts;
- voz padrão: marin;
- VAD: WebRTC local, agressividade 2.

Todos são configuráveis em config/default.toml.

## Privacidade

- áudio capturado fica em memória;
- WAV sintetizado fica em memória;
- conversa não é salva por padrão;
- telemetria externa do aplicativo está desligada;
- a chave da API não deve entrar no repositório.

## Documentação

- docs/PROJECT_TECHNICAL_V1.md — âncora do projeto;
- docs/ARCHITECTURE.md — decisões e fronteiras;
- docs/STATES.md — máquina de estados;
- docs/PROVIDERS.md — contratos de integração;
- docs/TEST_PLAN.md — estratégia de validação;
- docs/M1_AUDIO_STT.md — teste físico do primeiro caminho de áudio;
- docs/M5_VAD_HANDSFREE.md — arquitetura do VAD/hands-free;
- docs/WINDOWS_TEST_GUIDE.md — teste de mesa e chamada roteada;
- docs/REFERENCES.md — referências públicas estudadas.

Nenhum workflow de GitHub Actions é necessário para desenvolver, testar ou executar o projeto.
