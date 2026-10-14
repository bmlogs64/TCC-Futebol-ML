# Sistema de Recomendação de Jogadores de Futebol

Trabalho de Conclusão de Curso desenvolvido no curso de Ciência da Computação da UNIJORGE.

O projeto aplica técnicas de Machine Learning ao processo de scouting no futebol, buscando identificar jogadores com perfil estatístico semelhante ao de um atleta utilizado como referência e, entre os candidatos encontrados, priorizar alternativas com menor valor de mercado e idade favorável.

O sistema foi desenvolvido a partir de dados da temporada 2024/2025 e disponibiliza as recomendações finais por meio de uma API desenvolvida com FastAPI.

---

## Objetivo

O objetivo do sistema é apoiar a etapa inicial do processo de scouting por meio da identificação de jogadores estatisticamente semelhantes a um atleta de referência.

A recomendação considera três componentes principais:

- similaridade técnica;
- vantagem relativa de valor de mercado;
- idade.

O objetivo não é determinar automaticamente uma contratação nem substituir a análise realizada por scouts, analistas de desempenho ou outros profissionais.

A proposta funciona como um mecanismo de triagem capaz de reduzir o universo inicial de atletas que precisam ser avaliados de forma mais aprofundada.

---

## Bases de dados

Foram utilizadas duas bases disponibilizadas no Kaggle.

### Estatísticas de desempenho

Dataset:

```text
hubertsidorowicz/football-players-stats-2024-2025
```

Versão utilizada durante a execução final do notebook:

```text
43
```

A base contém estatísticas de desempenho de jogadores das principais ligas europeias na temporada 2024/2025.

---

### Dados de mercado

Dataset:

```text
davidcariboo/player-scores
```

Versão utilizada durante a execução final do notebook:

```text
679
```

Foram utilizados principalmente os arquivos:

```text
players.csv
player_valuations.csv
```

Para evitar a utilização de informações posteriores ao período analisado, foram consideradas somente avaliações de mercado realizadas até:

```text
30/06/2025
```

---

## Integração das bases

As bases estatística e de mercado não possuem um identificador comum de jogador.

Por esse motivo, foi desenvolvido um processo de associação entre os registros das duas fontes.

O processo utiliza informações como:

- nome normalizado;
- aliases de nome;
- ano de nascimento;
- posição;
- clube;
- histórico de clubes;
- similaridade textual.

Quando não existiam evidências suficientes para determinar a identidade do jogador com confiança, o registro era mantido sem associação.

Ao final do processo:

```text
2.607 de 2.854 linhas foram associadas
```

correspondendo a aproximadamente:

```text
91,35%
```

de cobertura.

Os 247 registros restantes permaneceram sem correspondência por não apresentarem evidências suficientes para uma associação considerada confiável.

---

## Consolidação dos jogadores

Jogadores que atuaram por mais de um clube durante a temporada podem aparecer em múltiplas linhas na base estatística.

Esses registros foram consolidados utilizando o `player_id` do Transfermarkt antes da aplicação definitiva do filtro de minutos.

Esse procedimento evita, por exemplo, que um jogador seja eliminado por possuir menos de 900 minutos em cada clube individualmente, mesmo tendo ultrapassado esse limite quando toda a temporada é considerada.

Após a associação das bases, as 2.607 linhas correspondentes resultaram em:

```text
2.469 jogadores identificados de forma única
```

Somente depois da consolidação foi aplicado o limite mínimo de:

```text
900 minutos
```

O limite foi definido para reduzir a influência de amostras muito pequenas nas métricas utilizadas pelos modelos.

Após o tratamento, a base utilizada na modelagem ficou com:

```text
1.494 jogadores únicos
```

---

## Grupos posicionais

Os jogadores foram organizados em quatro grupos:

```text
FW - atacantes
MF - meio-campistas
DF - defensores
GK - goleiros
```

A distribuição foi:

```text
FW - 471
MF - 696
DF - 638
GK - 114
```

A soma dos grupos é superior ao número de jogadores únicos porque atletas classificados em posições híbridas podem participar de mais de um grupo posicional.

---

## Variáveis de desempenho

As características utilizadas para representar os jogadores variam de acordo com o grupo posicional.

