# Sistema de Recomendação de Jogadores de Futebol

Projeto desenvolvido como Trabalho de Conclusão de Curso em Ciência da Computação, com foco na aplicação de técnicas de Machine Learning ao processo de scouting no futebol.

A proposta é identificar jogadores com características estatísticas semelhantes a um atleta utilizado como referência e, entre essas alternativas, priorizar aquelas que apresentam melhor relação entre desempenho técnico, valor de mercado e idade.

## Objetivo

O sistema busca apoiar a identificação de possíveis substitutos para jogadores de futebol utilizando dados de desempenho da temporada 2024/2025.

A recomendação considera três aspectos principais:

- similaridade técnica entre os jogadores;
- diferença de valor de mercado;
- diferença de idade.

O objetivo não é substituir a análise realizada por scouts ou analistas de desempenho, mas reduzir o universo de atletas que precisam ser avaliados manualmente.

## Bases de dados

Foram utilizadas duas bases disponíveis no Kaggle.

### Estatísticas de desempenho

Dataset:

```text
hubertsidorowicz/football-players-stats-2024-2025
```

A base contém estatísticas de jogadores das principais ligas europeias na temporada 2024/2025.

### Dados de mercado

Dataset:

```text
davidcariboo/player-scores
```

Foram utilizados principalmente os arquivos:

```text
players.csv
player_valuations.csv
```

Para evitar o uso de informações posteriores à temporada analisada, foram consideradas apenas avaliações de mercado realizadas até:

```text
30/06/2025
```

## Integração das bases

As duas bases não possuem um identificador comum de jogador. Por isso, foi necessário desenvolver um processo de associação entre os registros esportivos e os dados do Transfermarkt.

O processo considerou informações como:

- nome normalizado;
- aliases de nome;
- ano de nascimento;
- posição;
- clube;
- histórico de clubes;
- similaridade textual.

Casos ambíguos foram mantidos sem associação quando não havia evidências suficientes para garantir que os registros representavam a mesma pessoa.

Ao final do processo, 91,35% das linhas da base esportiva foram associadas a um jogador da base de mercado.

## Consolidação dos jogadores

Jogadores que atuaram por mais de um clube durante a temporada podem aparecer em múltiplas linhas na base estatística.

Esses registros foram consolidados utilizando o `player_id` do Transfermarkt antes da aplicação do filtro de minutos.

Essa etapa evita, por exemplo, eliminar jogadores que disputaram mais de 900 minutos na temporada, mas tiveram sua minutagem dividida entre dois clubes.

Foram considerados jogadores com pelo menos:

```text
900 minutos
```

Após o tratamento, 1.494 jogadores ficaram disponíveis para a etapa de modelagem.

A distribuição por grupo de posição foi:

```text
FW - 471
MF - 696
DF - 638
GK - 114
```

Jogadores com posições híbridas podem participar de mais de um grupo.

## Variáveis de desempenho

As características utilizadas na comparação variam de acordo com a posição.

Atacantes utilizam principalmente métricas relacionadas a finalização, produção ofensiva, progressão e criação.

Meio-campistas utilizam indicadores relacionados a passe, criação, progressão, participação ofensiva e recuperação de bola.

Defensores são avaliados principalmente por desarmes, interceptações, bloqueios, jogo aéreo, progressão e qualidade de passe.

Goleiros utilizam métricas específicas da posição, como defesas, gols sofridos, clean sheets e ações fora da área.

Métricas por 90 minutos, percentuais e razões foram recalculados após a consolidação dos registros dos jogadores.

## Comparação dos modelos

Foram avaliados três métodos para identificação de jogadores semelhantes:

### K-Nearest Neighbors

O KNN identifica os jogadores mais próximos de um atleta de referência utilizando a distância entre seus vetores de características.

### K-Means

O K-Means agrupa jogadores com características estatísticas semelhantes. As recomendações podem então ser realizadas considerando jogadores pertencentes ao mesmo grupo.

### Autoencoder

Também foi treinada uma rede neural do tipo Autoencoder, utilizada para criar uma representação compacta das características dos jogadores. A similaridade foi posteriormente calculada utilizando o espaço latente aprendido pela rede.

## Avaliação

Para comparar os modelos, foi utilizada como informação externa a subposição registrada no Transfermarkt.

Essa variável não participou do cálculo da similaridade e foi utilizada apenas para verificar se os modelos tendiam a recomendar jogadores que desempenhavam funções semelhantes.

A avaliação considerou 1.805 observações jogador-posição entre atacantes, meio-campistas e defensores.

Os resultados gerais foram:

| Modelo | Top-5 mesma subposição | Top-1 mesma subposição |
| --- | ---: | ---: |
| K-Means | 47,94% | 48,64% |
| KNN | 47,80% | 48,48% |
| Autoencoder | 45,35% | 46,93% |

Também foi utilizada reamostragem bootstrap com intervalo de confiança de 95%.

Os resultados mostraram que KNN e K-Means apresentaram desempenho semelhante, enquanto ambos tiveram desempenho superior ao Autoencoder no critério Top-5.

O KNN foi escolhido como modelo principal por apresentar desempenho competitivo e por se adaptar diretamente ao objetivo do sistema: receber um jogador como referência e encontrar os atletas mais próximos de seu perfil estatístico.

## Modelo final

Foi criado um modelo KNN separado para cada grupo de posição:

```text
FW - atacantes
MF - meio-campistas
DF - defensores
GK - goleiros
```

Antes da análise financeira, o sistema seleciona os 30 jogadores mais próximos tecnicamente do atleta de referência.

A distância é calculada sobre as características padronizadas de cada posição.

## Ranking de recomendação

O ranking final considera três componentes:

```text
55% - componente técnico
35% - componente financeiro
10% - idade
```

