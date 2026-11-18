# Galene · Dynamic Programming

**Global Solution 2026.2 · CitizenTech · FIAP Engenharia de Software · Turma 2ESPV**

---

## Ficha da CitizenTech

| Campo | Resposta |
|---|---|
| **Nome da CitizenTech** | Galene: som que se adapta ao seu mundo |
| **Cidade e bairro** | São Paulo – SP. A solução serve para qualquer bairro com ruído urbano (salas de aula, escritórios abertos, transporte público e trânsito). A demonstração deste módulo usa um bairro fictício de São Paulo. |
| **Cidadão beneficiado** | Jovens de 18 a 34 anos que estudam ou trabalham em ambientes ruidosos; pessoas com hipersensibilidade auditiva, TDAH, TEA, ansiedade, hiperacusia ou misofonia; e a rede de apoio delas (responsáveis e médicos). |
| **Problema, em uma frase** | O barulho das cidades causa sobrecarga sensorial e perda de foco, e as soluções usadas hoje são improvisadas, como aumentar o volume do fone e arriscar a audição. |
| **Como funciona** | App mobile freemium, com um fone próprio opcional (Galene Buds), que mede o ruído do ambiente pelo microfone e adapta em tempo real o som que a pessoa ouve (binaural, lo-fi ou mascaramento de ruído). O app também tem relatórios de exposição, a assistente Gal e o vínculo opcional com médico e responsável. |
| **O que cada parte faz** | **App mobile (React Native):** mede o ruído pelo microfone e adapta o som em tempo real. **Galene Player:** toca sons binaurais, lo-fi e de mascaramento, em modo automático ou manual. **Assistente Gal:** dá dicas de foco e conforto por texto ou voz, com IA generativa. **Backend (Java Spring Boot + Oracle):** guarda contas, vínculos com médico e responsável e relatórios. **Galene Buds:** fone opcional com cancelamento de ruído e teto de volume seguro. **Este módulo (Dynamic Programming):** Rota Tranquila (Dijkstra), que acha o caminho com menos exposição a ruído, e Playlist de Foco (tabulação), que monta a melhor sequência de sons para o tempo da sessão e o ruído do ambiente. |
| **Link do repositório** | https://github.com/dev-camila/galene-dynamic-programming.git |
| **Indicador de impacto** | Metros de trajeto em ruído Intenso/Crítico (acima de 70 dB) evitados por rota. Na demonstração, de Casa até a Faculdade, a Rota Tranquila evita **950 m** de ruído Intenso/Crítico andando só **150 m a mais**. |
| **ODS conectados** | **3** Saúde e bem-estar (principal, meta 3.4) · **10** Redução das desigualdades (10.2) · **4** Educação de qualidade (4.a) · **11** Cidades e comunidades sustentáveis (11.7) |

---

## Integrantes

| Nome | RM |
|---|---|
| Luís Felipe Scacchetti Mariano | RM 562241 |
| Pedro Lucas Almeida Cunha | RM 566256 |
| Gabriel Amara | RM 561403 |
| Camila Martins Lopes dos Santos | RM 561492 |
| Guilherme Godoy dos Santos | RM 564417 |

---

## Por que esses algoritmos no Galene

O Galene parte de uma ideia simples: **a pessoa não deveria precisar aumentar o volume para fugir do barulho.** Este módulo leva essa ideia para dois momentos do dia:

1. **No caminho (Rota Tranquila):** a pessoa quer chegar à faculdade ou ao trabalho passando pelas ruas menos barulhentas, e não só pelo caminho mais curto.
2. **Na hora de focar (Playlist de Foco):** o Galene Player precisa escolher quais sons tocar numa sessão de estudo, sem repetir faixas, respeitando o tempo da sessão e o nível de ruído medido naquele momento.

As duas funcionalidades usam as **cinco faixas de ruído** da documentação do projeto: Silencioso (até 40 dB), Tranquilo (40–55), Moderado (55–70), Intenso (70–85) e Crítico (acima de 85).

