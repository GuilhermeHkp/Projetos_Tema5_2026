"""
Login do sistema.

A tela de Login (Front-End/Login) pede 3 campos:
  - "ID do responsável"           -> USUARIO.usuario_id de quem está logando
  - "ID do colaborador associado" -> USUARIO.usuario_id da pessoa assistida
  - "Senha"                       -> USUARIO.senha do responsável

Antes esses 3 campos não eram checados em lugar nenhum (o front só validava
se estavam preenchidos e navegava direto pra Home). Esta função faz a
validação de verdade contra a tabela USUARIO.
"""
from repositories.usuario_repo import get_usuario_by_id


def autenticar(id_responsavel: int, id_associado: int, senha: str):
    """Retorna (True, usuario) se as credenciais forem válidas, ou (False, motivo)."""
    if id_responsavel is None or not senha:
        return False, "Preencha todas as informações."

    usuario = get_usuario_by_id(id_responsavel)
    if usuario is None:
        return False, "Usuário responsável não encontrado."

    if not usuario.ativo:
        return False, "Usuário inativo."

    # Comparação simples de senha (texto puro), igual ao resto do projeto.
    # Para produção o ideal é armazenar hash (ex.: bcrypt) em vez de texto puro.
    if usuario.senha != senha:
        return False, "Senha incorreta."

    if id_associado is not None:
        associado = get_usuario_by_id(id_associado)
        if associado is None or not associado.ativo:
            return False, "Colaborador associado não encontrado ou inativo."

    return True, usuario