A fórmula utilizada é:

```text
Score Final =
0.55 × Score Técnico
+ 0.35 × Score Financeiro
+ 0.10 × Score Idade
```

Antes do cálculo do Score Final, jogadores com valor de mercado igual ou superior ao jogador de referência são descartados.

### Score Técnico

O KNN identifica os 30 jogadores tecnicamente mais próximos.

Dentro desse grupo, o índice técnico é normalizado para uma escala de 0 a 100.

O jogador mais próximo tecnicamente recebe o maior valor dentro do pool.

Esse score representa uma medida relativa de proximidade técnica dentro do conjunto de candidatos e não deve ser interpretado como uma probabilidade.

O sistema também mantém o índice técnico bruto derivado diretamente da distância do KNN.

### Score Financeiro

O componente financeiro representa a economia percentual em relação ao valor de mercado do jogador de referência.

```text
Score Financeiro =
(Valor da referência - Valor do candidato)
/
Valor da referência
× 100
```

Quanto maior a economia, maior o Score Financeiro.

### Score de Idade

A idade funciona como um componente complementar.

Jogadores mais jovens recebem uma vantagem moderada em relação ao atleta de referência.

A fórmula utilizada é:

```text
Score Idade =
50 + (Idade da referência - Idade do candidato) × 5
```

O resultado é limitado ao intervalo entre 0 e 100.

Um candidato com a mesma idade do jogador de referência recebe Score 50.

## Análise de sensibilidade

Antes da definição dos pesos finais, foram comparadas três configurações:

```text
60% técnico + 30% financeiro + 10% idade
55% técnico + 35% financeiro + 10% idade
50% técnico + 40% financeiro + 10% idade
```

A configuração 55/35/10 apresentou alta estabilidade em relação às alternativas.

Nos quatro casos utilizados para análise, 90% dos nomes presentes no Top-5 permaneceram os mesmos quando comparados às configurações vizinhas.

Por isso, a configuração 55/35/10 foi adotada como padrão do sistema.

## Exemplo de funcionamento

Para um jogador como Kylian Mbappé, o fluxo é:

```text
Jogador de referência
        ↓
Seleção do modelo da posição
        ↓
Padronização das características
        ↓
KNN
        ↓
30 jogadores tecnicamente mais próximos
        ↓
Filtro de valor de mercado
        ↓
Score Técnico
+
Score Financeiro
+
Score de Idade
        ↓
Score Final
        ↓
Ranking de recomendação
```

Nos testes realizados, jogadores como Leroy Sané, Ferrán Torres, Ousmane Dembélé e Omar Marmoush apareceram entre as principais alternativas para Mbappé.

## API

O sistema possui uma API desenvolvida com FastAPI.

Os principais endpoints são:

### Health Check

```http
GET /health
```

Verifica se a aplicação está ativa e se os modelos foram carregados.

### Busca de jogadores

```http
GET /jogadores?q=mbappe
```

Permite pesquisar jogadores disponíveis na base.

### Recomendações

```http
GET /recomendacoes
```

Exemplo:

```text
/recomendacoes?jogador=Kylian%20Mbappé&posicao=FW&quantidade=5
```

A resposta inclui:

- posição no ranking;
- jogador recomendado;
- índice técnico;
- Score Técnico;
- Score Financeiro;
- Score de Idade;
- Score Final;
- valor de mercado;
- economia estimada;
- idade.

## Documentação da API

Com a aplicação em execução, a documentação interativa pode ser acessada em:

```text
/docs
```

O FastAPI disponibiliza a interface Swagger para teste dos endpoints.

## Estrutura do projeto

```text
TCC_Futebol/
│
├── TCC_Futebol.ipynb
├── api.py
├── README.md
│
└── modelos/
    ├── knn_fw.joblib
    ├── knn_mf.joblib
    ├── knn_df.joblib
    ├── knn_gk.joblib
    ├── dados_financeiros.joblib
    └── configuracao_ranking.json
```

## Tecnologias utilizadas

- Python
- Pandas
- NumPy
- Scikit-learn
- TensorFlow / Keras
- FastAPI
- Uvicorn
- Joblib
- KaggleHub
- Google Colab

## Execução

Instale as dependências:

```bash
pip install fastapi uvicorn joblib scikit-learn pandas numpy
```

Certifique-se de que a pasta `modelos` esteja no mesmo diretório do arquivo `api.py`.

Depois execute:

```bash
uvicorn api:app --reload
```

A API ficará disponível em:

```text
http://127.0.0.1:8000
```

A documentação poderá ser acessada em:

```text
http://127.0.0.1:8000/docs
```

## Fluxo do projeto

```text
Coleta das bases no Kaggle
        ↓
Análise e tratamento dos dados
        ↓
Associação FBref / Transfermarkt
        ↓
Consolidação dos registros
        ↓
Filtro de 900 minutos
        ↓
Construção das características por posição
        ↓
Comparação entre KNN, K-Means e Autoencoder
        ↓
Seleção do KNN
        ↓
Busca dos 30 jogadores mais próximos
        ↓
Filtro financeiro
        ↓
Score Técnico + Financeiro + Idade
        ↓
Ranking de recomendação
        ↓
FastAPI
```

## Limitações

Os resultados dependem das estatísticas disponíveis na temporada analisada e do valor de mercado estimado na base utilizada.

O modelo também não considera diretamente aspectos como lesões, duração de contrato, salário, adaptação à liga, comportamento tático, características psicológicas ou avaliações qualitativas realizadas por scouts.

Por isso, as recomendações devem ser utilizadas como um filtro inicial de apoio ao processo de scouting, e não como decisão automática de contratação.

## Autor

Bernardo Baptista Mello Gonçalves da Silva

Trabalho de Conclusão de Curso - Ciência da Computação
