from __future__ import annotations

from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = PROJECT_ROOT / "dataset"
CLASSES_FILE = DATASET_ROOT / "classes.txt"
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def load_classes() -> list[str]:
    if not CLASSES_FILE.is_file():
        raise FileNotFoundError(f"Arquivo de classes não encontrado: {CLASSES_FILE}")
    names = [line.strip() for line in CLASSES_FILE.read_text(encoding="utf-8").splitlines()]
    names = [name for name in names if name and not name.startswith("#")]
    if not names:
        raise ValueError("dataset/classes.txt não contém classes.")
    if len(names) != len(set(names)):
        raise ValueError("dataset/classes.txt contém nomes repetidos.")
    return names


def write_dataset_yaml(destination: Path) -> Path:
    names = load_classes()
    lines = [
        "path: ../dataset",
        "train: train/images",
        "val: val/images",
        "test: test/images",
        "",
        "names:",
    ]
    lines.extend(f"  {index}: {json.dumps(name, ensure_ascii=False)}" for index, name in enumerate(names))
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def images_in(directory: Path) -> list[Path]:
    return sorted(
        path for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
    )


def label_path_for(image: Path, images_root: Path, labels_root: Path) -> Path:
    return labels_root / image.relative_to(images_root).with_suffix(".txt")


def validate_label_file(label: Path, class_count: int) -> tuple[int, list[str]]:
    objects = 0
    errors: list[str] = []
    for line_no, raw in enumerate(label.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) != 5:
            errors.append(f"{label}:{line_no}: esperado 5 campos")
            continue
        try:
            class_id = int(parts[0])
            coords = [float(value) for value in parts[1:]]
        except ValueError:
            errors.append(f"{label}:{line_no}: valor não numérico")
            continue
        if not 0 <= class_id < class_count:
            errors.append(f"{label}:{line_no}: class_id {class_id} inválido")
        if any(value < 0.0 or value > 1.0 for value in coords):
            errors.append(f"{label}:{line_no}: coordenada fora de 0..1")
        if coords[2] <= 0 or coords[3] <= 0:
            errors.append(f"{label}:{line_no}: largura/altura deve ser positiva")
        objects += 1
    return objects, errors
