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
        <!-- <a class="button" href="/logs" target="_blank">Ver Logs</a> -->
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
                    setTimeout(loadGallery, 1500); // pequeno delay para geração dos gráficos
                }
            })
            .catch(error => {
                outputBox.innerText = "Erro: " + error;
            });
    }

    function loadGallery() {
        const galeria = document.getElementById("galeria");
        galeria.innerHTML = "";

        fetch("/listar_graficos")
            .then(response => response.json())
            .then(data => {
                const cenarios = Object.keys(data);
                if (cenarios.length === 0) {
                    galeria.innerHTML = "<p>⚠️ Nenhum gráfico encontrado.</p>";
                    return;
                }

                for (const cenario of cenarios) {
                    const section = document.createElement("div");
                    section.classList.add("cenario");

                    const titulo = document.createElement("h3");
                    titulo.textContent = "Cenário: " + cenario;
                    section.appendChild(titulo);

                    data[cenario].forEach(arquivo => {
                        const img = document.createElement("img");
                        img.src = `/grafico/${cenario}/${arquivo}?t=${Date.now()}`;
                        img.alt = arquivo;
                        img.classList.add("grafico");
                        section.appendChild(img);
                    });

                    galeria.appendChild(section);
                }
            })
            .catch(error => {
                galeria.innerHTML = "<p>Erro ao carregar galeria: " + error + "</p>";
            });
    }

    // Carrega a galeria ao abrir a página
    window.onload = loadGallery;
</script>

</body>
</html>
