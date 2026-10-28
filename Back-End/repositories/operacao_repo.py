import mysql.connector
from database.models import Operacao
from database.connection import get_connection

# Função para criar uma nova operação
def create_operacao(operacao: Operacao):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = """
    INSERT INTO OPERACAO (usuario_id, peca_id, tipo_operacao, quantidade, resultado, caminho_foto)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (operacao.usuario_id, operacao.peca_id, operacao.tipo_operacao, getattr(operacao, 'quantidade', 1), operacao.resultado, getattr(operacao, 'caminho_foto', None))
    cursor.execute(query, values)
    conexao.commit()
    operacao.operacao_id = cursor.lastrowid
    cursor.close()
    return operacao

# Função para obter uma operação por ID
def get_operacao_by_id(operacao_id: int):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM OPERACAO WHERE operacao_id = %s"
    cursor.execute(query, (operacao_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return Operacao(**result)
    return None

# Função para obter todas as operações
def get_all_operacoes():
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM OPERACAO"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return [Operacao(**row) for row in results]

# Função para obter operações por usuário
def get_operacoes_by_usuario(usuario_id: int):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM OPERACAO WHERE usuario_id = %s"
    cursor.execute(query, (usuario_id,))
    results = cursor.fetchall()
    cursor.close()
    return [Operacao(**row) for row in results]

# Função para atualizar uma operação
def update_operacao(operacao: Operacao):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = """
    UPDATE OPERACAO SET usuario_id = %s, peca_id = %s, tipo_operacao = %s, resultado = %s
    WHERE operacao_id = %s
    """
    values = (operacao.usuario_id, operacao.peca_id, operacao.tipo_operacao, operacao.resultado, operacao.operacao_id)
    cursor.execute(query, values)
    conexao.commit()
    cursor.close()

# Função para deletar uma operação
def delete_operacao(operacao_id: int):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = "DELETE FROM OPERACAO WHERE operacao_id = %s"
    cursor.execute(query, (operacao_id,))
    conexao.commit()
    cursor.close()
