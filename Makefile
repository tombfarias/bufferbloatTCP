SHELL := /bin/bash

# Detecta o sistema operacional
UNAME_S := $(shell uname -s)
IS_WINDOWS := $(findstring MINGW,$(UNAME_S))
IS_WSL := $(findstring Microsoft,$(shell uname -r))
IS_LINUX := $(filter Linux,$(UNAME_S))

define WINDOWS_MSG
[INFO] Ambiente Windows detectado. Usando deploy.bat.
endef

define LINUX_MSG
[INFO] Ambiente Linux/WSL detectado. Usando deploy.sh.
endef

# Variável opcional para argumentos adicionais
ARGS ?=

deploy:
ifeq ($(IS_WINDOWS),MINGW)
	@echo $(WINDOWS_MSG)
	@cmd.exe /C deploy.bat $(ARGS)
else ifneq ($(IS_WSL),)
	@echo $(LINUX_MSG)
	@chmod +x ./deploy.sh
	@./deploy.sh $(ARGS)
else ifeq ($(IS_LINUX),Linux)
	@echo $(LINUX_MSG)
	@chmod +x ./deploy.sh
	@./deploy.sh $(ARGS)
else
	@echo "[ERRO] Sistema operacional não suportado automaticamente."
	@echo "Rode manualmente ./deploy.sh ou deploy.bat conforme seu SO."
	@exit 1
endif

start: deploy
