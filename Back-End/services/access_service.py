import secrets
import threading
import time
from repositories.usuario_repo import get_usuario_by_id

_sessoes = {}
_lock = threading.Lock()

def criar_sessao(usuario):
    token = secrets.token_urlsafe(32)
    with _lock:
        agora = time.time()
        for chave in list(_sessoes):
            if _sessoes[chave][1] <= agora:
                del _sessoes[chave]
        _sessoes[token] = (usuario.usuario_id, agora + 8 * 3600)
    return token

def usuario_sessao(header):
    token = header.removeprefix("Bearer ") if header.startswith("Bearer ") else ""
    with _lock:
        sessao = _sessoes.get(token)
    if not sessao or sessao[1] <= time.time():
        return None
    usuario = get_usuario_by_id(sessao[0])
    return usuario if usuario and usuario.ativo else None

def encerrar_sessao(header):
    with _lock:
        _sessoes.pop(header.removeprefix("Bearer "), None)

def usuario_publico(usuario):
    return {"usuario_id": usuario.usuario_id, "nome": usuario.nome,
            "perfil": usuario.perfil if usuario.perfil in ("admin", "trabalhador") else "trabalhador"}