### Atacantes — FW

São utilizadas 11 características relacionadas principalmente a:

- gols;
- gols esperados sem pênalti;
- finalizações;
- finalizações no alvo;
- eficiência de finalização;
- recepções progressivas;
- conduções progressivas;
- ações que geram finalização;
- ações que geram gol.

### Meio-campistas — MF

São utilizadas 14 características relacionadas a:

- participação ofensiva;
- gols esperados;
- assistências esperadas;
- finalizações;
- passes;
- passes-chave;
- progressão;
- condução;
- criação;
- recuperação de bola.

### Defensores — DF

São utilizadas 11 características relacionadas a:

- desarmes;
- interceptações;
- bloqueios;
- cortes;
- duelos aéreos;
- passes;
- progressão;
- cruzamentos.

### Goleiros — GK

São utilizadas 8 características específicas da posição:

- gols sofridos por 90 minutos;
- percentual de defesas;
- percentual de jogos sem sofrer gols;
- PSxG por finalização no alvo;
- diferença entre PSxG e gols sofridos;
- cruzamentos interceptados;
- ações defensivas fora da área;
- lançamentos longos.

Métricas por 90 minutos, percentuais e razões foram recalculadas após a consolidação dos registros.

---

## Padronização

Antes da aplicação dos modelos, as características são padronizadas utilizando:

```text
StandardScaler
```

A transformação evita que métricas com escalas numéricas maiores exerçam influência desproporcional sobre os cálculos de distância.

Para cada grupo posicional é utilizado um `StandardScaler` específico, ajustado sobre as características correspondentes à posição.

---

## Modelos avaliados

Foram avaliadas três abordagens de Machine Learning:

### K-Nearest Neighbors — KNN

O KNN identifica diretamente os jogadores mais próximos de um atleta de referência no espaço das características padronizadas.

A similaridade é baseada na distância euclidiana entre os vetores dos jogadores.

### K-Means

O K-Means organiza os jogadores em clusters com características estatísticas semelhantes.

As recomendações são analisadas considerando inicialmente jogadores pertencentes ao mesmo agrupamento do atleta de referência.

### Autoencoder

Também foi utilizada uma rede neural do tipo Autoencoder.

O modelo aprende uma representação compacta das características dos jogadores e a similaridade é posteriormente analisada no espaço latente produzido pela rede.

---

## Avaliação dos modelos

Como não existe uma variável que indique qual jogador representa o "substituto correto" de outro atleta, o problema não foi tratado como uma classificação supervisionada tradicional.

A subposição registrada no Transfermarkt foi utilizada como uma informação externa para comparar a coerência funcional das recomendações.

A subposição:

- não participou do treinamento;
- não participou do cálculo da similaridade;
- foi utilizada somente como critério externo de comparação.

A avaliação considerou:

```text
1.805 observações jogador-posição
1.380 jogadores únicos
```

entre atacantes, meio-campistas e defensores.

Os goleiros não foram utilizados nessa comparação porque todos os jogadores desse grupo apresentavam a mesma subposição.

Os resultados gerais foram:

| Modelo | Top-5 mesma subposição | Top-1 mesma subposição |
| --- | ---: | ---: |
| KNN | 48,00% | 49,31% |
| K-Means | 47,75% | 48,86% |
| Autoencoder | 45,19% | 46,59% |

Esses valores devem ser interpretados como indicadores comparativos entre os modelos e não como uma medida de acurácia na identificação de substitutos.

---

## Bootstrap

Além da comparação das médias, foi realizada uma análise por bootstrap pareado.

Configuração utilizada:

```text
Reamostragens: 10.000
Semente aleatória: 42
Intervalo de confiança: 95%
```

Como um mesmo jogador pode participar de mais de um grupo posicional, o bootstrap foi realizado de forma agrupada pelo identificador do atleta.

A análise mostrou que KNN e K-Means apresentaram resultados próximos nos critérios avaliados.

---

## Modelo escolhido

O KNN foi escolhido como método principal para o sistema final.

A decisão não foi baseada apenas em uma pequena diferença numérica entre os resultados.

O método apresenta uma relação direta com o objetivo do sistema:

```text
Jogador de referência
        ↓
Busca direta pelos jogadores mais próximos
```

