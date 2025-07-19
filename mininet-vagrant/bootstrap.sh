#!/bin/bash

set -e  # Encerra imediatamente se algum comando falhar

FLAG="/home/vagrant/.provision_done"
REPORT="/home/vagrant/provision_report.txt"
DEBIAN_FRONTEND=noninteractive

# Verifica se o provisionamento já foi feito anteriormente
if [ -f "$FLAG" ]; then
    echo "Provisionamento já realizado anteriormente. Nada a fazer."
    exit 0
fi

echo "[Provisionamento] Iniciando..."

# Atualiza a lista de pacotes
sudo apt-get update -y

# Instala dependências básicas
sudo apt-get install -y \
   iperf python3-pip build-essential cgroup-tools \
   openvswitch-switch openvswitch-testcontroller help2man \
   net-tools curl git

# Remove Python 2, se ainda estiver presente
sudo apt-get remove -y python2 python2.7 python-pip || echo "[ok]"

# Corrige instalação anterior quebrada do pip
sudo pip uninstall -y mininet || true
sudo rm -f /usr/local/bin/mn


# Atualiza o pip do usuário e garante numpy/matplotlib locais
python3 -m pip install --user --upgrade pip
python3 -m pip install --user --no-cache-dir matplotlib numpy seaborn


# Mininet
cd /home/vagrant/mininet
if [ -f mnexec.c ]; then
    echo "[Provisionamento] Compilando mnexec manualmente..."
    gcc -Wall -Wextra -o mnexec mnexec.c
    sudo install -D mnexec /usr/local/bin/mnexec
    sudo chmod +s /usr/local/bin/mnexec
else
    echo "[Provisionamento] Arquivo mnexec.c não encontrado!"
fi

if [ -f mnexec.c ]; then
    echo "[Provisionamento] Compilando mnexec..."
    gcc -Wall -Wextra -o mnexec mnexec.c
    sudo install -D ./mnexec /usr/local/bin/mnexec
    sudo chmod +s /usr/local/bin/mnexec
else
    echo "[Erro] mnexec.c não encontrado!"
    exit 1
fi


if [ -f ./bin/mn ]; then
    sudo cp -v ./bin/mn /usr/local/bin/
    sudo chmod +x /usr/local/bin/mn
fi


if ! grep -q 'PYTHONPATH=' /home/vagrant/.bashrc; then
    echo 'export PYTHONPATH="/home/vagrant/mininet:/home/vagrant/.local/lib/python3.8/site-packages:$PYTHONPATH"' >> /home/vagrant/.bashrc
fi

sudo chmod +x ./util/install.sh
sudo ./util/install.sh



# Garante que o PATH contenha binários do pip local
if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' /home/vagrant/.bashrc; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> /home/vagrant/.bashrc
fi

# Garante que o PYTHONPATH contenha os diretórios corretos
if ! grep -q 'PYTHONPATH=' /home/vagrant/.bashrc; then
    echo 'export PYTHONPATH="/home/vagrant/mininet:/home/vagrant/.local/lib/python3.8/site-packages:$PYTHONPATH"' >> /home/vagrant/.bashrc
fi

# Gera relatório do provisionamento
{
    echo "Provisionamento realizado em: $(date)"
    echo ""
    echo "Versões dos pacotes Python:"
    python3 -c "import matplotlib; print('matplotlib', matplotlib.__version__)" 2>/dev/null || echo "matplotlib não encontrado"
    python3 -c "import numpy; print('numpy', numpy.__version__)" 2>/dev/null || echo "numpy não encontrado"
    echo ""
    echo "Verificação de módulo mininet:"
    python3 -c "from mininet.topo import Topo; print('Mininet OK')" 2>/dev/null || echo "Mininet NÃO encontrado"
    echo ""
    echo "Uso de memória (MB):"
    free -m || echo "[sem acesso ao comando free]"
    echo ""
    echo "Interfaces de rede:"
    ip -4 addr show | grep inet || echo "[sem acesso à rede]"
} > "$REPORT"

# Marca provisionamento como concluído
touch "$FLAG"
echo "[Provisionamento] Concluído com sucesso!"
