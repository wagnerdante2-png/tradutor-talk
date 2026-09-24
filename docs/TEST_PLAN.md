# Plano de testes

## M0

- ciclo nominal da máquina de estados;
- rejeição de transição inválida;
- pipeline mock STT → tradução → TTS;
- retorno automático para LISTENING;
- contexto limitado;
- ring buffer limitado;
- nenhum segredo no código;
- nenhuma chamada externa durante testes.

## M1

- enumeração de dispositivos;
- perda de microfone;
- troca de dispositivo;
- frame size;
- sample rate;
- ring buffer com áudio real;
- áudio vazio;
- silêncio;
- gravação curta.

## M2–M4

- timeout de provider;
- rate limit;
- queda de rede;
- respostas vazias;
- cancelamento;
- repetição de utterance;
- filas atrasadas;
- eco;
- PT-BR ⇄ EN ponta a ponta.

## Meta de qualidade

Nenhuma nova camada deverá ser adicionada enquanto a anterior não possuir teste determinístico e diagnóstico mínimo.
