import mysql.connector
from database.models import Localizacao
from database.connection import get_connection

# Função para criar uma nova localização
def create_localizacao(localizacao: Localizacao):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = "INSERT INTO LOCALIZACAO (setor_id, codigo, descricao) VALUES (%s, %s, %s)"
    values = (localizacao.setor_id, localizacao.codigo, localizacao.descricao)
    cursor.execute(query, values)
    conexao.commit()
    localizacao.localizacao_id = cursor.lastrowid
    cursor.close()
    return localizacao

# Função para obter uma localização por ID
def get_localizacao_by_id(localizacao_id: int):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM LOCALIZACAO WHERE localizacao_id = %s"
    cursor.execute(query, (localizacao_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return Localizacao(**result)
    return None
