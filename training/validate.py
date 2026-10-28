"""Valida o best.pt implantado usando o split de validação ou teste."""

from __future__ import annotations

import argparse

from pathlib import Path

from common import PROJECT_ROOT, write_dataset_yaml


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("val", "test"), default="val")
    parser.add_argument("--device", default=None)
    args = parser.parse_args()

    from ultralytics import YOLO

    weights = PROJECT_ROOT / "Back-End" / "models" / "best.pt"
    if not weights.is_file():
        raise FileNotFoundError(f"Modelo não encontrado: {weights}")
    dataset_yaml = write_dataset_yaml(Path(__file__).with_name("dataset.yaml"))
    kwargs = {"data": str(dataset_yaml), "split": args.split}
    if args.device is not None:
        kwargs["device"] = args.device
    metrics = YOLO(str(weights)).val(**kwargs)
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")


if __name__ == "__main__":
    main()
