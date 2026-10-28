# Pacote "database": modelos (dataclasses) e conexão com o MySQL.
#
# Observação: este projeto NÃO usa SQLAlchemy (não há engine/Session/Base
# aqui) - os modelos são simples dataclasses em models.py e o acesso ao
# banco é feito diretamente via mysql.connector em connection.py.

# --- Anotações originais do projeto (mantidas como referência) ---
# Login: senha, id do responsavel, id do associado
#
# Menu: Nada
#
# Historico:
# id, nome da peça, quantidade, descrição e horário de registro a partir da identificação da camera
#
# Cadastro dos produtos:
# id, nome do produto, descrição do produto, quantidade do produto registrado
#
# Página para adicionar os produtos (cadastro tambem, Id automático)
#
# menu de pesquisa:
# descrição, quantidade, nome, id, deve ser possível usar qualquer um dos quatro para fazer a filtragem, com uma barra de pesquisa com barra selecionavel com as opções de filtragens.
#
# Câmera:
# Programa que ao conectado com uma câmera, deve identificar produtos que passarão, de acordo com: cor, tamanho, formato e quantidade
#
# O programa funcionará como um "Check-in", que identificará se o que foi passado esta de acordo com oque foi requisitado/pedido
