# Entrega 2 — Bloco do Agente de Testes de Software

Texto pronto para colar no `Modelo_Entrega2.docx`, na seção **3. Testes, Estatísticas e Demonstração por Agente**
(um dos blocos "Agente 3/4/5 — [nome do agente]"). Os subtítulos abaixo seguem os do modelo, na mesma ordem.
Todos os números vêm de `resultados/resultados.json` (execução real em 12/11/2026) e podem ser reproduzidos com
`make avaliar`. As figuras estão em `resultados/graficos/`.

Também há trechos para as seções 2, 4, 5 e 8, que são da equipe. A seção 6 (retrospectiva) depende do grupo e
não foi preenchida aqui.

---

## Agente — Agente de Testes de Software

### Confirmação da base tecnológica e do modelo de interação (Entrega 1)

**Base tecnológica: mantida.** A implementação segue a arquitetura híbrida especificada. O LLM (Google Gemini ou
outra API compatível) é usado para interpretar código e requisitos, propor cenários e gerar código de teste, e a
verificação é feita por frameworks tradicionais (Pytest, com adaptadores para JUnit 5, Jest/Vitest e Newman),
executados em container Docker isolado (`--network none`, CPU, memória e PIDs limitados, usuário não-root). A
saída do LLM é tratada como hipótese: toda resposta é validada contra um esquema Pydantic, e o veredito vem só da
execução. Python 3.11+ e FastAPI foram mantidos. O agente foi executado em Python 3.9 no hospedeiro de testes e os
testes rodaram na imagem Python 3.12. O código mantém compatibilidade com 3.9.

**Modelo de interação: mantido.** O agente opera integrado (API REST `/analisar`, `/gerar-testes`, `/executar`,
`/relatorio`, com contrato JSON validado, envio do resultado consolidado ao Agente de Documentação e consulta da
especificação vigente) e também de forma independente, pela CLI e pelo GitHub Actions, no gatilho por PR e por
push em `feature/**`.

**Escopo do teste.** Os 12 casos e o teste de mutação foram executados no **modo determinístico** (sem LLM),
para que os resultados fossem reprodutíveis. Os dois casos que avaliam a camada de LLM (B05 e B06) usam um LLM
simulado que injeta exatamente as falhas que um modelo real comete (JSON inválido, alvo alucinado, exceção
acidental tratada como esperada), já que essas falhas não podem ser provocadas sob demanda num modelo real. A
mesma bancada roda com o Gemini via `make avaliar-llm`. *[Se a equipe executar o modo LLM antes da entrega,
acrescentar os números aqui; caso contrário, manter esta ressalva.]*

### Casos de teste executados (mínimo de 5)

12 casos (5 típicos e 7 de borda), cada um executado **5 vezes** (60 execuções). O gabarito de defeitos de cada
caso foi fixado antes das medições.

