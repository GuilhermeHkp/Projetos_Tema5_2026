"""
captura_frames.py

Script de CAPTURA MANUAL de frames para cadastro/galeria de peças, com
FILTRO AUTOMÁTICO DE DUPLICATAS por similaridade visual (ORB + BFMatcher).

O que mudou em relação ao script antigo (capture_image + save_image em
ml_service.py):
  - REMOVIDO: captura de um frame único e salvamento incondicional assim
    que a câmera abre (não havia preview nem chance de escolher o momento).
  - ADICIONADO: preview ao vivo da câmera + gatilho manual (tecla) — o
    usuário decide exatamente quando tentar salvar.
  - ADICIONADO: antes de gravar, o frame candidato é comparado (ORB +
    BFMatcher) com a galeria já salva; se a similaridade ultrapassar
    SIMILARITY_THRESHOLD, o salvamento é bloqueado (mesmo objeto/cena sob
    outro ângulo/iluminação).

Controles na janela de preview:
  [S] ou [ESPAÇO] -> tenta salvar o frame atual (roda o filtro de duplicatas)
  [Q] ou [ESC]     -> encerra a sessão de captura
"""

import os

import cv2
import numpy as np

import config  # reaproveita IMAGE_DIR / CAMERA_DEVICE já definidos no projeto
from services.image_storage import save_catalog_image, slugify

# --------------------------------------------------------------------------
# Configuração do filtro de duplicatas (ajustável sem mexer na lógica)
# --------------------------------------------------------------------------
IMAGE_DIR = config.IMAGE_DIR
ORB_N_FEATURES = 1000        # nº máx. de keypoints extraídos por imagem
RATIO_TEST = 0.75            # teste de razão de Lowe: descarta matches ambíguos
SIMILARITY_THRESHOLD = 0.20  # fração de matches "bons" a partir da qual é duplicata
MIN_KEYPOINTS = 10           # abaixo disso, features insuficientes p/ comparar com confiança

os.makedirs(IMAGE_DIR, exist_ok=True)

# ORB é usado por não exigir instalação extra (SIFT/CLIP pedem dependências
# a mais) e por ter bom custo-benefício para comparar o mesmo objeto sob
# ângulos/iluminação diferentes. NORM_HAMMING é a métrica correta para os
# descritores binários que o ORB produz.
_orb = cv2.ORB_create(nfeatures=ORB_N_FEATURES)
_matcher = cv2.BFMatcher(cv2.NORM_HAMMING)


def _extrair_features(imagem_bgr):
    """Extrai keypoints/descritores ORB de uma imagem (em escala de cinza)."""
    cinza = cv2.cvtColor(imagem_bgr, cv2.COLOR_BGR2GRAY)
    _, descritores = _orb.detectAndCompute(cinza, None)
    return descritores


def _similaridade(des_a, des_b):
    """Compara dois conjuntos de descritores ORB e retorna a fração de
    correspondências 'boas' (teste de razão de Lowe) — quanto maior, mais
    parecidos visualmente são os dois frames/objetos."""
    if des_a is None or des_b is None or len(des_a) < 2 or len(des_b) < 2:
        return 0.0
    matches = _matcher.knnMatch(des_a, des_b, k=2)
    bons = [m for m, n in matches if m.distance < RATIO_TEST * n.distance]
    total = min(len(des_a), len(des_b))
    return len(bons) / total if total else 0.0


