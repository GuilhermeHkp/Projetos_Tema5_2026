"""Valida o .env sem expor credenciais. Com --connect, testa o MySQL."""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path
from dotenv import dotenv_values

BACKEND_DIR = Path(__file__).resolve().parent
ENV_PATH = BACKEND_DIR / ".env"

REQUIRED = ("DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--connect", action="store_true")
    args = parser.parse_args()

    if not ENV_PATH.is_file():
        print(f"[ERRO] .env não encontrado: {ENV_PATH}")
        return 2

    values = dotenv_values(ENV_PATH)
    missing = [key for key in REQUIRED if values.get(key) is None]
    if missing:
        print("[ERRO] Variáveis ausentes no .env:", ", ".join(missing))
        return 3

    try:
        port = int(str(values["DB_PORT"]).strip())
        if not 1 <= port <= 65535:
            raise ValueError
    except Exception:
        print("[ERRO] DB_PORT inválida no .env.")
        return 4

    db_name = str(values["DB_NAME"]).strip()
    if not re.fullmatch(r"[A-Za-z0-9_]+", db_name):
        print("[ERRO] DB_NAME deve conter apenas letras, números e underscore.")
        return 5

    if str(values["DB_PASSWORD"]).strip() == "troque_esta_senha":
        print("[ERRO] DB_PASSWORD ainda está com o valor de exemplo.")
        return 6

    print("[OK] .env válido (credenciais não exibidas).")

    if not args.connect:
        return 0

    try:
        import mysql.connector
        con = mysql.connector.connect(
            host=str(values["DB_HOST"]).strip(),
            port=port,
            user=str(values["DB_USER"]).strip(),
            password=str(values["DB_PASSWORD"]),
        )
        cur = con.cursor()
        cur.execute("SHOW DATABASES LIKE %s", (db_name,))
        exists = cur.fetchone() is not None
        cur.close()
        con.close()
        print("[OK] Conexão com o servidor MySQL realizada.")
        if exists:
            print(f"[OK] Banco {db_name} existe.")
        else:
            print(f"[INFO] Banco {db_name} ainda não existe; CRIAR_TABELAS.cmd irá criá-lo.")
        return 0
    except Exception as exc:
        print(f"[ERRO] Não foi possível conectar ao MySQL: {exc}")
        return 7


if __name__ == "__main__":
    raise SystemExit(main())
