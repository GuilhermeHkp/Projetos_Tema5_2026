"""Configura o login de demonstração 1 / 2 / 123456 sem apagar tabelas."""
from __future__ import annotations
from database.connection import get_connection


def seed() -> int:
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute(
            """
            INSERT INTO EMPRESA (empresa_id, nome, cnpj)
            VALUES (1, %s, %s)
            ON DUPLICATE KEY UPDATE nome=VALUES(nome), cnpj=VALUES(cnpj)
            """,
            ("Empresa Padrao", "00.000.000/0001-00"),
        )
        cur.execute(
            """
            INSERT INTO USUARIO
              (usuario_id, empresa_id, nome, email, senha, ativo, id_responsavel, id_associado)
            VALUES
              (1, 1, %s, %s, %s, TRUE, NULL, 2)
            ON DUPLICATE KEY UPDATE
              empresa_id=1, nome=VALUES(nome), email=VALUES(email),
              senha=VALUES(senha), ativo=TRUE, id_responsavel=NULL, id_associado=2
            """,
            ("Responsavel Padrao", "responsavel1@ghce.local", "123456"),
        )
        cur.execute(
            """
            INSERT INTO USUARIO
              (usuario_id, empresa_id, nome, email, senha, ativo, id_responsavel, id_associado)
            VALUES
              (2, 1, %s, %s, %s, TRUE, 1, NULL)
            ON DUPLICATE KEY UPDATE
              empresa_id=1, nome=VALUES(nome), email=VALUES(email),
              senha=VALUES(senha), ativo=TRUE, id_responsavel=1, id_associado=NULL
            """,
            ("Colaborador Padrao", "colaborador2@ghce.local", "123456"),
        )
        cur.execute("UPDATE USUARIO SET perfil='admin' WHERE usuario_id=1")
        cur.execute("UPDATE USUARIO SET perfil='trabalhador' WHERE usuario_id=2")
        con.commit()

        cur.execute("SELECT usuario_id, senha, ativo FROM USUARIO WHERE usuario_id IN (1,2) ORDER BY usuario_id")
        rows = cur.fetchall()
        if len(rows) != 2 or [int(r[0]) for r in rows] != [1, 2]:
            raise RuntimeError("Não foi possível garantir os usuários 1 e 2.")
        print("[OK] Login configurado: responsavel=1, associado=2, senha=123456")
        return 0
    except Exception as exc:
        con.rollback()
        print(f"[ERRO] Falha ao configurar login: {exc}")
        return 1
    finally:
        cur.close()
        con.close()


if __name__ == "__main__":
    raise SystemExit(seed())
