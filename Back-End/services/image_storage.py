"""Organização centralizada das imagens geradas pela aplicação."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

import cv2

import config


IMAGE_ROOT = Path(config.IMAGE_DIR).resolve()


def slugify(value: str, default: str = "item") -> str:
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^A-Za-z0-9]+", "-", ascii_value).strip("-").lower()
    return slug[:60] or default


def _save(image, relative_path: Path) -> tuple[Path, Path]:
    absolute_path = (IMAGE_ROOT / relative_path).resolve()
    try:
        absolute_path.relative_to(IMAGE_ROOT)
    except ValueError as exc:
        raise ValueError("Caminho de imagem inválido.") from exc
    absolute_path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(absolute_path), image):
        raise OSError(f"Não foi possível salvar a imagem em {absolute_path}")
    return absolute_path, relative_path


def _readable_suffix(moment: datetime) -> str:
    milliseconds = moment.microsecond // 1000
    return f"{moment:%H-%M-%S}-{milliseconds:03d}_{uuid4().hex[:6]}"


def save_history_image(image, detections, moment: datetime | None = None) -> tuple[Path, Path]:
    moment = moment or datetime.now()
    class_names = sorted({slugify(item.get("name", "objeto"), "objeto") for item in detections})
    label = "-".join(class_names[:3]) or "objeto"
    if len(class_names) > 3:
        label += f"-mais-{len(class_names) - 3}"
    filename = f"deteccao_{_readable_suffix(moment)}_{label}.jpg"
    relative = Path("historico") / f"{moment:%Y}" / f"{moment:%m}" / f"{moment:%d}" / filename
    return _save(image, relative)


def save_catalog_image(image, item_name: str, moment: datetime | None = None) -> tuple[Path, Path]:
    moment = moment or datetime.now()
    item_slug = slugify(item_name, "peca")
    filename = f"{item_slug}_{_readable_suffix(moment)}.jpg"
    relative = (
        Path("cadastro") / item_slug / f"{moment:%Y}" / f"{moment:%m}" /
        f"{moment:%d}" / filename
    )
    return _save(image, relative)


def image_api_url(relative_path: Path) -> str:
    return "/api/imagens/" + quote(relative_path.as_posix(), safe="/")
