# Guia de teste Windows

## Ambiente corporativo

O launcher principal não depende mais de BAT.

Políticas de Endpoint Security podem bloquear arquivos batch antes que o programa seja iniciado. O caminho recomendado agora usa TESTAR_WINDOWS.py, executado pelo próprio Python.

Não desative antivírus, Endpoint Security ou políticas corporativas para testar o projeto.

## Caminho recomendado

Na raiz do projeto:

~~~text
TESTAR_WINDOWS.py
~~~

Tente nesta ordem:

1. duplo clique, se .py estiver associado ao Python;
2. botão direito -> Abrir com -> Python;
3. abrir um CMD normal e executar:

~~~text
py TESTAR_WINDOWS.py
~~~

## O que o launcher faz

1. verifica Python 3.12+;
2. cria .venv usando o módulo padrão venv;
3. usa diretamente .venv\Scripts\python.exe;
4. instala .[dev,runtime];
5. executa pytest;
6. abre tradutor_talk.app.windows_test.

Ele não executa activate.bat.

Se a política corporativa bloquear o próprio Python, pip ou acesso de rede necessário para baixar pacotes, o launcher mostrará a etapa que falhou.

## Modo mesa

Valida rapidamente microfone, VAD, STT, tradução PT-BR ⇄ EN, TTS, reprodução e repetição de rodadas.

Os dois lados usam o mesmo microfone e a mesma saída.

## Modo chamada roteada

~~~text
INTERLOCUTOR / CHAMADA
        |
        v
entrada de áudio remoto
        |
        v
STT -> tradução -> TTS
        |
        v
seu fone

VOCÊ
        |
        v
seu microfone
        |
        v
STT -> tradução -> TTS
        |
        v
saída virtual
        |
        v
microfone selecionado no app de chamada
~~~

O software mantém quatro papéis independentes: entrada local, entrada remota, saída local e saída remota.

## Preparação manual sem BAT

~~~text
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev,runtime]"
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m tradutor_talk.app.windows_test
~~~

## Listar dispositivos

~~~text
.venv\Scripts\python.exe -m tradutor_talk.app.device_probe
~~~

## Gate antes de M6

Observe durante o teste: corte do início de frase, encerramento do VAD, STT ms, tradução ms, TTS ms, playback ms, total do turno, eco e falhas de API ou áudio.
