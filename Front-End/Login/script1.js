const API_BASE = "http://127.0.0.1:5000/api";

async function fazerLogin() {

    const colaborador = document.getElementById("colaborador").value.trim();
    const associado = document.getElementById("associado").value.trim();
    const senha = document.getElementById("senha").value.trim();


    if (colaborador === "" || senha === "") {
        alert("Preencha as informações por favor");
        return;
    }

    try {
        const resposta = await fetch(`${API_BASE}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ colaborador, associado, senha })
        });
        const dados = await resposta.json();

        if (!resposta.ok || !dados.sucesso) {
            alert(dados.erro || "Não foi possível entrar. Verifique os dados.");
            return;
        }

        sessionStorage.setItem("usuario", JSON.stringify(dados.usuario));
        sessionStorage.setItem("token", dados.token);
        window.location.href = "../Home/index1_Home.html";
    } catch (erro) {
        alert("Não foi possível conectar ao servidor. Verifique se a API está rodando (python api.py).");
        console.error(erro);
    }
}

function mostrarSenha() {
    const campoSenha = document.getElementById("senha");
    const iconeSenha = document.getElementById("btn-senha");

    if (campoSenha.type === "password") {
        campoSenha.type = "text";
        iconeSenha.classList.remove("bi-eye-fill");
        iconeSenha.classList.add("bi-eye-slash-fill");
    } else {
        campoSenha.type = "password";
        iconeSenha.classList.remove("bi-eye-slash-fill");
        iconeSenha.classList.add("bi-eye-fill");
    }
}
