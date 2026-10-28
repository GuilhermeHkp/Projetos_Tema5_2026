"""Servidor HTTP do projeto, usando apenas a biblioteca padrão do Python.

Mantém os endpoints usados pelo Front-End sem adicionar Flask ou outro
framework web. Execute com: python api.py
"""
import json
import traceback
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote
import config

from database.connection import testar_conexao
from database.models import Peca
from repositories.peca_repo import get_all_pecas, create_peca, search_pecas
from repositories.historico_repo import get_all_historicos
from services.auth_service import autenticar
from services.access_service import criar_sessao, usuario_sessao, usuario_publico, encerrar_sessao
from services.admin_service import solicitar, listar, alterar
from services.ml_service import (
    detect_and_register_checkin_frame,
    get_detector_status,
    get_runtime_metrics,
    load_trained_model,
    DetectorUnavailableError,
    DetectorInferenceError,
)

HOST = "0.0.0.0"
PORT = 5000


def as_dict(obj):
    if hasattr(obj, "__dataclass_fields__"):
        data = {k: getattr(obj, k) for k in obj.__dataclass_fields__}
    else:
        data = dict(obj)
    for key, value in list(data.items()):
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
    return data


def send_json(handler, payload, status=200):
    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", config.CORS_ORIGIN)
    handler.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


def read_json(handler):
    length = int(handler.headers.get("Content-Length", "0"))
    if length > config.MAX_REQUEST_BYTES:
        raise ValueError("Requisição excede o limite permitido.")
    body = handler.rfile.read(length) if length else b"{}"
    return json.loads(body.decode("utf-8"))


