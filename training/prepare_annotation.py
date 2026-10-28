"""Prepara cópias com nomes únicos para importar em uma ferramenta de anotação."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

from common import DATASET_ROOT, images_in, load_classes


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--clear", action="store_true", help="substitui imagens preparadas existentes")
    args = parser.parse_args()

    classes = load_classes()
    raw_root = DATASET_ROOT / "raw"
    output_root = DATASET_ROOT / "annotated" / "images"
    output_root.mkdir(parents=True, exist_ok=True)
    manifest_path = DATASET_ROOT / "annotation_manifest.csv"

    rows: list[dict[str, str]] = []
    copied = 0
    for image in images_in(raw_root):
        relative = image.relative_to(raw_root)
        if len(relative.parts) < 3:
            print(f"Ignorada (esperado classe/sessão/arquivo): {relative}")
            continue
        class_name, session = relative.parts[0], relative.parts[1]
        if class_name not in classes:
            raise ValueError(f"Pasta de classe não declarada em classes.txt: {class_name}")
        destination_name = "__".join((class_name, session, image.name))
        destination = output_root / destination_name
        if args.clear or not destination.exists():
            shutil.copy2(image, destination)
            copied += 1
        rows.append({
            "arquivo_preparado": destination_name,
            "origem": relative.as_posix(),
            "classe_sugerida": class_name,
            "sessao": session,
            "status_anotacao": "PENDENTE",
        })

    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys() if rows else ["arquivo_preparado"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Imagens disponíveis para anotação: {len(rows)}")
    print(f"Imagens copiadas nesta execução: {copied}")
    print(f"Manifesto: {manifest_path}")
    print("Agora desenhe bounding boxes e exporte labels YOLO para dataset/annotated/labels.")


if __name__ == "__main__":
    main()
