"""A small, representative workflow used by the unit tests and by the
Airflow DagBag check in CI.

    crawl ──┬──> preprocess ──> topic_model
            └──> geolocate
"""

from uuid import UUID

import networkx as nx

PROJECT_UUID = UUID("0b6f3c0e-8a51-4d6c-9a57-6f1f8f0e2c11")

BLOCKS = [
    {
        "uuid": UUID("11111111-1111-4111-8111-111111111111"),
        "name": "crawl",
        "image": "ghcr.io/rwth-time/database-interactions:latest",
        "entry_name": "query_database",
        "environment": {
            "QUERY": "SELECT * FROM \"papers\" WHERE title LIKE '%ai%'",
            "DB_DSN": "postgresql://postgres:postgres@data-postgres:5432/x",
        },
    },
    {
        "uuid": UUID("22222222-2222-4222-8222-222222222222"),
        "name": "preprocess",
        "image": "ghcr.io/rwth-time/language-preprocessing:latest",
        "entry_name": "preprocess_txt",
        "environment": {"LANGUAGE": "en", "NGRAMS": '["1", "2"]'},
    },
    {
        "uuid": UUID("33333333-3333-4333-8333-333333333333"),
        "name": "topic_model",
        "image": "ghcr.io/rwth-time/topic-modeling:latest",
        "entry_name": "lda_topic_modeling",
        "environment": {"N_TOPICS": "10"},
    },
    {
        "uuid": UUID("44444444-4444-4444-8444-444444444444"),
        "name": "geolocate",
        "image": "ghcr.io/rwth-time/author-geolocation-mapper:latest",
        "entry_name": "map_authors",
        "environment": {},
    },
]

EDGES = [
    (BLOCKS[0]["uuid"], BLOCKS[1]["uuid"]),
    (BLOCKS[1]["uuid"], BLOCKS[2]["uuid"]),
    (BLOCKS[0]["uuid"], BLOCKS[3]["uuid"]),
]


def sample_graph() -> nx.DiGraph:
    graph = nx.DiGraph()
    for block in BLOCKS:
        graph.add_node(block["uuid"], **block)
    graph.add_edges_from(EDGES)
    return graph
