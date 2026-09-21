# Checkpoint 4 — Algoritmos e Estruturas de Dados · FIAP · Turma W

| Integrante | RM |
|---|---|
| Felipe Bernardes | RM564360 |
| Guilherme Romero | RM564431 |

**Seed do grupo:** `SEED = 564360` (definida em `src/config.py`). Todos os dados são gerados a partir dela.

---

## Sumário
1. [Problemas](#1-problemas)
2. [Modelo adotado](#2-modelo-adotado)
3. [Estruturas de dados](#3-estruturas-de-dados)
4. [Algoritmos](#4-algoritmos)
5. [Como executar](#5-como-executar)
6. [Resultados](#6-resultados)
7. [Complexidade](#7-complexidade)
8. [Limitações](#8-limitações)
9. [Estrutura do repositório](#9-estrutura-do-repositório)
10. [Pergunta final](#pergunta-final)

---

## 1. Problemas

**Questão 1 — Logística de emergência.** Após chuvas intensas, um centro de distribuição (CD) da Defesa Civil
precisa levar kits (água, remédios, alimentos, higiene, cobertores) a 20 pontos de atendimento. Algumas vias estão
bloqueadas e o veículo tem capacidade limitada. Queremos decidir **quais** pontos atender e **em que ordem**,
maximizando o benefício.

**Questão 2 — Consumo de energia.** Com medições horárias de consumo em 5 regiões, queremos encontrar o
**intervalo contínuo de tempo com maior criticidade acumulada** — o período em que o sistema esteve mais
tensionado — primeiro por força bruta e depois por dividir e conquistar, comparando a escalabilidade dos dois.

## 2. Modelo adotado

### Questão 1 — grafo ponderado + mochila 0/1

* **Vértices:** 1 CD + 20 pontos em um quadrado de 100 × 100 km. Cada ponto tem pessoas afetadas (80–1.500),
  prioridade (1–5), demanda em kits e benefício.
* **Benefício** = pessoas/10 × fator(prioridade), com fator = {1: 1; 2: 1,5; 3: 2; 4: 3; 5: 4}. Inteiro, para a DP.
* **Arestas:** cada ponto é ligado aos 3 vizinhos mais próximos → **42 vias** (grafo esparso, não completo).
  Peso = distância euclidiana × sinuosidade aleatória (1,00–1,35), em km.
* **Vias bloqueadas:** 15% das arestas (**6 vias**) — continuam no grafo (e na figura), mas o Dijkstra as ignora.
* **Capacidade do veículo:** 45% da demanda total → **C = 216 kits** de 481 necessários.
* Arquivos: `data/problema1_pontos.csv`, `data/problema1.csv` (arestas), `data/problema1_parametros.json`.

Separação de responsabilidades: **Dijkstra** calcula distâncias reais pela malha disponível; o **Greedy** decide
ordem e seleção ao mesmo tempo, usando essas distâncias; a **DP** resolve a seleção ótima sob a restrição de
capacidade (mochila 0/1) e a ordem de visita do conjunto ótimo é feita por vizinho mais próximo (apenas para a figura).

### Questão 2 — série temporal e subvetor contínuo de soma máxima

* **Dados sintéticos** (`src/dados_q2.py`): 5 regiões × 336 h (14 dias de janeiro/2026) = **1.680 observações**
  com `timestamp, regiao, consumo, capacidade, prioridade, custo`.
* **Geração documentada:** consumo = base × perfil diário (pico às 19h) × efeito de fim de semana × ondas de calor ×
  ruído gaussiano; capacidade = base × (1 + participação solar ao meio-dia) × (0,88 em falhas de geração).
  O resultado reproduz a "curva do pato": sobra capacidade ao meio-dia e ela aperta no início da noite.
* **Criticidade de cada hora:**

  `c = 100·(carga − 0,88) + 300·max(0, carga − 1) + 2·(prioridade − 3) + 5·(custo/250 − 1)`, carga = consumo/capacidade

  - acima de 88% de uso a hora começa a contar positivamente;
  - acima de 100% (consumo > capacidade) a penalidade triplica;
  - cargas essenciais (prioridade alta) e preço alto agravam.

  Horas folgadas ficam **negativas** — isso é essencial: sem valores negativos a resposta seria sempre a série inteira.
* O problema passa a ser: dado c₀ … cₙ₋₁, achar [i, j] que maximize cᵢ + … + cⱼ.

## 3. Estruturas de dados

### Questão 1

| Estrutura | Onde | Por que é adequada à operação |
|---|---|---|
| `dict[int, dict[int, float]]` | lista de adjacência (`Grafo._adj`) | Dijkstra percorre vizinhos: O(grau) por vértice, O(V+E) no total. Consultar/alterar o peso de u–v é O(1) — útil quando o professor muda um peso. Matriz de adjacência gastaria Θ(V²) para um grafo com E ≈ 2V. |
| `set[frozenset]` | vias bloqueadas | "u–v está bloqueada?" é perguntado a cada relaxamento: O(1) médio no set contra O(B) numa lista. `frozenset({u,v}) == frozenset({v,u})`, então a via é não direcionada sem duplicar chaves. Bloquear/desbloquear não apaga o peso. |
| heap (`heapq`) | fila do Dijkstra | extrai o vértice mais próximo em O(log V); sem ele o Dijkstra seria O(V²). |
| `dict` id → `Ponto` | candidatos restantes no Greedy | remover o escolhido em O(1). |
| `dict` cache origem → (dist, pred) | `MatrizDistancias` | um Dijkstra por posição visitada, reaproveitado em todos os passos. |
| `dataclass(frozen=True)` / `NamedTuple` | `Ponto`, `Item`, `Decisao` | registros imutáveis: um algoritmo não altera o dado usado pelo outro. |
| `list[list[int]]` | tabela DP | acesso O(1) a `DP[i-1][c-w]`; as linhas antigas são necessárias para a reconstrução. |

### Questão 2 (`IndiceEnergia`)

| Estrutura | Operação favorecida | Custo |
|---|---|---|
| `list` ordenada no tempo | série de uma região, acesso por índice e fatias — entrada dos algoritmos | O(1) por índice |
| `tuple` (`NamedTuple Registro`) | armazenar cada medição | imutável, ~3× mais leve que `dict` |
| `dict` região → índices | consumo por região | O(1) para localizar + O(k) |
| `dict` hora → índices | consumo por horário do dia | O(1) + O(k) |
| `set` de (timestamp, região) | "essa hora estava em sobrecarga?" | O(1) |
| heap (`heapq.nlargest`) | top-k picos | O(n log k) em vez de ordenar O(n log n) |
| `list` + `bisect` | selecionar intervalo [t₀, t₁] | O(log n) |
| somas de prefixo | consumo total em um intervalo | O(1) após o bisect |

## 4. Algoritmos

Nenhum algoritmo central usa biblioteca pronta: Dijkstra, Greedy, DP, força bruta e D&C foram implementados em `src/`.
Bibliotecas externas: `matplotlib` (figuras), `pandas` (tabelas nos notebooks), `pytest` (testes).

### 4.1 Greedy (`src/greedy.py`)

```
score(i | posição atual a) = (benefício_i / demanda_i) / (1 + d(a, i) / d̄)
```

* **benefício/demanda** = quanto benefício cada kit rende. A capacidade é o recurso que limita a solução; escolher a
  maior razão é escolher o maior ganho marginal por unidade do recurso escasso.
* **1 + d/d̄** = penalidade de deslocamento. `d(a, i)` vem do Dijkstra (vias bloqueadas excluídas) e `d̄` é a distância
  média do CD aos candidatos, o que torna o termo adimensional: um ponto a 2·d̄ tem o score dividido por 3.
* Prioridade e número de pessoas entram pelo benefício.
* A cada passo: filtra os candidatos que ainda cabem, escolhe o maior score, move o veículo, desconta a capacidade.
  **A decisão nunca é revista.**

Por que é localmente vantajosa: entre as opções viáveis, é a que entrega mais benefício por unidade dos dois
recursos que aquela decisão consome — espaço no caminhão e deslocamento. Uma regra "maior prioridade primeiro"
ignoraria que um ponto de prioridade 5 com demanda enorme pode ocupar o espaço de três pontos que, juntos, valem mais.
Também existe a variante `usar_distancia=False` (só benefício/kit), usada nas comparações.

### 4.2 Programação Dinâmica (`src/dynamic_programming.py`)

1. **Estado:** `DP[i][c]` = maior benefício usando apenas as *i* primeiras regiões candidatas com no máximo *c* kits.
2. **Decisão:** para a região *i*, atender (ganha vᵢ, ocupa wᵢ) ou não atender.
3. **Caso-base:** `DP[0][c] = 0` para todo *c* — sem regiões não há benefício.
4. **Recorrência:**
   ```
   DP[i][c] = DP[i-1][c]                                  se wᵢ > c
   DP[i][c] = max( DP[i-1][c],  DP[i-1][c-wᵢ] + vᵢ )     caso contrário
   ```
5. **Reconstrução:** começa em (N, C). Se `DP[i][c] ≠ DP[i-1][c]`, o valor só pode ter vindo de "atender" → registra
   *i* e faz `c -= wᵢ`. Repete até i = 0. A Figura 3a desenha exatamente esse caminho sobre a tabela.

Correção: numa solução ótima para (i, c), ou *i* fica fora e o resto é ótimo para (i−1, c), ou *i* entra e o resto
é ótimo para (i−1, c−wᵢ) — subestrutura ótima. Os subproblemas se repetem, por isso a tabela.
A DP é conferida contra a força bruta 2ᴺ em 60 instâncias aleatórias nos testes.

### 4.3 Força bruta (`src/brute_force.py`)

Para cada início *i* e cada fim *j ≥ i*, avalia a criticidade acumulada de [i, j] (a soma de [i, j] é a de
[i, j−1] + cⱼ). Todos os n(n+1)/2 intervalos são examinados explicitamente. Há também a versão literal Θ(n³)
(`intervalo_critico_ingenuo`), que recalcula cada soma do zero.

### 4.4 Dividir e Conquistar (`src/divide_conquer.py`)

```
DIVIDE          meio = (lo + hi) // 2
SOLVE LEFT      melhor intervalo dentro de [lo, meio]        (recursão)
SOLVE RIGHT     melhor intervalo dentro de [meio+1, hi]      (recursão)
SOLVE CROSSING  melhor intervalo que contém meio e meio+1
COMBINE         o maior dos três
```

* **Caso-base:** `lo == hi` → o único intervalo é [lo, lo].
* **Cruzamento:** todo intervalo que atravessa a divisão = (sufixo da esquerda terminando em `meio`) + (prefixo da
  direita começando em `meio+1`). As duas partes são independentes, então basta o **melhor sufixo** (varrendo de
  `meio` até `lo`) somado ao **melhor prefixo** (varrendo de `meio+1` até `hi`). Custo O(hi − lo + 1).
* Um teste específico (`test_intervalo_atravessando_a_divisao`) usa uma entrada em que o ótimo só pode vir do cruzamento.

## 5. Como executar

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run_all.py                 # Q1 + Q2: dados, algoritmos, figuras e results/*.json
python -m pytest                  # 33 testes
jupyter notebook notebooks/       # questao1.ipynb e questao2.ipynb (já executados)
```

Execução por questão e **alteração de entradas** (para a defesa — não altera os CSVs):

```bash
python -m src.questao1 --capacidade 150
python -m src.questao1 --bloquear 0-12 --desbloquear 1-9
python -m src.questao1 --peso 5-18=60 --prioridade 12=1
python -m src.questao2 --regiao Nordeste
python -m src.questao2 --inicio 0 --fim 200 --sem-experimento
python run_all.py --regenerar     # recria os dados a partir da SEED
```

## 6. Resultados

> Os tempos abaixo são da execução registrada em `results/`; em outra máquina os valores absolutos mudam, as razões não.

### Questão 1 (V = 21, E = 42, 6 bloqueadas, N = 20, C = 216 de 481 kits)

| Estratégia | Pontos atendidos | Benefício | Kits | Rota |
|---|---|---:|---:|---:|
| Greedy com distância | 12 → 18 → 15 → 14 → 13 → 6 → 11 | 2.124 | 212 | 311,5 km |
| Greedy benefício/kit | 15, 12, 18, 14, 6, 5, 4 | 2.153 | 216 | — |
| **DP (ótimo)** | {4, 5, 6, 12, 14, 15, 18} | **2.153** | 216 | 426,5 km |

* **Greedy ótimo:** na capacidade oficial, o Greedy por benefício/kit encontrou o ótimo (2.153).
* **Greedy não ótimo:** o Greedy com distância ficou 1,3% abaixo — mas com rota 27% mais curta. Ele troca
  benefício por deslocamento, algo que a DP não modela.
* **Varredura de capacidades** (5% a 100% da demanda, Figura 4): o Greedy por benefício/kit acertou o ótimo em
  10 de 20 capacidades; o Greedy com distância em 6 de 20. Pior perda: **26,5% em C = 48** — o Greedy por
  benefício/kit pega o ponto 15 (21 kits), o 12 (42 kits, benefício 574) deixa de caber e o total fica 438;
  a DP escolhe {11, 12} = 596. Na Figura 3b, o Greedy fica abaixo da DP em 102 das 217 capacidades possíveis.
* **Contraexemplo próprio** (`src/contraexemplo.py`, Figura 5): três abrigos à mesma distância, C = 10 kits.
  A (6 kits, 36), B (5 kits, 27), C (5 kits, 27). O Greedy escolhe A (6,0 por kit > 5,4) e sobram 4 kits, onde nem B
  nem C cabem → **36**. A DP escolhe B + C → **54** (+50%). A escolha gulosa é localmente a melhor, mas deixa capacidade
  ociosa que nenhuma decisão posterior aproveita; a mochila 0/1 não tem a propriedade da escolha gulosa.
* **Caso em que o Greedy é sempre ótimo:** demandas iguais (4 abrigos com 10 kits, C = 20) → 150 = 150; ordenar por
  benefício/kit vira ordenar por benefício, e o argumento de troca garante a otimalidade.
* **Simulação de alteração:** baixando a prioridade do ponto 12 de 5 para 1, previmos que ele sairia das duas
  soluções e que o ótimo cairia 15–20%. Resultado: DP passou de 2.153 para 1.805 (−16,2%), com o ponto 13 entrando.

### Questão 2 (1.680 observações)

| Região | Intervalo mais crítico | Horas | Criticidade | FB = D&C |
|---|---|---:|---:|:---:|
| **Sul** | 15/01 17h → 21h | 5 | **212,5** | ✔ |
| Sudeste | 16/01 17h → 22h | 6 | 210,9 | ✔ |
| Nordeste | 13/01 17h → 23h | 7 | 206,1 | ✔ |
| Centro-Oeste | 14/01 18h → 23h | 6 | 185,5 | ✔ |
| Norte | 12/01 16h → 21h | 6 | 144,8 | ✔ |

Todos os intervalos caem no início da noite de dias com onda de calor — exatamente onde o solar zera e o consumo é
máximo. Para n = 336 horas a força bruta fez 56.616 operações; o D&C, 3.184.

**Escalabilidade (Figura 3):**

| n | Força bruta | D&C | Razão |
|---:|---:|---:|---:|
| 100 | 0,44 ms | 0,19 ms | 2,3× |
| 1.000 | 44,0 ms | 2,25 ms | 20× |
| 5.000 | 1.075 ms | 11,9 ms | 91× |

Tempo/n² da força bruta fica constante (40–44 ns) e tempo/(n log n) do D&C quase constante (190–285 ns): o experimento confirma
Θ(n²) e Θ(n log n). Tabela completa em `docs/analise_complexidade.md` e `results/escalabilidade_q2.csv`.

### Figuras (geradas pelo código em `figures/`)

| Arquivo | Conteúdo |
|---|---|
| `questao1/fig1_grafo.png` | CD, pontos (cor = prioridade, tamanho = pessoas), pesos e vias bloqueadas ✕ |
| `questao1/fig2_solucao.png` | Greedy × DP: atendidos, não atendidos e sequência seguindo os caminhos de Dijkstra |
| `questao1/fig3_programacao_dinamica.png` | Heatmap de `DP[i][c]` com o caminho da reconstrução + benefício ótimo × capacidade |
| `questao1/fig4_greedy_vs_dp_capacidades.png` | Greedy × DP em 20 capacidades |
| `questao1/fig5_contraexemplo.png` | Contraexemplo 36 × 54 |
| `questao2/fig1_serie_temporal.png` | Consumo e capacidade × tempo, sobrecargas e intervalo crítico destacado |
| `questao2/fig2_dividir_conquistar.png` | 4 níveis da recursão sobre os dados reais, com E/D/X de cada nó e o vencedor |
| `questao2/fig3_escalabilidade.png` | Tempo × n (linear e log-log) e operações contadas |

## 7. Complexidade

Resumo (demonstrações em [`docs/analise_complexidade.md`](docs/analise_complexidade.md)):

| Algoritmo | Tempo | Espaço |
|---|---|---|
| Dijkstra com heap | O((V + E) log V) | O(V + E) |
| Greedy | O(N·(V + E) log V + N²) | O(N·V) |
| DP (mochila 0/1) | Θ(N·C) — pseudo-polinomial | Θ(N·C) (Θ(C) sem reconstrução) |
| Força bruta (intervalo) | T(n) = n(n+1)/2 = Θ(n²) | O(1) |
| Dividir e conquistar | T(n) = 2T(n/2) + Θ(n) = Θ(n log n) | O(log n) (pilha) |

**De 1.000 para 1.000.000 registros:** a força bruta passaria de 5·10⁵ para 5·10¹¹ operações (≈ 11,9 h projetadas
com a constante medida); o D&C, para ≈ 2,2·10⁷ operações (≈ 4 s) com recursão de profundidade 20. **Só o D&C
continua viável.** O limite da força bruta é tempo, não memória.

## 8. Limitações

* **Um veículo e uma viagem.** A DP escolhe o conjunto ótimo só pelo benefício; a rota é ordenada por vizinho mais
  próximo, que não é ótima (seria um problema do caixeiro-viajante). Tempo de viagem e janelas de atendimento não
  entram na DP.
* **Atendimento tudo-ou-nada.** Cada ponto recebe toda a demanda ou nada; atendimento parcial viraria mochila
  fracionária (onde o Greedy seria ótimo).
* **Recursos agregados em "kits".** Água, remédios etc. não são modelados separadamente (seria uma mochila
  multidimensional).
* **DP pseudo-polinomial.** Com capacidade em unidades muito finas (gramas, litros) a tabela explode.
* **Dados sintéticos.** Seguem padrões plausíveis (pico noturno, solar, ondas de calor), mas não são medições reais
  do ONS; os parâmetros da criticidade (limiar 0,88, pesos) foram escolhidos pelo grupo.
* **Medições em Python.** Os tempos incluem overhead do interpretador; as razões entre tamanhos são o que importa.
* **Kadane.** Existe solução Θ(n) para a Questão 2; não a usamos como resposta principal porque o enunciado pede
  força bruta e D&C.

## 9. Estrutura do repositório

```
checkpoint4/
├── README.md
├── requirements.txt
├── run_all.py
├── data/
│   ├── problema1.csv               # arestas (origem, destino, km, bloqueada)
│   ├── problema1_pontos.csv        # vértices
│   ├── problema1_parametros.json   # seed e capacidade
│   └── problema2.csv               # 1.680 medições horárias
├── src/
│   ├── config.py                   # SEED, caminhos, integrantes
│   ├── estruturas.py               # Ponto, Grafo, Registro, IndiceEnergia
│   ├── caminhos.py                 # Dijkstra + cache
│   ├── greedy.py
│   ├── dynamic_programming.py
│   ├── brute_force.py
│   ├── divide_conquer.py
│   ├── contraexemplo.py
│   ├── dados_q1.py / dados_q2.py   # geração reprodutível + criticidade
│   ├── experimento.py              # escalabilidade
│   ├── metricas.py                 # contador de operações
│   ├── visualizacao_q1.py / visualizacao_q2.py
│   └── questao1.py / questao2.py   # pipelines com CLI
├── notebooks/  questao1.ipynb, questao2.ipynb
├── figures/    questao1/, questao2/
├── results/    questao1.json, questao2.json, escalabilidade_q2.csv
├── tests/      test_questao1.py, test_questao2.py
└── docs/       analise_complexidade.md
```

---

## Pergunta final

**Qual foi a decisão algorítmica mais importante tomada pelo grupo?**

Modelar a seleção de atendimentos da Questão 1 como uma mochila 0/1 resolvida por Programação Dinâmica com a tabela
completa `DP[N][C]`, separando "quem atender" (capacidade) de "em que ordem visitar" (distância).

**Alternativa descartada:** usar apenas o Greedy, que parecia suficiente. Ele é mais barato — O(N²) passos mais
alguns Dijkstras, contra 21 × 217 = 4.557 células da DP — e na capacidade oficial até acertou o ótimo (2.153)
na versão por benefício/kit. Mas a varredura mostrou que isso foi sorte da instância: ele errou em 10 de 20
capacidades, perdeu 26,5% em C = 48 (438 contra 596) e o nosso contraexemplo mostra perda de 33% (36 contra 54).
Em logística de emergência, benefício perdido são pessoas sem atendimento.

Também descartamos duas outras opções. A força bruta garante o ótimo, mas testaria 2²⁰ ≈ 10⁶ subconjuntos para
N = 20, e dobra a cada ponto novo; a DP cresce linearmente em N e em C. A DP em uma dimensão economizaria memória
(217 inteiros em vez de 4.557), mas perderia a reconstrução — saberíamos o benefício, não quais pontos atender.
Com N·C na casa de milhares de células (dezenas de KB), a memória extra é irrelevante e a reconstrução é essencial.

O custo dessa escolha apareceu nos resultados: a rota do conjunto ótimo tem 426,5 km, contra 311,5 km do Greedy com
distância. Por isso mantivemos os dois — a DP como referência de benefício máximo e o Greedy como alternativa rápida
que considera deslocamento.
