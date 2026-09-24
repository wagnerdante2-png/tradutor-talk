# Referências públicas de arquitetura

Este projeto pode estudar implementações públicas para acelerar decisões técnicas, sem acoplar o núcleo a uma base externa.

Estado em 2026-09-24: nenhum trecho desses projetos foi copiado para o código do Tradutor Talk neste lote. As referências abaixo servem como fonte de arquitetura, roteamento de áudio e comparação de abordagem.

## Projetos de referência

- Realtime Translate — https://github.com/carlosvictorodrigues/realtime-translate
  - Referência principal para tradução bidirecional de chamada e roteamento Windows com dispositivos virtuais.
  - Licença indicada pelo repositório: MIT.

- Sokuji — https://github.com/kizuna-ai-lab/sokuji
  - Referência para providers substituíveis, inferência local e tradução two-way.
  - Licença indicada pelo repositório: AGPL-3.0.

- LiveTranslate — https://github.com/NBS282/LiveTranslate
  - Referência para captura local, pipeline offline, virtual audio cable e experiência desktop.
  - Licença indicada pelo repositório: MIT.

- OpenPolySphere — https://github.com/org-event/OpenPolySphere
  - Referência adicional para pipeline local e separação entre ASR, tradução e TTS.

- Meta Seamless Communication — https://github.com/facebookresearch/seamless_communication
  - Referência de pesquisa para speech-to-speech e streaming simultâneo.

- Hibiki — https://github.com/kyutai-labs/hibiki
  - Referência de pesquisa para tradução speech-to-speech simultânea.

## Regra de reaproveitamento futuro

Quando código externo for efetivamente adaptado ou copiado:

1. registrar arquivo e commit de origem;
2. manter comentário de referência próximo ao código adaptado quando fizer sentido;
3. registrar licença e aviso exigido em THIRD_PARTY_NOTICES.md;
4. não misturar código de licença copyleft em uma futura distribuição proprietária sem revisão específica;
5. preferir reproduzir a ideia arquitetural com implementação própria quando o objetivo for manter liberdade de distribuição.

A prioridade atual é uso pessoal e validação técnica, mas manter a origem registrada agora evita retrabalho de compliance se o projeto virar produto.
