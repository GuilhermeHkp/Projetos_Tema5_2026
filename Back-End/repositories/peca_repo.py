import mysql.connector
from database.models import Peca
from database.connection import get_connection

# Função para criar uma nova peça
def create_peca(peca: Peca):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = """
    INSERT INTO PECA (localizacao_id, categoria_id, codigo_patrimonial, nome, classe_yolo, descricao, imagem_path, quantidade, quantidade_disponivel, estoque_minimo)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (peca.localizacao_id, peca.categoria_id, peca.codigo_patrimonial, peca.nome, peca.classe_yolo, peca.descricao, peca.imagem_path, getattr(peca, 'quantidade', 0), getattr(peca, 'quantidade_disponivel', 0), getattr(peca, 'estoque_minimo', 1))
    cursor.execute(query, values)
    conexao.commit()
    peca.peca_id = cursor.lastrowid
    cursor.close()
    return peca

# Função para obter uma peça por ID
def get_peca_by_id(peca_id: int):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM PECA WHERE peca_id = %s"
    cursor.execute(query, (peca_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return Peca(**result)
    return None

# Função para obter todas as peças
def get_all_pecas():
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM PECA"
    cursor.execute(query)
    results = cursor.fetchall()
    cursor.close()
    return [Peca(**row) for row in results]

# Função para obter uma peça pela classe treinada no modelo (usado na sincronização automática)
def get_peca_by_classe_yolo(classe_yolo: str):
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    query = "SELECT * FROM PECA WHERE classe_yolo = %s LIMIT 1"
    cursor.execute(query, (classe_yolo,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return Peca(**result)
    return None

# Função para atualizar uma peça
def update_peca(peca: Peca):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = """
    UPDATE PECA SET localizacao_id = %s, categoria_id = %s, codigo_patrimonial = %s,
    nome = %s, classe_yolo = %s, descricao = %s, imagem_path = %s, quantidade = %s,
    quantidade_disponivel = %s, estoque_minimo = %s WHERE peca_id = %s
    """
    values = (peca.localizacao_id, peca.categoria_id, peca.codigo_patrimonial, peca.nome, peca.classe_yolo, peca.descricao, peca.imagem_path, getattr(peca, 'quantidade', 0), getattr(peca, 'quantidade_disponivel', 0), getattr(peca, 'estoque_minimo', 1), peca.peca_id)
    cursor.execute(query, values)
    conexao.commit()
    cursor.close()

# Função para baixar o estoque de uma peça (usada pelo detector).
# Faz a subtração direto no banco, em uma única instrução, para não
# sobrescrever os outros campos da peça nem perder baixas simultâneas.
# Nunca deixa a quantidade ficar negativa.
# coluna: "disponivel" (quantidade_disponivel), "quantidade" ou "ambas".
# Retorna a quantidade atual da coluna principal (disponivel, se afetada).
def baixar_estoque(peca_id: int, qtd: int = 1, coluna: str = "disponivel"):
    qtd = int(qtd)
    if qtd <= 0:
        return None
    if coluna not in ("disponivel", "quantidade", "ambas"):
        raise ValueError('coluna deve ser "disponivel", "quantidade" ou "ambas".')

    sets = []
    params = []
    if coluna in ("disponivel", "ambas"):
        sets.append("quantidade_disponivel = GREATEST(quantidade_disponivel - %s, 0)")
        params.append(qtd)
    if coluna in ("quantidade", "ambas"):
        sets.append("quantidade = GREATEST(quantidade - %s, 0)")
        params.append(qtd)
    params.append(peca_id)

    conexao = get_connection()
    cursor = conexao.cursor()
    cursor.execute(
        "UPDATE PECA SET " + ", ".join(sets) + " WHERE peca_id = %s",
        tuple(params),
    )
    conexao.commit()
    campo = "quantidade" if coluna == "quantidade" else "quantidade_disponivel"
    cursor.execute(f"SELECT {campo} FROM PECA WHERE peca_id = %s", (peca_id,))
    row = cursor.fetchone()
    cursor.close()
    return row[0] if row else None

# Função para deletar uma peça
def delete_peca(peca_id: int):
    conexao = get_connection()
    cursor = conexao.cursor()
    query = "DELETE FROM PECA WHERE peca_id = %s"
    cursor.execute(query, (peca_id,))
    conexao.commit()
    cursor.close()


def search_pecas(filters: dict):
    """filters: dict com chaves possíveis: 'peca_id', 'nome', 'descricao', 'quantidade'"""
    conexao = get_connection()
    cursor = conexao.cursor(dictionary=True)
    base = "SELECT * FROM PECA"
    clauses = []
    params = []
    if not filters:
        cursor.execute(base)
        results = cursor.fetchall()
        cursor.close()
        return [Peca(**row) for row in results]

    if 'peca_id' in filters and filters['peca_id'] is not None:
        clauses.append('peca_id = %s')
        params.append(filters['peca_id'])
    if 'nome' in filters and filters['nome']:
        clauses.append('nome LIKE %s')
        params.append(f"%{filters['nome']}%")
    if 'descricao' in filters and filters['descricao']:
        clauses.append('descricao LIKE %s')
        params.append(f"%{filters['descricao']}%")
    if 'quantidade' in filters and filters['quantidade'] is not None:
        clauses.append('quantidade = %s')
        params.append(filters['quantidade'])

    if clauses:
        query = base + ' WHERE ' + ' AND '.join(clauses)
    else:
        query = base

    cursor.execute(query, tuple(params))
    results = cursor.fetchall()
    cursor.close()
    return [Peca(**row) for row in results]