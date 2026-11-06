# Agente Inteligente de Testes de Software

Implementação do agente especificado em `../Agentes - ESA.pdf`. O agente recebe código-fonte (arquivos
completos ou diff) e requisitos. A partir deles, ele deriva cenários de **sucesso, falha e borda**, gera testes
automatizados no framework do projeto, executa esses testes em um **container Docker isolado** e interpreta os
resultados. Ao final, produz um relatório com aprovados, reprovados, erros, cobertura, trechos não cobertos e
riscos. O relatório funciona como **portão de qualidade** (ODS 9, metas 9.4 e 9.5).

## Como rodar

```bash
make instalar          # cria .venv e instala o pacote (comando `agente-testes`)
make imagens           # constrói a imagem de execução isolada (Docker)
make testes            # suíte do próprio agente
make exemplo-docker    # roda o agente no projeto de exemplo exemplos/loja
make api               # API REST em http://localhost:8000/docs
```

Modelo de linguagem (opcional; sem ele o agente funciona em **modo heurístico**, com análise por AST e
templates determinísticos):

| Variável | Efeito |
|---|---|
| `GEMINI_API_KEY` (+ `GEMINI_MODEL`, padrão `gemini-3.5-flash`; `GEMINI_MODELOS_ALTERNATIVOS`, padrão `gemini-3.8-flash`) | usa Google Gemini |
| `LLM_BASE_URL`, `LLM_MODEL`, `LLM_API_KEY` | qualquer modelo com API compatível (`/chat/completions`) |
| `AGENTE_LLM=nenhum` | força o modo heurístico |
| `AGENTE_EXECUTOR` = `auto` \| `docker` \| `local` | `auto` usa Docker se a imagem existir |
| `AGENTE_COBERTURA_MINIMA` | cobertura mínima (%) para aprovar o portão |
| `AGENTE_MAX_ITERACOES` | máximo de ciclos de regeneração (padrão 3) |
| `AGENTE_DOCUMENTACAO_URL` | URL do Agente de Documentação (integração opcional) |

### Exemplos de CLI

```bash
# pipeline completo sobre arquivos, com requisitos e contrato OpenAPI
agente-testes executar exemplos/loja/loja.py --raiz exemplos/loja \
  --requisitos exemplos/loja/requisitos.yaml \
  --openapi exemplos/loja/openapi.yaml --api-base-url http://localhost:8001

# apenas o que mudou desde a main (o mesmo modo usado no CI)
agente-testes executar --raiz . --diff-base origin/main --incluir-projeto --saida-md relatorio.md

agente-testes analisar src/          # filtros 0-2: contexto, riscos e cenários
agente-testes gerar src/ --destino . # filtros 0-4: grava os testes gerados sem executar
```

No exemplo `loja`, o agente aponta os dois defeitos plantados: `ticket_medio([])` gera `ZeroDivisionError`, o que
viola o critério do RF-03, e `aplicar_cupom(total=None)` é aceito sem validação. Ele também encontra um terceiro
problema: `Estoque.adicionar(sku=None)` é aceito sem validação.

### API REST (Controller do MVC)

| Endpoint | Pipeline | Retorno |
|---|---|---|
| `POST /analisar` | filtros 0-2 | intenção, unidades, riscos e cenários em linguagem natural |
| `POST /gerar-testes` | filtros 0-4 | plano por estratégia e código dos testes |
| `POST /executar` | filtros 0-6 + laço de regeneração | `Relatorio` persistido |
| `GET /relatorio`, `GET /relatorio/{id}`, `GET /relatorio/{id}/markdown` | — | consulta |

O corpo das requisições segue o contrato `EntradaAgente` (`agente_testes/contratos.py`): `arquivos`, `diff`,
`requisitos`, `descricao_funcionalidade`, `casos_de_uso`, `contrato_openapi`, `testes_existentes`,
`relatorios_anteriores`, `framework`, `tipos_teste` e `api_base_url`.

