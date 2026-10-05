# G26-Greed-PA-2026.2 — Gerenciador de Agenda para Conferências Acadêmicas

Os organizadores de um evento cadastram propostas de palestras, cada uma com horário de início e de fim.
O sistema calcula automaticamente a **grade com o maior número possível de palestras** que cabem
em **uma única sala** sem conflito de horário, mostra quais foram aceitas e quais foram rejeitadas
(e por quê) e calcula o **tempo total aproveitado da sala**.

## Algoritmo guloso: seleção de atividades

1. Ordene as palestras pelo **horário de término** (em caso de empate, pelo início).
2. Percorra a lista e **aceite** cada palestra cujo início seja `>=` ao fim da última aceita.
   Caso contrário, ela é **rejeitada**.

**Por que a escolha gulosa é ótima:** a palestra que termina primeiro libera a sala o mais cedo
possível. Em qualquer solução ótima, trocar a primeira palestra por essa mantém a solução válida e
do mesmo tamanho. Repetindo o argumento no subproblema restante, a solução gulosa tem o tamanho máximo.

**Complexidade:** `O(n log n)` (ordenação) + `O(n)` (varredura).

Os intervalos são semiabertos `[início, fim)`: uma palestra que termina às 10:00 **não** conflita
com outra que começa às 10:00. Os testes comparam o resultado com uma busca por força bruta em
200 casos aleatórios.

## Estrutura

```
agenda/
  modelos.py       # Palestra + conversão HH:MM <-> minutos
  algoritmo.py     # selecionar_palestras() e ResultadoAgenda (métricas)
  leitor.py        # leitura de JSON / CSV
  visualizacao.py  # relatório formatado para o terminal (tabelas, linha do tempo, ocupação)
  relatorio_html.py # relatório em HTML para abrir no navegador
  api.py           # API HTTP simples (biblioteca padrão)
exemplos/          # palestras.json e palestras.csv
tests/             # testes unitários
main.py            # linha de comando
```

Não há dependências externas: basta Python 3.10 ou mais recente.

## Como usar

```bash
# Relatório no terminal
python3 main.py exemplos/palestras.json
python3 main.py exemplos/palestras.csv

# Definindo a janela do evento (palestras fora dela são rejeitadas)
python3 main.py exemplos/palestras.json --inicio 08:00 --fim 18:00

# Relatório visual em HTML (abre no navegador)
python3 main.py exemplos/palestras.json --html grade.html --abrir

# Saída em JSON / sem cores
python3 main.py exemplos/palestras.json --json
python3 main.py exemplos/palestras.json --sem-cor
```

O relatório mostra:
- a tabela de **palestras aceitas** (horário, duração, título, palestrante);
- a tabela de **palestras rejeitadas**, com as palestras aceitas com que cada uma conflita;
- a **linha do tempo** da sala;
- o **resumo**: tempo total aproveitado, tempo ocioso, duração da janela e taxa de ocupação.

### Formato de entrada

JSON (lista ou objeto com a chave `palestras`):

```json
{"palestras": [
  {"titulo": "Abertura", "palestrante": "Comissão", "inicio": "08:00", "fim": "08:30"}
]}
```

CSV com cabeçalho `titulo,palestrante,inicio,fim` (`palestrante` é opcional).

## API

```bash
python3 main.py --api --porta 8000
```

```bash
curl -X POST localhost:8000/agenda -d '{
  "palestras": [
    {"titulo": "A", "inicio": "08:00", "fim": "09:00"},
    {"titulo": "B", "inicio": "08:30", "fim": "09:30"}
  ],
  "janela": {"inicio": "08:00", "fim": "12:00"}
}'
```

A resposta traz `aceitas`, `rejeitadas` (com o campo `conflita_com`) e `resumo`
(`tempo_ocupado_min`, `tempo_ocioso_min`, `taxa_ocupacao`, ...). `janela` é opcional.

## Testes

```bash
python3 -m unittest -v
```