Além disso, a implementação do KNN permite recuperar diretamente os vizinhos mais próximos do jogador consultado.

Foi mantido um modelo específico para cada grupo:

```text
knn_fw.joblib
knn_mf.joblib
knn_df.joblib
knn_gk.joblib
```

---

## Pool técnico

Para uma recomendação, o sistema começa recuperando:

```text
30 jogadores tecnicamente mais próximos
```

do atleta utilizado como referência.

O próprio jogador de referência é retirado da lista.

A distância euclidiana é calculada utilizando as características padronizadas correspondentes ao grupo posicional.

---

## Índice Técnico Bruto

A distância euclidiana é inicialmente normalizada pela quantidade de características utilizadas na posição:

```text
Distância Normalizada =
Distância Euclidiana / √n
```

em que:

```text
n = quantidade de características do grupo posicional
```

Em seguida é calculado:

```text
Índice Técnico Bruto =
100 / (1 + Distância Normalizada)
```

Quanto menor a distância entre os jogadores, maior o Índice Técnico Bruto.

---

## Score Técnico

Após a obtenção do pool técnico, o Índice Técnico Bruto é normalizado entre os candidatos que possuem os dados necessários para o ranking.

O resultado é convertido para uma escala entre:

```text
0 e 100
```

O candidato tecnicamente mais próximo recebe o maior Score Técnico dentro do pool analisado.

O Score Técnico é uma medida relativa dentro do conjunto de candidatos e não representa uma probabilidade de sucesso de contratação ou uma porcentagem absoluta de semelhança.

---

## Restrição financeira

Depois do cálculo do componente técnico, o sistema remove candidatos cujo valor de mercado seja igual ou superior ao valor do jogador de referência.

A condição utilizada é:

```text
Valor do candidato < Valor da referência
```

Essa regra garante que o ranking final contenha apenas alternativas com menor valor de mercado segundo os dados utilizados pelo projeto.

---

## Score Financeiro

Para os candidatos financeiramente elegíveis, é calculada a economia percentual em relação ao jogador de referência.

A fórmula é:

```text
Score Financeiro =

(Valor da referência - Valor do candidato)
------------------------------------------------ × 100
              Valor da referência
```

Quanto maior a diferença de valor de mercado, maior o Score Financeiro.

Esse componente representa somente a vantagem relativa de valor de mercado e não mede a qualidade técnica do atleta.

---

## Score de Idade

A idade é utilizada como critério complementar.

A fórmula é:

```text
Score Idade =
50 + (Idade da referência - Idade do candidato) × 5
```

O resultado é limitado ao intervalo:

```text
0 a 100
```

Interpretação:

```text
mesma idade → 50 pontos

1 ano mais jovem → 55 pontos
2 anos mais jovem → 60 pontos

1 ano mais velho → 45 pontos
2 anos mais velho → 40 pontos
```

A idade possui influência menor que os componentes técnico e financeiro.

---

## Score Final

O ranking utiliza três componentes:

```text
55% - Score Técnico
35% - Score Financeiro
10% - Score de Idade
```

A fórmula utilizada é:

```text
Score Final =
0.55 × Score Técnico
+ 0.35 × Score Financeiro
+ 0.10 × Score de Idade
```

Os pesos representam parâmetros metodológicos definidos para o projeto e não parâmetros aprendidos automaticamente pelo modelo.

A similaridade técnica permanece como o componente de maior influência.

---

## Configuração do ranking

A configuração utilizada pela API é armazenada em:

```text
modelos/configuracao_ranking.json
```

Configuração atual:

```json
{
    "modelo_tecnico": "KNN",
    "tamanho_pool_tecnico": 30,
    "peso_tecnico": 0.55,
    "peso_financeiro": 0.35,
    "peso_idade": 0.10,
    "restricao_financeira": "valor_candidato < valor_referencia",
    "data_limite_mercado": "2025-06-30"
}
```

Isso permite separar os parâmetros de configuração da implementação da API.

---

## Análise de sensibilidade

Foram comparadas três configurações de pesos:

```text
60% técnico + 30% financeiro + 10% idade
55% técnico + 35% financeiro + 10% idade
50% técnico + 40% financeiro + 10% idade
```

