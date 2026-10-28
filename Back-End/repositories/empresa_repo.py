import mysql.connector
from database.models import Empresa
from database.connection import get_connection

# Função para criar uma nova empresa
def create_empresa(empresa: Empresa):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = "INSERT INTO EMPRESA (nome, cnpj) VALUES (%s, %s)"
    values = (empresa.nome, empresa.cnpj)
    cursor.execute(query, values)
    conexao.commit()
    empresa.empresa_id = cursor.lastrowid
    cursor.close()
    return empresa
