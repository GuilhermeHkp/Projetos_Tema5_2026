"""Cria o banco/tabelas sem apagar dados e corrige colunas antigas."""
from __future__ import annotations
import os
import re
import sys
import mysql.connector
from mysql.connector import Error as MySQLError
import config


def _safe_db_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", name or ""):
        raise ValueError("DB_NAME inválido. Use apenas letras, números e underscore.")
    return name


def _column_exists(cursor, table, column):
    cursor.execute(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s AND COLUMN_NAME=%s",
        (config.DB_NAME, table, column),
    )
    return cursor.fetchone()[0] > 0


def _add_column(cursor, table, column, definition):
    if not _column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {definition}")
        print(f"Coluna adicionada: {table}.{column}")


def _statements(script: str):
    linhas = []
    for linha in script.splitlines():
        conteudo = linha.strip()
        if not conteudo or conteudo.startswith("--") or conteudo.startswith("#"):
            continue
        # O banco é criado pelo Python usando DB_NAME do .env.
        if conteudo.upper().startswith("CREATE DATABASE") or conteudo.upper().startswith("USE "):
            continue
        linhas.append(linha)
    for trecho in "\n".join(linhas).split(";"):
        trecho = trecho.strip()
        if trecho:
            yield trecho


def criar_tabelas():
    db_name = _safe_db_name(config.DB_NAME)
    schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        script = f.read()

    try:
        conexao = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
        )
    except MySQLError as e:
        print(f"Nao foi possivel conectar ao MySQL em {config.DB_HOST}:{config.DB_PORT}.")
        print(f"Detalhe do MySQL: {e}")
        print("Confira Back-End\\.env e se o servico MySQL esta rodando.")
        return 1

    cursor = conexao.cursor()
    try:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        conexao.database = db_name

        for statement in _statements(script):
            try:
                cursor.execute(statement)
            except MySQLError as e:
                if e.errno in (1050, 1060, 1061):
                    continue
                print("Falha ao executar SQL:")
                print(statement[:300])
                print(f"Erro do MySQL (codigo {e.errno}): {e.msg}")
                raise
        conexao.commit()

        # Migrações defensivas para bancos de versões antigas.
        _add_column(cursor, "USUARIO", "perfil", "VARCHAR(20) NOT NULL DEFAULT 'trabalhador'")
        _add_column(cursor, "USUARIO", "id_responsavel", "INT NULL")
        _add_column(cursor, "USUARIO", "id_associado", "INT NULL")
        _add_column(cursor, "PECA", "classe_yolo", "VARCHAR(100) NULL")
        _add_column(cursor, "PECA", "quantidade_disponivel", "INT NOT NULL DEFAULT 0")
        _add_column(cursor, "PECA", "estoque_minimo", "INT NOT NULL DEFAULT 1")
        _add_column(cursor, "OPERACAO", "quantidade", "INT NOT NULL DEFAULT 1")
        _add_column(cursor, "OPERACAO", "caminho_foto", "VARCHAR(255) NULL")
        conexao.commit()
        print(f"Banco '{db_name}' e tabelas verificados/criados com sucesso.")
        return 0
    except (MySQLError, ValueError) as exc:
        conexao.rollback()
        print(f"Falha ao preparar banco: {exc}")
        return 1
    finally:
        cursor.close()
        conexao.close()


if __name__ == "__main__":
    raise SystemExit(criar_tabelas())
