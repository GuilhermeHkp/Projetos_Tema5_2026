"""Audita imagens, labels YOLO, duplicatas exatas e distribuição por classe."""

from __future__ import annotations

import argparse
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from common import DATASET_ROOT, images_in, label_path_for, load_classes, validate_label_file


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=("raw", "annotated", "train", "val", "test"), default="raw")
    args = parser.parse_args()
    classes = load_classes()

    if args.source == "raw":
        images_root = DATASET_ROOT / "raw"
        labels_root = None
    else:
        images_root = DATASET_ROOT / args.source / "images"
        labels_root = DATASET_ROOT / args.source / "labels"

    images = images_in(images_root)
    hashes: dict[str, list[Path]] = defaultdict(list)
    for image in images:
        hashes[sha256(image)].append(image)
    duplicate_groups = [paths for paths in hashes.values() if len(paths) > 1]

    print(f"Fonte: {args.source}")
    print(f"Imagens: {len(images)}")
    print(f"Grupos de duplicatas exatas: {len(duplicate_groups)}")

    if args.source == "raw":
        counts = Counter(image.relative_to(images_root).parts[0] for image in images)
        for name in classes:
            print(f"  {name}: {counts[name]}")
        print("Labels: não se aplicam ao banco bruto; anote antes de treinar.")
        return

    missing = 0
    empty = 0
    objects_by_class = Counter()
    errors: list[str] = []
    for image in images:
        label = label_path_for(image, images_root, labels_root)
        if not label.is_file():
            missing += 1
            continue
        objects, label_errors = validate_label_file(label, len(classes))
        errors.extend(label_errors)
        if objects == 0:
            empty += 1
        for raw in label.read_text(encoding="utf-8").splitlines():
            parts = raw.split()
            if len(parts) == 5:
                try:
                    objects_by_class[int(parts[0])] += 1
                except ValueError:
                    pass

    print(f"Labels ausentes: {missing}")
    print(f"Labels sem objetos: {empty}")
    print(f"Erros de formato: {len(errors)}")
    for class_id, name in enumerate(classes):
        print(f"  {class_id} {name}: {objects_by_class[class_id]} objetos")
    for error in errors[:30]:
        print("ERRO:", error)


if __name__ == "__main__":
    main()