## Correspondência com a especificação

| Especificação | Onde está |
|---|---|
| **Pipe-and-Filter** | `pipeline/base.py`: `Filtro` e `Pipeline`, com validação do contrato em cada fronteira, trilha de auditoria e reexecução a partir de qualquer filtro |
| 0. Recebimento e normalização | `pipeline/filtros/f0_normalizacao.py`: detecção de linguagem e framework, interpretação do diff e leitura do OpenAPI |
| 1. Analisador de Contexto (LLM + AST/OpenAPI) | `f1_contexto.py`, `analise/estatica_python.py`, `analise/estatica_generica.py`, `analise/openapi.py` |
| 2. Gerador de Cenários | `f2_cenarios.py`, `analise/cenarios_heuristicos.py` |
| 3. Seleção da Estratégia (**Strategy**) | `f3_estrategia.py`, `estrategias/estrategias.py`: unitário, integração, contrato de API, validação de entrada e E2E |
| 4. Gerador de Código (**Factory Method**) | `f4_codigo.py`, `geradores/geradores.py`: `CriadorDeGerador.criar_gerador()` e criadores concretos |
| Adaptadores de framework (**Adapter**) | `adaptadores/`: Pytest, JUnit 5 (+JaCoCo), Jest/Vitest e Newman convertidos para `ResultadoDeTeste`/`Cobertura` |
| 5. Executor isolado (Docker) | `f5_execucao.py`, `execucao/executores.py`: `--network none`, limites de CPU, memória e PIDs, usuário não-root e `no-new-privileges` |
| 6. Analisador de Resultados | `f6_resultados.py`: classifica cada achado como defeito suspeito, validação ausente, erro no teste, regressão ou falha da suíte existente, e mapeia trechos não cobertos para as funções |
| Seta "falhas recorrentes: regenerar cenários" | `agente.py`: erros atribuídos ao teste gerado voltam ao Filtro 2 como feedback ao LLM |
| **GRASP Controller / Low Coupling** | `controlador.py` (sem regra de negócio); os filtros só se comunicam por `contratos.py` (Pydantic) |
| **MVC** | Model: `modelos/dominio.py` (Projeto, Requisito, CenarioDeTeste, CasoDeTeste, ExecucaoDeTeste, ResultadoDeTeste, Relatorio) e `modelos/repositorio.py`. View: JSON e `visoes/markdown.py`. Controller: `api/app.py` |
| LLM como hipótese, nunca como veredito | `llm/cliente.py`: toda resposta é validada contra um esquema Pydantic, com nova tentativa e queda para heurística; o código gerado passa por validação de sintaxe; alvos inexistentes são descartados; o veredito vem só da execução |
| Gatilho híbrido | sob demanda (API/CLI) e por evento (`.github/workflows/agente-testes.yml` em PR e push para `feature/**`) |
| Interação com outros agentes | `integracoes/agente_documentacao.py`: envia o resultado consolidado e consulta a especificação vigente |

## Limitações conhecidas

- No modo heurístico, os testes de sucesso e de borda verificam **robustez**: ausência de exceção não documentada
  e tipo do retorno. Valores esperados exatos vêm dos cenários do LLM, que também são tratados como hipótese.
- Java e JavaScript/TypeScript têm análise estática leve, feita por regex, e a geração de código para essas
  linguagens depende do LLM. Os adaptadores JUnit, Jest e Newman estão implementados, mas apenas o fluxo Pytest
  foi validado de ponta a ponta. A execução JUnit exige um `pom.xml` com JaCoCo no projeto.
- Quando há testes de API, o container recebe rede (bridge) para alcançar `API_BASE_URL`. Endereços `localhost`
  são reescritos para `host.docker.internal`.
- O código é compatível com Python 3.9+. As imagens Docker usam 3.12, conforme a especificação (3.11+).