| Nº | Cenário testado | Resultado esperado | Resultado obtido |
|---|---|---|---|
| 1 | [típico] Código correto com requisitos (sem defeito plantado) | Portão aprovado, nenhum achado de defeito e cobertura ≥ 70% | Portão aprovado; 22 testes (22 aprovados); nenhum achado; cobertura 100%. ✔ 5/5 |
| 2 | [típico] Módulo da loja com 2 defeitos plantados (`ticket_medio`, `aplicar_cupom`) | Os 2 defeitos plantados apontados e portão reprovado | Portão reprovado; 65 testes; defeitos apontados em `ticket_medio`, `aplicar_cupom` e `Estoque.adicionar`; cobertura 98%. ✔ 5/5 |
| 3 | [típico] Análise incremental: o diff altera só a função `dividir` | Cenários apenas para `dividir` e portão aprovado | Cenários só para `calc.dividir`; 9 testes; portão aprovado. ✔ 5/5 |
| 4 | [típico] Regressão: a suíte existente passava e a mudança a quebrou | Achado "regressão" em `test_dobro` e portão reprovado | Regressão apontada em `tests.test_calc::test_dobro`; portão reprovado. ✔ 5/5 |
| 5 | [típico] Contrato OpenAPI com a API da loja em execução | Testes de API gerados do contrato, executados contra a API e aprovados | 4/4 requisições conforme o contrato; portão aprovado. ✔ 5/5 |
| 6 | [borda] Entrada vazia (sem código, diff ou contrato) | Rejeição na validação do contrato, sem executar o pipeline | Rejeitada pelo esquema (`ValidationError`); pipeline não executado. ✔ 5/5 |
| 7 | [borda] Código-fonte que não compila | Risco ALTA "não compila", nenhum teste e portão reprovado | Risco ALTA registrado; 0 testes; portão reprovado. ✔ 5/5 |
| 8 | [borda] Laço infinito plantado em `fila.processar` | Testes interrompidos pelo limite por teste, achado "tempo_esgotado" e portão reprovado | 3 testes interrompidos por tempo em `fila.processar`; portão reprovado. ✔ 5/5 |
| 9 | [borda] Código que acessa a rede (bloqueada no isolamento) | Achado "dependencia_externa", nenhum falso defeito e portão reprovado | 2 achados `dependencia_externa`; 0 falsos defeitos; portão reprovado. ✔ 5/5 |
| 10 | [borda] LLM devolve respostas fora do esquema JSON | Respostas rejeitadas, queda para a heurística e pipeline concluído | Respostas rejeitadas; cenários de origem heurística; 22 testes; portão aprovado. ✔ 5/5 |
| 11 | [borda] LLM alucina alvo inexistente e legitima `ZeroDivisionError` | Alvo inexistente descartado, exceção acidental rejeitada e defeito apontado | Alvo descartado; `ZeroDivisionError` rejeitado como hipótese; defeito em `media` apontado. ✔ 5/5 |
| 12 | [borda] Código sem anotações de tipo e classe com construtor com argumentos | Risco de testabilidade registrado; o portão não aprova sem evidência executada | Risco registrado; 0 testes; portão reprovado ("nenhum teste executado"). ✔ 5/5 |

### Métricas e estatísticas coletadas

A Entrega 1 não fixou valores numéricos de aceitação. As metas abaixo foram definidas no início da Entrega 2,
**antes das medições**, a partir de elementos da própria especificação: o limiar de cobertura de 70% é o mesmo
configurado no portão do CI, e o orçamento de 60 s corresponde ao gatilho por PR.

| Métrica | Valor obtido | Meta/critério de aceitação (Entrega 1) |
|---|---|---|
| Taxa de acerto/precisão | Taxa de acerto: **100%** (12/12 casos, 60/60 execuções). Precisão na detecção de defeitos: **83,3%** (VP = 25, FP = 5) | Acerto ≥ 90% e precisão ≥ 80% — atingidas |
| Tempo médio de resposta | **1,28 s** ± 2,57 s por execução (IC 95%: ± 0,65 s; mediana 0,65 s; p95 9,63 s) | ≤ 60 s — atingida |
| Revocação na detecção de defeitos | **100%** (VP = 25, FN = 0); F1 = 90,9% | ≥ 90% — atingida |
| Falso positivo em código correto | **0%** das 35 execuções sem defeito plantado | 0% — atingida |
| Cobertura de linhas dos testes gerados | **95,5%** em média (mín. 83,3%; máx. 100%) | ≥ 70% — atingida |
| Escore de mutação (suíte gerada contra 30 mutantes) | **53,3%** (16/30) | ≥ 60% — **não atingida** |
| Detecção às cegas (agente acionado sobre o código já mutado) | **6,7%** (2/30) | sem meta (diagnóstico) |

Como as métricas foram calculadas:

- **Precisão e revocação.** Cada execução compara as unidades que o agente aponta como defeituosas (achados
  `defeito_suspeito`, `validacao_ausente`, `tempo_esgotado` e `regressao`) com o gabarito do caso. Um achado
  correto é VP; um achado fora do gabarito é FP; um defeito do gabarito que não foi apontado é FN. Os 5 FP
  correspondem a um único achado, repetido nas 5 execuções: `Estoque.adicionar(sku=None)` é aceito sem
  validação. Ele não estava no gabarito porque nenhum requisito proíbe `sku` nulo, então foi contado como erro do
  agente, mesmo sendo um achado discutível.
- **Tempo.** O tempo é medido do recebimento da entrada até o relatório. A distribuição é assimétrica: o caso 8
  (laço infinito) leva cerca de 9,7 s por esperar 3 limites de 3 s e eleva a média e o desvio-padrão. Por isso a
  mediana (0,65 s) também é reportada.
- **Escore de mutação.** 30 mutantes de primeira ordem, cada um alterando um único ponto de `precos.py`, que é
  um código correto: operadores relacional, aritmético, troca de constante e remoção de validação. A suíte gerada
  a partir do código correto roda em cada mutante; o mutante é "morto" quando algum teste falha.

