# Planejamento do Projeto Comunitário de Análise de Dados do Saúde Caixa

## 1. Contexto

Este projeto tem como objetivo construir uma base analítica comunitária, aberta e reproduzível sobre o **Saúde Caixa**, utilizando **dados públicos disponibilizados pela ANS**.

A motivação principal é transformar dados públicos dispersos em um ativo de transparência e análise, permitindo examinar dimensões como:

- rede de atendimento;
- qualidade do atendimento;
- relação entre beneficiários e rede credenciada;
- perfil demográfico;
- indicadores econômico-financeiros;
- evolução temporal do plano e de sua estrutura assistencial.

---

## 2. Situação atual

### Já realizado

O projeto já avançou na construção da camada inicial de ingestão de dados:

1. **Catálogo de dados em notebook Jupyter**
   - Estrutura inicial para concentrar as bases públicas da ANS.
   - Registro do código necessário para obtenção de cada base.
   - Organização inicial da documentação de entrada.

2. **Função geral de download e mesclagem**
   - Responsável por baixar arquivos e consolidar bases relacionadas.
   - Serve como núcleo operacional da etapa de ingestão.

3. **Separação em funções especializadas**
   - Função exclusiva para download.
   - Função exclusiva para mesclagem.
   - Melhoria de reutilização, manutenção e testabilidade.

### Diagnóstico da fase atual

O projeto encontra-se em uma fase de **fundação técnica**, já com capacidade inicial de obtenção e consolidação dos dados, mas ainda precisando evoluir nas camadas de:

- padronização;
- qualidade de dados;
- integração entre bases;
- modelagem analítica;
- produção de indicadores e visualizações.

---

## 3. Objetivos do planejamento

Este planejamento busca:

- organizar a evolução do projeto por etapas;
- priorizar entregas de maior impacto;
- reduzir retrabalho;
- facilitar documentação e colaboração;
- transformar o projeto em uma base analítica sustentável.

---

## 4. Objetivo geral

Construir uma plataforma analítica comunitária baseada em dados públicos da ANS para aumentar a transparência sobre o Saúde Caixa e apoiar análises consistentes sobre sua estrutura, desempenho e contexto assistencial.

---

## 5. Objetivos específicos

### Dados

- Catalogar todas as bases públicas relevantes.
- Automatizar a obtenção periódica dos arquivos.
- Criar trilha reprodutível entre origem, transformação e saída.

### Engenharia de dados

- Padronizar formatos, nomes de colunas e metadados.
- Estruturar camadas de dados brutos, intermediários e tratados.
- Criar rotinas de validação e controle de qualidade.

### Análise

- Definir indicadores prioritários.
- Produzir análises descritivas e comparativas.
- Desenvolver uma visão integrada de beneficiários, rede e finanças.

### Transparência

- Disponibilizar documentação clara.
- Tornar as análises auditáveis e replicáveis.
- Facilitar participação comunitária no projeto.

---

## 6. Perguntas estratégicas do projeto

### 6.1 Rede credenciada

- A rede acompanha adequadamente o tamanho da população coberta?
- Há desequilíbrios geográficos ou por tipo de prestador?
- Existem períodos de expansão ou retração relevantes?

### 6.2 Beneficiários

- Como evolui o número de beneficiários ao longo do tempo?
- Qual é o perfil demográfico observável nas bases públicas?
- Há mudanças de composição importantes?

### 6.3 Qualidade e acesso

- Existem indicadores públicos que permitam observar qualidade ou suficiência da rede?
- Há sinais indiretos de gargalos assistenciais?

### 6.4 Finanças e sustentabilidade

- Como se comportam indicadores financeiros disponíveis?
- Há associação entre expansão/redução da rede e variáveis econômico-financeiras?

### 6.5 Transparência pública

- Como traduzir dados técnicos em informações acessíveis para a comunidade?

---

## 7. Macroetapas do projeto

## Etapa 1 — Catalogação e inventário de bases

### Objetivo

Mapear, listar e documentar todas as bases públicas relevantes da ANS.

### Entregas

- Notebook de catálogo de dados.
- Lista padronizada de fontes.
- Metadados mínimos por base:
  - nome;
  - descrição;
  - periodicidade;
  - formato;
  - URL/fonte;
  - granularidade;
  - possíveis chaves de integração;
  - limitações conhecidas.

### Critério de conclusão

Todas as bases prioritárias do projeto identificadas e documentadas.

---

## Etapa 2 — Ingestão automatizada

### Objetivo

Garantir obtenção reprodutível dos arquivos públicos.

### Entregas

