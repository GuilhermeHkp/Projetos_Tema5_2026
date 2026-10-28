import mysql.connector
from database.models import Fabrica
from database.connection import get_connection

# Função para criar uma nova fábrica
def create_fabrica(fabrica: Fabrica):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = "INSERT INTO FABRICA (empresa_id, nome, localizacao) VALUES (%s, %s, %s)"
    values = (fabrica.empresa_id, fabrica.nome, fabrica.localizacao)
    cursor.execute(query, values)
    conexao.commit()
    fabrica.fabrica_id = cursor.lastrowid
    cursor.close()
    return fabrica
