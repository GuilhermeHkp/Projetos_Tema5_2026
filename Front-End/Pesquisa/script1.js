function escapar(valor) { const elemento = document.createElement("span"); elemento.textContent = valor ?? ""; return elemento.innerHTML; }
const API_BASE = "http://127.0.0.1:5000/api";

let produtosBase = [];
let produtosFiltrados = [];
let linhaAtualFocada = -1;

const corpoTabela = document.getElementById("corpoTabela");
const inputPesquisa = document.getElementById("inputPesquisa");
const areaAnuncio = document.createElement("div");
areaAnuncio.setAttribute("aria-live", "assertive");

function falarTexto(texto) {
    const fala = new SpeechSynthesisUtterance(texto);
    fala.lang = "pt-BR";
    fala.rate = 1.85;
    speechSynthesis.cancel();
    speechSynthesis.speak(fala);
}

function renderizarTabela() {
    if (!corpoTabela) return;
    corpoTabela.innerHTML = "";
    produtosFiltrados.forEach((p, i) => {
        const linha = document.createElement("tr");
        linha.setAttribute("tabindex", "0");
        linha.setAttribute("id", `linha-pesquisa-${i}`);
        linha.setAttribute("aria-label", `Item ${i + 1} de ${produtosFiltrados.length}: ${escapar(p.nome)}`);

        linha.innerHTML = `<td>${p.peca_id}</td><td>${escapar(p.nome)}</td><td>${escapar(p.descricao ?? "")}</td><td>${p.quantidade}</td>`;

        linha.addEventListener("focus", () => {
            linhaAtualFocada = i;
            falarTexto(`Item ${i + 1}. Produto: ${escapar(p.nome)}. Quantidade: ${p.quantidade}. Descrição: ${escapar(p.descricao ?? "")}.`);
        });

        corpoTabela.appendChild(linha);
    });
}

function filtrarProdutos() {
    const termo = inputPesquisa.value.toLowerCase().trim();

    produtosFiltrados = produtosBase.filter(p =>
        p.nome.toLowerCase().includes(termo) ||
        (p.descricao ?? "").toLowerCase().includes(termo) ||
        String(p.peca_id).includes(termo)
    );

    renderizarTabela();
}

async function carregarPecas() {
    try {
        const resposta = await fetch(`${API_BASE}/pecas`);
        produtosBase = await resposta.json();
    } catch (erro) {
        console.error("Não foi possível carregar as peças:", erro);
        produtosBase = [];
    }
    produtosFiltrados = [...produtosBase];
    renderizarTabela();
}

window.addEventListener("DOMContentLoaded", () => {
    carregarPecas();
    if (inputPesquisa) {
        inputPesquisa.addEventListener("input", filtrarProdutos);
        inputPesquisa.focus();
    }
});

document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") window.location.href = "../Home/index1_Home.html";

    if (e.key === "Enter" && document.activeElement === inputPesquisa) {
        e.preventDefault();
        const primeira = document.getElementById("linha-pesquisa-0");
        primeira ? primeira.focus() : falarTexto("Não há resultados para navegar.");
    }

    if (document.activeElement !== inputPesquisa) {
        if (e.key === "ArrowDown") {
            e.preventDefault();
            if (linhaAtualFocada < produtosFiltrados.length - 1) {
                document.getElementById(`linha-pesquisa-${++linhaAtualFocada}`).focus();
            } else {
                falarTexto("Fim dos resultados.");
            }
        }

        if (e.key === "ArrowUp") {
            e.preventDefault();
            if (linhaAtualFocada > 0) {
                document.getElementById(`linha-pesquisa-${--linhaAtualFocada}`).focus();
            } else if (linhaAtualFocada === 0) {
                linhaAtualFocada = -1;
                inputPesquisa.focus();
                falarTexto("Voltando para o campo de pesquisa.");
            }
        }
    }
});