### Gráfico(s) e visualização dos resultados

- `g2_metricas_vs_metas.png`: métricas obtidas comparadas às metas.
- `g1_tempo_por_caso.png`: tempo médio ± desvio-padrão por caso (5 repetições), separado em típico e borda.
- `g3_tempo_por_filtro.png`: tempo médio por filtro do pipeline. O Filtro 5 (execução isolada em Docker) responde
  por praticamente todo o tempo; os filtros de análise e geração levam milissegundos.
- `g4_mutacao.png`: mutantes detectados por operador, comparando a suíte gerada do código correto com o agente
  acionado às cegas.

### Evidência antes/depois

Artefato: `exemplos/loja/loja.py` (caso 2). Figura `g5_antes_depois.png`. Arquivos em `resultados/evidencias/`.

| | Antes (`evidencias/antes/`) | Depois (`evidencias/depois_relatorio.md` e `evidencias/workspace_depois/tests_gerados/`) |
|---|---|---|
| Testes automatizados | 0 | 65, em 3 arquivos (unitário, integração e validação de entrada) |
| Cobertura de linhas | 0% (código nunca exercitado) | 98% |
| Defeitos conhecidos | 0 | 3 unidades apontadas, com o teste que reproduz cada uma |
| Portão de qualidade | inexistente | REPROVADO, com a lista de motivos |

Trecho real do relatório gerado (`depois_relatorio.md`), para print ou citação:

```
**Portão de qualidade:** ❌ REPROVADO — 3 teste(s) reprovado(s)
| defeito_suspeito  | test_cen_…_ticket_medio_pedidos | ZeroDivisionError: division by zero |
| validacao_ausente | test_cen_…_aplicar_cupom_total_none_rejeitado | loja.aplicar_cupom aceitou entrada inválida sem rejeitá-la … retorno: None |
| validacao_ausente | test_cen_…_adicionar_sku_none_rejeitado | loja.Estoque.adicionar aceitou entrada inválida sem rejeitá-la … retorno: 7 |
```
*[Para o PDF: capturar a tela do terminal rodando `make exemplo-docker` e do arquivo `depois_relatorio.md`.]*

### Análise crítica do agente

**O que os resultados confirmam.** A especificação da Entrega 1 se confirma nos pontos estruturais:

- O pipeline Pipe-and-Filter executou os 7 filtros em todas as 60 execuções, com o contrato validado em cada
  fronteira.
- O princípio de "LLM como hipótese, nunca veredito" funcionou nos casos 10 e 11. JSON inválido não interrompe o
  pipeline, um alvo alucinado é descartado e uma exceção acidental proposta pelo LLM como "esperada" não
  legitima o defeito.
- O padrão Adapter permitiu usar o mesmo contrato `ResultadoDeTeste` para os testes de unidade e de API (caso 5).
- O Strategy separou unitário, integração, validação de entrada e API sem condicionais no núcleo.
- O isolamento em Docker, previsto na arquitetura, se mostrou necessário no caso 9: sem ele, o teste do código
  acessaria a rede de verdade.

**Ajustes de implementação que os testes exigiram.** A bancada encontrou três falhas na primeira versão, que
foram corrigidas antes da medição final:

1. **Laço infinito (caso 8).** O limite era só global (300 s). Ao estourar, todos os resultados se perdiam e o
   achado aparecia como "falha da suíte existente: framework não produziu resultados", sem apontar a unidade. Numa
   sondagem com limite global de 20 s, a resposta levou 51 s no Docker. O ajuste foi um limite por teste
   (`pytest-timeout`, `AGENTE_TIMEOUT_TESTE_S`) e a nova categoria `tempo_esgotado` no Filtro 6. Resultado: a
   unidade culpada é identificada e a resposta cai para cerca de 9,7 s.
2. **Dependência de rede (caso 9).** Código que acessa a rede gerava 5 achados `defeito_suspeito` no container sem
   rede, um falso diagnóstico. Foi criada a categoria `dependencia_externa` no Filtro 6, com a recomendação de usar
   um dublê ou um teste de integração.
