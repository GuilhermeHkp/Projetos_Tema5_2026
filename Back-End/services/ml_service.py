import cv2
import json
import hashlib
import math
import numpy as np
import os
import threading
import time
from collections import deque, OrderedDict
from datetime import datetime


try:
    from ultralytics import YOLO
    try:
        from ultralytics import YOLOWorld
    except ImportError:
        YOLOWorld = None
    YOLO_AVAILABLE = True
except Exception:
    YOLOWorld = None
    YOLO_AVAILABLE = False

from database.models import Peca, Historico
from repositories.peca_repo import search_pecas, get_peca_by_classe_yolo, create_peca, baixar_estoque
from repositories.historico_repo import create_historico
import config
from services.decision_brain import select_label as _brain_select_label, decide_class as _brain_decide_class

# Captura manual (preview ao vivo + gatilho por tecla) com filtro automático
# de duplicatas por similaridade visual (ORB + BFMatcher). Usada por
# cadastrar_peca() no lugar da antiga captura única e incondicional.
from services.captura_frames import capturar_com_filtro_duplicatas
from services.image_storage import image_api_url, save_history_image


# Caminho para salvar imagens capturadas (para cadastro de peças)
IMAGE_DIR = config.IMAGE_DIR
if not os.path.exists(IMAGE_DIR):
    os.makedirs(IMAGE_DIR)

# Estado global do modelo e itens identificados (para simular histórico de check-in) - em um sistema real, isso seria mais robusto e persistente, provavelmente usando o banco de dados para histórico completo.
model = None
detector_mode = None
model_load_attempted = False
catalog_entries = []
prompt_metadata = {}
_inference_lock = threading.Lock()
_temporal_lock = threading.Lock()
_temporal_histories = OrderedDict()
_TEMPORAL_MAX_SOURCES = 64
identified_items = {}
clip_model = None
clip_preprocess = None
clip_text_features = None
clip_reject_features = None
clip_reject_labels = []
clip_device = None
_model_load_lock = threading.Lock()
_model_last_error_code = None


# ============================================================
# FILTROS ANTI FALSO POSITIVO (modelo "custom")
# ============================================================
# Todas as chaves abaixo usam o nome técnico da classe do best.pt.
# Valores são pontos de partida: calibre com DEBUG_FILTROS = True.

# Imprime no terminal o que o modelo vê ([bruto]), o que cada filtro
# descarta e por quê ([descartado]), e o resultado final ([final]).
# Deixe True enquanto estiver diagnosticando; depois volte para False.
DEBUG_FILTROS = True

# Resolução da inferência. 640 = comportamento do código antigo (mais rápido).
# Se a porca (peça pequena) ainda falhar, teste 960 ou 1280.
INFERENCE_IMGSZ = 640

# Região da mesa onde as peças ficam, em proporção do frame
# (x1, y1, x2, y2), valores de 0 a 1. Detecções com centro fora dela são
# descartadas (ex.: teclado, mão, janela). None = desativado.
# Exemplo para a foto da bancada: (0.0, 0.17, 1.0, 0.80)
ROI_MESA = None

# Confiança mínima por classe (além do piso global de 0.45).
_CLASS_MIN_CONF = {
    "chave_inglesa_15cm": 0.70,
    "chave_phillips_19cm": 0.70,
    "chave_phillips_21cm": 0.70,
    "chave_fenda_15cm": 0.65,
    "porca_1cm": 0.70,
    "prego_3cm": 0.60,
    "parafuso_1_5cm": 0.60,
    "parafuso_3_5cm": 0.60,
    "parafuso_6cm": 0.60,
}
_DEFAULT_CLASS_MIN_CONF = 0.45

# Alongamento mínimo da caixa (lado maior / lado menor). Valores baixos de
# propósito: a caixa é alinhada aos eixos, então uma ferramenta na diagonal
# parece menos alongada do que é.
_SHAPE_MIN_ELONGATION = {
    "chave_inglesa_15cm": 1.3,
    "chave_phillips_19cm": 1.5,
    "chave_phillips_21cm": 1.5,
    "chave_fenda_15cm": 1.5,
    "prego_3cm": 1.5,
    "parafuso_3_5cm": 1.4,
    "parafuso_6cm": 1.5,
}

# Alongamento máximo. A porca vista de cima/ângulo fica entre 1.0 e ~2.0.
_SHAPE_MAX_ELONGATION = {
    "porca_1cm": 2.2,
}

# Área máxima da caixa em relação ao frame. É o filtro mais eficaz contra
# janela, ar-condicionado, apagador etc., que são bem maiores que as peças.
_MAX_AREA_RATIO = {
    "chave_inglesa_15cm": 0.20,
    "chave_phillips_19cm": 0.20,
    "chave_phillips_21cm": 0.20,
    "chave_fenda_15cm": 0.20,
    "porca_1cm": 0.02,
    "prego_3cm": 0.03,
    "parafuso_1_5cm": 0.02,
    "parafuso_3_5cm": 0.04,
    "parafuso_6cm": 0.06,
}

# Frames de confirmação por nome exibido (sobrescreve o padrão do modo
# custom, que é max(2, TEMPORAL_HITS)). Ex.: {"Porca sextavada": 1}.
_CLASS_HITS_NEEDED = {}

# Confirmação temporal tolerante a movimento: além do IoU, duas caixas são
# consideradas a mesma peça se a distância entre os centros for menor que
# este fator vezes o maior lado da caixa atual. Peça passando rápido quase
# não tem IoU entre frames, mas o centro continua perto.
# Use 0 para desativar e voltar a depender só do IoU.
_TEMPORAL_CENTER_FACTOR = 1.5


# ============================================================
# BAIXA AUTOMÁTICA DE ESTOQUE
# ============================================================
# Quando uma peça aparece na câmera, a quantidade dela no banco diminui.
# Cada peça física é rastreada como um "track" (nome + posição do centro).
# Uma detecção sem track próximo é uma peça NOVA e desconta 1. O track
# expira depois de ESTOQUE_TTL_TRACK segundos sem ser visto.

# Liga/desliga a baixa automática.
ESTOQUE_AUTOMATICO = True

# Coluna que diminui: "disponivel" (quantidade_disponivel), "quantidade"
# ou "ambas". Se a tela do sistema não mudar após uma detecção, troque.
ESTOQUE_COLUNA = "ambas"

# Segundos sem ver a peça para o track expirar. Depois disso, a mesma peça
# voltando à câmera conta de novo. (Use um valor menor enquanto testa.)
ESTOQUE_TTL_TRACK = 3.0

# Distância máxima entre centros (fração da imagem, 0 a ~1.41) para uma
# detecção ser considerada a "mesma peça" de um track existente.
#  - Mesma peça contada 2x (ela se move muito): aumente (ex.: 0.30).
#  - Duas peças juntas contadas como 1: reduza (ex.: 0.10).
ESTOQUE_DIST_MAX = 0.20

