#!/bin/bash

# Este script roda os experimentos de bufferbloat com diferentes tamanhos de fila
# comparando diferentes fluxos com controle de congestionamento diferentes.
# Deve ser chamado com: make run

# Garante que os binários locais do pip e o pacote Mininet estejam acessíveis
sudo kill -9 $(pgrep -f ovs-testcontroller) 2>/dev/null || true

export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="/home/vagrant/mininet:/home/vagrant/.local/lib/python3.8/site-packages:$PYTHONPATH"

# Parâmetros de simulação
time=50          # duração do experimento em segundos
bwnet=1.5        # banda do link em Mbps
delay=20           # atraso de cada link em ms (5ms + 5ms = 10ms RTT)
iperf_port=5001  # porta padrão do iperf3


RENO=${1:-2}  # padrão = 2
BBR=${2:-2}   # padrão = 2

# Limpa execuções anteriores do Mininet e reinicia OVS
sudo pkill -9 -f competition.py || true
sudo mn -c
for ns in $(ip netns list | cut -d ' ' -f1); do
  sudo ip netns delete "$ns" 2>/dev/null
done

sudo systemctl restart openvswitch-switch
sudo sync && sudo sysctl -w vm.drop_caches=3

# Mostra uso de memória antes do experimento
free -m

# Loop sobre diferentes tamanhos de fila (buffer)
for qsize in 20 100; do
    dir=competition/bb-q$qsize
    rm -rf "$dir" 2>/dev/null
    # Cria diretório e remove arquivos antigos
    mkdir -p "$dir"
    mkdir -p "$dir/graficos"


    # Executa o experimento com o script principal
    python3 competition.py -t $time \
    -b $bwnet --delay $delay --maxq $qsize --dir "$dir" \
    --reno $RENO \
    --bbr $BBR



  for ((i=0; i < BBR; i++)); do


      # Gera gráficos com base nos logs
      python3 plot_ping.py  -f "$dir/bbr$i-ping.txt" -o "$dir/graficos/bbr$i-rtt-q$qsize.png"


  done


  for ((i=0; i < RENO; i++)); do


      # Gera gráficos com base nos logs
      python3 plot_ping.py  -f "$dir/reno$i-ping.txt" -o "$dir/graficos/reno$i-rtt-q$qsize.png"


  done

  python3 plot_queue.py -f "$dir/q.txt" -o "$dir/graficos/buffer-q$qsize.png"

  python3 plot_throughput.py -d "$dir" --bwnet $bwnet -o "$dir/graficos/throughput-q$qsize.png"

  python3 plot_efic_fairness.py -d "$dir" --bwnet $bwnet -o "$dir/graficos/eficiencia_fairness-q$qsize.png"

  python3 plot_perdas.py -d "$dir" -o "$dir/graficos/perdas-q$qsize.png"

done
