(() => {
    const base = 'http://127.0.0.1:5000/api';
    const token = sessionStorage.getItem('token');
    if (!token) {
        location.replace('../Login/index1_pag_Login.html');
        return;
    }
    const original = window.fetch.bind(window);
    window.fetch = async (url, opcoes = {}) => {
        if (typeof url === 'string' && url.startsWith(base + '/')) {
            const headers = new Headers(opcoes.headers);
            headers.set('Authorization', `Bearer ${token}`);
            opcoes = { ...opcoes, headers };
        }
        const resposta = await original(url, opcoes);
        if (resposta.status === 401) {
            sessionStorage.clear();
            location.replace('../Login/index1_pag_Login.html');
            throw new Error('Sessão encerrada.');
        }
        return resposta;
    };
    let usuario;
    function modal({ titulo, mensagem = '', campos = [], confirmar = 'Entendi', perigo = false, cancelar = false }) {
        return new Promise(resolve => {
            const anterior = document.activeElement;
            const dialogo = document.createElement('dialog');
            dialogo.className = 'ghce-modal';
            dialogo.setAttribute('aria-labelledby', 'ghce-titulo-modal');
            const form = document.createElement('form');
            const cabecalho = document.createElement('h2');
            cabecalho.id = 'ghce-titulo-modal';
            cabecalho.textContent = titulo;
            const texto = document.createElement('p');
            texto.textContent = mensagem;
            form.append(cabecalho, texto);
            const entradas = {};
            campos.forEach(campo => {
                const label = document.createElement('label');
                label.textContent = campo.rotulo;
                const input = document.createElement(campo.nome === 'descricao' ? 'textarea' : 'input');
                input.name = campo.nome;
                input.value = campo.valor ?? '';
                if (campo.nome === 'quantidade') {
                    input.type = 'number'; input.min = '0'; input.step = '1'; input.required = true;
                } else { input.maxLength = campo.nome === 'nome' ? 150 : 255; input.required = campo.nome === 'nome'; }
                label.appendChild(input);
                form.appendChild(label);
                entradas[campo.nome] = input;
            });
            const acoes = document.createElement('div');
            acoes.className = 'ghce-modal-acoes';
            function fechar(valor) {
                dialogo.close(); dialogo.remove(); anterior?.focus(); resolve(valor);
            }
            if (cancelar) {
                const voltar = document.createElement('button');
                voltar.type = 'button'; voltar.className = 'ghce-botao ghce-neutro'; voltar.textContent = 'Cancelar';
                voltar.onclick = () => fechar(null); acoes.appendChild(voltar);
            }
            const salvar = document.createElement('button');
            salvar.type = 'submit'; salvar.className = 'ghce-botao ' + (perigo ? 'ghce-excluir' : 'ghce-editar');
            salvar.textContent = confirmar;
            acoes.appendChild(salvar); form.appendChild(acoes); dialogo.appendChild(form);
            form.addEventListener('submit', event => {
                event.preventDefault();
                if (entradas.nome && !entradas.nome.value.trim()) { entradas.nome.setCustomValidity('Informe o nome da peça.'); entradas.nome.reportValidity(); return; }
                const valores = {};
                Object.entries(entradas).forEach(([nome, input]) => valores[nome] = nome === 'quantidade' ? Number(input.value) : input.value.trim());
                fechar(campos.length ? valores : true);
            });
            entradas.nome?.addEventListener('input', () => entradas.nome.setCustomValidity(''));
            dialogo.addEventListener('cancel', event => { event.preventDefault(); fechar(null); });
            document.body.appendChild(dialogo); dialogo.showModal();
        });
    }
    const aviso = (mensagem, titulo = 'Aviso') => modal({ titulo, mensagem });
    function impedirAlteracao() {
        return aviso('Apenas o Admin pode cadastrar, editar ou excluir registros.', 'Permissão necessária');
    }
    window.ghceAviso = aviso;
    window.ghceFormularioPeca = () => modal({ titulo: 'Cadastrar peça', confirmar: 'Cadastrar peça', cancelar: true, campos: [
        { nome: 'nome', rotulo: 'Nome da peça' }, { nome: 'descricao', rotulo: 'Descrição' },
        { nome: 'quantidade', rotulo: 'Quantidade', valor: 0 }
    ] });
    async function requisitar(rota, metodo, dados) {
        const resposta = await fetch(base + rota, {
            method: metodo,
            headers: { 'Content-Type': 'application/json' },
            body: dados ? JSON.stringify(dados) : undefined
        });
        const resultado = await resposta.json();
        if (!resposta.ok) throw new Error(resultado.erro || 'Não foi possível concluir.');
        return resultado;
    }
    function botao(texto, acao) {
        const elemento = document.createElement('button');
        elemento.type = 'button';
        elemento.className = 'ghce-botao';
        elemento.textContent = texto;
        elemento.addEventListener('click', async event => {
            event.stopPropagation();
            elemento.disabled = true;
            try { await acao(); } catch (erro) { await aviso(erro.message, 'Não foi possível concluir'); }
            finally { elemento.disabled = false; }
        });
        return elemento;
    }
    async function pedirAuxilio() {
        const mensagem = prompt('Descreva a alteração desejada e informe o ID da peça ou histórico (até 1000 caracteres):');
        if (!mensagem || !mensagem.trim()) return;
        const resultado = await requisitar('/solicitacoes', 'POST', { mensagem });
        await aviso(resultado.mensagem, 'Solicitação registrada');
    }
    async function consultarPedidos() {
        const pedidos = await requisitar('/solicitacoes', 'GET');
        let painel = document.getElementById('painel-solicitacoes');
        if (!painel) {
            painel = document.createElement('section');
            painel.id = 'painel-solicitacoes';
            painel.setAttribute('aria-live', 'polite');
            document.querySelector('main')?.appendChild(painel) || document.body.appendChild(painel);
        }
        painel.replaceChildren();
        const titulo = document.createElement('h2');
        titulo.textContent = 'Solicitações de auxílio';
        painel.appendChild(titulo);
        if (!pedidos.length) painel.append('Nenhuma solicitação registrada.');
        pedidos.forEach(pedido => {
            const item = document.createElement('p');
            item.textContent = `#${pedido.solicitacao_id} — ${pedido.nome || 'Trabalhador ' + pedido.usuario_id}: ${pedido.mensagem} | ${pedido.status} | Telegram: ${pedido.telegram_enviado ? 'enviado' : 'não enviado'}`;
            if (usuario.perfil === 'admin' && pedido.status === 'pendente') {
                item.appendChild(botao('Marcar como atendida', async () => {
                    if (!confirm('Você já realizou a alteração solicitada?')) return;
                    await requisitar(`/solicitacoes/${pedido.solicitacao_id}`, 'PUT', { status: 'concluida' });
                    await consultarPedidos();
                }));
            }
            painel.appendChild(item);
        });
    }
    function adicionarAcoes() {
        const recurso = location.pathname.includes('/Historico/') ? 'historico' :
            location.pathname.includes('/Cadastro/') ? 'pecas' : null;
        if (!recurso) return;
        const corpo = document.getElementById('corpoTabela');
        if (!corpo) return;
        const tabela = corpo.closest('table');
        if (!tabela.querySelector('[data-acoes]')) {
            const th = document.createElement('th');
            th.dataset.acoes = 'true';
            th.textContent = 'Ações';
            tabela.querySelector('thead tr')?.appendChild(th);
        }
        const atualizar = () => {
            [...corpo.rows].forEach(linha => {
                if (linha.dataset.acoes || linha.cells.length < 4) return;
                const id = Number(linha.cells[0].textContent);
                if (!Number.isInteger(id) || id <= 0) return;
                linha.dataset.acoes = 'true';
                const td = document.createElement('td');
                td.className = 'ghce-acoes-registro';
                const editar = botao('Editar', async () => {
                    if (usuario.perfil !== 'admin') return impedirAlteracao();
                    const dados = await modal({ titulo: `Editar ${recurso === 'historico' ? 'registro do histórico' : 'peça'} #${id}`,
                        mensagem: recurso === 'historico' ? 'Esta edição altera somente o histórico, sem modificar o cadastro da peça.' : 'Atualize os dados da peça cadastrada.',
                        confirmar: 'Salvar alterações', cancelar: true, campos: [
                            { nome: 'nome', rotulo: 'Nome da peça', valor: linha.cells[1].textContent },
                            { nome: 'descricao', rotulo: 'Descrição', valor: linha.cells[2].textContent },
                            { nome: 'quantidade', rotulo: 'Quantidade', valor: linha.cells[recurso === 'historico' ? 4 : 3].textContent }
                        ] });
                    if (!dados) return;
                    const body = { descricao: dados.descricao, quantidade: dados.quantidade,
                        [recurso === 'historico' ? 'nome_peca' : 'nome']: dados.nome };
                    await requisitar(`/${recurso}/${id}`, 'PUT', body);
                    await aviso('As alterações foram salvas.', 'Registro atualizado');
                    location.reload();
                });
                editar.classList.add('ghce-editar');
                editar.setAttribute('aria-label', `Editar ${linha.cells[1].textContent}, registro ${id}`);
                const excluir = botao('Excluir', async () => {
                    if (usuario.perfil !== 'admin') return impedirAlteracao();
                    const confirmado = await modal({ titulo: 'Excluir registro?',
                        mensagem: `realmente deseja excluir?`,
                        confirmar: 'Sim, excluir', cancelar: true, perigo: true });
                    if (!confirmado) return;
                    await requisitar(`/${recurso}/${id}`, 'DELETE');
                    
                    location.reload();
                });
                excluir.classList.add('ghce-excluir');
                excluir.setAttribute('aria-label', `Excluir ${linha.cells[1].textContent}, registro ${id}`);
                td.append(editar, excluir);
                linha.appendChild(td);
            });
        };
        new MutationObserver(atualizar).observe(corpo, { childList: true });
        atualizar();
    }
    document.addEventListener('DOMContentLoaded', async () => {
        try {
            usuario = await requisitar('/me', 'GET');
            sessionStorage.setItem('usuario', JSON.stringify(usuario));
            const barra = document.createElement('div');
            barra.className = 'ghce-barra-acesso';
            const texto = document.createElement('span');
           const caminho = window.location.pathname;

let pagina = 'Home';

if (caminho.includes('/Pesquisa/')) pagina = 'Pesquisa';
if (caminho.includes('/Cadastro/')) pagina = 'Cadastro';
if (caminho.includes('/Historico/')) pagina = 'Histórico';
if (caminho.includes('/Camera/')) pagina = 'Câmera';

texto.textContent = `${pagina} — ${usuario.nome || 'Usuário'} — ${usuario.perfil === 'admin' ? 'Admin' : 'Trabalhador'}`;
            barra.appendChild(texto);
         
          
            barra.appendChild(botao('Sair', async () => {
                await requisitar('/logout', 'POST');
                sessionStorage.clear();
                location.replace('../Login/index1_pag_Login.html');
            }));
            document.body.prepend(barra);
            if (usuario.perfil !== 'admin') {
                const cadastro = document.getElementById('btnCadastrar');
                if (cadastro) {
                    cadastro.title = 'Cadastro disponível apenas para Admin. .';
                    cadastro.addEventListener('click', event => { event.preventDefault(); event.stopImmediatePropagation(); impedirAlteracao(); }, true);
                }
            }
            adicionarAcoes();
        } catch (erro) { await aviso(erro.message, 'Não foi possível concluir'); }
    });
})();