---

## Algoritmos abordados

### 1. Rota Tranquila: grafos + Dijkstra com fila de prioridade (`galene/rota_tranquila.py`)

**Modelagem.** O bairro é um **grafo não dirigido**: os vértices são locais (casa, estação, praça, faculdade…) e as arestas são trechos de rua com **comprimento (m)** e **ruído médio (dB)**. O grafo é guardado como dicionário de listas de adjacência.

**Custo de um trecho.**

```
custo = metros × (1 + sensibilidade × (fator_da_faixa − 1))
```

| Faixa | Silencioso | Tranquilo | Moderado | Intenso | Crítico |
|---|---|---|---|---|---|
| Fator | 1,0 | 1,2 | 1,6 | 2,5 | 4,0 |

- `sensibilidade = 0`: só a distância conta, e o resultado é a **rota mais curta**.
- `sensibilidade = 0,5 / 1 / 2`: o ruído pesa pouco, o padrão ou o dobro (a pessoa escolhe no menu).

Os fatores são uma escolha de projeto do grupo para representar o incômodo, e não uma medida científica.

**Algoritmo.** Dijkstra com `heapq` e "remoção preguiçosa": quando um item velho sai do heap com custo maior que o já conhecido, ele é ignorado. Depois, o caminho é reconstruído pelo dicionário `anteriores`.

**Complexidade.** `O((V + E) log V)` de tempo e `O(V + E)` de memória. Cada trecho coloca no máximo um item no heap, e cada operação do heap custa `O(log)`. Os custos nunca são negativos, que é a condição para o Dijkstra funcionar.

**Saída.** O programa compara a rota mais curta com a rota mais tranquila e mostra distância, ruído médio ponderado pelos metros, pior trecho e metros em nível Intenso/Crítico.

### 2. Playlist de Foco: tabulação, mochila 0/1 (`galene/playlist_foco.py`)

**Modelagem.** É a **mochila 0/1**:

- capacidade = minutos da sessão;
- itens = sons da biblioteca, cada um com **duração** (peso) e **nota** (valor);
- cada som entra no máximo uma vez (a playlist não repete faixas).

**Nota de cada som.** `afinidade × 10` (afinidade de 1 a 5, vinda do questionário de perfil) **+ 25** quando o tipo do som é o recomendado para a faixa de ruído do ambiente:

| Ambiente | Silencioso | Tranquilo | Moderado | Intenso | Crítico |
|---|---|---|---|---|---|
| Tipos recomendados | natureza, binaural | lo-fi, binaural | lo-fi, binaural | mascaramento, lo-fi | mascaramento |

**Algoritmo.** Tabulação igual à da confeitaria da apostila (5.2): `tabela[i][t]` é a melhor nota usando só os `i` primeiros sons em `t` minutos.

```
tabela[i][t] = max( tabela[i-1][t],                         # sem o som i
                    tabela[i-1][t - duracao_i] + nota_i )   # com o som i, se couber
```

Os sons escolhidos são descobertos voltando pela tabela: se a casa mudou em relação à linha de cima, o som entrou.

**Complexidade.** `O(n × T)` de tempo e de memória, com `n` sons e `T` minutos. Para 30 sons e 90 minutos são cerca de 2.800 casas (31 × 91), contra 2³⁰ (mais de 1 bilhão) de combinações na força bruta.

---

## Funcionalidades implementadas

| Menu | O que faz |
|---|---|
| **1. Rota tranquila** | Escolhe origem, destino e sensibilidade e compara a rota mais curta com a mais tranquila, mostrando quantos metros a mais se anda e quantos metros de ruído Intenso/Crítico são evitados. |
| **2. Playlist de foco** | Recebe o ruído medido (dB) e a duração da sessão e monta a playlist de maior nota que cabe no tempo, sem repetir sons. |
| **3. Análise de eficiência** | Mede o tempo dos algoritmos em entradas crescentes e compara com versões ingênuas, conferindo que as duas dão a mesma resposta. |
| **4. De onde vêm os dados** | Mostra a origem dos dados simulados. |

