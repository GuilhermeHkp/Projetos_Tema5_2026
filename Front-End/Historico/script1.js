function escapar(valor) { const elemento = document.createElement("span"); elemento.textContent = valor ?? ""; return elemento.innerHTML; }
const API_BASE = "http://127.0.0.1:5000/api";

let produtos = [];
const corpoTabela = document.getElementById("corpoTabela");
let linhaAtualFocada = -1;

const areaAnuncio = document.createElement("div");
areaAnuncio.setAttribute("aria-live", "assertive");
areaAnuncio.style.position = "absolute";
areaAnuncio.style.width = "1px";
areaAnuncio.style.height = "1px";
areaAnuncio.style.overflow = "hidden";
document.body.appendChild(areaAnuncio);

function falarTexto(texto) {
    const fala = new SpeechSynthesisUtterance(texto);
    fala.lang = "pt-BR";
    fala.volume = 1;
    fala.rate = 1.85;

    speechSynthesis.cancel();
    speechSynthesis.speak(fala);

    areaAnuncio.textContent = texto;
}

function carregarTabela() {
    if (!corpoTabela) return;
    corpoTabela.innerHTML = "";

    produtos.forEach((produto, index) => {
        const linha = document.createElement("tr");

        linha.setAttribute("tabindex", "0");
        linha.setAttribute("id", `linha-prod-${index}`);
        linha.setAttribute("role", "row");
        linha.setAttribute("aria-label", `Item ${index + 1} de ${produtos.length}: ${escapar(produto.nome_peca)}`);

        linha.innerHTML = `
            <td>${produto.historico_id}</td>
            <td>${escapar(produto.nome_peca)}</td>
            <td>${escapar(produto.descricao ?? "")}</td>
            <td>${escapar(produto.horario_registro ?? "")}</td>
            <td>${produto.quantidade}</td>
            <td>
                <button class="btn-audio" tabindex="-1" aria-hidden="true" onclick="falarLinhaEspecifica(${index})">
                    <i class="bi bi-volume-up-fill"></i>
                </button>
            </td>
        `;
        linha.addEventListener("focus", () => {
            linhaAtualFocada = index;
            anunciarDadosLinha(produto, index);
        });

        corpoTabela.appendChild(linha);
    });
}

async function carregarHistorico() {
    try {
        const resposta = await fetch(`${API_BASE}/historico`);
        produtos = await resposta.json();
    } catch (erro) {
        console.error("Não foi possível carregar o histórico:", erro);
        produtos = [];
    }
    carregarTabela();
}

function anunciarDadosLinha(produto, index) {
    const resumo = `Linha ${index + 1}. Produto: ${escapar(produto.nome_peca)}. Quantidade: ${produto.quantidade}. Descrição: ${escapar(produto.descricao ?? "")}.`;
    falarTexto(resumo);
}

function falarLinhaEspecifica(index) {
    if (produtos[index]) {
        anunciarDadosLinha(produtos[index], index);
    }
}

window.addEventListener("DOMContentLoaded", () => {
    carregarHistorico().then(() => {
        setTimeout(() => {
            falarTexto("Histórico de produtos carregado. Use as setas para cima e para baixo do teclado para navegar entre os registros.");
        }, 1000);
    });
});

document.addEventListener("keydown", function(event) {
    if (document.querySelector('.ghce-modal[open]') || event.target.closest('button, input, textarea')) return;
    if (event.key === "Escape") {
        window.location.href = "../Home/index1_Home.html";
    }

    if (event.key === "ArrowDown") {
        event.preventDefault();
        if (linhaAtualFocada < produtos.length - 1) {
            linhaAtualFocada++;
            const proximaLinha = document.getElementById(`linha-prod-${linhaAtualFocada}`);
            if (proximaLinha) proximaLinha.focus();
        } else {
            falarTexto("Fim do histórico.");
        }
    }

    if (event.key === "ArrowUp") {
        event.preventDefault();
        if (linhaAtualFocada > 0) {
            linhaAtualFocada--;
            const linhaAnterior = document.getElementById(`linha-prod-${linhaAtualFocada}`);
            if (linhaAnterior) linhaAnterior.focus();
        } else {
            falarTexto("Início do histórico.");
        }
    }
});
