from models.personalized_predictor import PersonalizedBasketPredictor


def test_personalized_predictor_prefers_user_history_candidate() -> None:
    predictor = PersonalizedBasketPredictor(history_weight=0.8, rule_weight=0.2).fit(
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

    predictions = predictor.predict(user_id=1, order_number=3, context=[10], top_k=2)

    assert predictions[0].product_id == 99
    assert "user's history" in predictions[0].reason
