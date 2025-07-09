# webcontrol/app.py
from bottle import TEMPLATE_PATH, route, run, template, static_file, response
import subprocess
import os
import json

# Caminhos corretos
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VAGRANT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../mininet-vagrant"))
BUFFERBLOAT_DIR = os.path.join(VAGRANT_DIR, "bufferbloat")
LOG_FILE = os.path.join(BUFFERBLOAT_DIR, "experimento.log")
GRAFICO_FILE = os.path.join(BUFFERBLOAT_DIR, "grafico.png")

# Garante que os templates serão buscados na pasta correta
TEMPLATE_PATH.insert(0, os.path.join(SCRIPT_DIR, 'views'))

def run_cmd(cmd, cwd=VAGRANT_DIR):
    """Executa comando shell e captura a saída"""
    try:
        result = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
        if result.returncode != 0:
            return f"[ERRO - Código {result.returncode}]\n{output}"
        return output
    except Exception as e:
        return f"[EXCEÇÃO]\n{str(e)}"


@route('/')
def index():
    return template('index', vagrant_dir=VAGRANT_DIR)


@route('/static/<filename>')
def server_static(filename):
    return static_file(filename, root=os.path.join(SCRIPT_DIR, 'static'))


@route('/up')
def vagrant_up():
    status = run_cmd("vagrant status")
    if "running" in status:
        return {'output': "🔄 VM já está em execução.\n\n" + status}
    output = run_cmd("vagrant up")
    return {'output': output}


@route('/status')
def vagrant_status():
    output = run_cmd("vagrant status")
    return {'output': output}


@route('/ssh')
def ssh_ping():
    output = run_cmd('vagrant ssh -c "ping -c 4 8.8.8.8"')
    return {'output': output}


@route('/run_reno')
def run_reno():
    output = run_cmd('vagrant ssh -c "cd bufferbloat && make run-reno"')
    return {'output': output}


@route('/run_bbr')
def run_bbr():
    output = run_cmd('vagrant ssh -c "cd bufferbloat && make run-bbr"')
    return {'output': output}


@route('/listar_graficos')
def listar_graficos():
    base_dir = os.path.join(SCRIPT_DIR, "../mininet-vagrant/bufferbloat")
    resultados = {}

    if os.path.isdir(base_dir):
        for pasta in sorted(os.listdir(base_dir)):
            subdir = os.path.join(base_dir, pasta, "graficos")
            if os.path.isdir(subdir):
                graficos = {"bbr": [], "reno": [], "outros": []}
                for f in sorted(os.listdir(subdir)):
                    if not f.endswith(".png"):
                        continue
                    if f.startswith("bbr-"):
                        graficos["bbr"].append(f)
                    elif f.startswith("reno-"):
                        graficos["reno"].append(f)
                    else:
                        graficos["outros"].append(f)
                resultados[pasta] = graficos

    response.content_type = "application/json"
    return json.dumps(resultados, indent=2)


@route('/grafico/<cenario>/<filename>')
def serve_named_grafico(cenario, filename):
    base_path = os.path.join(SCRIPT_DIR, f"../mininet-vagrant/bufferbloat/{cenario}/graficos/{filename}")
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
