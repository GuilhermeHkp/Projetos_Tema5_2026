"""
Configurações centrais do sistema.
Lê as variáveis de ambiente do arquivo .env (na raiz do projeto) e expõe
constantes usadas pelo restante do backend (conexão com banco de dados,
parâmetros do modelo YOLO e da câmera).
"""
import os
from dotenv import load_dotenv

# Carrega o .env que fica na raiz do projeto (mesmo diretório deste arquivo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _get_int(env_name: str, default: int) -> int:
    value = os.getenv(env_name)
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def _get_float(env_name: str, default: float) -> float:
    value = os.getenv(env_name)
    try:
        return float(value) if value is not None else default
    except ValueError:
        return default


def _get_bool(env_name: str, default: bool) -> bool:
    value = os.getenv(env_name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "sim", "on"}


# --- Banco de dados ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = _get_int("DB_PORT", 3306)
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "GHCE")

# --- Detecção / Câmera ---
# Modo "auto": usa o best.pt especializado quando existir; caso contrário,
# carrega o detector aberto leve incluído no projeto. Também são aceitos
# "custom" (somente best.pt) e "open" (somente detector aberto).
DETECTION_MODE = os.getenv("DETECTION_MODE", "auto").strip().lower()
_weights_env = os.getenv("YOLO_WEIGHTS", "models/best.pt")
YOLO_WEIGHTS = (
    _weights_env if os.path.isabs(_weights_env)
    else os.path.normpath(os.path.join(BASE_DIR, _weights_env))
)
_open_weights_env = os.getenv("OPEN_VOCAB_WEIGHTS", "models/yolov8s-worldv2.pt")
OPEN_VOCAB_WEIGHTS = (
    _open_weights_env if os.path.isabs(_open_weights_env)
    else os.path.normpath(os.path.join(BASE_DIR, _open_weights_env))
)
_catalog_env = os.getenv("OBJECT_CATALOG", "configuration/object_catalog.json")
OBJECT_CATALOG = (
    _catalog_env if os.path.isabs(_catalog_env)
    else os.path.normpath(os.path.join(BASE_DIR, _catalog_env))
)
_clip_env = os.getenv("CLIP_WEIGHTS", "weights/clip/ViT-B-32.pt")
CLIP_WEIGHTS = (
    _clip_env if os.path.isabs(_clip_env)
    else os.path.normpath(os.path.join(BASE_DIR, _clip_env))
)
# Confiança mínima para considerar uma detecção válida.
YOLO_CONF = _get_float("YOLO_CONF", 0.38)
# Limiar de IoU usado no NMS (supressão de caixas sobrepostas). Evita caixas
# duplicadas/quase-idênticas em cima do mesmo objeto.
YOLO_IOU = _get_float("YOLO_IOU", 0.45)
# Exige confirmação em frames consecutivos para reduzir falsos positivos.
TEMPORAL_HITS = max(1, _get_int("TEMPORAL_HITS", 2))
TEMPORAL_WINDOW = max(TEMPORAL_HITS, _get_int("TEMPORAL_WINDOW", 3))
IMMEDIATE_CONF = _get_float("IMMEDIATE_CONF", 0.78)
TEMPORAL_IOU = _get_float("TEMPORAL_IOU", 0.25)
CAMERA_DEVICE = _get_int("CAMERA_DEVICE", 0)

# Segunda etapa de validação semântica. O YOLO-World propõe as caixas e o
# CLIP local reavalia cada recorte entre as classes do catálogo. Isso reduz
# trocas entre itens visualmente próximos (caneta/lápis/marca-texto e
# parafuso/porca/arruela), aceitando a redução de FPS em favor da precisão.
CLIP_VERIFY = _get_bool("CLIP_VERIFY", True)
CLIP_SHA256 = os.getenv("CLIP_SHA256", "40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af").strip().lower()
# Similaridade cosseno do CLIP (não é probabilidade calibrada).
CLIP_MIN_SCORE = _get_float("CLIP_MIN_SCORE", 0.24)
CLIP_MIN_MARGIN = _get_float("CLIP_MIN_MARGIN", 0.050)
# Rejeição open-set: uma classe conhecida precisa vencer também os conceitos
# negativos (objetos fora do catálogo) por esta margem.
CLIP_REJECT_MARGIN = _get_float("CLIP_REJECT_MARGIN", 0.040)
CLIP_REJECT_MIN_SCORE = _get_float("CLIP_REJECT_MIN_SCORE", 0.20)
# Para liberar em um único frame, a margem CLIP deve ser excepcionalmente
# forte; correções de rótulo continuam exigindo confirmação temporal.
CLIP_IMMEDIATE_MARGIN = _get_float("CLIP_IMMEDIATE_MARGIN", 0.120)
# Para corrigir um rótulo entre famílias diferentes (ex.: tesoura -> chave de fenda),
# exige evidência CLIP bem mais forte. Se não houver, rejeita em vez de adivinhar.
CLIP_CROSS_GROUP_MARGIN = _get_float("CLIP_CROSS_GROUP_MARGIN", 0.100)
CLIP_MIN_VIEW_AGREEMENT = max(1, _get_int("CLIP_MIN_VIEW_AGREEMENT", 2))
CLIP_MAX_DETECTIONS = max(1, _get_int("CLIP_MAX_DETECTIONS", 12))
CLIP_FAIL_CLOSED = _get_bool("CLIP_FAIL_CLOSED", True)

# Limites defensivos da API. Evitam que uma requisição acidentalmente enorme
# ocupe memória excessiva no servidor.
MAX_REQUEST_BYTES = max(1_000_000, _get_int("MAX_REQUEST_BYTES", 12_000_000))
MAX_IMAGE_PIXELS = max(1_000_000, _get_int("MAX_IMAGE_PIXELS", 20_000_000))
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "*").strip() or "*"

# --- Diretórios ---
IMAGE_DIR = os.path.join(BASE_DIR, "images")