A análise utilizou quatro jogadores de referência:

```text
Kylian Mbappé
Kevin De Bruyne
Virgil van Dijk
Alisson
```

Considerando os quatro casos, a configuração 55/35/10 manteve:

```text
20 de 20 nomes
```

quando comparada a 60/30/10, correspondendo a:

```text
100%
```

de permanência no Top-5.

Quando comparada a 50/40/10, foram mantidos:

```text
18 de 20 nomes
```

correspondendo a:

```text
90%
```

Os resultados indicaram estabilidade do conjunto de candidatos dentro das configurações avaliadas.

A análise, entretanto, não permite afirmar que 55/35/10 seja uma combinação estatisticamente ótima ou universal.

---

## Exemplo de funcionamento

Para Kylian Mbappé, o fluxo completo é:

```text
Kylian Mbappé
        ↓
Grupo posicional FW
        ↓
Seleção das 11 características de atacantes
        ↓
StandardScaler
        ↓
KNN
        ↓
30 jogadores tecnicamente mais próximos
        ↓
Distância Euclidiana
        ↓
Índice Técnico Bruto
        ↓
Score Técnico
        ↓
Filtro de valor de mercado
        ↓
Score Financeiro
        ↓
Score de Idade
        ↓
Score Final
        ↓
Ranking de recomendação
```

No caso utilizado no trabalho, Mbappé apresentava valor de mercado de:

```text
€ 180 milhões
```

O Top-5 produzido pelo sistema foi:

| Rank | Jogador | Técnico | Financeiro | Idade | Final | Valor (€ mi) |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Leroy Sané | 100,00 | 82,22 | 35 | 87,28 | 32 |
| 2 | Ferrán Torres | 78,92 | 77,78 | 55 | 76,13 | 40 |
| 3 | Ousmane Dembélé | 85,99 | 50,00 | 40 | 68,80 | 90 |
| 4 | Omar Marmoush | 77,52 | 58,33 | 50 | 68,05 | 75 |
| 5 | Mohamed Salah | 66,76 | 72,22 | 15 | 63,50 | 50 |

O sistema não seleciona necessariamente o jogador mais barato ou o mais jovem.

A posição final depende da combinação dos três componentes.

---

# API

O sistema final é disponibilizado por meio de uma API construída com:

```text
FastAPI
```

O servidor é executado utilizando:

```text
Uvicorn
```

Ao iniciar a aplicação, os modelos KNN e os dados financeiros já processados são carregados diretamente dos arquivos armazenados na pasta `modelos`.

Dessa forma, não é necessário executar novamente todo o treinamento para utilizar a API.

---

## Endpoints

### Página inicial

```http
GET /
```

Retorna informações básicas do sistema, modelo técnico utilizado, pesos do ranking e endereço da documentação.

---

### Health Check

```http
GET /health
```

Verifica se a aplicação está ativa e informa os modelos carregados.

Exemplo de resposta:

```json
{
    "status": "ok",
    "modelos": [
        "FW",
        "MF",
        "DF",
        "GK"
    ],
    "jogadores": {
        "FW": 471,
        "MF": 696,
        "DF": 638,
        "GK": 114
    }
}
```

---

### Busca de jogadores

```http
GET /jogadores?q=mbappe
```

Permite localizar jogadores disponíveis no sistema.

O endpoint realiza normalização textual para facilitar a busca por nomes.

---

### Recomendações

```http
GET /recomendacoes
```

Parâmetros:

```text
jogador
posicao
quantidade
```

As posições permitidas são:

```text
FW
MF
DF
GK
```

Exemplo:

```http
/recomendacoes?jogador=Kylian%20Mbappé&posicao=FW&quantidade=5
```

A resposta contém, para cada candidato:

- posição no ranking;
- identificador do jogador;
- nome;
- clube(s);
- Índice Técnico Bruto;
- Score Técnico;
- Score Financeiro;
- Score de Idade;
- Score Final;
- valor de mercado;
- economia estimada;
- idade.

---

## Documentação Swagger

Com a API em execução, a documentação interativa é disponibilizada em:

```text
/docs
```

Em uma execução local:

```text
http://127.0.0.1:8000/docs
```