_estoque_lock = threading.Lock()
# origem -> lista de tracks {"nome", "cx", "cy", "visto"}
_estoque_tracks = {}
_ESTOQUE_MAX_ORIGENS = 64


# O best.pt atual foi treinado com nomes técnicos/tamanhos. A API e o banco
# usam nomes estáveis do catálogo; vários tamanhos podem mapear para a mesma
# classe exibida sem alterar o checkpoint.
_CUSTOM_CLASS_MAP = {
    "chave_fenda_15cm": ("Chave de fenda", "ferramenta"),
    "chave_phillips_19cm": ("Chave Phillips", "ferramenta"),
    "chave_phillips_21cm": ("Chave Phillips", "ferramenta"),
    "chave_inglesa_15cm": ("Chave inglesa", "ferramenta"),
    "prego_3cm": ("Prego", "fixador"),
    "parafuso_3_5cm": ("Parafuso", "fixador"),
    "parafuso_1_5cm": ("Parafuso", "fixador"),
    "parafuso_6cm": ("Parafuso", "fixador"),
    "porca_1cm": ("Porca sextavada", "fixador"),
}


def _dbg(*args):
    """Print de diagnóstico, controlado por DEBUG_FILTROS."""
    if DEBUG_FILTROS:
        print(*args)


def _custom_class_metadata(raw_name):
    key = str(raw_name).strip().casefold()
    name, group = _CUSTOM_CLASS_MAP.get(key, (str(raw_name), "modelo_especializado"))
    return {"display_name": name, "group": group}


class DetectorUnavailableError(RuntimeError):
    pass


class DetectorInferenceError(RuntimeError):
    pass


_metrics_lock = threading.Lock()
_metrics_started_at = time.time()
_metrics = {
    "frames": 0,
    "sucessos": 0,
    "erros": 0,
    "deteccoes_brutas": 0,
    "deteccoes_finais": 0,
    "rejeitadas_ambiguas": 0,
    "latencia_total_ms": 0.0,
    "ultima_latencia_ms": None,
    "ultimo_erro": None,
}


def _metric_add(**values):
    with _metrics_lock:
        for key, value in values.items():
            if key in {"ultimo_erro", "ultima_latencia_ms"}:
                _metrics[key] = value
            elif key in _metrics:
                _metrics[key] += value


def get_runtime_metrics():
    """Snapshot seguro para monitoramento, sem expor dados das imagens."""
    with _metrics_lock:
        data = dict(_metrics)
    frames = data["frames"]
    data["latencia_media_ms"] = round(
        data["latencia_total_ms"] / frames, 2
    ) if frames else None
    data["uptime_s"] = round(time.time() - _metrics_started_at, 1)
    data["taxa_sucesso"] = round(data["sucessos"] / frames, 4) if frames else None
    return data


def get_identified_items():
    """Retorna o dicionário atual de itens identificados.

    Usar esta função em vez de importar `identified_items` diretamente:
    `clear_identified_items()` limpa o dicionário no lugar (não cria um
    novo objeto), então qualquer referência obtida por aqui continua
    sempre válida e atualizada.
    """
    return identified_items


def capture_image(device=None):
    if device is None:
        device = config.CAMERA_DEVICE
    cap = cv2.VideoCapture(device)
    if not cap.isOpened():
        print("Erro: Câmera não encontrada.")
        return None
    ret, frame = cap.read()
    cap.release()
    if ret:
        return frame
    return None


def _clean_text_list(values):
    if not isinstance(values, list):
        return []
    result = []
    seen = set()
    for value in values:
        text = str(value).strip()
        key = text.casefold()
        if text and key not in seen:
            result.append(text)
            seen.add(key)
    return result


def _load_object_catalog():
    """Carrega classes, variações textuais e conceitos de rejeição.

    O catálogo aceita ``aliases`` (sinônimos usados pelo CLIP) e
    ``detector_aliases`` (variações adicionadas também ao YOLO-World).
    ``reject_concepts`` descreve objetos deliberadamente fora do inventário;
    eles nunca viram rótulos, servem apenas para impedir falsos positivos.
    """
    with open(config.OBJECT_CATALOG, "r", encoding="utf-8") as catalog_file:
        payload = json.load(catalog_file)
    entries = payload.get("objects", [])
    if not entries:
        raise ValueError("O catálogo de objetos está vazio.")

    prompts_seen = set()
    validated = []
    for entry in entries:
        prompt = str(entry.get("prompt", "")).strip()
        display_name = str(entry.get("display_name", "")).strip()
        if not prompt or not display_name:
            raise ValueError("Cada objeto precisa de prompt e display_name.")
        key = prompt.casefold()
        if key in prompts_seen:
            raise ValueError(f'Prompt duplicado no catálogo: "{prompt}".')
        prompts_seen.add(key)
        aliases = _clean_text_list(entry.get("aliases", []))
        detector_aliases = _clean_text_list(entry.get("detector_aliases", []))
        validated.append({
            "prompt": prompt,
            "display_name": display_name,
            "group": str(entry.get("group", "outros")),
            "min_conf": float(entry.get("min_conf", config.YOLO_CONF)),
            "aliases": aliases,
            "detector_aliases": detector_aliases,
            "min_elongation": float(entry.get("min_elongation", 0.0) or 0.0),
            "max_elongation": float(entry.get("max_elongation", 999.0) or 999.0),
            "score_bias": float(entry.get("score_bias", 0.0) or 0.0),
            "ambiguity_family": str(entry.get("ambiguity_family", "") or ""),
            "family_fallback": bool(entry.get("family_fallback", False)),
        })
    reject_concepts = _clean_text_list(payload.get("reject_concepts", []))
    return validated, reject_concepts


def _load_custom_model(weights):
    global catalog_entries, prompt_metadata
    global clip_model, clip_preprocess, clip_text_features, clip_reject_features, clip_reject_labels, clip_device
    catalog_entries = []
    prompt_metadata = {}
    clip_model = clip_preprocess = clip_text_features = clip_reject_features = clip_device = None
    clip_reject_labels = []
    loaded = YOLO(weights)
    print(f'Modelo especializado carregado: {weights}')
    return loaded


