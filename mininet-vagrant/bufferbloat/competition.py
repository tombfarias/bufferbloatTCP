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
                     default=2
                     )


parser.add_argument('--bbr',
                     type=int,
                     help='Amount of TCP BBR flows',
                     default=2
                     )




# Expt parameters
args = parser.parse_args()

os.makedirs(args.dir, exist_ok=True)

class BBTopo(Topo):
    "Simple topology for bufferbloat experiment."

    def build(self, n=2):
        # TODO: create two hosts

        self.renos = []
        self.bbrs = []

        for i in range(args.reno):
            self.renos.append(self.addHost(f'r{i}')) # Computadores domésticos para fluxo reno

        for i in range(args.bbr):
            self.bbrs.append(self.addHost(f'b{i}')) # Computadores domésticos para fluxo bbr

        s = self.addHost('s') # Servidor


        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        roteador = self.addSwitch('s0')

        self.addLink('s', roteador, # Definindo a implementação da fila na
                                    # interface de rede do servidor (todos os hospedeiros vão competir por essa fila)
                    bw=args.bwnet, 
                    delay="%sms" % args.delay, 
                    max_queue_size=args.maxq,
                    use_htb=True)



        # TODO: Add links with appropriate characteristics
        for i in self.renos:

            self.addLink(i, roteador, 
                        bw=args.bwhost, 
                        delay="%sms" % args.delay,
                        use_htb=True)

        for i in self.bbrs:

            self.addLink(i, roteador, 
                        bw=args.bwhost, 
                        delay="%sms" % args.delay,
                        use_htb=True)



        print(roteador)


# Simple wrappers around monitoring utilities.  You are welcome to
# contribute neatly written (using classes) monitoring scripts for
# Mininet!

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
    # For those who are curious about the -w 16m parameter, it ensures
    # that the TCP flow is not receiver window limited.  If it is,
    # there is a chance that the router buffer may not get filled up.
    servidor = s.popen("iperf -s -w 16m")

    # TODO: Start the iperf client on h1.  Ensure that you create a
    # long lived TCP flow.
    proc_clientes = []
    arquivos = []
    for cliente in hospedeiros:
        arquivo = open(f"{args.dir}/{nomeArquivo(cliente)}-vazao.txt", "w")
        arquivos.append(arquivo)
        proc_clientes.append(cliente.popen(f"iperf -c {s.IP()} -t {args.time} -i 1",
                                           stdout=arquivo,
                                           universal_newlines=True
                                           
                                           ))


    print("iperf server running successfully!")


    return servidor, proc_clientes, arquivos


def start_qmon(iface, interval_sec=0.1, outfile=f"{args.dir}/q.txt"):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_ping(h1, h2, ping_file):
    # TODO: Start a ping train from h1 to h2 (or h2 to h1, does it
    # matter?)  Measure RTTs every 0.1 second.  Read the ping man page
    # to see how to do this.

    # pings


    info(f"* Starting ping train {h1}->{h2}...\n")
    ping_c_to_s = h1.popen(f"ping -D -i 0.1 {h2.IP()} > {ping_file}", shell=True) 


    return ping_c_to_s

    # Hint: Use host.popen(cmd, shell=True).  If you pass shell=True
    # to popen, you can redirect cmd's output using shell syntax.
    # i.e. ping ... > /path/to/ping.
    

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

        # Lança todos os processos antes
        processos = []
        tipos = []

        for cliente in clientes:
            tipo = getTipo(cliente)
            proc = cliente.popen(f"curl -o {pagina_local}  -w %{{time_total}} -s {endereco_servidor}", stdout=PIPE)
            stats = cliente.cmd("ss -ti dst %s" % servidor.IP())
            match = re.search(r'retrans:\s*(\d+)', stats)
            if match:
                perdas = int(match.group(1))
            else:
                perdas = 0

            nome = nomeArquivo(cliente)
            with open(f"{args.dir}/{nome}-perdas.txt", "a") as f:
                f.write(f"{perdas}\n")

            processos.append(proc)
            tipos.append(tipo)

        # Aguarda todos os processos juntos
        for proc, tipo in zip(processos, tipos):
            output = float(proc.communicate()[0].decode().strip())
            tempos[tipo].append(output)



