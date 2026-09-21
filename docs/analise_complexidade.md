# Análise de complexidade

Notação: **V** vértices, **E** arestas, **N** regiões candidatas (alcançáveis), **C** capacidade do veículo
(kits), **n** tamanho da série temporal. Na nossa instância: V = 21, E = 42, N = 20, C = 216.

---

## Questão 1

### Construção do grafo — `Grafo` (`src/estruturas.py`)

Cada `adicionar_ponto` cria uma entrada vazia no dict de adjacência (O(1)); cada `adicionar_aresta` escreve
`adj[u][v]` e `adj[v][u]` (O(1) médio). Total: **T = O(V + E)**, **S = O(V + E)** — cada aresta aparece duas vezes
no dict (grafo não direcionado) e as bloqueadas mais uma vez no `set`.
Uma matriz de adjacência custaria S = Θ(V²) = 441 posições para guardar 42 arestas, e percorrer os vizinhos de um
vértice passaria a custar Θ(V) em vez de Θ(grau).

### Dijkstra — `src/caminhos.py`

* Cada vértice é **finalizado uma vez** (o `set` `finalizados` descarta entradas obsoletas do heap).
* Ao finalizar *u* percorremos seus vizinhos: somando para todos os *u*, cada aresta não direcionada é olhada
  2 vezes → Θ(E) relaxamentos; cada consulta ao `set` de bloqueadas é O(1).
* Cada relaxamento bem-sucedido faz um `heappush` (O(log |heap|)); no pior caso o heap chega a O(E) entradas e
  como E ≤ V², log E = O(log V).
* Pops: no máximo (pushes + 1).

**T(V, E) = O((V + E) log V)**, **S(V, E) = O(V + E)** (dist, pred, heap).

### Greedy — `src/greedy.py`

1. Candidatos: 1 Dijkstra a partir do CD → O((V + E) log V).
2. Laço principal: cada iteração remove um candidato do `dict restantes` (O(1)), logo há no máximo **N iterações**.
3. Em cada iteração varre os candidatos restantes (≤ N) calculando o score em O(1) — mas precisa da distância a
   partir da posição atual. `MatrizDistancias` executa **um Dijkstra por posição distinta do veículo** e guarda o
   resultado em cache. O veículo ocupa no máximo N + 1 posições → no máximo N + 1 Dijkstras
   (na execução real foram **8**: o CD + 7 pontos atendidos).

**T(N, V, E) = O(N·(V + E) log V + N²)**. Como V = N + 1 e o grafo é esparso (E = O(V)), fica O(N² log N).
**S = O(N·V)** para o cache de distâncias + O(V + E) do grafo.

### Programação Dinâmica — `src/dynamic_programming.py`

* `preencher_tabela`: dois laços aninhados, *i* de 1 a N e *c* de 0 a C; cada célula faz no máximo uma comparação
  e uma soma → **(N + 1)(C + 1) células × O(1) = Θ(N·C)**. Na instância: 21 × 217 = 4.557 células.
* `reconstruir`: um passo por região, O(1) cada → O(N).
* Espaço: a tabela inteira **Θ(N·C)** — necessária para a reconstrução (precisamos comparar `DP[i][c]` com
  `DP[i-1][c]` em linhas antigas). A variante `mochila_dp_1d` usa **O(C)** mas devolve só o valor.
* Verificação empírica (notebook 1, Parte F): ~80–100 ns por célula para C = 100 … 1.600 — tempo linear em C.

**Atenção: O(N·C) é pseudo-polinomial.** C é um *valor*, não o tamanho da entrada. Se a capacidade fosse medida em
gramas (C = 2.000.000) a tabela teria 42 milhões de células; nesse caso seria preciso mudar a unidade (kits) ou usar
outra formulação (DP por valor, branch and bound).

### Força bruta da mochila (apenas gabarito nos testes)

2^N subconjuntos, O(N) para somar cada um → **O(N·2^N)**. Para N = 20: ≈ 2·10⁷ operações contra 4.557 células da DP.

### Resumo Q1

| Algoritmo | Tempo | Espaço |
|---|---|---|
| Construção do grafo | O(V + E) | O(V + E) |
| Dijkstra (heap) | O((V + E) log V) | O(V + E) |
| Greedy | O(N·(V + E) log V + N²) | O(N·V) |
| DP (tabela completa) | Θ(N·C) | Θ(N·C) |
| DP 1D (sem reconstrução) | Θ(N·C) | Θ(C) |
| Força bruta (mochila) | O(N·2^N) | O(N) |

---

## Questão 2

### Estruturas — `IndiceEnergia`

| Operação | Estrutura | Custo |
|---|---|---|
| Construção | `sorted` + 1 passada | O(n log n) tempo, O(n) espaço |
| Consumo total por região | prefixo final | O(1) por região |
| Consumo médio por hora | dict hora → índices | O(n) total |
| Top-k picos | `heapq.nlargest` (heap de tamanho k) | O(n log k) |
| Hora em sobrecarga? | `set` | O(1) médio |
| Selecionar [t₀, t₁] | `bisect` em lista ordenada | O(log n + k) |
| Soma do consumo em [t₀, t₁] | somas de prefixo | O(log n) (bisect) + O(1) |

