# Tradutor Talk

Tradutor Talk é um projeto de intérprete bidirecional de conversação em tempo real, inicialmente para Windows, com foco em robustez, baixa latência e arquitetura substituível por provedores.

## Estado atual

**M0 — fundação arquitetural implementada.**

Já existem máquina de estados, orquestrador de sessão half-duplex, contratos de providers, mocks determinísticos, contexto limitado, glossário, ring buffer, configuração, métricas de latência e testes unitários.

O próximo marco é **M1: áudio real do Windows → captura controlada → STT**.

## Escopo inicial

```text
PT-BR ⇄ EN
áudio → STT → tradução → TTS → áudio
```

A arquitetura separa captura, reconhecimento, tradução e síntese para permitir diagnóstico, fallback e troca de fornecedor sem reconstruir o produto.

## Princípios

- estados explícitos e determinísticos;
- nenhum áudio persistido por padrão;
- providers substituíveis;
- timeout e cancelamento centralizados;
- contexto de conversa limitado;
- testes com mocks antes de APIs reais;
- métricas por etapa;
- interface de produto somente depois de o núcleo estar estável.

## Marcos

- ✅ **M0** — fundação, máquina de estados, modelos, mocks e testes.
- ⏭ **M1** — captura de microfone e STT.
- **M2** — tradução PT-BR ⇄ EN.
- **M3** — TTS e reprodução.
- **M4** — conversa bidirecional utilizável.
- **M5** — VAD e hands-free.
- **M6** — streaming e otimização de latência.
- **M7** — ES / JA / ZH e autodetecção.
- **M8** — contexto e glossário avançado.
- **M9** — recuperação e testes de falha.
- **M10** — executável Windows.
- **M11+** — full-duplex, realtime direto e clientes futuros.

## Regras do MVP

O MVP não inclui login, banco de dados, painel administrativo, mobile, clonagem de voz, AR ou armazenamento em nuvem. Primeiro validaremos o ciclo completo de conversação.

## Execução local

Requer Python 3.12+.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
python -m tradutor_talk
```

O último comando executa uma demonstração determinística usando providers mock, sem API e sem consumo externo.

## Documentação

- `docs/PROJECT_TECHNICAL_V1.md` — âncora do projeto;
- `docs/ARCHITECTURE.md` — decisões e fronteiras;
- `docs/STATES.md` — máquina de estados;
- `docs/PROVIDERS.md` — contratos de integração;
- `docs/TEST_PLAN.md` — estratégia de validação.