def read_image(handler):
    """Aceita JSON {imagem_base64: ...} ou multipart/form-data com campo imagem."""
    import base64
    content_type = handler.headers.get("Content-Type", "")
    length = int(handler.headers.get("Content-Length", "0"))
    if length > config.MAX_REQUEST_BYTES:
        raise ValueError("Imagem excede o limite permitido.")
    body = handler.rfile.read(length)

    if content_type.startswith("application/json"):
        data = json.loads(body.decode("utf-8"))
        encoded = data.get("imagem_base64", "")
        if "," in encoded:
            encoded = encoded.split(",", 1)[1]
        try:
            decoded = base64.b64decode(encoded, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise ValueError("Imagem base64 inválida.") from exc
        if len(decoded) > config.MAX_REQUEST_BYTES:
            raise ValueError("Imagem decodificada excede o limite permitido.")
        return decoded

    # O Front-End atual envia JSON; multipart fica suportado para facilitar testes.
    if content_type.startswith("multipart/form-data"):
        boundary = content_type.split("boundary=", 1)[-1].encode()
        parts = body.split(b"--" + boundary)
        for part in parts:
            if b"name=\"imagem\"" in part or b"name=\"file\"" in part:
                payload = part.split(b"\r\n\r\n", 1)[-1]
                return payload.rstrip(b"\r\n-")
    raise ValueError("Imagem não enviada. Use JSON com imagem_base64.")


class Handler(BaseHTTPRequestHandler):
    server_version = "GHCE/2.0"

    def log_message(self, fmt, *args):
        print("[API]", fmt % args)

    def do_OPTIONS(self):
        send_json(self, {}, 204)

    def autorizar(self, admin=False):
        usuario = usuario_sessao(self.headers.get("Authorization", ""))
        if not usuario:
            send_json(self, {"erro": "Entre novamente no sistema."}, 401)
            return None
        if admin and usuario.perfil != "admin":
            send_json(self, {"erro": "Apenas Admin pode alterar registros. Solicite auxílio."}, 403)
            return None
        return usuario

    def do_PUT(self):
        self.modificar(False)

    def do_DELETE(self):
        self.modificar(True)

    def modificar(self, excluir):
        if not self.autorizar(admin=True):
            return
        partes = urlparse(self.path).path.strip("/").split("/")
        if len(partes) != 3 or partes[0] != "api" or partes[1] not in ("pecas", "historico", "solicitacoes"):
            return send_json(self, {"erro": "Rota não encontrada."}, 404)
        if excluir and partes[1] == "solicitacoes":
            return send_json(self, {"erro": "Solicitações são mantidas para consulta."}, 405)
        try:
            ok = alterar(partes[1], int(partes[2]), None if excluir else read_json(self))
            return send_json(self, {"sucesso": ok}, 200 if ok else 404)
        except (ValueError, TypeError):
            return send_json(self, {"erro": "Dados inválidos para alteração."}, 400)
        except Exception:
            return send_json(self, {"erro": "Não foi possível alterar. A peça pode possuir registros vinculados."}, 409)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/api/ping":
                return send_json(self, {"api": "online"})

            usuario = self.autorizar()
            if not usuario:
                return
            if path == "/api/me":
                return send_json(self, usuario_publico(usuario))
            if path == "/api/solicitacoes":
                return send_json(self, [as_dict(s) for s in listar(usuario)])

            if path == "/api/status":
                return send_json(self, {
                    "banco_conectado": testar_conexao(),
                    "detector": get_detector_status(),
                })

            if path == "/api/modelo":
                return send_json(self, get_detector_status())

            if path == "/api/metricas":
                return send_json(self, get_runtime_metrics())

            if path == "/api/health":
                detector = get_detector_status()
                status = 200 if detector["carregado"] else 503
                return send_json(self, {"saudavel": status == 200, "detector": detector}, status)

            if path == "/api/pecas":
                q = parse_qs(parsed.query).get("q", [""])[0].strip()
                pecas = search_pecas({"nome": q}) if q else get_all_pecas()
                return send_json(self, [as_dict(p) for p in pecas])

            if path == "/api/historico":
                return send_json(self, [as_dict(h) for h in get_all_historicos()])

            if path.startswith("/api/imagens/"):
                image_root = (Path(__file__).resolve().parent / "images").resolve()
                relative = unquote(path.removeprefix("/api/imagens/")).lstrip("/")
                filepath = (image_root / relative).resolve()
                try:
                    filepath.relative_to(image_root)
                except ValueError:
                    return send_json(self, {"erro": "Caminho de imagem inválido."}, 400)
                if not filepath.is_file():
                    return send_json(self, {"erro": "Imagem não encontrada."}, 404)
                with filepath.open("rb") as f:
                    raw = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Access-Control-Allow-Origin", config.CORS_ORIGIN)
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return

            return send_json(self, {"erro": "Rota não encontrada."}, 404)
        except ValueError as exc:
            return send_json(self, {"erro": str(exc)}, 400)
        except DetectorUnavailableError:
            return send_json(self, {"erro": "Detector indisponível."}, 503)
        except DetectorInferenceError:
            return send_json(self, {"erro": "Falha ao processar a imagem."}, 500)
        except Exception:
            traceback.print_exc()
            return send_json(self, {"erro": "Erro interno do servidor."}, 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/api/login":
                body = read_json(self)
                try:
                    id_responsavel = int(body.get("colaborador"))
                    id_associado = int(body["associado"]) if body.get("associado") else None
                except (TypeError, ValueError):
                    return send_json(self, {"sucesso": False, "erro": "IDs inválidos."}, 400)
                ok, resultado = autenticar(id_responsavel, id_associado, (body.get("senha") or "").strip())
                if not ok:
                    return send_json(self, {"sucesso": False, "erro": resultado}, 401)
                return send_json(self, {"sucesso": True, "usuario": usuario_publico(resultado), "token": criar_sessao(resultado)})

            usuario = self.autorizar(admin=path == "/api/pecas")
            if not usuario:
                return
            if path == "/api/logout":
                encerrar_sessao(self.headers.get("Authorization", ""))
                return send_json(self, {"sucesso": True})
            if path == "/api/solicitacoes":
                return send_json(self, solicitar(usuario, read_json(self).get("mensagem")), 201)
            if path == "/api/pecas":
                body = read_json(self)
                if type(body.get("quantidade", 0)) is not int or body.get("quantidade", 0) < 0:
                    raise ValueError("Quantidade deve ser inteira e não negativa.")
                nome = (body.get("nome") or "").strip()
                if not nome:
                    return send_json(self, {"erro": "Nome é obrigatório."}, 400)
                peca = Peca(nome=nome, descricao=body.get("descricao"), quantidade=int(body.get("quantidade") or 0),
                            localizacao_id=body.get("localizacao_id"), categoria_id=body.get("categoria_id"))
                criada = create_peca(peca)
                return send_json(self, as_dict(criada), 201)

            if path == "/api/checkin/imagem":
                raw = read_image(self)
                if not raw:
                    return send_json(self, {"itens": [], "erro": "Imagem vazia."}, 400)
                # ?preview=1 => usado pelo stream contínuo da câmera (Front-End manda
                # vários frames por segundo). Nesse modo só detectamos e devolvemos as
                # caixas para desenhar na tela, sem gravar histórico/imagem a cada frame.
                query = parse_qs(parsed.query)
                preview = query.get("preview", ["0"])[0] == "1"
                conf = None
                if "conf" in query:
                    try:
                        conf = float(query["conf"][0])
                    except (TypeError, ValueError):
                        return send_json(self, {"erro": "Confiança inválida."}, 400)
                    if not 0.0 <= conf <= 1.0:
                        return send_json(self, {"erro": "Confiança deve estar entre 0 e 1."}, 400)
                source_id = query.get("source", [self.client_address[0]])[0][:128]
                result = detect_and_register_checkin_frame(raw, conf=conf, registrar=not preview, source_id=source_id)
                return send_json(self, result)

            # Compatibilidade com a rota antiga: ainda pode usar a câmera ligada ao Python.
            if path == "/api/checkin":
                from services.ml_service import detect_and_register_checkin
                historicos = detect_and_register_checkin()
                return send_json(self, {"itens": [as_dict(h) for h in (historicos or [])]})

            return send_json(self, {"erro": "Rota não encontrada."}, 404)
        except ValueError as exc:
            return send_json(self, {"erro": str(exc)}, 400)
        except DetectorUnavailableError:
            return send_json(self, {"erro": "Detector indisponível."}, 503)
        except DetectorInferenceError:
            return send_json(self, {"erro": "Falha ao processar a imagem."}, 500)
        except Exception:
            traceback.print_exc()
            return send_json(self, {"erro": "Erro interno do servidor."}, 500)


class GHCEHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 32


def _startup_checks():
    """Carrega integrações sem bloquear a abertura da porta HTTP."""
    if not testar_conexao():
        print("Aviso: MySQL não conectado. Verifique o .env e se o serviço MySQL está ativo.")
    try:
        load_trained_model()
    except Exception as exc:
        print(f"Aviso: modelo YOLO não carregado: {exc}")


if __name__ == "__main__":
    server = GHCEHTTPServer((HOST, PORT), Handler)
    print(f"[OK] GHCE API ONLINE em http://127.0.0.1:{PORT}")
    print(f"[OK] Teste rápido: http://127.0.0.1:{PORT}/api/ping")
    threading.Thread(target=_startup_checks, name="ghce-startup", daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nAPI encerrada.")
    finally:
        server.server_close()