### Força bruta — `intervalo_critico_forca_bruta`

Laço externo *i* = 0 … n − 1; laço interno *j* = i … n − 1, cada volta faz 1 soma e 1 comparação:

T(n) = Σᵢ (n − i) = n + (n − 1) + … + 1 = **n(n + 1)/2 = Θ(n²)**

O contador confirma exatamente: n = 1.000 → 500.500 operações; n = 5.000 → 12.502.500.
**S(n) = O(1)** extra (só `soma` e o melhor intervalo); a memória medida ficou constante (~0,4 KB).

A versão literal `intervalo_critico_ingenuo` recalcula a soma de cada intervalo:
Σᵢ Σⱼ (j − i + 1) = n(n + 1)(n + 2)/6 = **Θ(n³)**.

### Dividir e Conquistar — `intervalo_critico_dc`

Cada chamada sobre *m* elementos faz:
* 2 chamadas recursivas sobre ⌈m/2⌉ e ⌊m/2⌋;
* o cruzamento: um laço de `meio` até `lo` e outro de `meio + 1` até `hi` → exatamente *m* visitas;
* a combinação: 2 comparações, O(1).

**T(n) = 2T(n/2) + Θ(n)**, T(1) = Θ(1).

*Pelo Teorema Mestre*: a = 2, b = 2, f(n) = Θ(n) = Θ(n^(log₂2)) → caso 2 → **T(n) = Θ(n log n)**.

*Pela árvore de recursão*: no nível *k* há 2ᵏ subproblemas de tamanho n/2ᵏ; o cruzamento visita n elementos por
nível no total; há ⌈log₂ n⌉ níveis → n·log₂ n visitas + n casos-base. Para n = 2⁶ = 64 o teste confirma
**64·6 + 64 = 448** operações exatas; para n = 5.000 o contador registrou 66.808 ≈ 5.000·log₂5.000 + 5.000 ≈ 66.400.

**S(n)**: não copiamos fatias da lista (passamos `lo`, `hi`), então cada quadro da pilha guarda O(1) valores.
A profundidade da recursão é ⌈log₂ n⌉ → **S(n) = O(log n)** extra. A memória medida cresceu de 0,6 KB (n = 100)
para 2,5 KB (n = 5.000) — crescimento lento, compatível com log n. (Em uma primeira versão fazíamos
`list(valores)` e a memória crescia linearmente: 41,6 KB em n = 5.000; removemos a cópia.)
Registrar a árvore para a Figura 2 acrescenta no máximo 2^(p+1) − 1 = 15 nós (p = 3), O(1) em relação a n.

### Experimento (valores da execução registrada em `results/escalabilidade_q2.csv`)

| n | Força bruta (ms) | FB: t/n² (ns) | D&C (ms) | D&C: t/(n log₂n) (ns) | ops FB | ops D&C |
|---:|---:|---:|---:|---:|---:|---:|
| 100 | 0,44 | 44,1 | 0,19 | 284 | 5.050 | 772 |
| 250 | 2,51 | 40,2 | 0,47 | 235 | 31.375 | 2.244 |
| 500 | 10,2 | 41,0 | 1,00 | 224 | 125.250 | 4.988 |
| 1.000 | 44,0 | 44,0 | 2,25 | 226 | 500.500 | 10.976 |
| 2.000 | 171 | 42,8 | 4,79 | 219 | 2.001.000 | 23.952 |
| 5.000 | 1.075 | 43,0 | 11,9 | 193 | 12.502.500 | 66.808 |

* Na força bruta **t/n² é constante** (40–44 ns): a curva é quadrática, como previsto.
* No D&C **t/(n log n) é quase constante** (um pouco mais alta em n pequeno, onde o custo fixo das chamadas pesa mais).
* Ao dobrar n de 1.000 para 2.000: FB × 3,9 (≈ 4 = 2²); D&C × 2,13 (≈ 2·log(2000)/log(1000) = 2,2).
* Para n pequeno (100) a diferença é só 2,3×; o D&C tem constante maior (recursão), mas já em n = 5.000 é 91× mais rápido.

### De 1.000 para 1.000.000 registros

| | Força bruta Θ(n²) | Dividir e conquistar Θ(n log n) |
|---|---|---|
| Operações | n(n+1)/2 ≈ **5·10¹¹** | n log₂ n + n ≈ **2,2·10⁷** |
| Fator de crescimento (×1.000 em n) | ×1.000.000 | ≈ ×2.000 |
| Tempo projetado (constantes medidas) | ≈ **11,9 horas** | ≈ **4 segundos** |
| Memória extra | O(1) | O(log n): 20 quadros de pilha |
| Profundidade de recursão | — | ⌈log₂ 10⁶⌉ = 20 (limite do Python: 1.000) |

**Só o Dividir e Conquistar continua viável.** O gargalo da força bruta é tempo, não memória. O D&C cabe
folgado em memória (a lista de 10⁶ floats ocupa ~32 MB e é compartilhada, sem cópias) e a recursão é rasa.
Observação: para a mesma pergunta existe o algoritmo de Kadane, Θ(n) e O(1) de memória, que seria ainda melhor em
produção; não o usamos como solução porque o enunciado pede explicitamente força bruta e D&C.
