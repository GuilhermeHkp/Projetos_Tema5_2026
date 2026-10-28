# Imagens e treinamento

## Ordem

1. Salve imagens em `dataset\raw\<classe>\<sessão>\`.
2. Prepare as imagens:

```bat
python training\prepare_annotation.py
```

3. Desenhe as bounding boxes em um anotador que exporte YOLO Detection.
4. Coloque os labels em `dataset\annotated\labels\`.
5. Analise e divida o dataset:

```bat
python training\analyze_dataset.py --source annotated
python training\split_dataset.py --clear
```

6. Treine e valide:

```bat
python training\train.py --epochs 100 --imgsz 640 --device 0
python training\validate.py --split test --device 0
```

O melhor modelo é copiado para:

```text
Back-End\models\best.pt
```

Use pelo menos três sessões diferentes por classe. Varie iluminação, distância,
posição, fundo e unidade física do objeto.