A interface Swagger permite testar diretamente os endpoints da aplicação.

---

# Demonstração do sistema

O final do notebook `TCC_Futebol.ipynb` possui uma seção específica preparada para demonstração.

O caso utilizado é Kylian Mbappé.

A demonstração apresenta passo a passo:

```text
Jogador de referência
        ↓
Dados utilizados pelo modelo
        ↓
Características da posição
        ↓
Padronização com StandardScaler
        ↓
Vetor utilizado pelo KNN
        ↓
30 vizinhos técnicos
        ↓
Distância Euclidiana
        ↓
Índice Técnico Bruto
        ↓
Score Técnico
        ↓
Restrição financeira
        ↓
Score Financeiro
        ↓
Score de Idade
        ↓
Score Final
        ↓
Top-5
        ↓
Comparação com a API
```

Ao final, o ranking calculado passo a passo é comparado com o endpoint `/recomendacoes`.

Na validação realizada:

```text
Mesma ordem de jogadores: True
Mesmos Scores Finais: True
```

Esse teste confirma que o fluxo apresentado durante a demonstração reproduz o mesmo ranking retornado pela implementação final da API.

---

# Estrutura do projeto

Estrutura recomendada para entrega/repositório:

```text
TCC-Futebol-ML/
│
├── TCC_Futebol.ipynb
├── api.py
├── README.md
├── requirements.txt
│
└── modelos/
    ├── knn_fw.joblib
    ├── knn_mf.joblib
    ├── knn_df.joblib
    ├── knn_gk.joblib
    ├── dados_financeiros.joblib
    └── configuracao_ranking.json
```

No Google Drive utilizado durante o desenvolvimento, o notebook pode permanecer na pasta padrão `Colab Notebooks`.

Para a célula de inicialização rápida utilizada no Colab, os arquivos da API são esperados em:

```text
/content/drive/MyDrive/TCC_Futebol/
```

com os modelos em:

```text
/content/drive/MyDrive/TCC_Futebol/modelos/
```

---

## Arquivos dos modelos

### `knn_fw.joblib`

Modelo utilizado para atacantes.

### `knn_mf.joblib`

Modelo utilizado para meio-campistas.

### `knn_df.joblib`

Modelo utilizado para defensores.

### `knn_gk.joblib`

Modelo utilizado para goleiros.

Cada arquivo mantém as informações necessárias para utilização do modelo correspondente, incluindo o KNN, as características utilizadas, os dados padronizados e informações necessárias para recuperar os jogadores.

### `dados_financeiros.joblib`

Contém as informações utilizadas durante o ranking financeiro e o cálculo do componente de idade.

### `configuracao_ranking.json`

Armazena os parâmetros utilizados pelo sistema final.

---

# Tecnologias utilizadas

Principais tecnologias e bibliotecas:

- Python;
- Pandas;
- NumPy;
- Scikit-learn;
- TensorFlow / Keras;
- FastAPI;
- Uvicorn;
- Joblib;
- KaggleHub;
- RapidFuzz;
- Matplotlib;
- Requests;
- HTTPX;
- Google Colab.

---

# Dependências

## Notebook completo

Para executar todas as etapas do notebook em um ambiente Python que não possua as bibliotecas instaladas:

```bash
pip install \
    kagglehub \
    rapidfuzz \
    pandas \
    numpy \
    scikit-learn \
    matplotlib \
    tensorflow \
    joblib \
    fastapi \
    uvicorn \
    httpx \
    requests
```

O Google Colab já fornece parte dessas bibliotecas por padrão.

O notebook instala explicitamente algumas dependências adicionais quando necessário.

---

## Apenas API

Para utilizar somente os modelos já treinados e executar a API:

```bash
pip install \
    fastapi \
    uvicorn \
    joblib \
    scikit-learn \
    pandas \
    numpy
```

Depois, certifique-se de que `api.py` e a pasta `modelos` estejam no mesmo diretório.

Execute:

```bash
uvicorn api:app --reload
```

A API ficará disponível em:

```text
http://127.0.0.1:8000
```

e a documentação em:

```text
http://127.0.0.1:8000/docs
```

---

# Reprodutibilidade

