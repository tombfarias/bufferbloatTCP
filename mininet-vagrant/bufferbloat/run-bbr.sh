#!/bin/bash

# Este script roda os experimentos de bufferbloat com diferentes tamanhos de fila.
# Deve ser chamado com: make run

# Garante que os binários locais do pip e o pacote Mininet estejam acessíveis
sudo kill -9 $(pgrep -f ovs-testcontroller) 2>/dev/null || true

export PATH="$HOME/.local/bin:$PATH"
export PYTHONPATH="/home/vagrant/mininet:/home/vagrant/.local/lib/python3.8/site-packages:$PYTHONPATH"

# Parâmetros de simulação
time=90          # duração do experimento em segundos
bwnet=1.5        # banda do link em Mbps
delay=5       # atraso de cada link em ms (5ms + 5ms = 10ms RTT)
iperf_port=5001  # porta padrão do iperf3

# Limpa execuções anteriores do Mininet e reinicia OVS
sudo pkill -9 -f bufferbloat.py || true
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
    dir=bb-q$qsize

    # Cria diretório e remove arquivos antigos
    mkdir -p "$dir"
    mkdir -p "$dir/graficos"

    rm -f "$dir/q.txt" "$dir/bbr-q.txt" "$dir/bbr-ping.txt" "$dir/web.txt" 2>/dev/null

    touch "$dir/bbr-q.txt"
    touch "$dir/bbr-ping.txt"
    touch "$dir/web.txt"

    # Executa o experimento com o script principal
    python3 bufferbloat.py -t $time -b $bwnet --delay $delay --maxq $qsize --dir "$dir" \
    --cong bbr

    # Gera gráficos com base nos logs
    python3 plot_queue.py -f "$dir/bbr-q.txt" -o "$dir/graficos/bbr-buffer-q$qsize.png"
    python3 plot_ping.py  -f "$dir/bbr-ping.txt" -o "$dir/graficos/bbr-rtt-q$qsize.png"
done
