# bufferbloatTCP

Aplicativo interativo para experimentos de Bufferbloat com suporte a **Mininet + Vagrant**, com interface web opcional feita em **Bottle**.

Este projeto fornece um ambiente autocontido para:

- Subir e controlar uma VM com Mininet.
- Rodar experimentos com diferentes algoritmos de congestionamento.
- Gerar e visualizar gráficos automaticamente.
- Modificar facilmente a lógica experimental (via pasta `bufferbloat/`).

---

## Requisitos

Antes de tudo, instale os seguintes componentes conforme seu sistema operacional:

### Linux

- [Vagrant](https://www.vagrantup.com/) (`sudo apt install vagrant`)
- [VirtualBox](https://www.virtualbox.org/) (baixe o instalador .deb)
- Python 3.8 ou superior (`sudo apt install python3-venv`)
- Make (`sudo apt install make`)

### Windows (via Git Bash)

- [Git Bash](https://git-scm.com/)
- [Vagrant](https://www.vagrantup.com/downloads)
- [VirtualBox](https://www.virtualbox.org/)
- Python 3.8+ (com `python` disponível no terminal)

---

## Primeiros Passos

### 1. Clone o repositório

```bash
git clone https://github.com/tombfarias/bufferbloatTCP.git
cd bufferbloatTCP
```

### 2. Execute o script de deploy

No Linux ou Windows (Git Bash):

```bash
make start
```

> O comando acima detecta seu sistema automaticamente e executa `deploy.sh` ou `deploy.bat` conforme necessário.

---

## O que o `deploy` faz

- Verifica se Vagrant e VirtualBox estão instalados.
- Cria um ambiente virtual Python isolado (`.venv_bufferbloatTCP`).
- Instala automaticamente a dependência Bottle.
- Sobe a máquina virtual com Mininet.
- Inicia a interface web em uma porta disponível (entre 5210 e 5660).
- Se `--force` for usado, encerra o processo que estiver ocupando a porta.

As portas são **reutilizadas** com segurança: se o script for encerrado ou interrompido, elas ficam livres novamente.

---

## Interface Web

Após a execução, acesse no navegador:

```
http://localhost:5210
```

Você poderá:

- Subir/desligar a VM
- Testar conectividade com `ping`
- Rodar experimentos com congestionamento Reno ou BBR
- Visualizar os gráficos gerados automaticamente
- Acompanhar os logs de saída

---

## Editando o Experimento

Toda a lógica de rede está localizada na pasta:

```
mininet-vagrant/bufferbloat/
```

Você pode editar:

- Topologia da rede
- Algoritmos testados
- Scripts como `run.sh`, `run-reno.sh`, `run-bbr.sh`
- Estratégias de medição e coleta de dados
- Código de plotagem dos resultados

Este projeto serve como uma **ferramenta auxiliar** para acelerar a prototipação e análise de experimentos. Nenhuma parte da lógica experimental é engessada.

---

## Comandos Úteis

```bash
make run-reno   # Executa o experimento usando TCP Reno
make run-bbr    # Executa o experimento usando TCP BBR
make clean      # Remove arquivos gerados (logs, gráficos, etc.)
make backup     # Cria backup local da pasta bufferbloat
```

---

## Estrutura do Projeto

```
bufferbloatTCP/
│
├── webcontrol/             # Interface web em Bottle
│   ├── app.py              # Código principal do servidor
│   ├── views/index.tpl     # Template HTML
│   └── static/             # CSS e recursos visuais
│
├── mininet-vagrant/        # Máquina virtual com Mininet
│   └── bufferbloat/        # Lógica experimental modificável
│
├── deploy.sh               # Script de setup para Linux
├── deploy.bat              # Script de setup para Windows
├── Makefile                # Comando `make start` e automações
└── README.md               # Este arquivo
```

---

## Observações sobre Portas e Processos

- O servidor tenta usar as portas 5210, 5260, ..., 5660.
- Se uma porta estiver ocupada e `--force` for passado, o processo será encerrado.
- As portas **não ficam presas** após o uso: ao encerrar o script, elas são liberadas.
- O comportamento é consistente no Linux e no Windows.

---

## Contribuindo

Este projeto foi desenhado para **aprender fazendo**. Sinta-se à vontade para:

- Editar a lógica experimental
- Automatizar análises de desempenho
- Criar novos cenários de teste
- Compartilhar melhorias com outros usuários

---

## Referências

- [Vagrant + VirtualBox](https://www.vagrantup.com/)
- [Mininet](http://mininet.org/)
- [Bufferbloat.net](https://www.bufferbloat.net/)
- [TCP Congestion Algorithms (Wikipedia)](https://en.wikipedia.org/wiki/TCP_congestion_control)
