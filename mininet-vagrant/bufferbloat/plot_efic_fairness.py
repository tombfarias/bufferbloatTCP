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

R = float(args.bwnet) # Largura da banda em Mbits/s

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


# ... [tudo antes continua igual]

eff_fair = []
tempos_validos = []
for t, (r, b) in zip(tempos_em_comum, fairness_pontos):
    if r == 0 and b == 0:
        continue
    eficiencia = (r + b) / R # O quanto de banda está efetivamente sendo usado
    fairness = ((r + b)**2) / (2 * (r**2 + b**2))
    eff_fair.append((eficiencia, fairness))
    tempos_validos.append(t)

if len(eff_fair) < 2:
    print("[AVISO] Dados insuficientes para plotar trajetória de fairness.")
    exit(0)

fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

xs, ys = zip(*eff_fair)
zs = tempos_validos  # <- aqui estava o erro

sc = ax.scatter(xs, ys, zs, c=zs, cmap='viridis', s=60, edgecolors='k')
ax.set_xlabel("Eficiência(t)")
ax.set_ylabel("Fairness(t)")
ax.set_zlabel("Tempo (s)")
ax.set_title("Eficiência vs Fairness vs Tempo")
fig.colorbar(sc, ax=ax, label="Tempo (s)")
plt.tight_layout()

if args.out:
    plt.savefig(args.out, bbox_inches='tight')
else:
    plt.show()
