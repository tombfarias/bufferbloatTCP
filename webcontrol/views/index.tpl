<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <title>bufferbloatTCP - Controle da VM</title>
    <link rel="stylesheet" href="/static/style.css">
</head>

<body>

<header>
    <h1>Controle da Máquina Virtual</h1>
    <div class="tabs">
        <button class="tab-button active" onclick="showTab('bufferbloat')">Experimento Bufferbloat</button>
        <button class="tab-button" onclick="showTab('competition')">Experimento de Competição</button>
    </div>
</header>

<main>
    <p>Use os botões abaixo para controlar o ambiente de rede virtualizado com Mininet:</p>

    <!-- Botões Comuns -->
    <div id="botoes-comuns" class="button-group">
        <button class="button" onclick="runCommand('/up')">Subir VM</button>
        <button class="button" onclick="runCommand('/status')">Status da VM</button>
        <button class="button" onclick="runCommand('/ssh')">Testar Ping</button>
    </div>

    <!-- Botões Bufferbloat -->
    <div id="botoes-bufferbloat" class="button-group">
        <button class="button" onclick="runCommand('/run_reno')">Rodar Experimento (Reno)</button>
        <button class="button" onclick="runCommand('/run_bbr')">Rodar Experimento (BBR)</button>
    </div>

    <!-- Botões Competição -->
    <div id="botoes-competicao" class="button-group" style="display: none;">
        <button class="button" onclick="runCompetition()">Rodar Competição (Reno vs BBR)</button>

    <div class="controle-competicao">
        <div class="controle-slider">
            <label for="slider-reno">Reno:</label>
            <input type="range" id="slider-reno" min="1" max="3" value="2" oninput="updateSliderLabel('reno')">
            <span id="slider-reno-value">2</span>
        </div>

        <div class="controle-slider">
            <label for="slider-bbr">BBR:</label>
            <input type="range" id="slider-bbr" min="1" max="3" value="2" oninput="updateSliderLabel('bbr')">
            <span id="slider-bbr-value">2</span>
        </div>
    </div>



    </div>

    <section>
        <h2>Saída</h2>
        <pre id="output">Aguardando comando...</pre>
    </section>

    <h2>Galeria de Gráficos</h2>

    <div id="bufferbloat" class="tab-content active">
        <div id="galeria" class="galeria">
        </div>
    </div>

    <div id="competition" class="tab-content">
        <div id="galeria_competition" class="galeria">
        </div>
    </div>

    <div class="footer">
        Diretório do projeto Vagrant: <code>{{!vagrant_dir}}</code>
    </div>
</main>

<script>
let abaAtual = "bufferbloat";

function showTab(tabId) {
    document.getElementById("botoes-bufferbloat").style.display = (tabId === "bufferbloat") ? "block" : "none";
    document.getElementById("botoes-competicao").style.display = (tabId === "competition") ? "block" : "none";

    document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));

    document.querySelector(`.tab-button[onclick*="${tabId}"]`).classList.add('active');
    document.getElementById(tabId).classList.add('active');

    // Limpa galeria da aba anterior
    if (abaAtual === "bufferbloat") {
        document.getElementById("galeria").innerHTML = "";
    } else if (abaAtual === "competition") {
        document.getElementById("galeria_competition").innerHTML = "";
    }

    // Carrega a nova galeria
    if (tabId === "bufferbloat") {
        loadBufferbloatGallery();
    } else if (tabId === "competition") {
        loadCompetitionGallery();
    }

    abaAtual = tabId;
}

function runCommand(endpoint) {
    const outputBox = document.getElementById("output");
    outputBox.innerText = "Executando...\n";

    fetch(endpoint)
        .then(async response => {
            if (!response.ok) {
                outputBox.innerText += `[ERRO] HTTP ${response.status}`;
                return;
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                outputBox.innerText += chunk;
                outputBox.scrollTop = outputBox.scrollHeight; // scroll para o fim
            }

            outputBox.innerText += "\nComando finalizado.";
        })
        .catch(err => {
            outputBox.innerText = "[ERRO] Falha na requisição: " + err;
        });
}

function gerarLegenda(nomeArquivo) {
    const mapaTipo = {
        'rtt': 'RTT',
        'buffer': 'Uso do Buffer',
        'tempos-distribuicao': 'Distribuição dos Tempos'
    };

    if (nomeArquivo.startsWith("bbr") || nomeArquivo.startsWith("reno")) {
        const partes = nomeArquivo.replace(".png", "").split("-");
        const algoritmo = partes[0].toUpperCase();
        const tipo = mapaTipo[partes[1]] || partes[1];
        const fila = partes[2]?.replace("q", "Fila = ");
        return `${tipo} do ${algoritmo} (${fila})`;
    }

    if (nomeArquivo.startsWith("grafico-tempos-distribuicao")) {
        const fila = nomeArquivo.match(/q\d+/)?.[0]?.replace("q", "Fila = ");
        return `Distribuição dos Tempos (${fila})`;
    }

    return nomeArquivo;
}

