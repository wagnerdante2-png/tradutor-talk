# Plano de testes

## M0 — fundação

Cobertura implementada:

- ciclo nominal da máquina de estados;
- rejeição de transição inválida;
- pipeline mock STT → tradução → TTS;
- retorno automático para LISTENING;
- contexto limitado;
- ring buffer limitado;
- stop durante provider;
- cancelamento;
- rejeição de segunda utterance concorrente;
- timeout e recuperação explícita;
- nenhum segredo no código;
- nenhuma chamada externa durante testes.

## M1 — áudio + STT

Testes determinísticos já presentes:

- empacotamento PCM16 → WAV;
- sample rate e frame count;
- block size de 20 ms;
- adapter STT com client fake;
- composição do provider sem chamada externa.

Validação física pendente:

- enumeração de dispositivos no Windows;
- microfone padrão;
- perda e reconexão de microfone;
- PT-BR real;
- EN real;
- erro de credencial;
- ausência de persistência de áudio.

## M2 — tradução

Testes determinísticos já presentes:

- provider via Responses API com client fake;
- modelo e reasoning configuráveis;
- `store=False`;
- contexto incluído;
- glossário incluído;
- retorno vazio tratado como erro.

Validação real pendente:

- EN → PT-BR;
- PT-BR → EN;
- nomes próprios;
- números;
- termos técnicos;
- frases ambíguas dependentes de contexto;
- latência por utterance.

## M3 — TTS + reprodução

Testes determinísticos já presentes:

- adapter TTS com client fake;
- saída WAV;
- inspeção do WAV em memória.

Validação física pendente:

- reprodução no dispositivo padrão;
- voz PT-BR;
- voz EN;
- desconexão da saída;
- underflow;
- volume e inteligibilidade.

## M4 — conversa bidirecional controlada

O `conversation_probe` é o primeiro gate ponta a ponta.

Aceite:

1. interlocutor fala EN;
2. texto EN é reconhecido;
3. tradução PT-BR aparece;
4. áudio PT-BR é reproduzido;
5. usuário fala PT-BR;
6. texto PT-BR é reconhecido;
7. tradução EN aparece;
8. áudio EN é reproduzido;
9. o ciclo repete sem reiniciar;
10. falha de uma etapa não deixa a sessão presa.

## M5+

Depois do gate M4:

- VAD;
- hands-free;
- prevenção de eco;
- barge-in;
- streaming;
- rate limit e queda de rede sob carga;
- filas atrasadas;
- repetição/duplicidade;
- idiomas adicionais;
- rota realtime direta.

## Meta de qualidade

Nenhuma camada de produto deve esconder falhas da camada técnica. Cada nova etapa precisa de estado explícito, erro diagnosticável e teste determinístico antes de ser tratada como concluída.
