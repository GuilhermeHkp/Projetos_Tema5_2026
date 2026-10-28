"""Treina YOLO Detection e instala o melhor peso no backend."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from common import DATASET_ROOT, PROJECT_ROOT, images_in, load_classes, write_dataset_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="yolo11n.pt", help="peso/base Ultralytics para transferência")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", default=None, help="ex.: 0, cpu ou mps")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    load_classes()
    for split in ("train", "val"):
        if not images_in(DATASET_ROOT / split / "images"):
            raise RuntimeError(
                f"dataset/{split}/images está vazio. Anote as caixas e rode split_dataset.py antes de treinar."
            )

    from ultralytics import YOLO

    dataset_yaml = write_dataset_yaml(Path(__file__).with_name("dataset.yaml"))
    model = YOLO(args.model)
    kwargs = {
        "data": str(dataset_yaml),
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "workers": args.workers,
        "project": str(PROJECT_ROOT / "runs" / "detect"),
        "name": "custom",
    }
    if args.device is not None:
        kwargs["device"] = args.device
    results = model.train(**kwargs)

    save_dir = Path(results.save_dir)
    best = save_dir / "weights" / "best.pt"
    if not best.is_file():
        raise FileNotFoundError(f"Treinamento terminou sem gerar {best}")
    destination = PROJECT_ROOT / "Back-End" / "models" / "best.pt"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(best, destination)
    print(f"Modelo pronto para a aplicação: {destination}")


if __name__ == "__main__":
    main()
