from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Modelo para Empresa
@dataclass
class Empresa:
    empresa_id: Optional[int] = None
    nome: str = ""
    cnpj: str = ""

# Modelo para Categoria
@dataclass
class Categoria:
    categoria_id: Optional[int] = None
    nome: str = ""
    descricao: Optional[str] = None

# Modelo para Fabrica
@dataclass
class Fabrica:
    fabrica_id: Optional[int] = None
    empresa_id: int = 0
    nome: str = ""
    localizacao: str = ""

# Modelo para Usuario
@dataclass
class Usuario:
    usuario_id: Optional[int] = None
    empresa_id: int = 0
    nome: Optional[str] = None
    email: str = ""
    senha: str = ""
    perfil: str = "trabalhador"
    ativo: bool = True
    data_criacao: Optional[datetime] = None
    id_responsavel: Optional[int] = None
    id_associado: Optional[int] = None

# Modelo para Setor
@dataclass
class Setor:
    setor_id: Optional[int] = None
    fabrica_id: int = 0
    nome: str = ""
    descricao: Optional[str] = None

# Modelo para Localizacao
@dataclass
class Localizacao:
    localizacao_id: Optional[int] = None
    setor_id: int = 0
    codigo: Optional[str] = None
    descricao: Optional[str] = None

# Modelo para Peca
@dataclass
class Peca:
    peca_id: Optional[int] = None
    localizacao_id: Optional[int] = None
    categoria_id: Optional[int] = None
    codigo_patrimonial: Optional[str] = None
    nome: str = ""
    classe_yolo: Optional[str] = None
    descricao: Optional[str] = None
    quantidade: int = 0
    quantidade_disponivel: int = 0
    estoque_minimo: int = 1
    data_criacao: Optional[datetime] = None
    data_atualizacao: Optional[datetime] = None
    imagem_path: Optional[str] = None  # Caminho para a imagem da peça

# Modelo para RecursoML
@dataclass
class RecursoML:
    recurso_id: Optional[int] = None
    peca_id: int = 0
    tipo_recurso: str = ""
    descricao_audio: Optional[str] = None
    arquivo_audio: Optional[str] = None
    data_treinamento: Optional[datetime] = None

# Modelo para Operacao
@dataclass
class Operacao:
    operacao_id: Optional[int] = None
    usuario_id: int = 0
    peca_id: int = 0
    tipo_operacao: str = ""
    quantidade: int = 1
    data_operacao: Optional[datetime] = None
    resultado: Optional[str] = None
    caminho_foto: Optional[str] = None


# Modelo para Histórico de identificação (ex.: check-in via câmera)
@dataclass
class Historico:
    historico_id: Optional[int] = None
    peca_id: Optional[int] = None
    nome_peca: Optional[str] = None
    quantidade: int = 0
    descricao: Optional[str] = None
    horario_registro: Optional[datetime] = None

# Modelo para PerfilAcessibilidade
@dataclass
class PerfilAcessibilidade:
    perfil_id: Optional[int] = None
    usuario_id: int = 0
    contraste_alto: bool = False
    leitura_voz: bool = False
    tamanho_fonte: int = 12
    descricoes_audio: bool = False