3. **Valores-limite.** A primeira medição de mutação deu **20%** (6/30). Os testes de borda verificavam só
   robustez, e a análise estática lia apenas o primeiro termo de condições `a or b`, de modo que
   `percentual > 100` ficava de fora. Foram feitos dois ajustes: a leitura de todos os termos do `or` e a geração
   de cenários do **lado válido da fronteira**, por exemplo "percentual = 100 deve ser aceito" (análise de
   valor-limite, Myers et al., 2011). O escore subiu para **53,3%**, e os mutantes de remoção de validação e
   relacionais passaram a ser mortos em 100% e 83% dos casos.

**O que não se confirmou: o problema do oráculo.** O escore de 53,3% ficou abaixo da meta de 60%, e a detecção às
cegas foi de 6,7%. A causa é estrutural. Sem LLM, o oráculo de cada teste (o que ele espera como resultado) é
extraído **do próprio código**. Se o código já tem o defeito, por exemplo `frete *= 1.2` trocado por
`frete /= 1.2`, o agente gera testes coerentes com o código defeituoso. Os requisitos em linguagem natural ("acima
de 30 kg há acréscimo de 20%") são vinculados aos cenários apenas pelo identificador e não viram asserção, então
mutantes aritméticos e de constante sobrevivem (25% e 42% de detecção). Isso dá evidência quantitativa à decisão da
Entrega 1 de adotar uma base **híbrida**: transformar critérios de aceite em valores esperados exige
interpretação de linguagem natural, e esse é o papel do LLM no pipeline. O modo determinístico é confiável para
robustez, validação, contratos de API, regressão e travamentos, mas não para a correção funcional de cálculos.

**Próximos passos.**

- Medir o modo LLM com a mesma bancada (`make avaliar-llm`) e comparar o escore de mutação e a detecção às cegas.
- Oferecer, para código já aprovado, testes de caracterização (*snapshot*) como suíte de regressão. Eles matariam
  os mutantes aritméticos, mas não devem ser usados em código ainda não validado, porque legitimariam o
  comportamento atual.
- Ampliar o corpus de avaliação para Java e TypeScript: os adaptadores JUnit, Jest e Newman existem, mas só o
  fluxo Pytest foi validado de ponta a ponta.

---

## Trechos para as seções da equipe

### 2. Ambiente e Metodologia de Teste (parte do Agente de Testes)

Bancada automatizada `agente-testes avaliar` (módulo `agente_testes/avaliacao/`):

- **Ambiente.** macOS (darwin), Python 3.9.6 no hospedeiro, Docker com a imagem `agente-testes-runner-python`
  (Python 3.12, pytest 8, pytest-cov, pytest-timeout), limite de 3 s por teste e 120 s por execução.
- **Dados de entrada.** Um corpus versionado em `agente_testes/avaliacao/corpus/` e o projeto de exemplo
  `exemplos/loja` (código, `requisitos.yaml`, `openapi.yaml` e a API FastAPI levantada pela própria bancada).
- **Protocolo.** Cada caso é executado 5 vezes. Cada execução é comparada a um critério objetivo e a um gabarito de
  defeitos fixado antes das medições. Os tempos são resumidos por média, desvio-padrão, mediana, p95 e IC 95%
  (t de Student).
- **Análise de mutação.** 30 mutantes de primeira ordem gerados por AST.
- **Dados brutos.** `execucoes.csv`, `mutantes.csv` e `resultados.json`.

### 4. Consolidação Estatística Geral — linha deste agente

| Agente | Nº de testes | Taxa de sucesso | Tempo médio (s) |
|---|---|---|---|
| Agente de Testes de Software | 12 casos (60 execuções) | 100% | 1,28 |

### 5. Demonstração dos Resultados

`make exemplo-docker` (relatório da loja no terminal), `make api` com `POST /executar` em
`http://localhost:8000/docs`, e o workflow `.github/workflows/agente-testes.yml` comentando o relatório no PR.
*[Inserir os prints.]*

### 8. Referências adicionais (além das da Entrega 1)

- FEATHERS, Michael. *Working Effectively with Legacy Code*. Upper Saddle River: Prentice Hall, 2004.
- JIA, Yue; HARMAN, Mark. An Analysis and Survey of the Development of Mutation Testing. *IEEE Transactions on
  Software Engineering*, v. 37, n. 5, p. 649-678, 2011.
- BARR, Earl T. et al. The Oracle Problem in Software Testing: A Survey. *IEEE Transactions on Software
  Engineering*, v. 41, n. 5, p. 507-525, 2015.
- PYTEST-TIMEOUT. pytest-timeout documentation.
- MATPLOTLIB. Matplotlib documentation.
