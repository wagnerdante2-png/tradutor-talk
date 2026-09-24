# Tradutor Talk

Tradutor Talk é um intérprete bidirecional de conversação em tempo real, inicialmente para Windows, com foco em robustez, baixa latência, privacidade e arquitetura substituível por provedores.

## Estado atual

A fundação M0 está concluída e o caminho técnico de M1–M5 está implementado para validação física no Windows.

~~~text
REMOTO -> entrada remota -> tradução -> saída local -> VOCÊ
VOCÊ   -> entrada local  -> tradução -> saída remota -> INTERLOCUTOR
~~~

## Teste mais rápido no Windows

O launcher principal é agora:

~~~text
TESTAR_WINDOWS.py
~~~

Ele é Python puro e não depende de arquivos BAT.

Tente nesta ordem:

1. duplo clique no TESTAR_WINDOWS.py, se arquivos .py estiverem associados ao Python;
2. botão direito -> Abrir com -> Python;
3. em um CMD normal aberto pelo usuário:

~~~text
py TESTAR_WINDOWS.py
~~~

O launcher valida Python 3.12+, cria uma .venv local usando a biblioteca padrão do Python, instala as dependências, executa os testes determinísticos e abre o assistente real.

O launcher anterior em BAT foi retirado do caminho recomendado porque ambientes corporativos podem bloquear scripts batch antes de o aplicativo iniciar.

Guia completo: docs/WINDOWS_TEST_GUIDE.md.

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

## Instalação manual sem BAT

Requer Python 3.12+.

~~~text
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev,runtime]"
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m tradutor_talk.app.windows_test
~~~

Não é necessário executar activate.bat.

## Providers atuais

- STT: gpt-transcribe;
- tradução: gpt-5.6-luna, reasoning none;
- TTS: gpt-4o-mini-tts;
- voz padrão: marin;
- VAD: WebRTC local, agressividade 2.

## Privacidade

- áudio capturado fica em memória;
- WAV sintetizado fica em memória;
- conversa não é salva por padrão;
- a chave da API não deve entrar no repositório.

## Documentação

- docs/PROJECT_TECHNICAL_V1.md — âncora do projeto;
- docs/ARCHITECTURE.md — decisões e fronteiras;
- docs/TEST_PLAN.md — estratégia de validação;
- docs/M5_VAD_HANDSFREE.md — arquitetura do VAD/hands-free;
- docs/WINDOWS_TEST_GUIDE.md — teste Windows;
- docs/REFERENCES.md — referências públicas estudadas.

Nenhum workflow de GitHub Actions é necessário para desenvolver, testar ou executar o projeto.
