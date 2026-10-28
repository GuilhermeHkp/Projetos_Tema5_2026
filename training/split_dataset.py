"""Divide pares imagem/label em train, val e test sem misturar sessões."""

from __future__ import annotations

import argparse
import random
import shutil
from collections import defaultdict
from pathlib import Path

from common import DATASET_ROOT, images_in, label_path_for, load_classes, validate_label_file


def session_from_name(image: Path) -> str:
    parts = image.name.split("__", 2)
    return "__".join(parts[:2]) if len(parts) == 3 else image.stem


def class_from_name(image: Path) -> str:
    return image.name.split("__", 1)[0]


def split_counts(total: int, train_ratio: float, val_ratio: float) -> tuple[int, int, int]:
    if total < 3:
        raise ValueError("São necessários ao menos três itens/grupos para criar os três splits.")
    train_count = max(1, round(total * train_ratio))
    val_count = max(1, round(total * val_ratio))
    test_count = total - train_count - val_count
    if test_count < 1:
        test_count = 1
        if train_count >= val_count and train_count > 1:
            train_count -= 1
        else:
            val_count -= 1
    return train_count, val_count, test_count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=float, default=0.70)
    parser.add_argument("--val", type=float, default=0.20)
    parser.add_argument("--test", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--clear", action="store_true")
    parser.add_argument(
        "--allow-frame-split", action="store_true",
        help="permite dividir frames da mesma sessão (somente para experimento, causa leakage)",
    )
    args = parser.parse_args()
    if abs(args.train + args.val + args.test - 1.0) > 1e-9:
        raise ValueError("As proporções train/val/test devem somar 1.")

    classes = load_classes()
    images_root = DATASET_ROOT / "annotated" / "images"
    labels_root = DATASET_ROOT / "annotated" / "labels"
    images = images_in(images_root)
    if not images:
        raise RuntimeError("Nenhuma imagem preparada. Rode training/prepare_annotation.py primeiro.")

    valid: list[tuple[Path, Path]] = []
    errors: list[str] = []
    for image in images:
        label = label_path_for(image, images_root, labels_root)
        if not label.is_file():
            errors.append(f"label ausente: {label.name}")
            continue
        objects, label_errors = validate_label_file(label, len(classes))
        errors.extend(label_errors)
        if objects == 0:
            errors.append(f"label sem objetos: {label.name}")
        valid.append((image, label))
    if errors:
        preview = "\n".join(errors[:30])
        raise RuntimeError(f"Dataset não está pronto ({len(errors)} problemas):\n{preview}")

    sessions_by_class: dict[str, set[str]] = defaultdict(set)
    for image, _ in valid:
        sessions_by_class[class_from_name(image)].add(session_from_name(image))
    insufficient = {name: len(sessions) for name, sessions in sessions_by_class.items() if len(sessions) < 3}
    if insufficient and not args.allow_frame_split:
        details = ", ".join(f"{name}={count}" for name, count in sorted(insufficient.items()))
        raise RuntimeError(
            "São necessárias pelo menos 3 sessões independentes por classe para separar sem leakage. "
            f"Sessões atuais: {details}. Capture novas sessões ou use --allow-frame-split apenas para teste."
        )

    rng = random.Random(args.seed)
    assignments: dict[Path, str] = {}
    if args.allow_frame_split:
        pairs_by_class: dict[str, list[tuple[Path, Path]]] = defaultdict(list)
        for pair in valid:
            pairs_by_class[class_from_name(pair[0])].append(pair)
        for pairs in pairs_by_class.values():
            rng.shuffle(pairs)
            train_count, val_count, _ = split_counts(len(pairs), args.train, args.val)
            for index, (image, _) in enumerate(pairs):
                assignments[image] = (
                    "train" if index < train_count
                    else "val" if index < train_count + val_count
                    else "test"
                )
    else:
        groups: dict[tuple[str, str], list[tuple[Path, Path]]] = defaultdict(list)
        for pair in valid:
            image = pair[0]
            groups[(class_from_name(image), session_from_name(image))].append(pair)
        groups_by_class: dict[str, list[tuple[str, list[tuple[Path, Path]]]]] = defaultdict(list)
        for (class_name, session), pairs in groups.items():
            groups_by_class[class_name].append((session, pairs))
        for class_groups in groups_by_class.values():
            rng.shuffle(class_groups)
            train_count, val_count, _ = split_counts(len(class_groups), args.train, args.val)
            for index, (_, pairs) in enumerate(class_groups):
                split = (
                    "train" if index < train_count
                    else "val" if index < train_count + val_count
                    else "test"
                )
                for image, _ in pairs:
                    assignments[image] = split

    if args.clear:
        for split in ("train", "val", "test"):
            for kind in ("images", "labels"):
                target = DATASET_ROOT / split / kind
                for path in target.iterdir():
                    if path.is_file() and path.name != ".gitkeep":
                        path.unlink()

    counts = defaultdict(int)
    for image, label in valid:
        split = assignments[image]
        images_out = DATASET_ROOT / split / "images"
        labels_out = DATASET_ROOT / split / "labels"
        images_out.mkdir(parents=True, exist_ok=True)
        labels_out.mkdir(parents=True, exist_ok=True)
        shutil.copy2(image, images_out / image.name)
        shutil.copy2(label, labels_out / label.name)
        counts[split] += 1

    print("Divisão concluída:", dict(counts))
    if args.allow_frame_split:
        print("ATENÇÃO: frames da mesma sessão podem estar em splits diferentes; métricas podem ficar otimistas.")


if __name__ == "__main__":
    main()
