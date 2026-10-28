from repositories.operacao_repo import create_operacao
from database.models import Operacao

# Função para registrar uma operação
def registrar_operacao(usuario_id: int, peca_id: int, tipo_operacao: str, resultado: str = None):
    operacao = Operacao(
        usuario_id=usuario_id,
        peca_id=peca_id,
        tipo_operacao=tipo_operacao,
        resultado=resultado
    )
    return create_operacao(operacao)

# Função para registrar entrada de produto
def registrar_entrada(peca_id: int, usuario_id: int):
    registrar_operacao(usuario_id, peca_id, "Entrada", "Produto adicionado ao estoque")

# Função para registrar saída de produto
def registrar_saida(peca_id: int, usuario_id: int):
    registrar_operacao(usuario_id, peca_id, "Saída", "Produto removido do estoque")
