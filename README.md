# Tradutor Talk

Tradutor Talk é um projeto de intérprete bidirecional de conversação em tempo real, inicialmente para Windows, com foco em robustez, baixa latência e arquitetura substituível por provedores.

## Escopo inicial

O primeiro fluxo validado será:

```text
PT-BR ⇄ EN
áudio → STT → tradução → TTS → áudio
```

A arquitetura separa captura, reconhecimento, tradução e síntese para permitir diagnóstico, fallback e troca de fornecedor sem reconstruir o produto.

## Princípios

- estados explícitos e determinísticos;
- nenhum áudio persistido por padrão;
- providers substituíveis;
- tratamento de timeout, cancelamento e falhas;
- contexto de conversa limitado;
- testes com mocks antes de APIs reais;
- interface simples somente depois de o núcleo estar estável.

## Marcos

- **M0** — fundação, máquina de estados, modelos, mocks e testes.
- **M1** — captura de microfone e STT.
- **M2** — tradução PT-BR ⇄ EN.
- **M3** — TTS e reprodução.
- **M4** — conversa bidirecional utilizável.
- **M5** — VAD e hands-free.
- **M6** — streaming e otimização de latência.
- **M7** — ES / JA / ZH e autodetecção.
- **M8** — contexto e glossário.
- **M9** — recuperação e testes de falha.
- **M10** — executável Windows.
- **M11+** — full-duplex, realtime direto e clientes futuros.

## Regras do MVP

O MVP não inclui login, banco de dados, painel administrativo, mobile, clonagem de voz, AR ou armazenamento em nuvem. Primeiro validaremos o ciclo completo de conversação.

## Execução local (M0)

Requer Python 3.12+.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
pytest
python -m tradutor_talk
```

O comando final executa uma demonstração determinística usando providers mock, sem API e sem consumo externo.

Consulte `docs/` para arquitetura, estados, providers e plano de testes.
