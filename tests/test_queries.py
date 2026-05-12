from __future__ import annotations

import pandas as pd

from src.data.queries import get_response_tree


def test_get_response_tree_computes_expected_propagation_metrics(mocker) -> None:
    dataset = pd.DataFrame(
        [
            {
                "id": "root-1",
                "threadId": "thread-1",
                "parentId": "",
                "author": "autor-root",
                "text": "Mensaje raiz",
                "sentiment": "NEUTRAL",
                "isComment": False,
                "createdAtDatetime": pd.Timestamp("2024-01-01T10:00:00Z"),
                "socialType": "facebook",
                "url": "https://example.com/root",
                "sourceURL": "",
            },
            {
                "id": "child-1",
                "threadId": "thread-1",
                "parentId": "root-1",
                "author": "autor-1",
                "text": "Primera respuesta",
                "sentiment": "NEGATIVE",
                "isComment": True,
                "createdAtDatetime": pd.Timestamp("2024-01-01T10:10:00Z"),
                "socialType": "facebook",
                "url": "https://example.com/child-1",
                "sourceURL": "",
            },
            {
                "id": "child-2",
                "threadId": "thread-1",
                "parentId": "root-1",
                "author": "autor-2",
                "text": "Segunda respuesta",
                "sentiment": "POSITIVE",
                "isComment": True,
                "createdAtDatetime": pd.Timestamp("2024-01-01T10:30:00Z"),
                "socialType": "facebook",
                "url": "https://example.com/child-2",
                "sourceURL": "",
            },
            {
                "id": "grandchild-1",
                "threadId": "thread-1",
                "parentId": "child-1",
                "author": "autor-3",
                "text": "Respuesta anidada",
                "sentiment": "NEUTRAL",
                "isComment": True,
                "createdAtDatetime": pd.Timestamp("2024-01-01T11:00:00Z"),
                "socialType": "facebook",
                "url": "https://example.com/grandchild-1",
                "sourceURL": "",
            },
        ]
    )

    mocker.patch("src.data.queries.load_normalized_dataset", return_value=dataset)

    result = get_response_tree("root-1", max_depth=5)

    assert result["root_found"] is True
    assert result["direct_replies"] == 2
    assert result["total_descendants"] == 3
    assert result["max_depth_observed"] == 2
    assert result["metrics"]["reach"] == 3
    assert result["metrics"]["unique_authors"] == 3
    assert result["metrics"]["first_reply_delay_minutes"] == 10.0
    assert result["metrics"]["propagation_minutes"] == 50.0
    assert result["metrics"]["average_replies_per_hour"] == 3.0