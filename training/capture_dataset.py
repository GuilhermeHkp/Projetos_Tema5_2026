"""Captura fotos localmente para o banco bruto (alternativa ao Roboflow Collect)."""

from __future__ import annotations

import argparse
import re
from datetime import datetime

from common import DATASET_ROOT, load_classes


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    if not cleaned:
        raise ValueError("Nome de sessão inválido.")
    return cleaned


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--class-name", required=True)
    parser.add_argument("--session", default=datetime.now().strftime("sessao_%Y%m%d_%H%M%S"))
    parser.add_argument("--device", type=int, default=0)
    args = parser.parse_args()

    classes = load_classes()
    if args.class_name not in classes:
        raise ValueError(f"Classe desconhecida. Opções: {', '.join(classes)}")

    import cv2

    destination = DATASET_ROOT / "raw" / args.class_name / safe_name(args.session)
    destination.mkdir(parents=True, exist_ok=True)
    camera = cv2.VideoCapture(args.device)
    if not camera.isOpened():
        raise RuntimeError(f"Não foi possível abrir a câmera {args.device}.")

    counter = len(list(destination.glob("*.jpg")))
    print("Espaço/S: salvar | Q/Esc: sair")
    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                raise RuntimeError("Falha ao ler frame da câmera.")
            cv2.imshow("Captura do dataset", frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key in (ord("s"), 32):
                counter += 1
                filename = destination / f"{args.class_name}_foto_{counter:05d}.jpg"
                cv2.imwrite(str(filename), frame)
                print("Salva:", filename)
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
