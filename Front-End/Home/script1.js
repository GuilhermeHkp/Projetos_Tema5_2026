let vozSelecionada = null;

function carregarVozes() {
    const vozes = window.speechSynthesis.getVoices();
    vozSelecionada = vozes.find(
        voz => voz.lang === 'pt-BR' || voz.lang.startsWith('pt')
    );
}

if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = carregarVozes;
}

carregarVozes();

function falar(texto, aoTerminar) {
    window.speechSynthesis.cancel();
    const fala = new SpeechSynthesisUtterance(texto);
    fala.lang = "pt-BR";
    fala.pitch = 0.20;
    fala.rate = 1.7;

    if (vozSelecionada) {
        fala.voice = vozSelecionada;
    }
    if (aoTerminar) {
        fala.onend = aoTerminar;
    }
    window.speechSynthesis.speak(fala);
}

async function enviarPedidoAdmin(tipo) {
    const detalhe = prompt('Descreva o pedido para o Admin (até 1000 caracteres):');
    if (!detalhe || !detalhe.trim()) return;
    try {
        const resposta = await fetch('http://127.0.0.1:5000/api/solicitacoes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensagem: tipo + ': ' + detalhe })
        });
        const dados = await resposta.json();
        if (!resposta.ok) throw new Error(dados.erro || 'Não foi possível registrar.');
        alert(dados.mensagem);
        falar(dados.mensagem);
    } catch (erro) { alert(erro.message); }
}

const textoCustomizado =
    "Bem vindo à tela principal. " +
    "Pressione um para ir à Checagem. " +
    "Pressione dois para ir à tela Histórico. " +
    "Pressione três para ir à tela de Cadastro. " +
    "Pressione quatro para ir à tela de Pesquisa. " +
    "Pressione cinco para solicitar revisão. " +
    "Pressione seis para solicitar ajuda. " +
    "Pressione Esc para voltar para a tela home.";

function irParaCamera() {
    falar("Você clicou em checagem", () => {
        window.location.href = '../Camera/index_pag_camera.html';
    });
}

function irParaHistorico() {
    falar("Você clicou em histórico", () => {
        window.location.href = '../Historico/index_pag_historico.html';
    });
}

function irParaCadastro() {
    falar("Você clicou em cadastro", () => {
        window.location.href = '../Cadastro/index_pag_cadastro.html';
    });
}

function irParaPesquisa() {
    falar("Você clicou em pesquisa", () => {
        window.location.href = '../Pesquisa/index_pag_pesquisa.html';
    });
}

async function acaoRevisao() {
    await enviarPedidoAdmin('Revisão');
}

async function acaoAjuda() {
    await enviarPedidoAdmin('Ajuda');
}

// Vincula os cliques do MOUSE aos IDs após a página carregar
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("btnCamera")?.addEventListener("click", irParaCamera);
    document.getElementById("btnHistorico")?.addEventListener("click", irParaHistorico);
    document.getElementById("btnCadastro")?.addEventListener("click", irParaCadastro);
    document.getElementById("btnPesquisa")?.addEventListener("click", irParaPesquisa);
    document.getElementById("btnRevisao")?.addEventListener("click", acaoRevisao);
    document.getElementById("btnAjuda")?.addEventListener("click", acaoAjuda);
});


document.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        falar(textoCustomizado);
    }
    else if (event.key === '1') {
        irParaCamera();
    }
    else if (event.key === '2') {
        irParaHistorico();
    }
    else if (event.key === '3') {
        irParaCadastro();
    }
    else if (event.key === '4') {
        irParaPesquisa();
    }
    else if (event.key === '5') {
        acaoRevisao();
    }
    else if (event.key === '6') {
        acaoAjuda();
    }
    else if (event.key === 'Escape') {
        window.location.href = '../Home/index1_Home.html';
    }
});
