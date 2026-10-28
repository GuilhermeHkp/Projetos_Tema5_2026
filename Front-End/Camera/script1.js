const API_BASE = "http://127.0.0.1:5000/api";

// Intervalo entre frames enviados para detecção contínua (tempo real).
const INTERVALO_DETECCAO_MS = 600;
// A cada quantos ciclos de detecção um frame também é REGISTRADO no
// histórico (grava no banco e salva a imagem). Evita gravar várias vezes
// por segundo, mas mantém o histórico sendo alimentado automaticamente.
const CICLOS_ATE_REGISTRAR = 8; // 600ms * 8 = aproximadamente 4,8s
// Largura máxima do frame enviado ao backend (reduz o tamanho do payload e
// acelera a inferência, sem prejudicar a exibição, que continua em resolução cheia).
const LARGURA_MAX_ENVIO = 960;

let video = null;
let overlayCanvas = null;
let overlayCtx = null;
let captureCanvas = null;
let captureCtx = null;

let mediaStream = null;
let loopId = null;
let cicloAtual = 0;
let enviandoFrame = false;
const CAMERA_SOURCE_ID = sessionStorage.getItem("ghce_camera_source") || ((globalThis.crypto && typeof globalThis.crypto.randomUUID === "function") ? globalThis.crypto.randomUUID() : `${Date.now()}-${Math.random()}`);
sessionStorage.setItem("ghce_camera_source", CAMERA_SOURCE_ID);

// Últimos itens identificados na tela (usado pelo botão de TTS).
let ultimasDeteccoes = [];

function traduzirNome(nome) {
    // As classes agora vêm diretamente do best.pt treinado pelo usuário.
    return nome;
}

// Cooldown (ms) para não ficar repetindo o nome do mesmo item o tempo todo
// enquanto ele continua parado em frente à câmera.
const COOLDOWN_ANUNCIO_MS = 6000;
let ultimoAnuncioPorItem = {};

function falar(texto) {
    const voz = new SpeechSynthesisUtterance(texto);
    voz.lang = "pt-BR";
    voz.volume = 1;
    voz.rate = 1.65;
    voz.pitch = 0.4;
    speechSynthesis.cancel();
    speechSynthesis.speak(voz);
}

/** Fala sem cancelar uma fala em andamento — usado no anúncio automático,
 * para não cortar o áudio de um item no meio por causa do próximo frame. */
function falarEnfileirado(texto) {
    const voz = new SpeechSynthesisUtterance(texto);
    voz.lang = "pt-BR";
    voz.volume = 1;
    voz.rate = 1.5;
    voz.pitch = 1;
    speechSynthesis.speak(voz);
}

/** Anuncia em voz alta, automaticamente, os itens recém identificados no
 * frame (respeitando um intervalo mínimo por item, para não repetir sem
 * parar enquanto o objeto permanece visível). */
function anunciarDeteccoesAutomaticamente(deteccoes) {
    if (!deteccoes || deteccoes.length === 0) return;
    const agora = Date.now();
    const contagem = {};
    deteccoes.forEach(d => {
        contagem[d.name] = (contagem[d.name] || 0) + 1;
    });

    const novos = [];
    Object.entries(contagem).forEach(([nome, qtd]) => {
        const ultimaVez = ultimoAnuncioPorItem[nome] || 0;
        if (agora - ultimaVez >= COOLDOWN_ANUNCIO_MS) {
            const nomePt = traduzirNome(nome);
            novos.push(qtd > 1 ? `${qtd} ${nomePt}` : nomePt);
            ultimoAnuncioPorItem[nome] = agora;
        }
    });

    if (novos.length > 0) {
        falarEnfileirado(`Identificado: ${novos.join(", ")}.`);
    }
}

function falarInstrucoes() {
    falar(`Aperte espaço para ouvir os itens identificados no momento, ou shift para repetir estas instruções.`);
}

function atualizarStatus(texto) {
    const status = document.querySelector('.status span');
    if (status) status.textContent = texto;
}

/** Monta a frase falada/exibida a partir das detecções atuais (agrupando por nome e contando). */
function descreverDeteccoes(deteccoes) {
    if (!deteccoes || deteccoes.length === 0) {
        return "Nenhum item identificado no momento.";
    }
    const contagem = {};
    deteccoes.forEach(d => {
        contagem[d.name] = (contagem[d.name] || 0) + 1;
    });
    const partes = Object.entries(contagem).map(([nome, qtd]) => {
        const nomePt = traduzirNome(nome);
        return qtd > 1 ? `${qtd} ${nomePt}` : nomePt;
    });
    return `Identificado: ${partes.join(", ")}.`;
}

/** Fala os itens identificados no exato momento em que o botão é clicado. */
function falarItensIdentificados() {
    falar(descreverDeteccoes(ultimasDeteccoes));
}

/** Pede acesso à câmera do dispositivo e inicia a transmissão de vídeo em tempo real. */
async function iniciarCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        atualizarStatus("Este navegador não suporta acesso à câmera.");
        return false;
    }
    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" },
            audio: false
        });
        video.srcObject = mediaStream;
        await video.play();
        ajustarCanvasAoVideo();
        return true;
    } catch (erro) {
        console.error("Erro ao acessar a câmera:", erro);
        atualizarStatus("Não foi possível acessar a câmera. Verifique a permissão.");
        return false;
    }
}

