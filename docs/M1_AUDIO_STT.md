# M1 — Áudio real + STT

## Estado

A implementação do caminho controlado **microfone → WAV em memória → STT** está pronta no repositório.

A validação física ainda deve ser executada em uma máquina Windows com microfone e credencial do provider. O projeto não grava o áudio capturado em arquivo.

## O que foi implementado

- captura mono PCM16 pelo microfone padrão;
- blocos de 20 ms por padrão;
- captura limitada por duração;
- WAV criado somente em memória;
- enumeração de dispositivos de áudio;
- adapter de STT isolado do core;
- modelo configurável;
- dica opcional de idioma;
- teste do adapter com client fake, sem chamada externa;
- probe manual de microfone.

## Instalação do runtime

Requer Python 3.12+.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[runtime]"
```

## Credencial

A credencial deve ser fornecida por variável de ambiente. Nunca grave uma chave real no repositório.

No PowerShell da sessão atual:

```powershell
$env:OPENAI_API_KEY="SUA_CHAVE"
```

## Teste do núcleo

```bash
pytest
```

Os testes do adapter não usam rede nem consomem API.

## Probe de microfone

Português:

```bash
python -m tradutor_talk.app.microphone_probe --seconds 3 --language pt-BR
```

Inglês:

```bash
python -m tradutor_talk.app.microphone_probe --seconds 3 --language en-US
```

O probe grava o intervalo solicitado, mantém os bytes em memória, envia o WAV ao STT e imprime a transcrição.

## Limite deliberado

M1 trabalha com uma utterance fechada antes da transcrição. Isso é proposital.

Microfone contínuo, VAD e transcrição em streaming serão introduzidos depois da validação deste caminho. Assim, defeitos de dispositivo, reconhecimento e streaming permanecem separáveis durante o endurecimento do produto.

## Critério de aceite do M1

M1 é considerado validado quando, no Windows alvo:

1. o microfone padrão é aberto sem erro;
2. três segundos de PT-BR são transcritos corretamente;
3. três segundos de EN são transcritos corretamente;
4. a segunda execução funciona sem reiniciar o aplicativo;
5. nenhum arquivo de áudio permanece em disco;
6. um erro de dispositivo ou credencial produz erro explícito em vez de travamento silencioso.
