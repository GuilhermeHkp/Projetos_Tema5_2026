import mysql.connector
from database.models import Setor
from database.connection import get_connection

# Função para criar um novo setor
def create_setor(setor: Setor):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = "INSERT INTO SETOR (fabrica_id, nome, descricao) VALUES (%s, %s, %s)"
    values = (setor.fabrica_id, setor.nome, setor.descricao)
    cursor.execute(query, values)
    conexao.commit()
    setor.setor_id = cursor.lastrowid
    cursor.close()
    return setor