function pararCamera() {
    if (loopId) {
        clearInterval(loopId);
        loopId = null;
    }
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
        mediaStream = null;
    }
}

/** Faz o canvas de overlay acompanhar exatamente o tamanho exibido do vídeo. */
function ajustarCanvasAoVideo() {
    const frame = document.querySelector('.camera-frame');
    if (!frame || !overlayCanvas) return;
    overlayCanvas.width = frame.clientWidth;
    overlayCanvas.height = frame.clientHeight;
}

/** Desenha as caixas dos itens identificados sobre o vídeo. */
function desenharDeteccoes(deteccoes, larguraFrameEnviado, alturaFrameEnviado) {
    if (!overlayCtx) return;
    overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    if (!deteccoes || deteccoes.length === 0) return;

    const escalaX = overlayCanvas.width / larguraFrameEnviado;
    const escalaY = overlayCanvas.height / alturaFrameEnviado;

    overlayCtx.lineWidth = 3;
    overlayCtx.strokeStyle = "#3cd070";
    overlayCtx.font = "16px Arial";

    deteccoes.forEach(d => {
        const [x1, y1, x2, y2] = d.bbox;
        const rx = x1 * escalaX;
        const ry = y1 * escalaY;
        const rw = (x2 - x1) * escalaX;
        const rh = (y2 - y1) * escalaY;

        overlayCtx.strokeStyle = "#3cd070";
        overlayCtx.strokeRect(rx, ry, rw, rh);

        const rotulo = `${d.name}`;
        const larguraTexto = overlayCtx.measureText(rotulo).width + 8;
        overlayCtx.fillStyle = "#3cd070";
        overlayCtx.fillRect(rx, Math.max(0, ry - 20), larguraTexto, 20);
        overlayCtx.fillStyle = "#0d192b";
        overlayCtx.fillText(rotulo, rx + 4, Math.max(14, ry - 5));
    });
}

/** Captura o frame atual do vídeo, redimensionado, como JPEG em base64. */
function capturarFrameBase64() {
    const largura = video.videoWidth;
    const altura = video.videoHeight;
    if (!largura || !altura) return null;

    const escala = Math.min(1, LARGURA_MAX_ENVIO / largura);
    const larguraEnvio = Math.round(largura * escala);
    const alturaEnvio = Math.round(altura * escala);

    captureCanvas.width = larguraEnvio;
    captureCanvas.height = alturaEnvio;
    captureCtx.drawImage(video, 0, 0, larguraEnvio, alturaEnvio);

    return {
        base64: captureCanvas.toDataURL("image/jpeg", 0.6),
        largura: larguraEnvio,
        altura: alturaEnvio
    };
}

/** Envia um frame para o backend (preview contínuo ou registro completo no histórico). */
async function enviarFrameParaDeteccao() {
    if (enviandoFrame || !mediaStream) return;
    const frame = capturarFrameBase64();
    if (!frame) return;

    enviandoFrame = true;
    cicloAtual++;
    const deveRegistrar = (cicloAtual % CICLOS_ATE_REGISTRAR) === 0;

    try {
        const parametros = new URLSearchParams({ source: CAMERA_SOURCE_ID });
        if (!deveRegistrar) parametros.set("preview", "1");
        const resposta = await fetch(`${API_BASE}/checkin/imagem?${parametros.toString()}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ imagem_base64: frame.base64 })
        });
        const dados = await resposta.json();
        if (!resposta.ok) throw new Error(dados.erro || `HTTP ${resposta.status}`);

        ultimasDeteccoes = dados.deteccoes || [];
        desenharDeteccoes(ultimasDeteccoes, frame.largura, frame.altura);
        atualizarStatus(descreverDeteccoes(ultimasDeteccoes));
        anunciarDeteccoesAutomaticamente(ultimasDeteccoes);
    } catch (erro) {
        console.error("Erro ao enviar frame para detecção:", erro);
        atualizarStatus(erro.message || "Não foi possível conectar ao servidor.");
    } finally {
        enviandoFrame = false;
    }
}

async function iniciarDeteccaoContinua() {
    const cameraOk = await iniciarCamera();
    if (!cameraOk) return;

    atualizarStatus("Analisando itens...");
    loopId = setInterval(enviarFrameParaDeteccao, INTERVALO_DETECCAO_MS);
}

document.addEventListener('DOMContentLoaded', () => {
    video = document.getElementById('videoFeed');
    overlayCanvas = document.getElementById('overlayCanvas');
    overlayCtx = overlayCanvas.getContext('2d');
    captureCanvas = document.createElement('canvas');
    captureCtx = captureCanvas.getContext('2d');

    window.addEventListener('resize', ajustarCanvasAoVideo);

    const botaoOuvir = document.getElementById('btnOuvir');
    if (botaoOuvir) {
        botaoOuvir.addEventListener('click', falarItensIdentificados);
    }

    iniciarDeteccaoContinua();
});

document.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
        falarInstrucoes();
    }

    if (event.code === 'Space') {
        event.preventDefault();
        falarItensIdentificados();
    }

    if (event.key === 'Escape') {
        speechSynthesis.cancel();
        pararCamera();
        window.location.href = '../Home/index1_Home.html';
    }
});

window.addEventListener('beforeunload', pararCamera);
