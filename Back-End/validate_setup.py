"""Valida instalação/modelos sem abrir câmera nem alterar banco."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

import config

BACKEND_DIR = Path(__file__).resolve().parent
CATALOG_PATH = Path(config.OBJECT_CATALOG)
OPEN_MODEL_PATH = Path(config.OPEN_VOCAB_WEIGHTS)
CLIP_MODEL_PATH = Path(config.CLIP_WEIGHTS)
CUSTOM_MODEL_PATH = Path(config.YOLO_WEIGHTS)
ENV_PATH = BACKEND_DIR / ".env"
EXPECTED_CLIP_SHA256 = config.CLIP_SHA256


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def valid_torch_zip(path: Path) -> bool:
    try:
        if not zipfile.is_zipfile(path):
            return False
        with zipfile.ZipFile(path) as archive:
            return archive.testzip() is None and len(archive.namelist()) > 10
    except (OSError, zipfile.BadZipFile):
        return False


def report(level: str, message: str) -> None:
    print(f"[{level}] {message}")


def load_catalog():
    try:
        payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        entries = payload.get("objects", [])
        rejects = payload.get("reject_concepts", [])
        if not entries:
            raise ValueError("catálogo sem objetos")
        return entries, rejects
    except Exception as exc:
        raise RuntimeError(f"Catálogo inválido: {exc}") from exc


def validate_custom_model() -> tuple[bool, int]:
    if not CUSTOM_MODEL_PATH.is_file():
        return False, 0
    if CUSTOM_MODEL_PATH.stat().st_size < 1_000_000 or not valid_torch_zip(CUSTOM_MODEL_PATH):
        report("ERRO", f"best.pt ausente/incompleto/corrompido: {CUSTOM_MODEL_PATH}")
        return False, 0
    try:
        from ultralytics import YOLO
        loaded = YOLO(str(CUSTOM_MODEL_PATH))
        names = loaded.names.values() if isinstance(loaded.names, dict) else loaded.names
        count = len(list(names))
        report("OK", f"Modelo especializado carregável: {CUSTOM_MODEL_PATH.name} ({count} classes)")
        return True, count
    except Exception as exc:
        report("ERRO", f"best.pt existe, mas não carregou no Ultralytics instalado: {exc}")
        return False, 0


def validate_open_stack() -> tuple[bool, int]:
    if not OPEN_MODEL_PATH.is_file():
        report("AVISO", f"YOLO-World não incluído: {OPEN_MODEL_PATH.name}")
        return False, 0
    if OPEN_MODEL_PATH.stat().st_size < 1_000_000 or not valid_torch_zip(OPEN_MODEL_PATH):
        report("ERRO", f"YOLO-World corrompido/incompleto: {OPEN_MODEL_PATH}")
        return False, 0

    if not CLIP_MODEL_PATH.is_file() or CLIP_MODEL_PATH.stat().st_size < 1_000_000:
        report("ERRO", f"CLIP ausente/incompleto: {CLIP_MODEL_PATH}")
        return False, 0
    digest = sha256(CLIP_MODEL_PATH)
    if digest != EXPECTED_CLIP_SHA256.lower():
        report("ERRO", f"CLIP com SHA-256 incorreto: {digest}")
        return False, 0
    try:
        import clip  # noqa: F401
    except Exception:
        report("ERRO", "YOLO-World existe, mas o pacote Python 'clip' não está instalado. Rode INSTALAR_CLIP.cmd.")
        return False, 0

    try:
        entries, rejects = load_catalog()
        report("OK", f"Fallback aberto disponível: {len(entries)} classes, {len(rejects)} conceitos de rejeição")
        return True, len(entries)
    except Exception as exc:
        report("ERRO", str(exc))
        return False, 0


def main() -> int:
    if not ENV_PATH.is_file():
        report("ERRO", f".env ausente: {ENV_PATH}")
        return 2

    try:
        entries, rejects = load_catalog()
        report("OK", f"Catálogo legível: {len(entries)} objetos; open-set: {len(rejects)}")
    except Exception as exc:
        report("ERRO", str(exc))
        return 3

    mode = (config.DETECTION_MODE or "auto").strip().lower()
    if mode not in {"auto", "custom", "open"}:
        report("ERRO", f"DETECTION_MODE inválido: {mode!r}")
        return 4

    custom_ok, custom_classes = validate_custom_model()
    need_open = mode == "open" or (mode == "auto" and not custom_ok)
    open_ok = False
    open_classes = 0
    if need_open:
        open_ok, open_classes = validate_open_stack()
    elif OPEN_MODEL_PATH.is_file():
        # Fallback presente: valida também, mas não bloqueia o modo custom.
        try:
            open_ok, open_classes = validate_open_stack()
        except Exception:
            open_ok = False
    else:
        report("INFO", "YOLO-World/CLIP são opcionais porque o best.pt especializado está disponível.")

    if mode == "custom" and not custom_ok:
        report("ERRO", "DETECTION_MODE=custom exige Back-End\\models\\best.pt carregável.")
        return 5
    if mode == "open" and not open_ok:
        report("ERRO", "DETECTION_MODE=open exige YOLO-World + CLIP.")
        return 6
    if mode == "auto" and not (custom_ok or open_ok):
        report("ERRO", "DETECTION_MODE=auto não encontrou detector utilizável.")
        return 7

    selected = "custom" if custom_ok and mode in {"auto", "custom"} else "open"
    report("OK", f"Detector selecionado pelo modo {mode}: {selected}")
    report("OK", f"Configuração válida. Classes do detector selecionado: {custom_classes if selected == 'custom' else open_classes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
