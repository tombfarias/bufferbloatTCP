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
</header>

<main>
    <p>Use os botões abaixo para controlar o ambiente de rede virtualizado com Mininet:</p>

    <div class="button-group">
        <button class="button" onclick="runCommand('/up')">Subir VM</button>
        <button class="button" onclick="runCommand('/status')">Status da VM</button>
        <button class="button" onclick="runCommand('/ssh')">Testar Ping</button>
        <button class="button" onclick="runCommand('/run_reno')">Rodar Experimento (Reno)</button>
        <button class="button" onclick="runCommand('/run_bbr')">Rodar Experimento (BBR)</button>
    </div>

    <section>
        <h2>Saída</h2>
        <pre id="output" style="max-height: 300px; overflow-y: auto;">Aguardando comando...</pre>
    </section>

    <section>
        <h2>Galeria de Gráficos</h2>
        <div id="galeria" class="galeria">
            <p>Carregando gráficos...</p>
        </div>
    </section>

    <div class="footer">
        Diretório do projeto Vagrant: <code>{{!vagrant_dir}}</code>
    </div>
</main>

<script>
    function runCommand(endpoint) {
        const outputBox = document.getElementById("output");
        outputBox.innerHTML = "Executando...";

        fetch(endpoint)
            .then(response => response.json())
            .then(data => {
                outputBox.innerText = data.output;

                if (endpoint.includes("run_")) {
                    setTimeout(loadGallery, 1500);
                }
            })
            .catch(error => {
                outputBox.innerText = "Erro: " + error;
            });
    }

    function gerarLegenda(nomeArquivo) {
        const mapaTipo = {
            'rtt': 'RTT',
            'buffer': 'Uso do Buffer',
            'tempos-distribuicao': 'Distribuição dos Tempos'
        };

        if (nomeArquivo.startsWith("bbr-") || nomeArquivo.startsWith("reno-")) {
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

    function loadGallery() {
    const galeria = document.getElementById("galeria");
    galeria.innerHTML = "";

    fetch("/listar_graficos")
        .then(response => response.json())
        .then(data => {
            const cenarios = Object.keys(data);
            if (cenarios.length === 0) {
                galeria.innerHTML = "<p>Nenhum gráfico encontrado.</p>";
                return;
            }

            for (const cenario of cenarios) {
                const section = document.createElement("div");
                section.classList.add("cenario");

                const titulo = document.createElement("h3");
                titulo.textContent = "Cenário: " + cenario;
                section.appendChild(titulo);

                const algoritmos = data[cenario];

                for (const nome_algoritmo in algoritmos) {
                    const subtitulo = document.createElement("h4");
                    subtitulo.textContent = "Algoritmo: " + nome_algoritmo.toUpperCase();
                    section.appendChild(subtitulo);

                    const arquivos = algoritmos[nome_algoritmo];
                    for (const arquivo of arquivos) {
                        const bloco = document.createElement("div");
                        bloco.classList.add("grafico-bloco");

                        const legenda = document.createElement("div");
                        legenda.className = "legenda";
                        legenda.textContent = gerarLegenda(arquivo);

                        const img = document.createElement("img");
                        img.src = `/grafico/${cenario}/${arquivo}?t=${Date.now()}`;
                        img.alt = arquivo;
                        img.classList.add("grafico");

                        bloco.appendChild(legenda);
                        bloco.appendChild(img);
                        section.appendChild(bloco);
                    }
                }

                galeria.appendChild(section);
            }
        })
        .catch(error => {
            galeria.innerHTML = "<p>Erro ao carregar galeria: " + error + "</p>";
        });
}


    window.onload = loadGallery;
</script>

</body>
</html>
