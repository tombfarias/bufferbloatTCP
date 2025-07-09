#!/bin/bash
set -e

echo "[Mininet Installer] Iniciando instalação do Mininet..."

# Caminho para binários locais do pip
PIP_LOCAL="$HOME/.local/bin"
export PATH="$PIP_LOCAL:$PATH"

# Garante que ~/.local/bin esteja no PATH permanentemente
if ! grep -q "$PIP_LOCAL" "$HOME/.bashrc"; then
  echo "[Mininet Installer] Adicionando ~/.local/bin ao PATH permanentemente..."
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

# Vai até o diretório raiz do Mininet (assumindo que este script está em ./util/)
cd "$(dirname "$0")/.."

# Cria symlink python → python3 se necessário (usado por mn)
if ! command -v python >/dev/null; then
  echo "[Mininet Installer] Criando symlink de python → python3"
  sudo ln -s /usr/bin/python3 /usr/bin/python
fi

# Instala binários de sistema (mnexec, man pages etc)
# sudo make install

# Instala o pacote Python do Mininet (modificável em user space)
sudo python3 setup.py install

echo "[Mininet Installer] Instalação concluída com sucesso!"