As versões das bases utilizadas durante a execução final foram:

```text
football-players-stats-2024-2025: versão 43
player-scores: versão 679
```

A data-limite utilizada para valores de mercado foi:

```text
2025-06-30
```

O notebook foi desenvolvido e executado principalmente no Google Colab.

Como o ambiente do Colab pode receber atualizações ao longo do tempo, as instalações atualmente presentes no notebook não fixam todas as versões das bibliotecas.

Para registrar exatamente as versões de um ambiente de execução, pode-se utilizar:

```bash
pip freeze > requirements.txt
```

ou, para consultar somente as principais dependências:

```bash
pip show \
    pandas \
    numpy \
    scikit-learn \
    tensorflow \
    fastapi \
    uvicorn \
    joblib \
    kagglehub \
    rapidfuzz
```

Para máxima reprodutibilidade, o arquivo `requirements.txt` deve ser gerado no mesmo ambiente utilizado para a execução final do trabalho.

---

# Execução no Google Colab

## Execução completa

1. Abra `TCC_Futebol.ipynb` no Google Colab.
2. Conecte o notebook ao Google Drive quando solicitado.
3. Execute as células na ordem apresentada.
4. As bases serão obtidas por meio do KaggleHub.
5. O notebook executará:
   - preparação das bases;
   - integração;
   - consolidação;
   - construção das características;
   - comparação dos modelos;
   - geração do ranking;
   - persistência dos modelos;
   - testes da API.

---

## Inicialização rápida da API

Caso os modelos já tenham sido gerados, não é necessário executar novamente todo o notebook.

A seção:

```text
Inicialização rápida da API
```

realiza automaticamente:

```text
Montagem do Google Drive
        ↓
Verificação dos arquivos necessários
        ↓
Instalação das dependências da API
        ↓
Inicialização do Uvicorn
        ↓
Teste do endpoint /health
        ↓
Geração do endereço da API
        ↓
Geração do endereço do Swagger
```

Os seguintes arquivos são verificados:

```text
knn_fw.joblib
knn_mf.joblib
knn_df.joblib
knn_gk.joblib
dados_financeiros.joblib
configuracao_ranking.json
api.py
```

Caso algum deles esteja ausente, a inicialização é interrompida e o arquivo ausente é informado.

---

# Fluxo geral do projeto

```text
Bases do Kaggle
        ↓
Análise e tratamento dos dados
        ↓
Integração das bases estatística e Transfermarkt
        ↓
Associação dos jogadores
        ↓
Consolidação por player_id
        ↓
Filtro mínimo de 900 minutos
        ↓
Construção das características por posição
        ↓
Padronização
        ↓
Comparação:
KNN × K-Means × Autoencoder
        ↓
Avaliação por subposição
        ↓
Bootstrap
        ↓
Seleção do KNN
        ↓
30 vizinhos técnicos
        ↓
Índice Técnico Bruto
        ↓
Score Técnico
        ↓
Restrição financeira
        ↓
Score Financeiro
        ↓
Score de Idade
        ↓
Score Final
        ↓
Ranking
        ↓
Persistência dos modelos
        ↓
FastAPI
```

---

# Limitações

Os resultados devem ser interpretados dentro do escopo das bases e métricas utilizadas.

O sistema não considera diretamente fatores como:

- salário;
- duração de contrato;
- cláusula de rescisão;
- disponibilidade real para transferência;
- histórico de lesões;
- adaptação à liga;
- características táticas não representadas nas estatísticas;
- características psicológicas;
- comportamento;
- preferência do jogador;
- avaliação qualitativa realizada por scouts;
- situação financeira real do clube interessado.

O valor de mercado utilizado representa uma estimativa presente na base de dados e não necessariamente o preço real de uma negociação.

A correspondência de subposição utilizada na comparação dos modelos também não representa uma validação definitiva da qualidade de uma recomendação.

Por isso, o sistema deve ser interpretado como:

```text
ferramenta de apoio à triagem inicial
```

e não como:

```text
decisão automática de contratação
```

---

# Autor

**Bernardo Baptista Mello Gonçalves da Silva**

Trabalho de Conclusão de Curso  
Ciência da Computação  
Centro Universitário Jorge Amado — UNIJORGE
