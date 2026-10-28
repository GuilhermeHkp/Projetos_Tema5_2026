function escapar(valor) { const elemento = document.createElement("span"); elemento.textContent = valor ?? ""; return elemento.innerHTML; }
const API_BASE = "http://127.0.0.1:5000/api";

function preencherTabela(produtos) {
    const corpoTabela = document.getElementById("corpoTabela");

    if (!corpoTabela) return;

    corpoTabela.innerHTML = "";
    produtos.forEach(produto => {
        corpoTabela.innerHTML += `
            <tr>
                <td>${produto.peca_id}</td>
                <td>${escapar(produto.nome)}</td>
                <td>${escapar(produto.descricao ?? "")}</td>
                <td>${produto.quantidade}</td>
            </tr>
        `;
    });
}

async function carregarPecas() {
    const corpoTabela = document.getElementById("corpoTabela");
    try {
        const resposta = await fetch(`${API_BASE}/pecas`);
        const produtos = await resposta.json();
        preencherTabela(produtos);
    } catch (erro) {
        console.error("Não foi possível carregar as peças:", erro);
        if (corpoTabela) {
            corpoTabela.innerHTML = `<tr><td colspan="4">Não foi possível conectar ao servidor (python api.py).</td></tr>`;
        }
    }
}

async function cadastrarPeca() {
    const dados = await window.ghceFormularioPeca();
    if (!dados) return;
    const { nome, descricao, quantidade } = dados;

    try {
        const resposta = await fetch(`${API_BASE}/pecas`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nome, descricao, quantidade })
        });
        if (!resposta.ok) {
            const erro = await resposta.json();
            await window.ghceAviso(erro.erro || "Não foi possível cadastrar.");
            return;
        }
        await carregarPecas();
        await window.ghceAviso("A peça foi cadastrada.", "Cadastro concluído");
    } catch (erro) {
        await window.ghceAviso("Não foi possível conectar ao servidor.");
        console.error(erro);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    carregarPecas();

    const btnCadastrar = document.getElementById("btnCadastrar");
    if (btnCadastrar) btnCadastrar.addEventListener("click", cadastrarPeca);

    const btnPesquisar = document.getElementById("btnPesquisar");
    if (btnPesquisar) btnPesquisar.addEventListener("click", () => {
        window.location.href = "../Pesquisa/index_pag_pesquisa.html";
    });
});
document.addEventListener('keydown', function(event) {
    if (document.querySelector('.ghce-modal[open]')) return;
    if (event.key === 'Escape') {
        window.location.href = '../Home/index1_Home.html';
    }
});
