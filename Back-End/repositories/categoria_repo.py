import mysql.connector
from database.models import Categoria
from database.connection import get_connection

# Função para criar uma nova categoria
def create_categoria(categoria: Categoria):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = "INSERT INTO CATEGORIA (nome, descricao) VALUES (%s, %s)"
    values = (categoria.nome, categoria.descricao)
    cursor.execute(query, values)
    conexao.commit()
    categoria.categoria_id = cursor.lastrowid
    cursor.close()
    return categoria

# Função para obter uma categoria por ID
def get_categoria_by_id(categoria_id: int):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM CATEGORIA WHERE categoria_id = %s"
    cursor.execute(query, (categoria_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return Categoria(**result)
    return None

# Função para obter todas as categorias
def get_all_categorias():
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM CATEGORIA"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return [Categoria(**row) for row in results]

# Função para atualizar uma categoria
def update_categoria(categoria: Categoria):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = "UPDATE CATEGORIA SET nome = %s, descricao = %s WHERE categoria_id = %s"
    values = (categoria.nome, categoria.descricao, categoria.categoria_id)
    cursor.execute(query, values)
    conexao.commit()
    cursor.close()

# Função para deletar uma categoria
def delete_categoria(categoria_id: int):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = "DELETE FROM CATEGORIA WHERE categoria_id = %s"
    cursor.execute(query, (categoria_id,))
    conexao.commit()
    cursor.close()