- Função geral de download e mesclagem documentada.
- Função de download isolada documentada.
- Função de mesclagem isolada documentada.
- Estrutura de pastas para dados brutos.
- Registro de logs de execução.

### Evoluções desejadas

- controle de versões dos arquivos baixados;
- identificação automática de mudanças de layout;
- geração de manifesto de arquivos processados.

### Critério de conclusão

Execução confiável da obtenção de dados prioritários com mínimo esforço manual.

---

## Etapa 3 — Padronização e qualidade de dados

### Objetivo

Transformar arquivos heterogêneos em bases consistentes para análise.

### Entregas

- Padronização de encoding, separadores e nomes de colunas.
- Conversão para formatos mais eficientes quando necessário.
- Regras de tratamento de dados ausentes.
- Validação de duplicidades.
- Validação de esquema por base.
- Dicionário de dados operacional.

### Critério de conclusão

Bases tratadas com qualidade mínima documentada e prontas para integração.

---

## Etapa 4 — Integração entre bases

### Objetivo

Relacionar dados de beneficiários, rede, indicadores assistenciais e finanças.

### Entregas

- Mapa de chaves de relacionamento.
- Tabelas analíticas intermediárias.
- Camada de dados processados por tema.
- Documentação das regras de integração.

### Critério de conclusão

Existência de datasets analíticos reutilizáveis para múltiplos notebooks e relatórios.

---

## Etapa 5 — Análises exploratórias

### Objetivo

Produzir as primeiras análises descritivas e hipóteses de investigação.

### Entregas

- Notebooks temáticos.
- Gráficos exploratórios.
- Séries temporais básicas.
- Tabelas-resumo por tema.

### Temas iniciais sugeridos

- evolução do número de beneficiários;
- evolução da rede credenciada;
- relação beneficiários/rede;
- distribuição geográfica;
- indicadores financeiros principais;
- comparativos temporais.

### Critério de conclusão

Primeiro conjunto de análises públicas reproduzíveis e documentadas.

---

## Etapa 6 — Indicadores e painéis

### Objetivo

Estruturar indicadores de acompanhamento recorrente.

### Entregas

- Lista de KPIs do projeto.
- Definições metodológicas de cada indicador.
- Painéis ou tabelas consolidadas.
- Camada de outputs para comunicação pública.

### Indicadores sugeridos

- número de beneficiários;
- variação temporal de beneficiários;
- volume de prestadores por categoria;
- razão beneficiários/prestador;
- cobertura por localidade, quando possível;
- indicadores financeiros selecionados;
- indicadores assistenciais disponíveis;
- completude e atualização das bases.

### Critério de conclusão

Conjunto inicial de indicadores estáveis, documentados e reaproveitáveis.

---

## Etapa 7 — Comunicação e transparência

### Objetivo

Traduzir resultados técnicos em materiais públicos compreensíveis.

### Entregas

- README robusto no GitHub.
- documentação metodológica;
- notas técnicas;
- relatórios sintéticos;
- visualizações interpretáveis;
- glossário de termos.

### Critério de conclusão

Projeto acessível tanto para perfil técnico quanto para público geral interessado.

---

## 8. Roadmap futuro sugerido

## Curto prazo (0 a 1 mês)

### Prioridades

- finalizar o catálogo de dados inicial;
- documentar formalmente as funções já criadas;
- padronizar a estrutura do repositório;
- separar dados em camadas (`raw`, `interim`, `processed`);
- selecionar as bases prioritárias para o Saúde Caixa;
- criar o primeiro dicionário de dados resumido;
- produzir um notebook de exploração inicial.

### Entregas esperadas

- repositório organizado;
- documentação mínima publicável;
- pipeline inicial funcional;
- primeira versão do inventário de bases.

---

## Médio prazo (1 a 3 meses)

### Prioridades

- implementar validações de qualidade por base;
- estruturar datasets analíticos por tema;
- produzir análises exploratórias recorrentes;
- definir indicadores principais;
- começar a gerar outputs consolidados para comunicação.

### Entregas esperadas

- primeiras análises comparativas;
- tabelas analíticas reutilizáveis;
- metodologia inicial documentada;
- primeira versão de painéis ou relatórios.

---

## Longo prazo (3 a 6 meses)

### Prioridades

- amadurecer a governança do projeto;
- automatizar atualização de bases;
- melhorar performance para grandes volumes de dados;
- ampliar comparações históricas;
- consolidar a camada de comunicação pública.

### Entregas esperadas

- pipeline estável e mais automatizado;
- indicadores recorrentes;
- documentação madura;
- ecossistema de notebooks e relatórios temáticos.

---

## 9. Frentes de trabalho futuras

## 9.1 Frente de dados e catálogo

Responsável por mapear, atualizar e documentar fontes.

