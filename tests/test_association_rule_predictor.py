from models.association_rule_predictor import AssociationRulePredictor


def test_association_rule_predictor_uses_pair_rule() -> None:
    predictor = AssociationRulePredictor(
        max_antecedent_size=2,
        min_antecedent_support=1,
        min_rule_support_count=1,
        min_confidence=0.0,
    ).fit(
        baskets=[
            [1, 2, 9],
            [1, 2, 9],
            [1, 3, 8],
            [4, 5, 7],
        ],
        product_names={
            1: "Bananas",
            2: "Milk",
            3: "Bread",
            7: "Yogurt",
            8: "Eggs",
            9: "Peanut Butter",
        },
    )

    predictions = predictor.predict([1, 2], top_k=2)

    assert predictions[0].product_id == 9
    assert "confidence=" in predictions[0].reason
