#!/bin/bash

echo "Iniciando bufferbloatTCP..."

APP_NAME="bufferbloatTCP"
VENV=".venv_${APP_NAME}"

# Verifica se o Vagrant está instalado
if ! command -v vagrant &> /dev/null; then
  echo "[ERRO] Vagrant não está instalado."
  echo "Instale com: sudo apt install vagrant"
  exit 1
fi

# Verifica se o VirtualBox está instalado
if ! command -v VBoxManage &> /dev/null; then
  echo "[ERRO] VirtualBox não está instalado."
  echo "Baixe em: https://www.virtualbox.org/"
  exit 1
fi

# Lista de portas menos comuns (alta chance de estarem livres)
PORTAS=(5210 5260 5310 5360 5410 5460 5510 5560 5610 5660)
FORCE=0

# Verifica se o argumento --force foi passado
if [[ "$1" == "--force" ]]; then
  FORCE=1
fi

# Cria o ambiente virtual se não existir
if [[ ! -d "$VENV" ]]; then
  echo "Ambiente virtual não encontrado. Criando em '$VENV'..."
  python3 -m venv "$VENV"
fi

# Ativa o ambiente virtual
source "$VENV/bin/activate"

# Instala bottle se não estiver instalado
if ! python -c "import bottle" &> /dev/null; then
  echo "Instalando dependência 'bottle'..."
  pip install --quiet bottle
fi

# Tenta rodar o servidor na primeira porta livre
for PORTA in "${PORTAS[@]}"; do
  PID=$(lsof -ti :$PORTA)

  if [[ -z "$PID" ]]; then
    echo "Porta $PORTA está livre. Iniciando servidor..."
    exec python3 webcontrol/app.py "$PORTA"
  elif [[ $FORCE -eq 1 ]]; then
    echo "Porta $PORTA ocupada pelo processo $PID. Finalizando..."
    kill "$PID"
    sleep 1
    echo "Reiniciando na porta $PORTA..."
    exec python3 webcontrol/app.py "$PORTA"
  else
    echo "Porta $PORTA em uso. Tentando próxima..."
  fi
done

echo "Nenhuma porta disponível. Finalize os processos manualmente ou use ./deploy.sh --force"
exit 1
