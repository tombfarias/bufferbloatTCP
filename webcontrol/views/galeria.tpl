<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Galeria de Gráficos</title>
    <style>
        body { font-family: sans-serif; margin: 20px; }
        h2 { margin-top: 40px; }
        .grafico-bloco { margin-bottom: 20px; }
        .grafico-bloco img { max-width: 600px; display: block; }
        .legenda { font-size: 14px; margin-bottom: 10px; color: #444; }
    </style>
</head>
<body>
    <h1>Galeria de Gráficos</h1>

    % for cenario, algoritmos in graficos.items():
        <h2>Cenário: {{ cenario }}</h2>

        % for algoritmo, imagens in algoritmos.items():
            <h3>Algoritmo: {{ algoritmo.upper() }}</h3>
            % for img in imagens:
                <div class="grafico-bloco">
                    <div class="legenda">{{ img }}</div>
                    <img src="/grafico/{{ cenario }}/{{ img }}" alt="{{ img }}">
                </div>
            % end
        % end
    % end
</body>
</html>
