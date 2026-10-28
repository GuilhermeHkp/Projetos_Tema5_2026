from __future__ import annotations
import hashlib
import os
import sys
import tempfile
import urllib.request
import subprocess
from pathlib import Path

URL = "https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt"
EXPECTED_SHA256 = "40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af"
ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "Back-End" / "weights" / "clip" / "ViT-B-32.pt"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_load(path: Path) -> None:
    import clip
    model, _ = clip.load(str(path), device="cpu")
    model.eval()
    del model


def main() -> int:
    DEST.parent.mkdir(parents=True, exist_ok=True)
    if DEST.is_file() and sha256(DEST) == EXPECTED_SHA256:
        try:
            validate_load(DEST)
        except Exception as exc:
            print(f"Checkpoint existente tem hash correto, mas falhou no carregamento CLIP: {exc}")
            return 2
        print(f"CLIP já está íntegro e carregável: {DEST}")
        return 0

    fd, temp_name = tempfile.mkstemp(prefix="ViT-B-32-", suffix=".pt", dir=str(DEST.parent))
    os.close(fd)
    temp = Path(temp_name)
    try:
        print("Baixando CLIP ViT-B/32 da fonte oficial da OpenAI...")
        try:
            urllib.request.urlretrieve(URL, temp)
        except Exception as first_exc:
            print(f"Download Python falhou ({first_exc}). Tentando curl.exe...")
            result = subprocess.run(
                ["curl.exe", "-fL", "--retry", "5", "--retry-delay", "3", "-o", str(temp), URL],
                check=False,
            )
            if result.returncode != 0:
                raise RuntimeError(f"download falhou tambem via curl.exe (codigo {result.returncode})") from first_exc
        digest = sha256(temp)
        if digest != EXPECTED_SHA256:
            raise RuntimeError(f"SHA-256 inválido: {digest}")
        print("SHA-256 conferido. Testando clip.load() em CPU...")
        validate_load(temp)
        os.replace(temp, DEST)
        print(f"OK: instalado em {DEST}")
        return 0
    except Exception as exc:
        print(f"FALHA: {exc}")
        return 1
    finally:
        if temp.exists():
            temp.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
