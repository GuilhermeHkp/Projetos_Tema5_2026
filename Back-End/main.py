from mysql.connector import Error as MySQLError

from services.ml_service import (
    load_trained_model,
    cadastrar_peca,
    clear_identified_items,
    get_identified_items,
    detect_and_register_checkin,
    load_yolo_model,
)
from services.operacao_service import registrar_entrada, registrar_saida
from repositories.peca_repo import get_all_pecas
from services.peca_service import cadastrar_produto, buscar_pecas
from database.connection import testar_conexao


def ler_inteiro(mensagem: str):
    """input() que só aceita número inteiro; retorna None se o usuário deixar em branco."""
    valor = input(mensagem).strip()
    if not valor:
        return None
    try:
        return int(valor)
    except ValueError:
        print("Valor inválido, digite apenas números.")
        return None


def escolher_peca():
    """Lista as peças cadastradas e retorna a peça escolhida (ou None)."""
    pecas = get_all_pecas()
    if not pecas:
        print("Nenhuma peça cadastrada ainda.")
        return None
    print("Peças disponíveis:")
    for i, peca in enumerate(pecas):
        print(f"{i + 1}. {peca.nome}")
    idx = ler_inteiro("Escolha o número da peça: ")
    if idx is None or not (1 <= idx <= len(pecas)):
        print("Opção inválida.")
        return None
    return pecas[idx - 1]


def main():
    print("Sistema GHCE - Controle de Estoque com IA")

    # Verifica a conexão com o banco de dados logo no início, com uma
    # mensagem clara em vez de deixar o programa quebrar mais adiante.
    if not testar_conexao():
        print(
            "\nAviso: não foi possível conectar ao banco de dados MySQL.\n"
            "Verifique se o MySQL está rodando e se as credenciais em '.env' estão corretas.\n"
            "Para criar o banco e as tabelas automaticamente, rode:\n"
            "    python -m database.create_tables\n"
        )

    # Tenta carregar exclusivamente o best.pt treinado com o dataset próprio.
    # Sem esse arquivo, o restante do sistema continua disponível, mas a
    # detecção por câmera fica desativada até o treinamento ser concluído.
    try:
        load_trained_model()
    except Exception as e:
        print(f"Aviso: não foi possível carregar o modelo YOLO agora ({e}).")
        print("As opções de câmera/check-in ficarão indisponíveis até isso ser resolvido.\n")

    while True:
        print("\nOpções:")
        print("1. Cadastrar peça")
        print("2. Cadastrar produto (cadastro rápido)")
        print("3. Buscar peças (filtros)")
        print("4. Registrar entrada de produto")
        print("5. Registrar saída de produto")
        print("6. Ver itens identificados")
        print("7. Check-in via câmera (YOLO)")
        print("8. Sair")
        choice = input("Escolha uma opção: ").strip()

        try:
            if choice == '1':
                cadastrar_peca()
            elif choice == '2':
                nome = input('Nome do produto: ').strip()
                if not nome:
                    print('Nome é obrigatório.')
                    continue
                descricao = input('Descrição (opcional): ').strip()
                quantidade = ler_inteiro('Quantidade inicial (número): ') or 0
                cadastrar_produto(nome=nome, descricao=descricao, quantidade=quantidade)
                print('Produto cadastrado.')
            elif choice == '3':
                print('Filtros disponíveis: id, nome, descricao, quantidade')
                fid = input('ID (enter para pular): ').strip()
                fnome = input('Nome (enter para pular): ').strip()
                fdesc = input('Descrição (enter para pular): ').strip()
                fq = input('Quantidade (enter para pular): ').strip()
                filtros = {}
                if fid:
                    filtros['peca_id'] = int(fid)
                if fnome:
                    filtros['nome'] = fnome
                if fdesc:
                    filtros['descricao'] = fdesc
                if fq:
                    filtros['quantidade'] = int(fq)
                results = buscar_pecas(filtros)
                if not results:
                    print('Nenhuma peça encontrada.')
                for p in results:
                    print(f"{p.peca_id} - {p.nome} - {p.descricao} - qty: {getattr(p, 'quantidade', 0)}")
            elif choice == '4':
                peca = escolher_peca()
                if peca:
                    registrar_entrada(peca.peca_id, 1)  # Assumir usuario_id=1
                    print("Entrada registrada.")
            elif choice == '5':
                peca = escolher_peca()
                if peca:
                    registrar_saida(peca.peca_id, 1)
                    print("Saída registrada.")
            elif choice == '6':
                itens = get_identified_items()
                if not itens:
                    print("Nenhum item identificado ainda.")
                else:
                    print("Itens identificados:")
                    for name, count in itens.items():
                        print(f"{name}: {count} itens")
            elif choice == '7':
                print('Iniciando check-in via câmera...')
                load_yolo_model()
                historicos = detect_and_register_checkin()
                if historicos:
                    print(f'Registrados {len(historicos)} históricos.')
                else:
                    print('Nenhum item registrado.')
            elif choice == '8':
                clear_identified_items()
                print("Arrays limpos. Saindo...")
                break
            else:
                print("Opção inválida.")
        except MySQLError as e:
            print(f"Erro de banco de dados: {e}")
        except ValueError:
            print("Valor inválido informado, tente novamente.")
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")


if __name__ == "__main__":
    main()
