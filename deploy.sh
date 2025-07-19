#!/bin/bash

echo "Iniciando bufferbloatTCP..."

APP_NAME="bufferbloatTCP"
VENV=".venv_${APP_NAME}"
PIDFILE=".bufferbloattcp-pids"
PORTAS=(5210 5260 5310 5360 5410)

# Verifica se o Vagrant está instalado
if ! command -v vagrant &> /dev/null; then
  echo "[ERRO] Vagrant não está instalado. Instale com: sudo apt install vagrant"
  exit 1
fi

# Verifica se o VirtualBox está instalado
if ! command -v VBoxManage &> /dev/null; then
  if [[ "$IS_WSL" == "1" ]]; then
    echo "[AVISO] VBoxManage não visível no WSL, mas pode estar disponível no Windows."
  else
    echo "[ERRO] VirtualBox não está instalado. Baixe em: https://www.virtualbox.org/"
    exit 1
  fi
fi


# Cria o ambiente virtual se não existir
if [[ ! -d "$VENV" ]]; then
  echo "Ambiente virtual não encontrado. Criando em '$VENV'..."
  python3 -m venv "$VENV"
fi

# Ativa o ambiente virtual
source "$VENV/bin/activate"

# Instala bottle se necessário
if ! python -c "import bottle" &> /dev/null; then
  echo "Instalando dependência 'bottle'..."
  pip install --quiet bottle
fi

# Função de limpeza ao sair
cleanup() {
  if [[ -n "$PID" ]] && ps -p "$PID" &> /dev/null; then
    echo "Encerrando servidor (PID $PID)..."
    kill "$PID" 2>/dev/null
    sed -i "/:$PID$/d" "$PIDFILE" 2>/dev/null
  fi
  exit 0
}
trap cleanup SIGINT SIGTERM

# Cria arquivo de PID se não existir
touch "$PIDFILE"

# Remove PIDs mortos do arquivo
while IFS=: read -r PORT PID; do
  if ! ps -p "$PID" &> /dev/null; then
    sed -i "/^$PORT:$PID$/d" "$PIDFILE"
  fi
done < "$PIDFILE"

# Verifica se o PID foi criado pelo script
foi_criado_por_mim() {
  grep -q "^$1:$2$" "$PIDFILE"
}

# Pergunta antes de finalizar o processo
pergunta_finalizar_processo() {
  local PORTA="$1"
  local PID="$2"

  echo
  echo ">>> A porta $PORTA está ocupada pelo processo $PID"
  echo "Comando: $(ps -p $PID -o cmd --no-headers)"
  echo "Iniciado há:       $(ps -p $PID -o etime --no-headers)"
  read -p "Deseja finalizar esse processo? [y/N] " resposta

  if [[ "$resposta" =~ ^[Yy]$ ]]; then
    STATE=$(ps -o state= -p "$PID" | awk '{print $1}')
    if [[ "$STATE" == "T" ]]; then
      echo "Processo está parado (T). Enviando CONT..."
      kill -CONT "$PID"
      sleep 1
    fi

    kill "$PID"
    sleep 1

    if ps -p "$PID" &> /dev/null; then
      echo "Processo ainda ativo. Tentando kill -9..."
      kill -9 "$PID"
      sleep 1
      if ps -p "$PID" &> /dev/null; then
        echo "[ERRO] Processo $PID ainda está ativo mesmo após kill -9. Abortando."
        return 1
      fi
    fi

    sed -i "/^$PORTA:$PID$/d" "$PIDFILE"
    echo "Processo $PID finalizado com sucesso."
    return 0
  else
    echo "Ignorando finalização da porta $PORTA."
    return 1
  fi
}

# Tenta iniciar o servidor
for PORTA in "${PORTAS[@]}"; do
  PID_EXISTENTE=$(lsof -ti :$PORTA)

  if [[ -z "$PID_EXISTENTE" ]]; then
    echo "Porta $PORTA está livre. Iniciando servidor em foreground..."
    python3 webcontrol/app.py "$PORTA" &
    PID=$!
    sed -i "/^$PORTA:/d" "$PIDFILE"
    echo "$PORTA:$PID" >> "$PIDFILE"
    echo "Servidor iniciado com PID $PID (http://localhost:$PORTA)"
    wait $PID
    echo "Servidor finalizado."
    sed -i "/^$PORTA:$PID$/d" "$PIDFILE"
    exit 0
  else
    if foi_criado_por_mim "$PORTA" "$PID_EXISTENTE"; then
      pergunta_finalizar_processo "$PORTA" "$PID_EXISTENTE"
      if [[ $? -eq 0 ]]; then
        echo "Reiniciando na porta $PORTA..."
        python3 webcontrol/app.py "$PORTA" &
        PID=$!
        sed -i "/^$PORTA:/d" "$PIDFILE"
        echo "$PORTA:$PID" >> "$PIDFILE"
        echo "Servidor reiniciado com PID $PID (http://localhost:$PORTA)"
        wait $PID
        echo "Servidor finalizado."
        sed -i "/^$PORTA:$PID$/d" "$PIDFILE"
        exit 0
      fi
    else
      echo "Porta $PORTA ocupada por processo que não foi iniciado por este script. Pulando..."
    fi
  fi
done

echo
echo "[ERRO] Nenhuma porta disponível. Finalize os processos manualmente ou libere portas."
exit 1

