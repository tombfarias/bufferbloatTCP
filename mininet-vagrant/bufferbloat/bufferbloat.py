from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.log import lg, info
from mininet.util import dumpNodeConnections
from mininet.cli import CLI
import seaborn as sns

from subprocess import Popen, PIPE
from time import sleep, time
from multiprocessing import Process
from argparse import ArgumentParser

from monitor import monitor_qlen

import sys
import os
import math

import numpy as np
import matplotlib.pyplot as plt

parser = ArgumentParser(description="Bufferbloat tests")
parser.add_argument('--bw-host', '-B',
                    type=float,
                    help="Bandwidth of host links (Mb/s)",
                    default=1000)

parser.add_argument('--bw-net', '-b',
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





# Linux uses CUBIC-TCP by default that doesn't have the usual sawtooth
# behaviour.  For those who are curious, invoke this script with
# --cong cubic and see what happens...
# sysctl -a | grep cong should list some interesting parameters.
parser.add_argument('--cong',
                    help="Congestion control algorithm to use",
                    default="reno") # Começaremos com o reno

# Expt parameters
args = parser.parse_args()

os.makedirs(args.dir, exist_ok=True)

class BBTopo(Topo):
    "Simple topology for bufferbloat experiment."

    def build(self, n=2):
        # TODO: create two hosts
        h1 = self.addHost('h1') # Computador doméstico
        h2 = self.addHost('h2') # Servidor
 

        # Here I have created a switch.  If you change its name, its
        # interface names will change from s0-eth1 to newname-eth1.
        roteador = self.addSwitch('s0')



        # TODO: Add links with appropriate characteristics
        self.addLink(h1, roteador, 
                     bw=1000, 
                     delay="%sms" % args.delay,
                     use_htb=True)
        self.addLink(h2, roteador, 
                     bw=1.5, 
                     delay="%sms" % args.delay, 
                     max_queue_size=args.maxq,
                     )



        print(roteador)


# Simple wrappers around monitoring utilities.  You are welcome to
# contribute neatly written (using classes) monitoring scripts for
# Mininet!




def start_iperf(net):
    h1 = net.get('h1')
    h2 = net.get('h2')

    
    print("Starting iperf server...")
    # For those who are curious about the -w 16m parameter, it ensures
    # that the TCP flow is not receiver window limited.  If it is,
    # there is a chance that the router buffer may not get filled up.
    servidor = h2.popen("iperf -s -w 16m")

    # TODO: Start the iperf client on h1.  Ensure that you create a
    # long lived TCP flow.
    cliente = h1.popen(f"iperf -c {h1.IP()} -t {args.time} -i 1") 

    print("iperf server running successfully!")

    return servidor, cliente


def start_qmon(iface, interval_sec=0.1, outfile="%s-q.txt" % (args.cong)):
    monitor = Process(target=monitor_qlen,
                      args=(iface, interval_sec, outfile))
    monitor.start()
    return monitor

def start_ping(h1, h2):
    # TODO: Start a ping train from h1 to h2 (or h2 to h1, does it
    # matter?)  Measure RTTs every 0.1 second.  Read the ping man page
    # to see how to do this.

    # pings
    ping_c_to_s = h1.popen(f"ping -D -i 0.1 {h2.IP()} > {args.dir}/{args.cong}-ping.txt", shell=True)

    return ping_c_to_s

    # Hint: Use host.popen(cmd, shell=True).  If you pass shell=True
    # to popen, you can redirect cmd's output using shell syntax.
    # i.e. ping ... > /path/to/ping.
    

def start_webserver(net):
    servidor = net.get('h2')
    proc = servidor.popen("python webserver.py", shell=True)
    sleep(1)

    print(f"webpage ready: {proc}")
    return [proc]

# for _
def pegar_pagina(cliente, servidor):
        
        resultado = cliente.popen(f"curl -o {args.dir}/web.txt -s -w %{{time_total}} http://{servidor.IP()}/index.html",
                                  stdout=PIPE,
                                  )
        tempo = resultado.communicate()[0].decode().strip()

        print(tempo)
        return np.float32(tempo)

def plotar_tempos(tempos):

    plt.figure(figsize=(10, 5))

    # Histograma + KDE
    sns.histplot(tempos, bins=20, kde=True, color='skyblue', edgecolor='black')

    # Linha da média
    media = np.mean(tempos)
    plt.axvline(media, color='green', linestyle='--', label=f'Média = {media:.4f}s')

    plt.title('Distribuição dos Tempos de Download da Página index.html', fontsize=14)
    plt.xlabel('Tempo (s)', fontsize=12)
    plt.ylabel('Frequência', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'{args.dir}/graficos/grafico-tempos-distribuicao-q{args.maxq}.png')

def bufferbloat():
    if not os.path.exists(args.dir):
        os.makedirs(args.dir)
    os.system("sysctl -w net.ipv4.tcp_congestion_control=%s" % args.cong)
    topo = BBTopo()
    net = Mininet(topo=topo, host=CPULimitedHost, link=TCLink)
    net.start()
    # This dumps the topology and how nodes are interconnected through
    # links.
    dumpNodeConnections(net.hosts)

    # This performs a basic all pairs ping test.
    net.pingAll()


    servidor = net.get('h2')
    cliente = net.get('h1')

    # TODO: Start monitoring the queue sizes.  Since the switch I
    # created is "s0", I monitor one of the interfaces.  Which
    # interface?  The interface numbering starts with 1 and increases.
    # Depending on the order you add links to your network, this
    # number may be 1 or 2.  Ensure you use the correct number.
    qmon = start_qmon(iface=f's0-et{servidor}',
                      outfile='%s/%s-q.txt' % (args.dir, args.cong))


    # TODO: Start iperf, webservers, etc.
    iperf_servidor, iperf_cliente = start_iperf(net) # Conexão tcp contínua
    web = start_webserver(net)


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

    ping = start_ping(cliente, servidor)
    tempos = []
    start_time = time()
    while True:

        # 3 vezes a cada 5 segundos (será que era para dividir
        # igualmente o tempo?)

        tempo = pegar_pagina(cliente, servidor)
        tempos.append(tempo)

        tempo = pegar_pagina(cliente, servidor)
        tempos.append(tempo)

        tempo = pegar_pagina(cliente, servidor)
        tempos.append(tempo)

        sleep(5)
        now = time()
        delta = now - start_time
        if len(tempos) > 30 * 3 or delta > args.time:
            print("Teste encerrado")
            break
        print("%.1fs left..." % (args.time - delta))

    ping.terminate()

    # TODO: compute average (and standard deviation) of the fetch
    # times.  You don't need to plot them.  Just note it in your
    # README and explain.

    tempos = np.array(tempos)

    # Plotar gráfico e salvar
    plotar_tempos(tempos)


    # Hint: The command below invokes a CLI which you can use to
    # debug.  It allows you to run arbitrary commands inside your
    # emulated hosts h1 and h2.
    # CLI(net)

    # Encerrar todos os processos
    ping.terminate()
    iperf_cliente.terminate()
    iperf_servidor.terminate()
    qmon.terminate()
    for p in web:
        p.terminate()

    net.stop()

    # Ensure that all processes you create within Mininet are killed.
    # Sometimes they require manual killing.
    Popen("pgrep -f webserver.py | xargs kill -9", shell=True).wait()

if __name__ == "__main__":
    bufferbloat()
