import mysql.connector
from database.models import RecursoML
from database.connection import get_connection

# Função para criar um novo recurso ML
def create_recurso_ml(recurso: RecursoML):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = """
    INSERT INTO RECURSO_ML (peca_id, tipo_recurso, descricao_audio, arquivo_audio)
    VALUES (%s, %s, %s, %s)
    """
    values = (recurso.peca_id, recurso.tipo_recurso, recurso.descricao_audio, recurso.arquivo_audio)
    cursor.execute(query, values)
    conexao.commit()
    recurso.recurso_id = cursor.lastrowid
    cursor.close()
    return recurso

# Função para obter recursos ML por peça
def get_recursos_by_peca(peca_id: int):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM RECURSO_ML WHERE peca_id = %s"
    cursor.execute(query, (peca_id,))
    results = cursor.fetchall()
    cursor.close()
    return [RecursoML(**row) for row in results]