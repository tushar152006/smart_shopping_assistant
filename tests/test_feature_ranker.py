from models.feature_ranker import FeatureRanker


def test_feature_ranker_includes_target_candidate_with_positive_label() -> None:
    ranker = FeatureRanker().fit(
        baskets=[
            {"user_id": 1, "order_number": 1, "product_ids": [10, 20, 99]},
            {"user_id": 1, "order_number": 2, "product_ids": [10, 30, 99]},
            {"user_id": 2, "order_number": 1, "product_ids": [10, 20, 77]},
        ],
        product_names={
            10: "Bananas",
            20: "Milk",
            30: "Bread",
            77: "Eggs",
            99: "Peanut Butter",
        },
    )

    candidate_rows = ranker.build_candidate_rows(
        user_id=1,
        order_number=3,
        context=[10],
        target_product_id=99,
    )

    target_rows = [row for row in candidate_rows if row["product_id"] == 99]
    assert target_rows
    assert target_rows[0]["label"] == 1