function loadBufferbloatGallery() {
    const galeria = document.getElementById("galeria");
    galeria.innerHTML = "";

    fetch("/listar_graficos")
        .then(resp => resp.json())
        .then(data => {
            for (const cenario in data) {
                const section = document.createElement("div");
                section.classList.add("cenario");

                const titulo = document.createElement("h3");
                titulo.textContent = "Cenário: " + cenario;
                section.appendChild(titulo);

                const algoritmos = data[cenario];
                for (const alg in algoritmos) {
                    const subtitulo = document.createElement("h4");
                    subtitulo.textContent = "Algoritmo: " + alg.toUpperCase();
                    section.appendChild(subtitulo);

                    const arquivos = algoritmos[alg];
                    if (arquivos.length === 0) {
                        const aviso = document.createElement("p");
                        aviso.textContent = "Nenhum gráfico encontrado.";
                        aviso.classList.add("aviso-grafico-vazio");
                        section.appendChild(aviso);
                        continue;
                    }

                    for (const arquivo of arquivos) {
                        const bloco = document.createElement("div");
                        bloco.className = "grafico-bloco";

                        const legenda = document.createElement("div");
                        legenda.className = "legenda";
                        legenda.textContent = gerarLegenda(arquivo);

                        const img = document.createElement("img");
                        img.src = `/grafico/${cenario}/${arquivo}?t=${Date.now()}`;
                        img.alt = arquivo;
                        img.className = "grafico";

                        bloco.appendChild(legenda);
                        bloco.appendChild(img);
                        section.appendChild(bloco);
                    }
                }

                galeria.appendChild(section);
            }
        });
}


function loadCompetitionGallery() {
    const galeria = document.getElementById("galeria_competition");
    galeria.innerHTML = "";
    fetch("/listar_graficos_competition")
        .then(resp => resp.json())
        .then(data => {
            for (const cenario in data) {
                const section = document.createElement("div");
                section.classList.add("cenario");

                const titulo = document.createElement("h3");
                titulo.textContent = "Cenário: " + cenario;
                section.appendChild(titulo);

                const categorias = data[cenario];
// Primeiro os gráficos gerais
                if (categorias.gerais && categorias.gerais.length > 0) {
                    const subtitulo = document.createElement("h4");
                    subtitulo.textContent = "Gerais";
                    section.appendChild(subtitulo);

                    for (const arquivo of categorias.gerais) {
                        const bloco = document.createElement("div");
                        bloco.className = "grafico-bloco";

                        const legenda = document.createElement("div");
                        legenda.className = "legenda";
                        legenda.textContent = gerarLegenda(arquivo);

                        const img = document.createElement("img");
                        img.src = `/grafico_competition/${cenario}/${arquivo}?t=${Date.now()}`;
                        img.alt = arquivo;
                        img.className = "grafico";

                        bloco.appendChild(legenda);
                        bloco.appendChild(img);
                        section.appendChild(bloco);
                    }
                }

                // Depois os fluxos (bbr0, reno1, etc.)
                if (categorias.fluxos) {
                    for (const fluxo in categorias.fluxos) {
                        const subtitulo = document.createElement("h4");
                        subtitulo.textContent = "Fluxo: " + fluxo.toUpperCase();
                        section.appendChild(subtitulo);

                        for (const arquivo of categorias.fluxos[fluxo]) {
                            const bloco = document.createElement("div");
                            bloco.className = "grafico-bloco";

                            const legenda = document.createElement("div");
                            legenda.className = "legenda";
                            legenda.textContent = gerarLegenda(arquivo);

                            const img = document.createElement("img");
                            img.src = `/grafico_competition/${cenario}/${arquivo}?t=${Date.now()}`;
                            img.alt = arquivo;
                            img.className = "grafico";

                            bloco.appendChild(legenda);
                            bloco.appendChild(img);
                            section.appendChild(bloco);
                        }
                    }
                }


                galeria.appendChild(section);
            }
        });
}
function runCompetition() {
    const reno = document.getElementById("slider-reno").value;
    const bbr = document.getElementById("slider-bbr").value;
    const outputBox = document.getElementById("output");

    outputBox.innerText = "Executando...\n";

    fetch(`/run_competition?reno=${reno}&bbr=${bbr}`)
        .then(async response => {
            const reader = response.body.getReader();
            const decoder = new TextDecoder("utf-8");

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                const texto = decoder.decode(value, { stream: true });
                outputBox.innerText += texto;
                outputBox.scrollTop = outputBox.scrollHeight;
            }

            outputBox.innerText += "\nComando finalizado.";
            loadCompetitionGallery();  // atualiza galeria ao final
        })
        .catch(err => {
            outputBox.innerText = "[ERRO] Falha na requisição: " + err;
        });
}


function updateSliderLabel(tipo) {
    const valor = document.getElementById(`slider-${tipo}`).value;
    document.getElementById(`slider-${tipo}-value`).textContent = valor;
}

window.addEventListener("DOMContentLoaded", () => {
    updateSliderLabel("reno");
    updateSliderLabel("bbr");
});

window.onload = () => {
    showTab("bufferbloat");
};
</script>

</body>
</html>
