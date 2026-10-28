from repositories.peca_repo import get_peca_by_id, get_all_pecas
from repositories.peca_repo import search_pecas, create_peca as repo_create_peca
from repositories.categoria_repo import get_categoria_by_id
from repositories.localizacao_repo import get_localizacao_by_id  # Assuming we create this
from database.models import Peca

# Função para obter detalhes de uma peça com categoria e localização
def get_peca_detalhes(peca_id: int):
    peca = get_peca_by_id(peca_id)
    if not peca:
        return None
    categoria = get_categoria_by_id(peca.categoria_id)
    localizacao = get_localizacao_by_id(peca.localizacao_id)  # Need to implement localizacao_repo
    return {
        "peca": peca,
        "categoria": categoria,
        "localizacao": localizacao
    }

# Função para listar todas as peças
def listar_pecas():
    return get_all_pecas()


def cadastrar_produto(nome: str, descricao: str = None, quantidade: int = 0, localizacao_id: int = 0, categoria_id: int = 0, imagem_path: str = None):
    peca = Peca(nome=nome, descricao=descricao, quantidade=quantidade, localizacao_id=localizacao_id, categoria_id=categoria_id, imagem_path=imagem_path)
    return repo_create_peca(peca)


def buscar_pecas(filtros: dict):
    """Filtros possíveis: 'peca_id', 'nome', 'descricao', 'quantidade'"""
    return search_pecas(filtros)

# Função para identificar peça e fornecer feedback em áudio (simulado)
def identificar_peca_e_audio(codigo_patrimonial: str):
    # Simula identificação via sensor/câmera
    # Aqui, busca pela peça no BD
    pecas = get_all_pecas()
    peca = next((p for p in pecas if p.codigo_patrimonial == codigo_patrimonial), None)
    if not peca:
        return "Peça não encontrada."
    
    detalhes = get_peca_detalhes(peca.peca_id)
    if not detalhes:
        return "Erro ao obter detalhes."
    
    # Simula geração de áudio
    audio_texto = f"Peça identificada: {peca.nome}. Categoria: {detalhes['categoria'].nome if detalhes['categoria'] else 'Desconhecida'}. Localização: {detalhes['localizacao'].codigo if detalhes['localizacao'] else 'Desconhecida'}."
    # Em um sistema real, converteria para áudio
    return audio_texto
