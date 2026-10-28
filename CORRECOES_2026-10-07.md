# Correções desta revisão — 07/10/2026

## Causas encontradas

1. `validate_setup.py` exigia `yolov8s-worldv2.pt` mesmo com `DETECTION_MODE=auto` e um `best.pt` especializado presente.
2. `DIAGNOSTICAR.cmd` exigia `clip` incondicionalmente, embora o modo custom não use CLIP.
3. `INSTALAR_WINDOWS.cmd` chamava `INSTALAR_CLIP.cmd` sempre, tornando uma dependência opcional um bloqueio de instalação.
4. O `best.pt` foi treinado com Ultralytics 8.4.171, mas o projeto fixava 8.3.40.
5. O `best.pt` usa nove nomes técnicos/tamanhos; agora eles são mapeados para nomes estáveis da aplicação.
6. `schema.sql` traz `GHCE` fixo; `create_tables.py` agora usa `DB_NAME` do `.env` e ignora CREATE DATABASE/USE fixos do schema.
7. `seed.py` anterior não garantia o login 1 / 2 / 123456.
8. O frontend voltou a usar `localhost:5000`; foi alterado para `127.0.0.1:5000`.
9. A API carregava banco/modelo antes de abrir a porta; agora `/api/ping` fica disponível imediatamente.

## Verificações reais executadas neste ambiente

- ZIP de entrada: íntegro.
- `.env`: sintaxe válida, chaves obrigatórias presentes; credenciais não foram exibidas.
- CLIP `ViT-B-32.pt`: SHA-256 oficial conferido.
- `best.pt`: arquivo PyTorch/ZIP íntegro, 509 entradas internas.
- Metadados do `best.pt`: Ultralytics 8.4.171 e 9 classes.
- Mapeamento das 9 classes do checkpoint: 9/9 cobertas.
- Python: 39 arquivos compilados sem erro.
- JavaScript: todos os arquivos passaram em `node --check`.
- `tests.test_decision_brain`: 7/7 testes passaram.
- Frontend visual: 20/20 hashes HTML/CSS/imagens inalterados.
- Lógica do validador em modo `auto` com `best.pt`: teste simulado passou sem exigir YOLO-World.

## Não testado aqui

- Autenticação real no MySQL do computador do usuário.
- Execução dos `.cmd` no Windows.
- Carregamento real do `best.pt` com Ultralytics 8.4.171 no Windows.
- Inferência real com câmera.

Esses itens dependem do ambiente Windows/MySQL/hardware local.
