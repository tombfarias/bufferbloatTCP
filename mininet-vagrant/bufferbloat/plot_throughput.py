# plot_throughput.py
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
                    required=True)
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
                    taxa /= 1e6
                elif unidade == "kbits/sec":
                    taxa /= 1e3
                elif unidade == "mbits/sec":
                    pass
                elif unidade == "gbits/sec":
                    taxa *= 1e3
                else:
                    continue
                tempos.append(tempo_medio)
                vazoes.append(taxa)
            except:
                continue
    return tempos, vazoes

def agrupar_por_tempo(lista_de_series):
    conjunto_tempos = set.intersection(*[set(t) for (t, _) in lista_de_series])
    agrupado = defaultdict(list)
    for t in sorted(conjunto_tempos):
        for tempos, valores in lista_de_series:
            idx = tempos.index(t)
            agrupado[t].append(valores[idx])
    return agrupado

arquivos_bbr = []
arquivos_reno = []
for d in args.dir:
    padrao = os.path.join(d, "*-vazao.txt")
    arquivos = glob.glob(padrao)
    arquivos_bbr += [f for f in arquivos if "bbr" in os.path.basename(f).lower()]
    arquivos_reno += [f for f in arquivos if "reno" in os.path.basename(f).lower()]

series_bbr = [parse_vazao_com_tempo(f) for f in arquivos_bbr]
series_reno = [parse_vazao_com_tempo(f) for f in arquivos_reno]

bbr_agrupado = agrupar_por_tempo(series_bbr)
reno_agrupado = agrupar_por_tempo(series_reno)

tempos_comuns = sorted(bbr_agrupado.keys())
fairness_pontos = []
for t in tempos_comuns:
    if reno_agrupado[t] and bbr_agrupado[t]:
        fairness_pontos.append((
            np.mean(reno_agrupado[t]),
            np.mean(bbr_agrupado[t])
        ))

if len(fairness_pontos) < 2:
    print("[AVISO] Dados insuficientes para plotar trajetória de fairness.")
    exit(0)

xs, ys = zip(*fairness_pontos)
plt.figure(figsize=(6, 6))
plt.plot(xs, ys, color='red', linewidth=1, marker='o')

step = 10
xs_s = xs[::step]
ys_s = ys[::step]
colors = cm.plasma(np.linspace(0, 1, len(xs_s)))
for i in range(len(xs_s) - 1):
    plt.arrow(xs_s[i], ys_s[i],
              xs_s[i + 1] - xs_s[i], ys_s[i + 1] - ys_s[i],
              color=colors[i],
              width=0.002, head_width=0.015, head_length=0.03,
              length_includes_head=True)

plt.scatter(xs_s, ys_s, c=colors, cmap='plasma', s=20)
plt.scatter(xs_s[0], ys_s[0], color='blue', label='Início', zorder=5)
plt.scatter(xs_s[-1], ys_s[-1], color='green', label='Fim', zorder=5)

R = float(args.bwnet)
n = len(series_reno)
m = len(series_bbr)
# agora considera n·x + m·y = R
x_vals = np.linspace(0, R / n, 200)
y_vals = (R - n * x_vals) / m
plt.plot(x_vals, y_vals, 'k-', label=f'Uso total da banda (n·x + m·y = {R})')

plt.plot([0, R], [0, R], 'k--', label='Fair Share (x = y)')
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