class GaleriaDuplicatas:
    """Mantém em memória os descritores de todas as imagens já salvas em
    IMAGE_DIR, para comparar cada novo frame candidato sem reprocessar o
    disco inteiro a cada tentativa de salvar."""

    def __init__(self, pasta):
        self.pasta = pasta
        self._descritores = []  # lista de (nome_arquivo, descritores)
        self._carregar_existentes()

    def _carregar_existentes(self):
        if not os.path.isdir(self.pasta):
            return
        for pasta_atual, _, arquivos in os.walk(self.pasta):
            for nome in arquivos:
                caminho = os.path.join(pasta_atual, nome)
                imagem = cv2.imread(caminho)
                if imagem is None:
                    continue
                des = _extrair_features(imagem)
                if des is not None:
                    relativo = os.path.relpath(caminho, self.pasta)
                    self._descritores.append((relativo, des))
        print(f"[Galeria] {len(self._descritores)} imagem(ns) carregada(s) de '{self.pasta}'.")

    def encontrar_duplicata(self, des_novo):
        """Retorna (arquivo_mais_parecido, score) se algum item da galeria
        ultrapassar o limiar de similaridade; caso contrário (None, melhor_score)."""
        melhor_arquivo, melhor_score = None, 0.0
        for arquivo, des in self._descritores:
            score = _similaridade(des_novo, des)
            if score > melhor_score:
                melhor_arquivo, melhor_score = arquivo, score
        if melhor_score >= SIMILARITY_THRESHOLD:
            return melhor_arquivo, melhor_score
        return None, melhor_score

    def adicionar(self, arquivo, des):
        self._descritores.append((arquivo, des))


def _salvar_frame(frame, nome_peca):
    caminho, relativo = save_catalog_image(frame, nome_peca)
    caminho_portavel = (os.path.join("images", relativo.as_posix())).replace("\\", "/")
    return relativo.as_posix(), str(caminho), caminho_portavel


def capturar_com_filtro_duplicatas(nome_peca, device=None):
    """Loop principal de captura manual: mostra o preview ao vivo, espera o
    gatilho do usuário e só grava em disco se o frame passar no filtro de
    duplicatas. Retorna a lista de caminhos efetivamente salvos na sessão."""
    device = config.CAMERA_DEVICE if device is None else device
    cap = cv2.VideoCapture(device)
    if not cap.isOpened():
        print("Erro: câmera não encontrada.")
        return []

    pasta_peca = os.path.join(IMAGE_DIR, "cadastro", slugify(nome_peca, "peca"))
    galeria = GaleriaDuplicatas(pasta_peca)
    salvos = []
    print("\n[Captura Manual] [S]/[ESPAÇO] = salvar frame  |  [Q]/[ESC] = sair\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Erro ao ler frame da câmera.")
            break

        cv2.imshow("Captura de Frames - pressione S para salvar", frame)
        tecla = cv2.waitKey(1) & 0xFF

        # --- GATILHO MANUAL: nenhum frame é salvo fora deste bloco --------
        if tecla in (ord('s'), ord('S'), 32):  # 32 = barra de espaço
            des_novo = _extrair_features(frame)
            if des_novo is None or len(des_novo) < MIN_KEYPOINTS:
                print("Frame com poucas features detectáveis; tente outro ângulo/iluminação.")
                continue

            # --- FILTRO DE DUPLICATAS (processamento automático) ----------
            duplicata, score = galeria.encontrar_duplicata(des_novo)
            if duplicata:
                print(f"Bloqueado: muito parecido com '{duplicata}' (similaridade={score:.0%}).")
                continue

            nome_arquivo, caminho, caminho_portavel = _salvar_frame(frame, nome_peca)
            galeria.adicionar(nome_arquivo, des_novo)
            salvos.append(caminho_portavel)
            print(f"Frame novo salvo em '{caminho}' (similaridade máx. encontrada={score:.0%}).")

        elif tecla in (ord('q'), ord('Q'), 27):  # 27 = ESC
            break

    cap.release()
    cv2.destroyAllWindows()
    return salvos


if __name__ == "__main__":
    nome_digitado = input("Nome da peça a cadastrar: ").strip() or "peca"
    arquivos_salvos = capturar_com_filtro_duplicatas(nome_digitado)
    print(f"\nSessão encerrada. {len(arquivos_salvos)} imagem(ns) nova(s) salva(s).")
