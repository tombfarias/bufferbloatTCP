# competition.py
from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
import seaborn as sns
import re

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

from monitor import monitor_qlen

import sys
import os
import math

import random
import numpy as np
import matplotlib.pyplot as plt

parser = ArgumentParser(description="Bufferbloat tests")
parser.add_argument('--bwhost', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)
parser.add_argument('--bwnet', '-b',
                    type=float,
                    help="Bandwidth of bottleneck (network) link (Mb/s)",
                    required=True)
parser.add_argument('--delay',
                    type=float,
                    help="Link propagation delay (ms)",
                    required=True)
parser.add_argument('--dir', '-d',
                    help="Directory to store outputs",
                    required=True)
parser.add_argument('--time', '-t',
                    help="Duration (sec) to run the experiment",
                    type=int,
                    default=10)
parser.add_argument('--maxq',
                    type=int,
                    help="Max buffer size of network interface in packets",
                    default=100)
parser.add_argument('--reno',
                    type=int,
                    help='Amount of TCP Reno flows',
                    default=2)
parser.add_argument('--bbr',
                    type=int,
                    help='Amount of TCP BBR flows',
                    default=2)

args = parser.parse_args()
os.makedirs(args.dir, exist_ok=True)

class BBTopo(Topo):
    "Simple topology for bufferbloat experiment."

    def build(self, n=2):
        self.renos = []
        self.bbrs = []

        for i in range(args.reno):
            self.renos.append(self.addHost(f'r{i}'))

        for i in range(args.bbr):
            self.bbrs.append(self.addHost(f'b{i}'))

        s = self.addHost('s')
        roteador = self.addSwitch('s0')

        # -- Link de gargalo: usando TBF (shape estrito), sem bursts inesperados --
        self.addLink('s', roteador,
                     bw=args.bwnet,
                     delay=f"{args.delay}ms",
                     max_queue_size=args.maxq)

        # links dos hosts clientes (Reno e BBR) ao roteador
        for i in self.renos + self.bbrs:
            self.addLink(i, roteador,
                         bw=args.bwhost,
                         delay=f"{args.delay}ms",
                         use_htb=True)

def getRenos(net):
    return [net.get(f"r{i}") for i in range(args.reno)]

def getBBRs(net):
    return [net.get(f"b{i}") for i in range(args.bbr)]

def getServidor(net):
    return net.get("s")

def getTipo(host):
    if host.name.startswith("r"):
        return "reno"
    elif host.name.startswith("b"):
        return "bbr"
    else:
        return "servidor"

def getHospedeiros(net):
    return getRenos(net) + getBBRs(net)

def nomeArquivo(cliente):
    tipo = getTipo(cliente)
    numero = int(''.join(filter(str.isdigit, cliente.name)))
    return f'{tipo}{numero}'

def start_iperf(net):
    s = net.get('s')
    hospedeiros = getHospedeiros(net)

    print("Starting iperf server...")
    servidor = s.popen("iperf -s -w 16m")

    proc_clientes = []
    arquivos = []
    for cliente in hospedeiros:
        arquivo = open(f"{args.dir}/{nomeArquivo(cliente)}-vazao.txt", "w")
        arquivos.append(arquivo)
        # -O 2: pula 2s de aquecimento; -i 0.5: janelas de 0.5s
        cmd = f"iperf -c {s.IP()} -t {args.time} -O 2 -i 0.5 -w 16m"
        proc_clientes.append(cliente.popen(cmd,
                                           stdout=arquivo,
                                           universal_newlines=True))
    print("iperf server running successfully!")
    return servidor, proc_clientes, arquivos

def start_qmon(iface, interval_sec=0.1, outfile=f"{args.dir}/q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_ping(h1, h2, ping_file):
    info(f"* Starting ping train {h1}->{h2}...\n")
    return h1.popen(f"ping -D -i 0.1 {h2.IP()} > {ping_file}", shell=True)

def start_webserver(servidor):
    info(f"* Starting webserver on {servidor}...\n")
    proc = servidor.popen("python webserver.py", shell=True)
    sleep(1)
    print(f"webpage ready: {proc}")
    return [proc]

def pegar_pagina(net, clientes, tempos):
    servidor = getServidor(net)
    pagina_local = f'{args.dir}/web.txt'
    endereco_servidor = f'http://{servidor.IP()}:8080/index.html'

    processos = []
    tipos = []
    for cliente in clientes:
        tipo = getTipo(cliente)
        proc = cliente.popen(f"curl -o {pagina_local} -w %{{time_total}} -s {endereco_servidor}",
                             stdout=PIPE, shell=True)
        stats = cliente.cmd("ss -ti dst %s" % servidor.IP())
        match = re.search(r'retrans:\s*(\d+)', stats)
        perdas = int(match.group(1)) if match else 0
        with open(f"{args.dir}/{nomeArquivo(cliente)}-perdas.txt", "a") as f:
            f.write(f"{perdas}\n")
        processos.append(proc)
        tipos.append(tipo)

    for proc, tipo in zip(processos, tipos):
        output = float(proc.communicate()[0].decode().strip())
        tempos[tipo].append(output)

def competition():
    topo = BBTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()

    renos = getRenos(net)
    bbrs = getBBRs(net)
    clientes = getHospedeiros(net)
    servidor = getServidor(net)

    # Define CC
    for h in renos:
        h.cmd("sysctl -w net.ipv4.tcp_congestion_control=reno")
    for h in bbrs:
        h.cmd("sysctl -w net.ipv4.tcp_congestion_control=bbr")

    dumpNodeConnections(net.hosts)
    net.pingAll()

    # Inicia monitor de fila (escolha a interface correta)
    iface = net.get('s0').connectionsTo(servidor)[0][0].name
    qmon = start_qmon(iface=iface, outfile=f'{args.dir}/q.txt')

    iperf_servidor, iperf_clientes, iperf_arquivos = start_iperf(net)
    web = start_webserver(servidor)
    pings = [start_ping(c, servidor, f'{args.dir}/{nomeArquivo(c)}-ping.txt')
             for c in clientes]

    tempos = {'bbr': [], 'reno': []}
    amostras_por_grupo = 30
    start_time = time()
    for _ in range(amostras_por_grupo):
        pegar_pagina(net, clientes, tempos)
        pegar_pagina(net, clientes, tempos)
        pegar_pagina(net, clientes, tempos)
        sleep(5)
        if time() - start_time > args.time:
            print("Teste encerrado")
            break
        print(f"{args.time - (time() - start_time):.1f}s left...")

    for ping in pings: ping.terminate()
    for c in iperf_clientes: c.terminate()
    for f in iperf_arquivos: f.close()
    iperf_servidor.terminate()
    qmon.terminate()
    for p in web: p.terminate()
    net.stop()
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    competition()
