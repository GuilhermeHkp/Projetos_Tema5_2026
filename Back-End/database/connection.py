"""
Gerenciamento da conexão com o banco de dados MySQL.

Antes a conexão era aberta uma única vez, no momento em que este módulo era
importado (`conexao = mysql.connector.connect(...)`). Isso tinha dois
problemas graves:
  1. Se o MySQL não estivesse disponível (ou as credenciais estivessem
     erradas), o programa inteiro quebrava antes mesmo de exibir o menu.
  2. Uma única conexão/cursor era compartilhada por todo o sistema. Se a
     conexão caísse (timeout, restart do MySQL, etc.) todas as próximas
     operações passavam a falhar até reiniciar o programa.

Agora a conexão é criada sob demanda (lazy) através de `get_connection()`,
que reaproveita a conexão enquanto ela estiver ativa e reconecta
automaticamente caso tenha caído.
"""
import mysql.connector
from mysql.connector import Error

import config

import threading
_local = threading.local()


def get_connection():
    """Retorna uma conexão MySQL válida, criando/reconectando se necessário."""
    conexao = getattr(_local, "conexao", None)
    if conexao is None or not conexao.is_connected():
        conexao = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
        )
    _local.conexao = conexao
    return conexao


def get_cursor(dictionary: bool = False):
    """Atalho para obter (conexao, cursor) já prontos para uso."""
    conexao = get_connection()
    return conexao, conexao.cursor(dictionary=dictionary)


def testar_conexao() -> bool:
    """Testa se é possível conectar ao banco. Retorna True/False."""
    try:
        conexao = get_connection()
        return conexao.is_connected()
    except Error as e:
        print(f"Não foi possível conectar ao banco de dados: {e}")
        return False