### Tarefas

- revisar fontes da ANS;
- acompanhar mudanças de layout;
- atualizar metadados;
- manter catálogo vivo.

## 9.2 Frente de engenharia de dados

Responsável por ingestão, padronização e processamento.

### Tarefas

- robustecer funções existentes;
- registrar logs e manifests;
- criar validações automáticas;
- preparar formatos eficientes para análise.

## 9.3 Frente analítica

Responsável por hipóteses, indicadores e estudos temáticos.

### Tarefas

- definir perguntas prioritárias;
- construir métricas;
- interpretar resultados;
- documentar limitações.

## 9.4 Frente de documentação e transparência

Responsável por tornar o projeto compreensível e auditável.

### Tarefas

- README;
- notas metodológicas;
- glossário;
- documentação dos dados e transformações.

---

## 10. Estrutura analítica sugerida por camadas

### Camada 1 — Dados brutos

Arquivos originais baixados das fontes públicas.

### Camada 2 — Dados intermediários

Arquivos tratados minimamente, padronizados e mesclados quando necessário.

### Camada 3 — Dados processados

Tabelas analíticas organizadas por tema.

### Camada 4 — Indicadores

Métricas já calculadas e prontas para visualização.

### Camada 5 — Comunicação

Relatórios, gráficos, dashboards e notas técnicas.

---

## 11. Riscos e cuidados

### Riscos técnicos

- mudança de estrutura das páginas e diretórios;
- alteração de schema nas bases;
- inconsistências entre períodos;
- arquivos corrompidos ou incompletos;
- limitações de performance em arquivos grandes.

### Riscos analíticos

- comparação inadequada entre bases de granularidade distinta;
- interpretação excessiva de indicadores indiretos;
- inferências não suportadas pelos dados públicos.

### Mitigações

- documentar premissas;
- registrar transformações;
- validar consistência por período;
- separar claramente dado, indicador e interpretação.

---

## 12. Critérios de sucesso do projeto

O projeto será bem-sucedido se conseguir:

- organizar as bases públicas mais relevantes para o tema;
- manter uma trilha reprodutível de obtenção e tratamento;
- produzir indicadores compreensíveis e verificáveis;
- documentar limitações e metodologia com clareza;
- facilitar o uso comunitário e a colaboração técnica.

---

## 13. Próximas ações práticas recomendadas

### Ação 1 — Fechar o inventário inicial

Criar uma tabela mestra com todas as bases candidatas.

### Ação 2 — Priorizar fontes

Classificar as bases em:

- essenciais;
- complementares;
- exploratórias.

### Ação 3 — Formalizar metadados

Para cada base, registrar:

- origem;
- periodicidade;
- formato;
- granularidade;
- chave de identificação;
- uso pretendido no projeto.

### Ação 4 — Documentar as funções existentes

Criar documentação objetiva para:

- função geral de download e mesclagem;
- função de download;
- função de mesclagem.

### Ação 5 — Criar primeiro pipeline analítico

Escolher um tema inicial, por exemplo:

- beneficiários;
- rede credenciada;
- indicador financeiro.

### Ação 6 — Publicar primeira entrega mínima viável

Publicar o repositório com:

- README;
- planejamento;
- catálogo inicial;
- notebook exploratório;
- documentação das funções.

---

## 14. Sugestão de priorização analítica

Se for necessário escolher uma ordem de ataque, a sequência recomendada é:

1. **Catalogação das bases**
2. **Robustez da ingestão**
3. **Padronização e qualidade**
4. **Integração entre bases**
5. **Análises descritivas**
6. **Indicadores recorrentes**
7. **Comunicação pública**

Essa ordem reduz o risco de construir análises sobre bases ainda instáveis.

---

## 15. Visão de futuro

No estágio mais maduro, este projeto pode se tornar:

- um repositório de referência sobre bases públicas da ANS aplicadas ao Saúde Caixa;
- uma base comunitária de monitoramento e transparência;
- um conjunto de pipelines reproduzíveis de dados públicos em saúde suplementar;
- uma plataforma para análises periódicas, notas técnicas e painéis temáticos.

---

## 16. Resumo executivo

### Já existe

- propósito claro;
- recorte temático definido;
- catálogo de dados iniciado;
- funções centrais de ingestão e mesclagem já construídas.

### Falta consolidar

- governança do repositório;
- padronização definitiva dos dados;
- integração analítica entre bases;
- indicadores principais;
- comunicação pública mais estruturada.

### Próximo marco recomendado

Publicar uma **versão mínima viável do repositório**, contendo documentação, catálogo inicial, funções já desenvolvidas e uma primeira análise exploratória reproduzível.
