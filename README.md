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
git clone https://github.com/seu-usuario/bufferbloatTCP.git
cd bufferbloatTCP
```

### 2. Execute o script de deploy

No Linux:

```bash
make start
```

No Windows (Git Bash):

```bash
make start
```

> O comando acima detecta seu sistema automaticamente e roda `deploy.sh` ou `deploy.bat` conforme necessário.

---

## O que o `deploy` faz

- Verifica se Vagrant e VirtualBox estão instalados.
- Cria um ambiente virtual Python isolado (`.venv_bufferbloatTCP`).
- Instala as dependências da interface Bottle.
- Sobe a máquina virtual com Mininet.
- Inicia a interface web em uma porta disponível (ex: http://localhost:5210).

---

## Interface Web

Acesse no navegador:

```
http://localhost:5210
```

Você poderá:

- Subir/desligar a VM
- Testar conexão com `ping`
- Rodar o experimento com congestionamento Reno ou BBR
- Ver os gráficos gerados automaticamente
- Acompanhar os logs de saída dos comandos

---

## Editando o Experimento

Toda a lógica de rede está na pasta:

```
mininet-vagrant/bufferbloat/
```

Você pode (e deve!) editar:

- Topologia da rede
- Algoritmos testados
- Scripts `run.sh` e `run-bbr.sh`
- Plotagem dos resultados
- Estratégias de medição

O aplicativo **não impõe nenhuma limitação** sobre a lógica experimental. Ele serve como uma **ferramenta auxiliar** para facilitar a execução e a análise dos testes.

---

## Comandos Úteis

```bash
make run-reno   # Roda o experimento usando TCP Reno
make run-bbr    # Roda o experimento usando TCP BBR
make clean      # Remove arquivos de saída e gráficos antigos
make backup     # Faz um backup local do projeto
```

---

## Limpeza Manual

Para apagar todos os resultados gerados:

```bash
make clean
```

---

## Estrutura do Projeto

```
bufferbloatTCP/
│
├── webcontrol/             # Código da interface Bottle
│   ├── app.py              # Servidor Bottle
│   ├── views/index.tpl     # Template da interface
│   └── static/             # Estilo CSS
│
├── mininet-vagrant/        # VM com Mininet
│   └── bufferbloat/        # Lógica experimental modificável
│
├── deploy.sh               # Script de setup Linux
├── deploy.bat              # Script de setup Windows
├── Makefile                # Automação com make
└── README.md               # Este arquivo
```

---

## Contribuindo

Este projeto foi desenhado para **aprender fazendo**. Sinta-se à vontade para adaptar o experimento, rodar novas configurações, automatizar análises e explorar novas soluções para o problema de bufferbloat.

---

## Referências

- [Vagrant + VirtualBox](https://www.vagrantup.com/)
- [Mininet](http://mininet.org/)
- [Bufferbloat.net](https://www.bufferbloat.net/)
- [TCP Congestion Algorithms](https://en.wikipedia.org/wiki/TCP_congestion_control)
