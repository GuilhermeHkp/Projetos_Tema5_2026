# Precisão do detector

O modo aberto é um **ensemble neural**: YOLO-World propõe as caixas; CLIP ViT-B/32 compara cada recorte com o catálogo inteiro usando vários prompts e três enquadramentos; a camada de consenso rejeita baixa margem/discordância; a confirmação temporal exige repetição em frames próximos. Ele foi configurado para preferir **nenhum rótulo** a um rótulo conflitante.

Para precisão alta no seu ambiente, treine `Back-End\models\best.pt`. O modo `DETECTION_MODE=auto` usa esse modelo automaticamente quando ele existir. O dataset vazio do ZIP não permite produzir um `best.pt` confiável agora.

Para classes críticas como `Chave Phillips`, `Chave de fenda`, `Tesoura` e `Escova de dentes`, fotografe várias **unidades físicas**, fundos, iluminações, distâncias, rotações e oclusões. Inclua exemplos difíceis das classes confundidas. Separe train/val/test por sessão para não medir o mesmo vídeo nos três conjuntos.

No CMD, a partir de `PROJETOSV1`:

```cmd
call .venv\Scripts\activate.bat
python training\prepare_annotation.py
python training\analyze_dataset.py --source annotated
python training\split_dataset.py --clear
python training\train.py --epochs 150 --imgsz 640
python training\validate.py --split test
```

Não trate `conf` do YOLO nem similaridade do CLIP como probabilidade calibrada. A qualidade deve ser medida no conjunto `test` e, para a demonstração real, em vídeos da câmera e iluminação que serão usados.