def _validate_clip_checkpoint():
    if not os.path.isfile(config.CLIP_WEIGHTS):
        raise FileNotFoundError("Checkpoint CLIP local ausente.")
    digest = hashlib.sha256()
    with open(config.CLIP_WEIGHTS, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    actual = digest.hexdigest().lower()
    if actual != config.CLIP_SHA256.lower():
        raise RuntimeError("Checkpoint CLIP local falhou na validação SHA-256.")
    return actual


def _load_open_model(weights):
    global catalog_entries, prompt_metadata
    global clip_model, clip_preprocess, clip_text_features, clip_reject_features, clip_reject_labels, clip_device
    catalog_entries, reject_concepts = _load_object_catalog()

    # O YOLO-World recebe nomes principais e apenas aliases selecionados. Isso
    # aumenta recall para variações importantes sem transformar todo sinônimo
    # em um rótulo diferente na resposta final.
    detector_prompts = []
    prompt_metadata = {}
    for entry in catalog_entries:
        for text in [entry["prompt"], *entry.get("detector_aliases", [])]:
            key = text.casefold()
            if key not in prompt_metadata:
                detector_prompts.append(text)
                prompt_metadata[key] = entry

    _validate_clip_checkpoint()
    try:
        import clip
        import torch
    except ImportError as exc:
        raise RuntimeError("Dependência CLIP ausente.") from exc

    original_clip_load = clip.load
    loaded_clip_instances = []

    def load_local_clip(name, *args, **kwargs):
        if name == "ViT-B/32":
            name = config.CLIP_WEIGHTS
        instance = original_clip_load(name, *args, **kwargs)
        loaded_clip_instances.append(instance)
        return instance

    loader = YOLOWorld if YOLOWorld is not None else YOLO
    loaded = loader(weights)
    if not hasattr(loaded, "set_classes"):
        raise RuntimeError("A versão da Ultralytics instalada não oferece YOLO-World.")
    clip.load = load_local_clip
    try:
        loaded.set_classes(detector_prompts)
    finally:
        clip.load = original_clip_load

    if config.CLIP_VERIFY:
        if loaded_clip_instances:
            clip_model, clip_preprocess = loaded_clip_instances[-1]
        else:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            clip_model, clip_preprocess = original_clip_load(config.CLIP_WEIGHTS, device=device)
        clip_model.eval()
        clip_device = next(clip_model.parameters()).device

        templates = (
            "a close-up photo of {}",
            "a clear photo of {} on a plain background",
            "an object photo showing {}",
            "a handheld {}",
            "a real-world photo of {}",
        )
        per_class_features = []
        with torch.no_grad():
            for entry in catalog_entries:
                concepts = [entry["prompt"], *entry.get("aliases", [])]
                descriptions = [template.format(concept) for concept in concepts for template in templates]
                tokens = clip.tokenize(descriptions).to(clip_device)
                features = clip_model.encode_text(tokens)
                features = features / features.norm(dim=-1, keepdim=True)
                mean_feature = features.mean(dim=0, keepdim=True)
                mean_feature = mean_feature / mean_feature.norm(dim=-1, keepdim=True)
                per_class_features.append(mean_feature)
            clip_text_features = torch.cat(per_class_features, dim=0)

            clip_reject_labels = reject_concepts
            if reject_concepts:
                reject_descriptions = [
                    template.format(concept)
                    for concept in reject_concepts
                    for template in templates[:3]
                ]
                tokens = clip.tokenize(reject_descriptions).to(clip_device)
                features = clip_model.encode_text(tokens)
                features = features / features.norm(dim=-1, keepdim=True)
                # Mantemos um vetor por conceito (média dos templates), não uma
                # média global: basta um desconhecido específico competir bem
                # para a detecção ser rejeitada.
                feature_dim = features.shape[-1]
                per_reject = features.reshape(len(reject_concepts), len(templates[:3]), feature_dim).mean(dim=1)
                per_reject = per_reject / per_reject.norm(dim=-1, keepdim=True)
                clip_reject_features = per_reject
            else:
                clip_reject_features = None

    print(
        f'Detector aberto carregado com {len(catalog_entries)} classes, '
        f'{len(detector_prompts)} prompts de detecção e {len(reject_concepts)} conceitos de rejeição: {weights}'
    )
    return loaded


def load_yolo_model(weights: str = None):
    """Carrega o detector no máximo uma vez por processo."""
    global model, detector_mode, model_load_attempted, _model_last_error_code
    with _model_load_lock:
        if model is not None or model_load_attempted:
            return model
        model_load_attempted = True
        _model_last_error_code = None
        if not YOLO_AVAILABLE:
            _model_last_error_code = "ultralytics_ausente"
            print('Ultralytics YOLO não está instalado.')
            return None

        requested_mode = config.DETECTION_MODE
        if requested_mode not in {"auto", "custom", "open"}:
            print(f'DETECTION_MODE inválido: "{requested_mode}". Usando "auto".')
            requested_mode = "auto"
        custom_weights = weights or config.YOLO_WEIGHTS
        try:
            if requested_mode in {"auto", "custom"} and os.path.isfile(custom_weights):
                model = _load_custom_model(custom_weights)
                detector_mode = "custom"
                return model
            if requested_mode == "custom":
                _model_last_error_code = "best_pt_ausente"
                print(f'Modelo especializado não encontrado em "{custom_weights}".')
                return None
            if not os.path.isfile(config.OPEN_VOCAB_WEIGHTS):
                _model_last_error_code = "yolo_world_ausente"
                raise FileNotFoundError("Detector aberto não encontrado.")
            model = _load_open_model(config.OPEN_VOCAB_WEIGHTS)
            detector_mode = "open"
            return model
        except FileNotFoundError as exc:
            model = None
            detector_mode = None
            if _model_last_error_code is None:
                _model_last_error_code = "clip_ausente" if "CLIP" in str(exc) else "arquivo_ausente"
            print(f'Erro ao carregar o detector: {exc}')
            return None
        except Exception as exc:
            model = None
            detector_mode = None
            _model_last_error_code = "falha_carregamento"
            print(f'Erro ao carregar o detector: {exc}')
            return None


def get_detector_status():
    return {
        "carregado": model is not None,
        "modo": detector_mode,
        "modelo_especializado": os.path.basename(config.YOLO_WEIGHTS),
        "modelo_aberto": os.path.basename(config.OPEN_VOCAB_WEIGHTS),
        "catalogo": os.path.basename(config.OBJECT_CATALOG),
        "classes": len(catalog_entries) if detector_mode == "open" else (
            len(model.names) if model is not None and hasattr(model, "names") else 0
        ),
        "verificador_clip": bool(
            detector_mode == "open" and config.CLIP_VERIFY and clip_model is not None
        ),
        "rejeicao_ambigua": bool(config.CLIP_FAIL_CLOSED),
        "rejeicao_open_set": bool(
            detector_mode == "open" and config.CLIP_VERIFY and clip_reject_features is not None
        ),
        "conceitos_rejeicao": len(clip_reject_labels) if detector_mode == "open" else 0,
        "estado": "pronto" if model is not None else (_model_last_error_code or "nao_carregado"),
    }


def sincronizar_classes_no_banco():
    """Sincroniza os nomes finais exibidos pelo detector com o banco."""
    criadas = []
    if model is None:
        return criadas
    if detector_mode == "open":
        nomes = list(dict.fromkeys(entry["display_name"] for entry in catalog_entries))
    else:
        raw_names = model.names.values() if isinstance(model.names, dict) else model.names
        nomes = list(dict.fromkeys(_custom_class_metadata(nome)["display_name"] for nome in raw_names))
    for nome in nomes:
        nome = str(nome)
        try:
            existente = get_peca_by_classe_yolo(nome)
            if existente:
                continue
            nova = Peca(
                nome=nome,
                classe_yolo=nome,
                descricao=f"Classe do detector {detector_mode or 'configurado'}.",
                quantidade=0,
                quantidade_disponivel=0,
                estoque_minimo=0,
            )
            create_peca(nova)
            criadas.append(nome)
        except Exception as e:
            print(f'Aviso: não foi possível sincronizar a classe "{nome}":', e)
            print('Sincronização interrompida; o detector continuará funcionando sem o banco.')
            break
    if criadas:
        print(f"Classes sincronizadas com o banco: {', '.join(criadas)}")
    return criadas


def speak_name(name):
    # áudio removido: frontend fará reprodução quando necessário, por enquanto está dando muitos problemas no back.
    return


def display_name(name):
    print(f"Peça identificada: {name}")


def add_identified_item(name):
    if name not in identified_items:
        identified_items[name] = 0
    identified_items[name] += 1


def clear_identified_items():
    # Importante: usar .clear() em vez de reatribuir (identified_items = {}).
    # Reatribuir criaria um novo dicionário e qualquer código que já tivesse
    # importado a referência antiga (ex.: main.py) ficaria "vendo" o
    # dicionário antigo, desatualizado.
    identified_items.clear()


# Tradução das cores (chave interna em inglês -> texto em pt-BR usado no
# histórico e na fala/TTS do front-end).
NOME_COR_PT = {
    'black': 'preto', 'white': 'branco', 'gray': 'cinza',
    'red': 'vermelho', 'orange': 'laranja', 'yellow': 'amarelo',
    'green': 'verde', 'cyan': 'ciano', 'blue': 'azul',
    'purple': 'roxo', 'pink': 'rosa', 'unknown': 'indefinida',
}


def traduzir_cor(cor_en):
    return NOME_COR_PT.get(cor_en, cor_en)


def analyze_color(bgr_roi):
    """Retorna a cor dominante do objeto (em inglês, ver NOME_COR_PT).

    Usa só a região central da caixa (reduz fundo), decide primeiro se a cor
    é acromática (preto/branco/cinza) olhando S e V, e só depois calcula o
    matiz com média circular, descartando pixels de baixa saturação/brilho.
    """
    try:
        h_px, w_px = bgr_roi.shape[:2]
        if h_px == 0 or w_px == 0:
            return 'unknown'

        # Região central (corta ~20% de cada borda) para reduzir a chance
        # de pegar fundo/mesa que sobra dentro da bounding box.
        margem_y, margem_x = int(h_px * 0.2), int(w_px * 0.2)
        roi_central = bgr_roi[margem_y:h_px - margem_y, margem_x:w_px - margem_x]
        if roi_central.size == 0:
            roi_central = bgr_roi

        hsv = cv2.cvtColor(roi_central, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        h = h.flatten().astype(np.float32)
        s = s.flatten().astype(np.float32)
        v = v.flatten().astype(np.float32)

        media_v = float(np.mean(v))
        media_s = float(np.mean(s))

        # 1) Cores acromáticas primeiro (matiz não é confiável aqui).
        if media_v < 50:
            return 'black'
        if media_s < 35:
            return 'white' if media_v > 180 else 'gray'

        # 2) Só usa pixels "coloridos o bastante" pra não deixar sombra ou
        # reflexo (baixa saturação/brilho) distorcer a média do matiz.
        mascara = (s > 40) & (v > 40)
        h_validos = h[mascara] if np.any(mascara) else h

        # Média circular do matiz: H é um ângulo (0-179 no OpenCV).
        angulos = h_validos * 2.0 * np.pi / 180.0
        seno_medio = float(np.mean(np.sin(angulos)))
        cos_medio = float(np.mean(np.cos(angulos)))
        mh = (np.degrees(np.arctan2(seno_medio, cos_medio)) / 2.0) % 180

        if mh < 10 or mh >= 170:
            return 'red'
        if mh < 22:
            return 'orange'
        if mh < 35:
            return 'yellow'
        if mh < 85:
            return 'green'
        if mh < 100:
            return 'cyan'
        if mh < 130:
            return 'blue'
        if mh < 150:
            return 'purple'
        return 'pink'
    except Exception:
        return 'unknown'


def analyze_size(bbox, frame_shape):
    # bbox: (x1,y1,x2,y2) - retorna a categoria de tamanho pela área relativa ao frame.
    x1, y1, x2, y2 = bbox
    area = (x2 - x1) * (y2 - y1)
    frame_area = frame_shape[0] * frame_shape[1]
    ratio = area / (frame_area + 1e-6)
    if ratio < 0.001:
        return 'muito pequeno'
    if ratio < 0.01:
        return 'pequeno'
    if ratio < 0.05:
        return 'médio'
    return 'grande'


def analyze_shape(bbox):
    x1, y1, x2, y2 = bbox
    w = x2 - x1
    h = y2 - y1
    ar = w / (h + 1e-6)
    if 0.9 <= ar <= 1.1:
        return 'mais ou menos quadrado'
    if ar > 1.1:
        return 'amplo'
    return 'alto'


def _bbox_iou(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    intersection = max(0, ix2 - ix1) * max(0, iy2 - iy1)
    area_a = max(0, ax2 - ax1) * max(0, ay2 - ay1)
    area_b = max(0, bx2 - bx1) * max(0, by2 - by1)
    return intersection / max(area_a + area_b - intersection, 1)


def _mesma_regiao(old_bbox, new_bbox):
    """True se as duas caixas parecem ser a mesma peça em frames vizinhos.

    Aceita por IoU (peça parada) OU por proximidade dos centros (peça em
    movimento, quando o IoU cai a quase zero).
    """
    if _bbox_iou(old_bbox, new_bbox) >= config.TEMPORAL_IOU:
        return True
    if _TEMPORAL_CENTER_FACTOR <= 0:
        return False
    ox = (old_bbox[0] + old_bbox[2]) / 2.0
    oy = (old_bbox[1] + old_bbox[3]) / 2.0
    nx = (new_bbox[0] + new_bbox[2]) / 2.0
    ny = (new_bbox[1] + new_bbox[3]) / 2.0
    maior_lado = max(new_bbox[2] - new_bbox[0], new_bbox[3] - new_bbox[1], 1)
    return math.hypot(nx - ox, ny - oy) <= _TEMPORAL_CENTER_FACTOR * maior_lado


def _select_clip_label(scores):
    """Compatibilidade interna: delega a decisão de margem ao cérebro de consenso."""
    return _brain_select_label(scores, config.CLIP_MIN_SCORE, config.CLIP_MIN_MARGIN)


def _verify_with_clip(frame, detections):
    """Segundo estágio neural: CLIP global + múltiplas vistas + rejeição de incerteza.

    O YOLO-World propõe caixas/rótulos. O CLIP NÃO fica preso ao grupo proposto:
    ele compara o recorte contra todo o catálogo. Isso permite corrigir erros como
    "tesoura" -> "Chave de fenda". Porém uma troca entre grupos só é aceita com
    margem forte; caso contrário a detecção é descartada para evitar alucinação.
    """
    if detector_mode != "open" or not config.CLIP_VERIFY or not detections:
        return detections
    if clip_model is None or clip_preprocess is None or clip_text_features is None:
        if config.CLIP_FAIL_CLOSED:
            _metric_add(rejeitadas_ambiguas=len(detections))
            return []
        return detections

    selected = sorted(detections, key=lambda item: item["conf"], reverse=True)[
        :config.CLIP_MAX_DETECTIONS
    ]
    try:
        import torch
        from PIL import Image

        frame_h, frame_w = frame.shape[:2]
        view_tensors = []
        view_owners = []

        # Três enquadramentos por objeto: caixa exata, +8% e +20% de contexto.
        # Consistência entre vistas reduz a chance de um detalhe/fundo dominar.
        for det_index, detection in enumerate(selected):
            x1, y1, x2, y2 = detection["bbox"]
            for pad_ratio in (0.0, 0.08, 0.20):
                pad_x = int((x2 - x1) * pad_ratio)
                pad_y = int((y2 - y1) * pad_ratio)
                cx1, cy1 = max(0, x1 - pad_x), max(0, y1 - pad_y)
                cx2, cy2 = min(frame_w, x2 + pad_x), min(frame_h, y2 + pad_y)
                if cx2 - cx1 < 8 or cy2 - cy1 < 8:
                    continue
                crop = cv2.cvtColor(frame[cy1:cy2, cx1:cx2], cv2.COLOR_BGR2RGB)
                view_tensors.append(clip_preprocess(Image.fromarray(crop)))
                view_owners.append(det_index)

        if not view_tensors:
            return [] if config.CLIP_FAIL_CLOSED else detections

        batch = torch.stack(view_tensors).to(clip_device)
        with torch.no_grad():
            image_features = clip_model.encode_image(batch)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            all_similarities = image_features @ clip_text_features.T
            reject_similarities = (
                image_features @ clip_reject_features.T
                if clip_reject_features is not None else None
            )

        scores_by_detection = [[] for _ in selected]
        rejects_by_detection = [[] for _ in selected]
        reject_rows = (
            reject_similarities.detach().cpu().tolist()
            if reject_similarities is not None else [None] * len(view_owners)
        )
        for owner, scores, reject_scores in zip(
            view_owners, all_similarities.detach().cpu().tolist(), reject_rows
        ):
            scores_by_detection[owner].append(scores)
            if reject_scores is not None:
                rejects_by_detection[owner].append(reject_scores)

        verified = []
        rejected = 0
        for detection, view_scores, reject_view_scores in zip(
            selected, scores_by_detection, rejects_by_detection
        ):
            if len(view_scores) < config.CLIP_MIN_VIEW_AGREEMENT:
                rejected += 1
                continue

            # Média por classe entre vistas + votação independente de cada vista.
            class_count = len(catalog_entries)
            averaged = [
                sum(scores[class_id] for scores in view_scores) / len(view_scores)
                for class_id in range(class_count)
            ]
            averaged_rejects = []
            if reject_view_scores:
                reject_count = len(reject_view_scores[0])
                averaged_rejects = [
                    sum(scores[idx] for scores in reject_view_scores) / len(reject_view_scores)
                    for idx in range(reject_count)
                ]
            decision = _brain_decide_class(
                averaged, view_scores, catalog_entries,
                detection.get("group", "outros"),
                min_score=config.CLIP_MIN_SCORE,
                min_margin=config.CLIP_MIN_MARGIN,
                cross_group_margin=config.CLIP_CROSS_GROUP_MARGIN,
                min_view_agreement=config.CLIP_MIN_VIEW_AGREEMENT,
                reject_scores=averaged_rejects,
                reject_margin=config.CLIP_REJECT_MARGIN,
                reject_min_score=config.CLIP_REJECT_MIN_SCORE,
            )
            if decision is None:
                rejected += 1
                continue
            class_id = decision["class_id"]
            verifier_score = decision["score"]
            verifier_margin = decision["margin"]
            votes = decision["votes"]
            entry = decision["entry"]
            chosen_group = entry.get("group", "outros")

            # Regra geométrica defensiva para objetos muito alongados. Não
            # "classifica" sozinha; apenas rejeita rótulos incompatíveis.
            w = max(1, detection["bbox"][2] - detection["bbox"][0])
            h = max(1, detection["bbox"][3] - detection["bbox"][1])
            elongation = max(w, h) / max(1.0, min(w, h))
            min_elongation = float(entry.get("min_elongation", 0.0) or 0.0)
            max_elongation = float(entry.get("max_elongation", 999.0) or 999.0)
            if not (min_elongation <= elongation <= max_elongation):
                rejected += 1
                continue

            verified.append({
                **detection,
                "proposal_name": detection.get("name"),
                "proposal_class_id": detection.get("class_id"),
                "proposal_conf": detection.get("conf"),
                "name": entry["display_name"],
                "class_id": class_id,
                "group": chosen_group,
                "prompt": entry["prompt"],
                "verified": True,
                # Scores internos servem para auditoria/decisão; não são
                # probabilidades calibradas e não são usados no rótulo da UI.
                "verifier_score": round(float(verifier_score), 6),
                "verifier_margin": round(float(verifier_margin), 6),
                "verifier_votes": votes,
                "verifier_views": len(view_scores),
                "open_set_checked": bool(averaged_rejects),
            })
        if rejected:
            _metric_add(rejeitadas_ambiguas=rejected)
        return verified
    except Exception as exc:
        _metric_add(erros=1, ultimo_erro="clip_inferencia")
        print("Erro na verificação CLIP:", exc)
        if config.CLIP_FAIL_CLOSED:
            raise DetectorInferenceError("Falha na verificação CLIP.") from exc
        return detections


def _suppress_conflicting_labels(detections):
    """Remove rótulos concorrentes na mesma região.

    O NMS do modelo normalmente é separado por classe. Assim, uma caneta pode
    aparecer simultaneamente como lápis e marca-texto. Esta segunda passagem
    compara classes do mesmo grupo sem apagar objetos distintos lado a lado.
    """
    accepted = []
    for candidate in sorted(detections, key=lambda item: item["conf"], reverse=True):
        conflicts = False
        for kept in accepted:
            same_name = candidate["name"] == kept["name"]
            same_group = candidate.get("group") == kept.get("group")
            overlap = _bbox_iou(candidate["bbox"], kept["bbox"])
            if (same_name and overlap >= 0.50) or (same_group and overlap >= 0.65):
                _dbg(
                    f"[conflito] removido {candidate['name']} "
                    f"(iou={overlap:.2f} com {kept['name']})"
                )
                conflicts = True
                break
        if not conflicts:
            accepted.append(candidate)
    return accepted


def _stabilize_detections(detections, source_id="default"):
    """Confirma classes em frames próximos sem misturar origens distintas.

    No modelo custom exige pelo menos 2 frames (um falso positivo costuma
    aparecer só em um frame). Use _CLASS_HITS_NEEDED para ajustar por classe.

    A correspondência entre frames usa IoU OU proximidade de centros
    (ver _mesma_regiao), para não perder peças que passam rápido.
    """
    if detector_mode == "custom":
        hits_needed = max(2, config.TEMPORAL_HITS)
    else:
        hits_needed = config.TEMPORAL_HITS

    if hits_needed <= 1 and not _CLASS_HITS_NEEDED:
        return detections

    key = str(source_id or "default")[:128]
    with _temporal_lock:
        history = _temporal_histories.get(key)
        if history is None:
            history = deque(maxlen=max(config.TEMPORAL_WINDOW, hits_needed))
            _temporal_histories[key] = history
        else:
            _temporal_histories.move_to_end(key)
        while len(_temporal_histories) > _TEMPORAL_MAX_SOURCES:
            _temporal_histories.popitem(last=False)
        previous_frames = list(history)
        history.append(detections)
    stable = []
    for detection in detections:
        hits = 1
        for previous in previous_frames:
            if any(
                old["name"] == detection["name"]
                and _mesma_regiao(old["bbox"], detection["bbox"])
                for old in previous
            ):
                hits += 1
        proposal_name = detection.get("proposal_name")
        same_as_proposal = proposal_name in (None, detection.get("name"))
        verifier_margin = float(detection.get("verifier_margin", 0.0) or 0.0)
        verifier_votes = int(detection.get("verifier_votes", 0) or 0)
        verifier_views = int(detection.get("verifier_views", 0) or 0)
        verifier_is_strong = (
            verifier_views > 0
            and verifier_votes == verifier_views
            and verifier_margin >= config.CLIP_IMMEDIATE_MARGIN
        )
        # No modelo custom não há atalho de "confiança alta": é justamente
        # por ele que um falso positivo forte passaria no primeiro frame.
        immediate = (
            detector_mode != "custom"
            and detection["conf"] >= config.IMMEDIATE_CONF
            and same_as_proposal
            and (not detection.get("verified") or verifier_is_strong)
        )
        class_hits_needed = _CLASS_HITS_NEEDED.get(detection.get("name"), hits_needed)
        if immediate or hits >= class_hits_needed:
            stable.append({**detection, "temporal_hits": hits})
        else:
            _dbg(
                f"[temporal] aguardando confirmação: {detection['name']} "
                f"hits={hits}/{class_hits_needed}"
            )
    return stable


def _raw_class_name(cls):
    """Nome técnico da classe, seja `names` um dict ou uma lista."""
    names = getattr(model, "names", None)
    if isinstance(names, dict):
        return names.get(cls, str(cls))
    if isinstance(names, (list, tuple)) and 0 <= cls < len(names):
        return names[cls]
    return str(cls)


def detect_frame(frame, conf=None, iou=None, source_id="default"):
    """Retorna lista de detecções: dicts com 'name','bbox','conf'"""

    conf = max(0.45, config.YOLO_CONF if conf is None else float(conf))
    iou = 0.50 if iou is None else float(iou)

    detections = []

    if model is None and YOLO_AVAILABLE and not model_load_attempted:
        load_yolo_model()

    if model is not None:
        try:
            inference_conf = conf

            if detector_mode == "open" and catalog_entries:
                inference_conf = min(
                    conf,
                    min(item["min_conf"] for item in catalog_entries)
                )

            # Executa a detecção com o YOLO
            with _inference_lock:
                results = model(
                    frame,
                    conf=inference_conf,
                    iou=iou,
                    imgsz=INFERENCE_IMGSZ,
                    verbose=False
                )

            height, width = frame.shape[:2]

            for res in results:
                boxes = res.boxes

                if DEBUG_FILTROS and len(boxes) > 0:
                    print("[bruto]", [
                        (str(_raw_class_name(int(b.cls[0]))), round(float(b.conf[0]), 2))
                        for b in boxes
                    ])

                for box in boxes:
                    conf_score = float(box.conf[0]) if hasattr(box, 'conf') else float(box.conf)
                    cls = int(box.cls[0]) if hasattr(box.cls, '__len__') else int(box.cls)

                    raw_name = _raw_class_name(cls)
                    raw_key = str(raw_name).casefold()

                    if detector_mode == "custom":
                        metadata = _custom_class_metadata(raw_name)
                    else:
                        metadata = prompt_metadata.get(raw_key, {})

                    min_conf = max(conf, float(metadata.get("min_conf", conf)))
                    min_conf = max(
                        min_conf,
                        _CLASS_MIN_CONF.get(raw_key, _DEFAULT_CLASS_MIN_CONF)
                    )

                    if conf_score < min_conf:
                        _dbg(f"[descartado] {raw_key} confianca {conf_score:.2f} < {min_conf:.2f}")
                        continue

                    name = metadata.get("display_name", str(raw_name))
                    xyxy = box.xyxy[0].tolist() if hasattr(box, 'xyxy') else box.xyxy.tolist()

                    x1 = max(0, min(width - 1, int(xyxy[0])))
                    y1 = max(0, min(height - 1, int(xyxy[1])))
                    x2 = max(0, min(width, int(xyxy[2])))
                    y2 = max(0, min(height, int(xyxy[3])))

                    if x2 <= x1 or y2 <= y1:
                        continue

                    # ---- Filtros anti falso positivo ----
                    w_box = x2 - x1
                    h_box = y2 - y1
                    elongation = max(w_box, h_box) / max(1, min(w_box, h_box))
                    box_ratio = (w_box * h_box) / max(width * height, 1)

                    _dbg(
                        "[filtros]", raw_key,
                        "conf=", round(conf_score, 2),
                        "alongamento=", round(elongation, 2),
                        "area=", round(box_ratio, 4),
                    )

                    # Região da mesa: descarta o que está fora (teclado, mão, janela)
                    if ROI_MESA is not None:
                        cx = ((x1 + x2) / 2) / width
                        cy = ((y1 + y2) / 2) / height
                        rx1, ry1, rx2, ry2 = ROI_MESA
                        if not (rx1 <= cx <= rx2 and ry1 <= cy <= ry2):
                            _dbg(f"[descartado] {raw_key} fora da ROI_MESA (cx={cx:.2f}, cy={cy:.2f})")
                            continue

                    shape_min = _SHAPE_MIN_ELONGATION.get(raw_key)
                    if shape_min is not None and elongation < shape_min:
                        _dbg(f"[descartado] {raw_key} alongamento {elongation:.2f} < {shape_min}")
                        continue

                    shape_max = _SHAPE_MAX_ELONGATION.get(raw_key)
                    if shape_max is not None and elongation > shape_max:
                        _dbg(f"[descartado] {raw_key} alongamento {elongation:.2f} > {shape_max}")
                        continue

                    max_ratio = _MAX_AREA_RATIO.get(raw_key)
                    if max_ratio is not None and box_ratio > max_ratio:
                        _dbg(f"[descartado] {raw_key} area {box_ratio:.4f} > {max_ratio}")
                        continue

                    detections.append({
                        'name': name,
                        'class_id': cls,
                        'bbox': (x1, y1, x2, y2),
                        'conf': conf_score,
                        'prompt': str(raw_name),
                        'group': metadata.get("group", "modelo_especializado"),
                        'engine': detector_mode,
                    })

            _metric_add(deteccoes_brutas=len(detections))

            # Verificação auxiliar
            with _inference_lock:
                detections = _verify_with_clip(frame, detections)

            # Remove conflitos e estabiliza detecções
            detections = _suppress_conflicting_labels(detections)
            detections = _stabilize_detections(detections, source_id=source_id)

            _metric_add(deteccoes_finais=len(detections))

            if DEBUG_FILTROS and (detections or results):
                _dbg("[final]", [d["name"] for d in detections])

            return detections

        except Exception as e:
            print('Erro na detecção:', e)
            _metric_add(erros=1, ultimo_erro="detector_inferencia")
            raise DetectorInferenceError("Falha durante a inferência do detector.") from e

    raise DetectorUnavailableError("Detector não está carregado.")


def _register_detections(frame, detections):
    """Registra detecções no histórico e devolve dados serializáveis.

    Cada detecção tem sua cor calculada individualmente ANTES de agrupar, e o
    agrupamento é por (nome, cor): objetos do mesmo tipo e da mesma cor são
    somados num único registro com quantidade > 1.
    """
    # 1) Calcula os atributos (cor/tamanho/formato) de CADA detecção
    # individualmente, antes de qualquer agrupamento.
    enriquecidas = []
    for d in detections:
        x1, y1, x2, y2 = d['bbox']
        roi = frame[y1:y2, x1:x2] if y2 > y1 and x2 > x1 else None
        color = analyze_color(roi) if roi is not None and roi.size > 0 else 'unknown'
        size = analyze_size(d['bbox'], frame.shape)
        shape = analyze_shape(d['bbox'])
        enriquecidas.append({**d, 'color': color, 'size': size, 'shape': shape})

    # 2) Agrupa por (nome, cor) — não só por nome.
    grouped = {}
    for d in enriquecidas:
        chave = (d['name'], d['color'])
        grouped.setdefault(chave, []).append(d)

    historicos = []
    for (name, color), items in grouped.items():
        count = len(items)
        # Dentro do mesmo grupo (nome+cor), os itens já são equivalentes;
        # usa o de maior confiança como referência para tamanho/formato/conf.
        d0 = max(items, key=lambda item: item['conf'])
        size = d0['size']
        shape = d0['shape']
        pecas = search_pecas({'nome': name})
        peca_id = pecas[0].peca_id if pecas else None
        descricao = (f"cor={traduzir_cor(color)}, tamanho={size}, "
                     f"formato={shape}, score_detector={d0['conf']:.2f}")
        historico = Historico(peca_id=peca_id, nome_peca=name, quantidade=count,
                              descricao=descricao, horario_registro=datetime.now())
        create_historico(historico)
        historicos.append(historico)
        add_identified_item(name)
    return historicos


def annotate_frame(frame, detections):
    """Desenha as caixas de identificação na imagem para exibição no Front-End."""
    output = frame.copy()
    for d in detections:
        x1, y1, x2, y2 = d['bbox']
        label = f"{d['name']} score={d['conf']:.2f}"
        cv2.rectangle(output, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(output, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (0, 255, 0), 2, cv2.LINE_AA)
    return output


def _localizar_peca_para_estoque(nome):
    """Acha a peça do banco: primeiro por classe_yolo (única), depois por nome."""
    peca = get_peca_by_classe_yolo(nome)
    if peca:
        return peca
    pecas = search_pecas({'nome': nome})
    return pecas[0] if pecas else None


def _aplicar_baixa_estoque(detections, frame_shape, source_id="default"):
    """Diminui o estoque das peças detectadas, uma vez por peça física.

    Cada peça visível é um "track" (nome + posição do centro no frame).
    Uma detecção que não casa com nenhum track existente do mesmo nome,
    dentro de ESTOQUE_DIST_MAX, é uma peça NOVA e desconta 1 da sua linha
    no banco. Tracks expiram após ESTOQUE_TTL_TRACK segundos sem serem
    vistos; a peça que volta depois disso conta de novo.

    Assim, 2 chaves iguais entrando juntas descontam 2, uma terceira que
    entra enquanto as outras continuam desconta só mais 1, e uma nova
    passagem de peças iguais (depois do TTL) volta a descontar.

    Retorna a lista do que entrou neste frame. O item entra na lista mesmo se
    o banco falhar, para o histórico não deixar de listar a peça.
    """
    if not ESTOQUE_AUTOMATICO:
        return []

    agora = time.time()
    origem = str(source_id or "default")[:128]
    altura, largura = frame_shape[:2]
    altura = max(1, altura)
    largura = max(1, largura)
    baixas = {}

    with _estoque_lock:
        tracks = _estoque_tracks.setdefault(origem, [])
        # Remove tracks expirados.
        tracks[:] = [t for t in tracks if agora - t["visto"] <= ESTOQUE_TTL_TRACK]

        # Limita o número de origens guardadas em memória.
        if len(_estoque_tracks) > _ESTOQUE_MAX_ORIGENS:
            for k in [k for k, v in _estoque_tracks.items() if not v and k != origem]:
                del _estoque_tracks[k]

        usados = set()

        # Maior confiança primeiro: ela escolhe o track antes das outras.
        for d in sorted(detections, key=lambda x: x["conf"], reverse=True):
            x1, y1, x2, y2 = d["bbox"]
            cx = ((x1 + x2) / 2) / largura
            cy = ((y1 + y2) / 2) / altura

            melhor, melhor_dist = None, ESTOQUE_DIST_MAX
            for i, t in enumerate(tracks):
                if i in usados or t["nome"] != d["name"]:
                    continue
                dist = math.hypot(cx - t["cx"], cy - t["cy"])
                if dist < melhor_dist:
                    melhor, melhor_dist = i, dist

            if melhor is None:
                # Peça nova: cria o track e desconta 1.
                tracks.append({"nome": d["name"], "cx": cx, "cy": cy, "visto": agora})
                usados.add(len(tracks) - 1)
                baixas[d["name"]] = baixas.get(d["name"], 0) + 1
            else:
                # Mesma peça de antes (talvez só se moveu): atualiza o track.
                tracks[melhor].update(cx=cx, cy=cy, visto=agora)
                usados.add(melhor)

        if baixas or len(detections) > 1:
            print(
                f"[estoque] detectadas={len(detections)} "
                f"tracks={len(tracks)} baixas={baixas}"
            )

    resultado = []
    for nome, qtd in baixas.items():
        item = {
            "nome": nome,
            "peca_id": None,
            "baixou": qtd,
            "quantidade_atual": None,
        }
        try:
            peca = _localizar_peca_para_estoque(nome)
            if peca is None:
                print(f'Aviso: peça "{nome}" não encontrada no banco; estoque não alterado.')
            else:
                antes = getattr(peca, "quantidade_disponivel", None)
                atual = baixar_estoque(peca.peca_id, qtd, ESTOQUE_COLUNA)
                item["peca_id"] = peca.peca_id
                item["quantidade_atual"] = atual
                print(f'[estoque] "{nome}" peca_id={peca.peca_id} '
                      f'antes={antes} baixou={qtd} depois={atual}')
        except Exception as e:
            print(f'Aviso: falha ao baixar estoque de "{nome}":', e)
        resultado.append(item)
    return resultado


def detect_and_register_checkin_frame(image_bytes, conf=None, registrar=True, source_id="default"):
    """Processa uma imagem enviada pelo navegador (um frame do stream ao vivo),
    sem abrir a câmera do servidor.

    Quando entra uma peça NOVA (mesma regra da baixa de estoque), o histórico
    registra TODAS as peças que estão na câmera naquele momento. Uma peça
    parada, sem entrada nova, não gera novas linhas. O parâmetro `registrar`
    é mantido por compatibilidade com a API, mas não muda o comportamento.
    """
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    frame = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if frame is None:
        raise ValueError("Não foi possível decodificar a imagem enviada.")
    if frame.shape[0] * frame.shape[1] > config.MAX_IMAGE_PIXELS:
        raise ValueError(
            f"Imagem excede o limite de {config.MAX_IMAGE_PIXELS} pixels."
        )
    inicio = time.perf_counter()
    detections = detect_frame(frame, conf=conf, source_id=source_id)
    latency_ms = round((time.perf_counter() - inicio) * 1000, 2)
    _metric_add(
        frames=1,
        sucessos=1,
        latencia_total_ms=latency_ms,
        ultima_latencia_ms=latency_ms,
    )

    estoque = _aplicar_baixa_estoque(detections, frame.shape, source_id)

    if estoque:
        _dbg(
            f"[debug] source={source_id!r} "
            f"detectou={[d['name'] for d in detections]} "
            f"baixas={[(e['nome'], e['baixou'], e['peca_id'], e['quantidade_atual']) for e in estoque]}"
        )

    # Entrou algo novo -> registra TODAS as peças visíveis na câmera agora.
    if estoque and detections:
        try:
            historicos = _register_detections(frame, detections)
            _, relative_image = save_history_image(
                annotate_frame(frame, detections), detections
            )
            image_url = image_api_url(relative_image)
            return {
                "itens": [{**asdict_historico(h), "imagem": image_url} for h in historicos],
                "imagem": image_url,
                "deteccoes": detections,
                "estoque": estoque,
                "latency_ms": latency_ms,
                "mensagem": "Itens identificados na tela.",
            }
        except Exception as e:
            print("Aviso: não foi possível gravar o histórico da passagem:", e)

    # Nada novo: só devolve a detecção, sem gravar nada
    return {
        "itens": [],
        "imagem": None,
        "deteccoes": detections,
        "estoque": estoque,
        "latency_ms": latency_ms,
        "mensagem": "Itens identificados na tela." if detections else "Nenhuma detecção confiável.",
    }


def asdict_historico(h):
    return {
        "historico_id": h.historico_id,
        "peca_id": h.peca_id,
        "nome_peca": h.nome_peca,
        "quantidade": h.quantidade,
        "descricao": h.descricao,
        "horario_registro": h.horario_registro.isoformat() if h.horario_registro else None,
    }


def detect_and_register_checkin(device=None, conf=None):
    """Compatibilidade com o modo antigo: captura a câmera ligada ao Python."""
    if device is None:
        device = config.CAMERA_DEVICE
    frame = capture_image(device)
    if frame is None:
        return None
    detections = detect_frame(frame, conf=conf)
    if not detections:
        return []
    return _register_detections(frame, detections)


def cadastrar_peca():
    # Delega para capturar_com_filtro_duplicatas(), que abre um preview ao
    # vivo e só grava quando o usuário aciona o gatilho manual (tecla S/ESPAÇO)
    # E o frame passa no filtro de similaridade visual (ORB) contra a galeria.
    nome = input('Digite o nome da peça: ').strip()
    if not nome:
        print('Nome é obrigatório.')
        return

    imagens_salvas = capturar_com_filtro_duplicatas(nome)
    if not imagens_salvas:
        print('Nenhuma imagem nova foi salva (cancelado ou tudo bloqueado como duplicata); peça não cadastrada.')
        return

    peca = Peca(nome=nome, imagem_path=imagens_salvas[0])
    create_peca(peca)
    print(f'Peça "{nome}" cadastrada com {len(imagens_salvas)} imagem(ns), ex.: {imagens_salvas[0]}')


def load_trained_model():
    # Alias preservado para api.py e main.py.
    if YOLO_AVAILABLE:
        loaded = load_yolo_model()
        try:
            if loaded is not None:
                sincronizar_classes_no_banco()
        except Exception as e:
            print('Aviso: não foi possível sincronizar as classes do modelo com o banco agora:', e)
        return loaded
    else:
        print('Ultralytics indisponível; a detecção não será iniciada.')
        return None