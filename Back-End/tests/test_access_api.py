import importlib.util
import json
import sys
import threading
import types
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

class AccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.modules = patch.dict(sys.modules)
        cls.modules.start()
        config = types.ModuleType('config')
        config.CORS_ORIGIN = '*'
        config.MAX_REQUEST_BYTES = 12000000
        sys.modules['config'] = config
        connection = types.ModuleType('database.connection')
        connection.testar_conexao = lambda: True
        connection.get_connection = lambda: None
        sys.modules['database.connection'] = connection
        for name in ('repositories.usuario_repo', 'repositories.peca_repo', 'repositories.historico_repo'):
            module = types.ModuleType(name)
            sys.modules[name] = module
        cls.admin = types.SimpleNamespace(usuario_id=1, nome='Admin', perfil='admin', ativo=True, senha='secret')
        cls.worker = types.SimpleNamespace(usuario_id=2, nome='Trabalhador', perfil='trabalhador', ativo=True, senha='secret')
        sys.modules['repositories.usuario_repo'].get_usuario_by_id = lambda uid: {1: cls.admin, 2: cls.worker}.get(uid)
        pecas = sys.modules['repositories.peca_repo']
        pecas.get_all_pecas = lambda: []
        pecas.search_pecas = lambda q: []
        pecas.create_peca = lambda p: p
        sys.modules['repositories.historico_repo'].get_all_historicos = lambda: []
        ml = types.ModuleType('services.ml_service')
        for name in ('detect_and_register_checkin_frame', 'get_detector_status', 'get_runtime_metrics', 'load_trained_model'):
            setattr(ml, name, lambda *a, **k: {})
        ml.DetectorUnavailableError = type('DetectorUnavailableError', (Exception,), {})
        ml.DetectorInferenceError = type('DetectorInferenceError', (Exception,), {})
        sys.modules['services.ml_service'] = ml
        spec = importlib.util.spec_from_file_location('api_testado', ROOT / 'api.py')
        cls.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.api)
        cls.server = cls.api.GHCEHTTPServer(('127.0.0.1', 0), cls.api.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.modules.stop()

    def request(self, path, method='GET', body=None, token=None):
        headers = {'Content-Type': 'application/json'}
        if token: headers['Authorization'] = 'Bearer ' + token
        req = urllib.request.Request(self.url + path, json.dumps(body).encode() if body is not None else None, headers, method=method)
        try:
            response = urllib.request.urlopen(req)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def login(self, uid):
        status, data = self.request('/api/login', 'POST', {'colaborador': uid, 'senha': 'secret', 'perfil': 'admin'})
        self.assertEqual(status, 200)
        self.assertNotIn('senha', data['usuario'])
        return data

    def test_login_perfil_vem_do_banco(self):
        self.assertEqual(self.login(2)['usuario']['perfil'], 'trabalhador')

    def test_sem_sessao_e_token_falso(self):
        for token in (None, 'inventado'):
            self.assertEqual(self.request('/api/pecas', token=token)[0], 401)

    def test_trabalhador_consulta_mas_nao_modifica(self):
        token = self.login(2)['token']
        self.assertEqual(self.request('/api/pecas', token=token)[0], 200)
        for path, method in [('/api/pecas', 'POST'), ('/api/pecas/1', 'PUT'), ('/api/historico/1', 'DELETE'), ('/api/solicitacoes/1', 'PUT')]:
            self.assertEqual(self.request(path, method, {}, token)[0], 403)

    def test_admin_altera_e_logout_revoga(self):
        token = self.login(1)['token']
        with patch.object(self.api, 'alterar', return_value=True) as alterar:
            self.assertEqual(self.request('/api/historico/1', 'PUT', {'quantidade': 3}, token)[0], 200)
            alterar.assert_called_once_with('historico', 1, {'quantidade': 3})
        self.assertEqual(self.request('/api/logout', 'POST', {}, token)[0], 200)
        self.assertEqual(self.request('/api/pecas', token=token)[0], 401)

    def test_solicitacao_identifica_usuario_da_sessao(self):
        token = self.login(2)['token']
        with patch.object(self.api, 'solicitar', return_value={'telegram_enviado': False}) as solicitar:
            self.assertEqual(self.request('/api/solicitacoes', 'POST', {'mensagem': 'Editar peça 3', 'usuario_id': 1}, token)[0], 201)
            solicitar.assert_called_once_with(self.worker, 'Editar peça 3')

    def test_expiracao_e_usuario_desativado(self):
        from services import access_service
        token = self.login(2)['token']
        access_service._sessoes[token] = (2, 0)
        self.assertEqual(self.request('/api/pecas', token=token)[0], 401)
        token = self.login(2)['token']
        self.worker.ativo = False
        try:
            self.assertEqual(self.request('/api/pecas', token=token)[0], 401)
        finally:
            self.worker.ativo = True

    def test_telegram_falha_mantem_pedido(self):
        from services import admin_service
        from unittest.mock import MagicMock
        con = MagicMock()
        con.cursor.return_value.lastrowid = 7
        with patch.object(admin_service, 'get_connection', return_value=con), patch.dict(admin_service.os.environ, {'TELEGRAM_BOT_TOKEN': 'fake', 'TELEGRAM_ADMIN_CHAT_ID': '123'}), patch.object(admin_service.urllib.request, 'urlopen', side_effect=OSError('offline')):
            resultado = admin_service.solicitar(self.worker, 'Ajuda')
        self.assertEqual(resultado['solicitacao_id'], 7)
        self.assertFalse(resultado['telegram_enviado'])
        con.commit.assert_called_once()

    def test_quantidade_negativa_rejeitada(self):
        from services.admin_service import alterar
        with self.assertRaises(ValueError):
            alterar('pecas', 1, {'quantidade': -1})

if __name__ == '__main__':
    unittest.main()
