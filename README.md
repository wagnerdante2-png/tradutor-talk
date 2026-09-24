# Tradutor Talk

Tradutor Talk é um intérprete bidirecional de conversação em tempo real, com núcleo Python substituível por providers e dois caminhos de I/O:

~~~text
DESKTOP FUTURO
microfone/driver local -> núcleo -> saída local/virtual

LABORATÓRIO CODESPACES
microfone do Chrome -> HTTPS -> núcleo no Codespace -> HTTPS -> áudio no Chrome
~~~

A arquitetura do produto não foi convertida em uma aplicação web. O modo Codespaces é um adaptador de teste temporário para executar o backend fora do notebook corporativo.

## Teste recomendado no notebook corporativo

Use GitHub Codespaces.

Nada do runtime Python precisa ser instalado no notebook. O Chrome local fornece microfone e reprodução; Python, SDKs e chamadas de API rodam dentro do Codespace.

### Passo 1 — criar o Codespace

No GitHub, abra o repositório e use:

~~~text
Code -> Codespaces -> Create codespace on main
~~~

O arquivo .devcontainer/devcontainer.json prepara Python 3.12 e instala automaticamente:

~~~text
.[dev,web]
~~~

Somente dentro do Codespace.

### Passo 2 — iniciar o laboratório

No terminal do Codespace:

~~~text
python -m tradutor_talk.web
~~~

ou:

~~~text
tradutor-talk-web
~~~

O servidor escuta na porta 8000. O Codespaces deve detectar a porta e encaminhá-la ao navegador.

Em ambientes onde a autenticação da porta privada do Codespaces retorna HTTP 401, use temporariamente a porta como Pública. O laboratório protege todas as rotas de API com um token aleatório gerado dentro do Codespace; sem esse token não é possível configurar chave, enviar áudio ou consumir STT/TTS. Ao terminar, volte a porta para Privada ou pare o Codespace.

### Passo 3 — token e microfone

Se estiver usando a porta Pública por causa do HTTP 401, obtenha primeiro o token do laboratório no terminal:

~~~text
cat /tmp/tradutor-talk-lab-token
~~~

Cole-o no primeiro painel da página.

Depois, na página Tradutor Talk:

1. permita o microfone quando o Chrome solicitar;
2. se a OPENAI_API_KEY não estiver configurada no Codespace, cole a chave no painel da página;
3. a chave fica somente na memória do processo do laboratório;
4. grave primeiro um turno do interlocutor;
5. pare a gravação para enviar o WAV ao Codespace;
6. aguarde STT -> tradução -> TTS;
7. escute a tradução;
8. faça o turno inverso.

A interface mostra texto original, tradução e latência de STT, tradução, TTS e processamento total.

## O que o laboratório valida

- captura real do microfone pelo Chrome;
- transporte browser -> Codespace;
- STT real;
- tradução PT-BR ⇄ EN;
- contexto entre turnos;
- TTS real;
- transporte Codespace -> browser;
- reprodução real no notebook;
- lifecycle half-duplex até o final do playback;
- latência de cada provider.

O primeiro laboratório usa início/fim de gravação manual. Isso é deliberado: VAD/hands-free no navegador só entra depois de validar o ciclo ponta a ponta.

## Rotas do produto preservadas

O desktop continua preparado para:

~~~text
REMOTO -> entrada remota -> tradução -> saída local -> VOCÊ
VOCÊ   -> entrada local  -> tradução -> saída remota -> INTERLOCUTOR
~~~

O modo Codespaces não substitui drivers/dispositivos virtuais necessários futuramente para injetar áudio traduzido diretamente em Teams, Meet, WhatsApp ou Discord.

## Providers atuais

- STT: gpt-transcribe;
- tradução: gpt-5.6-luna, reasoning none;
- TTS: gpt-4o-mini-tts;
- voz padrão: marin.

## Marcos

- ✅ M0 — fundação, estados, mocks e resiliência.
- 🟡 M1–M5 — núcleo desktop implementado; validação física local ainda pendente.
- 🧪 Codespaces Lab — browser ⇄ backend remoto pronto para teste real sem instalação local.
- ⏸ M6 — streaming/otimização após medir o laboratório.
- M7 — ES / JA / ZH e autodetecção.
- M8 — contexto e glossário avançado.
- M9 — recuperação e carga.
- M10 — executável Windows.
- M11+ — full-duplex e rota realtime direta.

## Privacidade do laboratório

- a gravação é mantida em memória no navegador;
- ao encerrar um turno, um WAV é enviado ao backend do Codespace;
- o backend lê o corpo da requisição em memória;
- o Tradutor Talk não salva o áudio por padrão;
- a chave da API não é colocada no código;
- a porta encaminhada deve permanecer privada.

## Windows local

TESTAR_WINDOWS.py continua disponível para futuro teste em equipamento próprio. Ele não é o caminho recomendado no notebook corporativo atual.

## Documentação

- docs/CODESPACES_TEST_GUIDE.md — laboratório remoto;
- docs/PROJECT_TECHNICAL_V1.md — âncora;
- docs/ARCHITECTURE.md — arquitetura;
- docs/TEST_PLAN.md — testes;
- docs/M5_VAD_HANDSFREE.md — VAD/hands-free desktop;
- docs/WINDOWS_TEST_GUIDE.md — execução Windows local;
- docs/REFERENCES.md — projetos públicos estudados.

Nenhum workflow de GitHub Actions é necessário.
