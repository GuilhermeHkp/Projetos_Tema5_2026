import json
import os
import urllib.request
from database.connection import get_connection


def solicitar(usuario, mensagem):
    if not isinstance(mensagem, str) or not mensagem.strip() or len(mensagem) > 1000:
        raise ValueError("Descreva o pedido em até 1000 caracteres.")
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute("INSERT INTO SOLICITACAO_ADMIN (usuario_id, mensagem) VALUES (%s,%s)",
                    (usuario.usuario_id, mensagem.strip()))
        sid = cur.lastrowid
        con.commit()
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        chat = os.getenv("TELEGRAM_ADMIN_CHAT_ID", "").strip()
        enviado = False
        if token and chat:
            payload = json.dumps({"chat_id": chat, "text":
                f"GHCE — Solicitação #{sid}\nTrabalhador: {usuario.nome} (ID {usuario.usuario_id})\n{mensagem.strip()}\nEntre no GHCE como Admin para atender o pedido."}).encode()
            req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", payload,
                                          {"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    enviado = bool(json.load(response).get("ok"))
            except Exception:
                enviado = False
        if enviado:
            cur.execute("UPDATE SOLICITACAO_ADMIN SET telegram_enviado=TRUE WHERE solicitacao_id=%s", (sid,))
            con.commit()
        return {"solicitacao_id": sid, "telegram_enviado": enviado,
                "mensagem": "Pedido registrado. Admin notificado no Telegram." if enviado else
                "Pedido registrado, mas o Telegram não foi enviado. O Admin pode consultar no sistema."}
    finally:
        cur.close()


def listar(usuario):
    cur = get_connection().cursor(dictionary=True)
    try:
        if usuario.perfil == "admin":
            cur.execute("SELECT s.*, u.nome FROM SOLICITACAO_ADMIN s JOIN USUARIO u ON u.usuario_id=s.usuario_id ORDER BY s.criado_em DESC")
        else:
            cur.execute("SELECT * FROM SOLICITACAO_ADMIN WHERE usuario_id=%s ORDER BY criado_em DESC", (usuario.usuario_id,))
        return cur.fetchall()

    finally:
        cur.close()


def alterar(recurso, identificador, body=None):
    tabelas = {"pecas": ("PECA", "peca_id", {"nome", "descricao", "quantidade"}),
               "historico": ("HISTORICO", "historico_id", {"nome_peca", "descricao", "quantidade"}),
               "solicitacoes": ("SOLICITACAO_ADMIN", "solicitacao_id", {"status"})}
    tabela, chave, permitidos = tabelas[recurso]
    if body is not None:
        if not isinstance(body, dict) or not body or set(body) - permitidos:
            raise ValueError("Campos inválidos para edição.")
        for campo, valor in body.items():
            if campo == "quantidade" and (type(valor) is not int or valor < 0):
                raise ValueError("Quantidade deve ser inteira e não negativa.")
            if campo in ("nome", "nome_peca") and (not isinstance(valor, str) or not valor.strip() or len(valor)>150):
                raise ValueError("Nome obrigatório, até 150 caracteres.")
            if campo == "descricao" and (not isinstance(valor, str) or len(valor)>255):
                raise ValueError("Descrição deve ter até 255 caracteres.")
            if campo == "status" and valor not in ("pendente", "concluida"):
                raise ValueError("Status inválido.")
    con = get_connection()
    cur = con.cursor()
    try:
        cur.execute(f"SELECT {chave} FROM {tabela} WHERE {chave}=%s", (identificador,))
        if cur.fetchone() is None:
            return False
        if body is None:
            cur.execute(f"DELETE FROM {tabela} WHERE {chave}=%s", (identificador,))
        else:
            campos = ', '.join(f"{c}=%s" for c in body)
            cur.execute(f"UPDATE {tabela} SET {campos} WHERE {chave}=%s", (*body.values(), identificador))
        con.commit()
        return True
    except Exception:
        con.rollback()
        raise
    finally:
        cur.close()
