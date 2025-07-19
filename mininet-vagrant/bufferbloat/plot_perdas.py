import os
import glob
import argparse
import matplotlib.pyplot as plt
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('--dir', '-d',
                    help="Diretório com arquivos de perda",
                    required=True)
parser.add_argument('--out', '-o',
                    help="Arquivo de saída PNG para o histograma",
                    default="perdas.png")

args = parser.parse_args()

def contar_perdas_cumulativas(fname):
    with open(fname, 'r') as f:
        linhas = [int(l.strip()) for l in f if l.strip().isdigit()]
        if len(linhas) < 2:
            return 0
        return linhas[-1] - linhas[0]  # diferença acumulada

# Buscar arquivos de perda
arquivos = glob.glob(os.path.join(args.dir, "*-perdas.txt"))

# Coletar perdas por fluxo
perdas_por_fluxo = {}
perdas_reno = []
perdas_bbr = []

for arq in arquivos:
    nome = os.path.basename(arq).replace("-perdas.txt", "")
    perdas = contar_perdas_cumulativas(arq)
    perdas_por_fluxo[nome] = perdas
    if "reno" in nome:
        perdas_reno.append(perdas)
    elif "bbr" in nome:
        perdas_bbr.append(perdas)

# Dados para histograma
labels = list(perdas_por_fluxo.keys())
valores = list(perdas_por_fluxo.values())

# Gráfico
plt.figure(figsize=(10, 5))
plt.bar(labels, valores, color=['skyblue' if 'reno' in l else 'lightcoral' for l in labels])
if perdas_reno:
    plt.axhline(np.mean(perdas_reno), color='blue', linestyle='--', label=f'Média Reno ({np.mean(perdas_reno):.2f})')
if perdas_bbr:
    plt.axhline(np.mean(perdas_bbr), color='red', linestyle='--', label=f'Média BBR ({np.mean(perdas_bbr):.2f})')
plt.title("Histograma de Perdas TCP (baseado em retransmissões cumulativas)")
plt.xlabel("Fluxo")
plt.ylabel("Bytes retransmitidos")
plt.xticks(rotation=45)
plt.grid(True, axis='y', linestyle='--', alpha=0.7)
plt.legend()
plt.tight_layout()

plt.savefig(args.out)