Todas as entradas do usuário são validadas (`try/except` em números inválidos e fora da faixa), e os arquivos de dados são conferidos ao carregar (arquivo ausente, JSON inválido, trecho com local inexistente, som sem campo obrigatório).

---

## Análise prática de eficiência

A opção 3 do menu roda as medições com `time.perf_counter` (os tempos variam de máquina para máquina). Exemplo de execução:

**Rota: Dijkstra com heap `O((V+E) log V)` × sem heap `O(V²)`**

| Esquinas | Com heap | Sem heap | Ganho | Mesmo resultado |
|---:|---:|---:|---:|:---:|
| 225 | 0,65 ms | 4,28 ms | 7× | sim |
| 900 | 2,95 ms | 57,03 ms | 19× | sim |
| 2.025 | 6,80 ms | 209,04 ms | 31× | sim |

Só com heap: 10.000 esquinas em ~28 ms e 40.000 esquinas em ~157 ms. Com 4 vezes mais esquinas, o tempo cresce pouco mais de 4 vezes, como esperado para `(V+E) log V`. Na versão sem heap, o tempo cresce com o quadrado.

**Playlist: tabulação `O(n·T)` × força bruta `O(2ⁿ)` (sessão de 90 min)**

| Sons | Tabulação | Força bruta | Ganho | Mesmo resultado |
|---:|---:|---:|---:|:---:|
| 10 | ~0,1 ms | ~0,2 ms | ~2× | sim |
| 20 | ~0,2 ms | ~13 ms | ~50× | sim |
| 30 | ~0,2 ms | ~270 ms | ~1.000× | sim |

Só com tabulação: 1.000 sons numa sessão de 180 min em ~24 ms. A cada 10 sons a mais, o tempo da força bruta é multiplicado, enquanto o da tabulação quase não muda.

**Cuidados de eficiência seguidos:** fila de prioridade com `heapq` no Dijkstra (nada de `pop(0)`), tabela pré-alocada na tabulação e reconstrução do caminho e da playlist em tempo linear.

---

## Como rodar

Requer **Python 3.8+** e nenhuma biblioteca externa.

```bash
python main.py                          # programa com menu
python -m unittest discover testes      # 14 testes automáticos
python -m doctest galene/*.py           # exemplos das docstrings
```

Rode os comandos de dentro da pasta do projeto.

---

## Estrutura

```
galene_dp/
├── main.py                 # interface (menu, input/print, tratamento de erros)
├── galene/                 # funções puras: recebem dados e devolvem dados
│   ├── ruido.py            # as 5 faixas de ruído do Galene
│   ├── rota_tranquila.py   # grafo + Dijkstra (heap) e Dijkstra ingênuo
│   ├── playlist_foco.py    # mochila 0/1 por tabulação e força bruta
│   ├── dados.py            # leitura e validação dos JSON
│   └── eficiencia.py       # geradores de entrada e medição de tempo
├── dados/
│   ├── bairro.json         # bairro fictício (14 locais, 22 trechos)
│   └── sons.json           # biblioteca de 12 sons com afinidade de exemplo
├── testes/
│   └── test_galene.py      # testes automáticos
└── README.md
```

---

## Dados utilizados

**Nenhum dado pessoal real.** Todos os dados são **simulados pelo grupo**:

- `dados/bairro.json`: bairro fictício de São Paulo. Distâncias e níveis de ruído foram inventados para ficar coerentes com as faixas do Galene (avenida, terminal e hospital mais barulhentos; parque, biblioteca e rua arborizada mais silenciosos).
- `dados/sons.json`: nomes de faixas inventados, com a afinidade (1 a 5) de um questionário de perfil fictício.
- Na análise de eficiência, os bairros em grade e as bibliotecas de sons são gerados com `random` e semente fixa (42), para o resultado ser reproduzível.

As faixas de decibéis vêm da documentação do projeto Galene (seção 1.2).