def competition():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)



    topo = BBTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink) 
    net.start()    

    renos = getRenos(net)
    bbrs = getBBRs(net)
    clientes = getHospedeiros(net)
    servidor = getServidor(net)

    # Set TPC CC algorith
    for host in renos:
        host.cmd("sysctl -w net.ipv4.tcp_congestion_control=reno")

    for host in bbrs:
        host.cmd("sysctl -w net.ipv4.tcp_congestion_control=bbr")


    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)

    # This performs a basic all pairs ping test.
    net.pingAll()


    # TODO: Start monitoring the queue sizes.  Since the switch I
    # created is "s0", I monitor one of the interfaces.  Which
    # interface?  The interface numbering starts with 1 and increases.
    # Depending on the order you add links to your network, this
    # number may be 1 or 2.  Ensure you use the correct number.
    qmon = start_qmon(iface=net.get('s0').connectionsTo(servidor)[0][0].name,
                      outfile=f'{args.dir}/q.txt'
                      )

    

    # TODO: Start iperf, webservers, etc.
    iperf_servidor, iperf_clientes, iperf_arquivos = start_iperf(net) # Conexão tcp contínua
    web = start_webserver(servidor)


    # TODO: measure the time it takes to complete webpage transfer
    # from h1 to h2 (say) 3 times.  Hint: check what the following
    # command does: curl -o /dev/null -s -w %{time_total} google.com
    # Now use the curl command to fetch webpage from the webserver you
    # spawned on host h1 (not from google!)
    # reno
    # Hint: Verify the url by running your curl command without the
    # flags. The html webpage should be returned as the response.
   

    
    # Hint: have a separate function to do this and you may find the
    # loop below useful.
    pings = [start_ping(cliente, servidor, f'{args.dir}/{nomeArquivo(cliente)}-ping.txt') for cliente in clientes]

    tempos = dict()
    tempos['bbr'] = []
    tempos['reno'] = []

    amostras_por_grupo = 30 # Análise estatística robusta

    start_time = time()
    for _ in range(amostras_por_grupo):

        # 3 vezes a cada 5 segundos (será que era para dividir
        # igualmente o tempo?)


        # Colocar as 3 páginas pra buscar ao mesmo tempo
        pegar_pagina(net, clientes, tempos)


        # ****************************************************************************

        # Colocar as 3 páginas pra buscar ao mesmo tempo
        pegar_pagina(net, clientes, tempos)


        # ***********************************************************

        # Colocar as 3 páginas pra buscar ao mesmo tempo
        pegar_pagina(net, clientes, tempos)


        sleep(5)
        now = time()
        delta = now - start_time
        if delta > args.time: # Esgotou o tempo limite
            print("Teste encerrado")
            break
        print("%.1fs left..." % (args.time - delta))


    # =====================================================================


    # Encerra pings
    for ping in pings:
        ping.terminate()

    # Encerra as conexões tcp dos clientes
    for cliente in iperf_clientes:
        cliente.terminate()

    for arquivo in iperf_arquivos:
        arquivo.close()


    # Encerra as conexões tcp do servidor (?)
    iperf_servidor.terminate()
    qmon.terminate()
    for p in web:
        p.terminate()

    # Fecha rede
    net.stop()

    # TODO: compute average (and standard deviation) of the fetch
    # times.  You don't need to plot them.  Just note it in your
    # README and explain.

    local_salvar_bbr = os.path.join(args.dir, 'graficos', 'bbr',f'grafico-tempos-distribuicao-bbr-q{args.maxq}.png')
    local_salvar_reno = os.path.join(args.dir, 'graficos', 'reno',f'grafico-tempos-distribuicao-reno-q{args.maxq}.png')

    tempos['bbr'] = np.array(tempos['bbr'])
    tempos['reno'] = np.array(tempos['reno'])

    # Plotar gráfico e salvar
    # plotar_tempos(tempos['bbr'], local_salvar_bbr)
    # plotar_tempos(tempos['reno'], local_salvar_reno)


    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    competition()
