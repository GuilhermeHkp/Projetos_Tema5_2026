import mysql.connector
from database.models import Usuario
from database.connection import get_connection

# Função para criar um novo usuário
def create_usuario(usuario: Usuario):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = """
    INSERT INTO USUARIO (empresa_id, nome, email, senha, ativo)
    VALUES (%s, %s, %s, %s, %s)
    """
    values = (usuario.empresa_id, usuario.nome, usuario.email, usuario.senha, usuario.ativo)
    cursor.execute(query, values)
    conexao.commit()
    usuario.usuario_id = cursor.lastrowid
    cursor.close()
    return usuario

# Função para obter um usuário por ID
def get_usuario_by_id(usuario_id: int):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM USUARIO WHERE usuario_id = %s"
    cursor.execute(query, (usuario_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return Usuario(**result)
    return None

# Função para obter um usuário por email
def get_usuario_by_email(email: str):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM USUARIO WHERE email = %s"
    cursor.execute(query, (email,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return Usuario(**result)
    return None

# Função para obter todos os usuários
def get_all_usuarios():
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM USUARIO"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return [Usuario(**row) for row in results]

# Função para atualizar um usuário
def update_usuario(usuario: Usuario):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = """
    UPDATE USUARIO SET empresa_id = %s, nome = %s, email = %s, senha = %s, ativo = %s
    WHERE usuario_id = %s
    """
    values = (usuario.empresa_id, usuario.nome, usuario.email, usuario.senha, usuario.ativo, usuario.usuario_id)
    cursor.execute(query, values)
    conexao.commit()
    cursor.close()

# Função para deletar um usuário
def delete_usuario(usuario_id: int):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = "DELETE FROM USUARIO WHERE usuario_id = %s"
    cursor.execute(query, (usuario_id,))
    conexao.commit()
    cursor.close()