# Caminhos
RUN_RENO=run.sh
RUN_BBR=run-bbr.sh
RUN_COMPETITION=run-competition.sh
REPORT=provision_report.txt

# Argumentos para competition.py
RENO ?= 2
BBR ?= 2

# Roda o experimento principal com permissões corretas
run-reno: $(RUN_RENO)
	sudo chmod +x $(RUN_RENO)
	sudo ./$(RUN_RENO)

run-bbr: $(RUN_BBR)
	sudo chmod +x $(RUN_BBR)
	sudo ./$(RUN_BBR)


# Roda a competição
run-competition: $(RUN_COMPETITION)
	sudo chmod +x $(RUN_COMPETITION)
	sudo ./$(RUN_COMPETITION) $(RENO) $(BBR)

# Remove arquivos gerados automaticamente
clean:
	rm -f bb-q*/*.txt
	rm -f *.png

# Mostra relatório de provisionamento (se existir)
report:
	@echo "=== Relatório de provisionamento ==="
	@cat ../$(REPORT) || echo "Relatório não encontrado."

# Backup local do projeto
backup:
	cp -r . ~/backup_bufferbloat_$$USER

.PHONY: run plot clean report backup
