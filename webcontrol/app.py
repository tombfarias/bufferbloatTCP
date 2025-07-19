from bottle import TEMPLATE_PATH, route, run, template, static_file, response, request
import subprocess
import os
import json
import re


# Caminhos corretos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAGRANT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../mininet-vagrant"))
BUFFERBLOAT_DIR = os.path.join(VAGRANT_DIR, "bufferbloat/bufferbloat")
COMPETITION_DIR = os.path.join(VAGRANT_DIR, "bufferbloat/competition")

# Garante que os templates serão buscados na pasta correta
TEMPLATE_PATH.insert(0, os.path.join(SCRIPT_DIR, 'views'))

def run_cmd(cmd, cwd=VAGRANT_DIR):
    """Executa comando shell e envia saída linha a linha"""
    def generate():
        try:
            process = subprocess.Popen(cmd, cwd=cwd, shell=True,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT,
                                       text=True)
            for line in process.stdout:
                yield line
            process.wait()
            if process.returncode != 0:
                yield f"\n[ERRO - Código {process.returncode}]\n"
        except Exception as e:
            yield f"[EXCEÇÃO] {str(e)}\n"

    response.content_type = 'text/plain'
    return generate()

@route('/')
def index():
    return template('index.tpl', vagrant_dir=f"{VAGRANT_DIR}")


@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root=os.path.join(SCRIPT_DIR, 'static'))


@route('/up')
def vagrant_up():
    return run_cmd("vagrant up")


@route('/status')
def vagrant_status():
    return run_cmd("vagrant status")


@route('/ssh')
def ssh_ping():
    return run_cmd('vagrant ssh -c "ping -c 4 8.8.8.8"')


@route('/run_reno')
def run_reno():
    return run_cmd('vagrant ssh -c "cd bufferbloat && make run-reno"')


@route('/run_bbr')
def run_bbr():
    return run_cmd('vagrant ssh -c "cd bufferbloat && make run-bbr"')


@route('/run_competition')
def competition_run():
    try:
        reno = int(request.query.reno)
        bbr = int(request.query.bbr)
    except (ValueError, TypeError):
        response.status = 400
        return "Parâmetros inválidos. Use /run_competition_custom?nreno=2&nbbr=3"

    comando = f'make run-competition RENO={reno} BBR={bbr}'
    return run_cmd(f'vagrant ssh -c "cd bufferbloat && {comando}"')



@route('/listar_graficos')
def listar_graficos():
    base_dir = BUFFERBLOAT_DIR
    resultados = {}

    if os.path.isdir(base_dir):
        for pasta in sorted(os.listdir(base_dir)):
            subdir = os.path.join(base_dir, pasta, "graficos")
            if os.path.isdir(subdir):
                graficos = {"bbr": [], "reno": []}
                for f in sorted(os.listdir(subdir)):
                    if not f.endswith(".png"):
                        continue

                    nome = f.lower()
                    if nome.startswith("bbr-") or "bbr" in nome:
                        graficos["bbr"].append(f)
                    elif nome.startswith("reno-") or "reno" in nome:
                        graficos["reno"].append(f)

                resultados[pasta] = graficos

    response.content_type = "application/json"
    return json.dumps(resultados, indent=2)


@route('/listar_graficos_competition')
def listar_graficos_competition():
    base_dir = COMPETITION_DIR
    resultados = {}

    if os.path.isdir(base_dir):
        for cenario in sorted(os.listdir(base_dir)):
            subdir = os.path.join(base_dir, cenario, "graficos")
            if not os.path.isdir(subdir):
                continue

            dados = {"fluxos": {}, "gerais": []}
            for nome in sorted(os.listdir(subdir)):
                if not nome.endswith(".png"):
                    continue

                if any(prefixo in nome for prefixo in ["bbr", "reno"]):
                    match = re.match(r"(bbr|reno)(\d+)-", nome)
                    if match:
                        fluxo = f"{match.group(1)}{match.group(2)}"
                        dados["fluxos"].setdefault(fluxo, []).append(nome)
                    else:
                        dados["gerais"].append(nome)
                else:
                    dados["gerais"].append(nome)

            resultados[cenario] = dados

    response.content_type = "application/json"
    return json.dumps(resultados, indent=2)




@route('/grafico/<cenario>/<filename>')
def serve_named_grafico(cenario, filename):
    base_path = os.path.join(BUFFERBLOAT_DIR, f"{cenario}/graficos/{filename}")
    if os.path.exists(base_path):
        response.set_header('Cache-Control', 'no-store')
        return static_file(filename, root=os.path.dirname(base_path), mimetype="image/png")
    else:
        response.status = 404
        return f"<p>Gráfico {filename} não encontrado no cenário {cenario}.</p>"

from urllib.parse import unquote

@route('/grafico_competition/<cenario>/<filename:path>')
def serve_grafico_competition(cenario, filename):
    filename = unquote(filename.split('?')[0])  # <-- remove o ?t=...
    base_path = os.path.join(COMPETITION_DIR, f"{cenario}/graficos/{filename}")
    if os.path.exists(base_path):
        response.set_header('Cache-Control', 'no-store')
        return static_file(filename, root=os.path.dirname(base_path), mimetype="image/png")
    else:
        response.status = 404
        return f"<p>Gráfico {filename} não encontrado no cenário {cenario}.</p>"




if __name__ == '__main__':
    import sys
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run(host='localhost', port=porta, debug=True)
