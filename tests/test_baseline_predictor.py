from models.baseline_predictor import BasketBaselinePredictor


def test_predict_prefers_cooccurring_target_over_global_popularity() -> None:
    predictor = BasketBaselinePredictor().fit(
        contexts=[
            [1, 2],
            [1, 2],
            [1, 3],
            [4, 5],
        ],
        targets=[9, 9, 8, 7],
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
    assert "Bananas" in predictions[0].reason or "Milk" in predictions[0].reason
