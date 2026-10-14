
from pathlib import Path
from typing import Literal
import json
import re
import unicodedata

import joblib
import numpy as np
import pandas as pd

from fastapi import FastAPI, HTTPException, Query

BASE_DIR = Path(__file__).resolve().parent
MODELOS_DIR = BASE_DIR / "modelos"

modelos = {
    "FW": joblib.load(MODELOS_DIR / "knn_fw.joblib"),
    "MF": joblib.load(MODELOS_DIR / "knn_mf.joblib"),
    "DF": joblib.load(MODELOS_DIR / "knn_df.joblib"),
    "GK": joblib.load(MODELOS_DIR / "knn_gk.joblib")
}

df_financeiro = joblib.load(
    MODELOS_DIR / "dados_financeiros.joblib"
)

with open(
    MODELOS_DIR / "configuracao_ranking.json",
    "r",
    encoding="utf-8"
) as arquivo:
    configuracao = json.load(arquivo)


TAMANHO_POOL = configuracao[
    "tamanho_pool_tecnico"
]

PESO_TECNICO = configuracao[
    "peso_tecnico"
]

PESO_FINANCEIRO = configuracao[
    "peso_financeiro"
]

PESO_IDADE = configuracao[
    "peso_idade"
]

app = FastAPI(
    title="API de Scouting de Jogadores",
    description=(
        "Sistema de recomendação baseado em KNN, "
        "valor de mercado e idade."
    ),
    version="1.0.0"
)

def normalizar_texto(texto):

    if texto is None:
        return ""

    texto = str(texto).lower().strip()

    texto = unicodedata.normalize(
        "NFKD",
        texto
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(
            caractere
        )
    )

    texto = re.sub(
        r"[^a-z0-9\s]",
        " ",
        texto
    )

    return re.sub(
        r"\s+",
        " ",
        texto
    ).strip()


def encontrar_jogador(
    jogador,
    posicao
):

    df_posicao = modelos[
        posicao
    ]["dataframe"]

    procurado = normalizar_texto(
        jogador
    )

    nomes = (
        df_posicao["Player"]
        .apply(normalizar_texto)
    )

    encontrados = df_posicao[
        nomes == procurado
    ]

    if encontrados.empty:
        return None

    return encontrados.index[0]

@app.get("/")
def inicio():

    return {
        "projeto":
            "Scouting de jogadores",

        "modelo_tecnico":
            configuracao[
                "modelo_tecnico"
            ],

        "pesos": {
            "tecnico":
                PESO_TECNICO,

            "financeiro":
                PESO_FINANCEIRO,

            "idade":
                PESO_IDADE
        },

        "documentacao":
            "/docs"
    }

@app.get("/health")
def health():

    return {
        "status": "ok",

        "modelos":
            list(
                modelos.keys()
            ),

        "jogadores": {
            posicao:
                len(
                    modelo[
                        "dataframe"
                    ]
                )

            for posicao, modelo
            in modelos.items()
        }
    }

@app.get("/jogadores")
def buscar_jogadores(
    q: str = Query(
        min_length=2
    ),
    limite: int = Query(
        default=20,
        ge=1,
        le=50
    )
):

    termo = normalizar_texto(q)

    resultados = []

    for posicao, modelo in modelos.items():

        df_posicao = modelo[
            "dataframe"
        ]

        for _, linha in (
            df_posicao.iterrows()
        ):

            if termo not in normalizar_texto(
                linha["Player"]
            ):
                continue

            resultados.append({
                "player_id":
                    int(
                        linha[
                            "player_id_match"
                        ]
                    ),

                "jogador":
                    linha["Player"],

                "posicao":
                    posicao,

                "clubes":
                    list(
                        linha["clubes"]
                    )
            })

    return resultados[:limite]

