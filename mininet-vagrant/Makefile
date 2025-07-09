# Caminhos e variáveis
PROJECT_DIR=bufferbloat
RUN_SCRIPT=run.sh
VAGRANT_CMD=vagrant

# Objetivo padrão
.DEFAULT_GOAL := up

# Sobe a VM
up:
	$(VAGRANT_CMD) up

# Reinicia a VM
reload:
	$(VAGRANT_CMD) reload

# Entra na VM via SSH
ssh:
	$(VAGRANT_CMD) ssh


# Mostra o relatório gerado durante o provisionamento
relatorio:
	$(VAGRANT_CMD) ssh -c "cat /home/vagrant/provision_report.txt"


# Destroi a VM (sem apagar os arquivos locais)
destroy:
	$(VAGRANT_CMD) destroy -f

