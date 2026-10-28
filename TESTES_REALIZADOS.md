# Testes realizados nesta revisão

## Passaram de fato neste ambiente

- Compilação sintática de todo o Python do backend, ferramentas e treinamento.
- `node --check` em todos os JavaScript do Front-End.
- 7/7 testes unitários do cérebro de decisão: margem, consenso, correção entre grupos, rejeição open-set e fallback de família de garrafas.
- Comparação de hash dos arquivos visuais: 20/20 HTML/CSS/imagens permaneceram idênticos à versão anterior.
- Verificação de presença dos scripts de instalação, diagnóstico e execução.

## Não foi possível executar aqui

- Inferência neural real YOLO-World + CLIP, porque o checkpoint `ViT-B-32.pt` não está presente neste ambiente.
- Câmera física.
- Conexão MySQL real.
- Bot Telegram real.

Esses itens são verificados/diagnosticados no Windows por `DIAGNOSTICAR_GHCE.cmd` e durante a execução normal.

## Política de precisão

Os limites padrão foram endurecidos para priorizar menos falsos positivos. Portanto, é esperado que alguns objetos difíceis resultem em nenhuma detecção em vez de um nome incorreto. Para precisão superior e específica do ambiente, treine `Back-End\models\best.pt` com fotos anotadas dos objetos reais.