@app.get("/recomendacoes")
def recomendar(
    jogador: str,
    posicao: Literal[
        "FW",
        "MF",
        "DF",
        "GK"
    ],
    quantidade: int = Query(
        default=10,
        ge=1,
        le=20
    )
):

    modelo = modelos[
        posicao
    ]

    df_posicao = modelo[
        "dataframe"
    ]

    X = modelo["X"]
    knn = modelo["knn"]
    features = modelo["features"]

    indice = encontrar_jogador(
        jogador,
        posicao
    )

    if indice is None:

        raise HTTPException(
            status_code=404,
            detail=(
                "Jogador não encontrado "
                "na posição informada."
            )
        )

    referencia = df_posicao.loc[
        indice
    ]

    player_id_referencia = int(
        referencia[
            "player_id_match"
        ]
    )

    financeiro_referencia = (
        df_financeiro[
            df_financeiro[
                "player_id"
            ]
            == player_id_referencia
        ]
    )

    if financeiro_referencia.empty:

        raise HTTPException(
            status_code=404,
            detail=(
                "Dados financeiros "
                "não encontrados."
            )
        )

    financeiro_referencia = (
        financeiro_referencia.iloc[0]
    )

    valor_referencia = float(
        financeiro_referencia[
            "market_value_in_eur"
        ]
    )

    idade_referencia = int(
        financeiro_referencia[
            "Idade"
        ]
    )

    quantidade_busca = min(
        TAMANHO_POOL + 1,
        len(df_posicao)
    )

    distancias, indices = (
        knn.kneighbors(
            X[indice].reshape(
                1,
                -1
            ),
            n_neighbors=
                quantidade_busca
        )
    )

    registros = []

    for distancia, indice_candidato in zip(
        distancias[0],
        indices[0]
    ):

        if indice_candidato == indice:
            continue

        candidato = df_posicao.loc[
            indice_candidato
        ]

        player_id = int(
            candidato[
                "player_id_match"
            ]
        )

        financeiro = (
            df_financeiro[
                df_financeiro[
                    "player_id"
                ]
                == player_id
            ]
        )

        if financeiro.empty:
            continue

        financeiro = financeiro.iloc[0]

        valor = float(
            financeiro[
                "market_value_in_eur"
            ]
        )

        idade = int(
            financeiro["Idade"]
        )

        distancia_normalizada = (
            float(distancia)
            / np.sqrt(
                len(features)
            )
        )

        indice_tecnico = (
            1
            /
            (
                1
                + distancia_normalizada
            )
            * 100
        )

        registros.append({
            "player_id":
                player_id,

            "jogador":
                candidato["Player"],

            "clubes":
                list(
                    candidato["clubes"]
                ),

            "indice_tecnico_bruto":
                indice_tecnico,

            "valor":
                valor,

            "idade":
                idade
        })


    resultado = pd.DataFrame(
        registros
    )

    minimo = resultado[
        "indice_tecnico_bruto"
    ].min()

    maximo = resultado[
        "indice_tecnico_bruto"
    ].max()

    if maximo == minimo:

        resultado[
            "score_tecnico"
        ] = 100.0

    else:

        resultado[
            "score_tecnico"
        ] = (
            (
                resultado[
                    "indice_tecnico_bruto"
                ]
                - minimo
            )
            /
            (
                maximo
                - minimo
            )
            * 100
        )

    resultado = resultado[
        resultado[
            "valor"
        ] < valor_referencia
    ].copy()

    resultado[
        "score_financeiro"
    ] = (
        (
            valor_referencia
            - resultado["valor"]
        )
        / valor_referencia
        * 100
    )

    resultado[
        "score_idade"
    ] = (
        50
        +
        (
            idade_referencia
            - resultado["idade"]
        )
        * 5
    )

    resultado[
        "score_idade"
    ] = np.clip(
        resultado[
            "score_idade"
        ],
        0,
        100
    )

    resultado[
        "score_final"
    ] = (
        PESO_TECNICO
        * resultado[
            "score_tecnico"
        ]
        +
        PESO_FINANCEIRO
        * resultado[
            "score_financeiro"
        ]
        +
        PESO_IDADE
        * resultado[
            "score_idade"
        ]
    )


    resultado = (
        resultado
        .sort_values(
            "score_final",
            ascending=False
        )
        .head(quantidade)
        .reset_index(drop=True)
    )


    recomendacoes = []

    for i, linha in (
        resultado.iterrows()
    ):

        recomendacoes.append({
            "ranking":
                i + 1,

            "player_id":
                int(
                    linha[
                        "player_id"
                    ]
                ),

            "jogador":
                linha[
                    "jogador"
                ],

            "clubes":
                linha[
                    "clubes"
                ],

            "indice_tecnico_bruto":
                round(
                    linha[
                        "indice_tecnico_bruto"
                    ],
                    2
                ),

            "score_tecnico":
                round(
                    linha[
                        "score_tecnico"
                    ],
                    2
                ),

            "score_financeiro":
                round(
                    linha[
                        "score_financeiro"
                    ],
                    2
                ),

            "score_idade":
                round(
                    linha[
                        "score_idade"
                    ],
                    2
                ),

            "score_final":
                round(
                    linha[
                        "score_final"
                    ],
                    2
                ),

            "valor_mercado_milhoes":
                round(
                    linha["valor"]
                    / 1_000_000,
                    2
                ),

            "economia_milhoes":
                round(
                    (
                        valor_referencia
                        - linha["valor"]
                    )
                    / 1_000_000,
                    2
                ),

            "idade":
                int(
                    linha["idade"]
                )
        })


    return {
        "referencia": {
            "jogador":
                referencia["Player"],

            "posicao":
                posicao,

            "valor_mercado_milhoes":
                round(
                    valor_referencia
                    / 1_000_000,
                    2
                ),

            "idade":
                idade_referencia
        },

        "configuracao": {
            "pool_tecnico":
                TAMANHO_POOL,

            "peso_tecnico":
                PESO_TECNICO,

            "peso_financeiro":
                PESO_FINANCEIRO,

            "peso_idade":
                PESO_IDADE
        },

        "recomendacoes":
            recomendacoes
    }
