import mysql.connector
from datetime import datetime
from database.models import Historico
from database.connection import get_connection


def create_historico(historico: Historico):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = """
    INSERT INTO HISTORICO (peca_id, nome_peca, quantidade, descricao, horario_registro)
    VALUES (%s, %s, %s, %s, %s)
    """
    horario = historico.horario_registro if historico.horario_registro else datetime.now()
    values = (historico.peca_id, historico.nome_peca, historico.quantidade, historico.descricao, horario)
    cursor.execute(query, values)
    conexao.commit()
    historico.historico_id = cursor.lastrowid
    cursor.close()
    return historico


def get_all_historicos():
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM HISTORICO ORDER BY horario_registro DESC"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return [Historico(**row) for row in results]
