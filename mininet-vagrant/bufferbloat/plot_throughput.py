import os
import glob
import argparse
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from collections import defaultdict
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--dir', '-d',
                    help="Diretório(s) com arquivos de vazão iperf",
                    required=True,
                    nargs='+')
parser.add_argument('--bwnet',
                    help="Largura de banda do servidor em Mbits/s",
                    required=True,
                    )

parser.add_argument('--out', '-o',
                    help="Arquivo de saída PNG para o gráfico",
                    default=None)

args = parser.parse_args()

def parse_vazao_com_tempo(fname):
    tempos = []
    vazoes = []
    with open(fname, 'r') as f:
        for line in f:
            if "sec" not in line or "/sec" not in line:
                continue
            try:
                tokens = line.strip().split()
                intervalo = tokens[2]  # ex: "0.0-1.0"
                start, end = map(float, intervalo.split('-'))
                tempo_medio = (start + end) / 2

                taxa = float(tokens[-2])
                unidade = tokens[-1].lower()
                if unidade == "bits/sec":
                    taxa = taxa / 1e6
                elif unidade == "kbits/sec":
                    taxa = taxa / 1e3
                elif unidade == "mbits/sec":
                    pass
                elif unidade == "gbits/sec":
                    taxa = taxa * 1e3
                else:
                    continue

                tempos.append(tempo_medio)
                vazoes.append(taxa)
            except:
                continue
    return tempos, vazoes


def agrupar_por_tempo(lista_de_series):
    """Converte listas [(tempos, vazoes), ...] em dicionário tempo → lista de valores"""
    conjunto_tempos = set.intersection(*[set(t) for (t, _) in lista_de_series])
    agrupado = defaultdict(list)
    for t in sorted(conjunto_tempos):
        for tempos, valores in lista_de_series:
            idx = tempos.index(t)
            agrupado[t].append(valores[idx])
    return agrupado

# Carrega todos os arquivos
arquivos_bbr = []
arquivos_reno = []

for d in args.dir:
    padrao = os.path.join(d, "*-vazao.txt")
    arquivos = glob.glob(padrao)
    arquivos_bbr.extend([f for f in arquivos if "bbr" in os.path.basename(f).lower()])
    arquivos_reno.extend([f for f in arquivos if "reno" in os.path.basename(f).lower()])


series_bbr = [parse_vazao_com_tempo(f) for f in arquivos_bbr]
series_reno = [parse_vazao_com_tempo(f) for f in arquivos_reno]

# Agrupar por tempo
bbr_agrupado = agrupar_por_tempo(series_bbr)
reno_agrupado = agrupar_por_tempo(series_reno)

# Gerar trajetória fairness
tempos_em_comum = sorted(bbr_agrupado.keys())
fairness_pontos = []
for t in tempos_em_comum:
    if reno_agrupado[t] and bbr_agrupado[t]:
        fairness_pontos.append((
            np.mean(reno_agrupado[t]),
            np.mean(bbr_agrupado[t])
        ))

if len(fairness_pontos) < 2:
    print("[AVISO] Dados insuficientes para plotar trajetória de fairness.")
    exit(0)  # ou continue se estiver dentro de um loop

xs, ys = zip(*fairness_pontos)
plt.figure(figsize=(6, 6))
plt.plot(xs, ys, color='red', linewidth=1, marker='o')

step = 10
xs = xs[::step]
ys = ys[::step]
colors = cm.plasma(np.linspace(0, 1, len(xs)))
# Trajetória com cor variando no tempo
for i in range(len(xs) - 1):
    plt.arrow(xs[i], ys[i],
              xs[i + 1] - xs[i], ys[i + 1] - ys[i],
              color=colors[i],
              width=0.002, head_width=0.015, head_length=0.03,
              length_includes_head=True)

# Pontos discretos ao longo da trajetória
plt.scatter(xs, ys, c=colors, cmap='plasma', s=20)
plt.scatter(xs[0], ys[0], color='blue', label='Início', zorder=5)
plt.scatter(xs[-1], ys[-1], color='green', label='Fim', zorder=5)


R = float(args.bwnet)  # largura de banda total da rede em Mbits/s

# Linha de justiça: x = y
plt.plot([0, R], [0, R], 'k--', label='Fair Share (x = y)')

# Linha de eficiência total: x + y = R ⇒ y = R - x
x_vals = np.linspace(0, R, 100)
y_vals = R - x_vals
plt.plot(x_vals, y_vals, 'k-', label=f'Uso total da banda (x + y = {R})')


plt.xlabel("Throughput médio Reno (Mbits/s)")
plt.ylabel("Throughput médio BBR (Mbits/s)")
plt.title("Fairness")
plt.legend()
plt.grid(True)
plt.axis('equal')
if args.out:
    plt.savefig(args.out, bbox_inches='tight')
else:
    plt.show()
