from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

from models.association_rule_predictor import AssociationRulePredictor, RulePrediction


@dataclass(frozen=True)
class PersonalizedPrediction:
    product_id: int
    score: float
    reason: str


class PersonalizedBasketPredictor:
    def __init__(
        self,
        history_weight: float = 0.7,
        rule_weight: float = 0.3,
    ) -> None:
        self.history_weight = history_weight
        self.rule_weight = rule_weight
        self.rule_predictor = AssociationRulePredictor()
        self.product_names: dict[int, str] = {}
        self.user_product_counts: dict[int, Counter[int]] = defaultdict(Counter)
        self.user_product_last_order: dict[int, dict[int, int]] = defaultdict(dict)
        self._fitted = False

    def fit(
        self,
        baskets: list[dict[str, object]],
        product_names: dict[int, str] | None = None,
    ) -> "PersonalizedBasketPredictor":
        if product_names:
            self.product_names.update(product_names)

        all_product_lists: list[list[int]] = []
        for basket in baskets:
            user_id = int(basket["user_id"])
            order_number = int(basket["order_number"])
            product_ids = [int(product_id) for product_id in basket["product_ids"]]
            all_product_lists.append(product_ids)

            for product_id in set(product_ids):
                self.user_product_counts[user_id][product_id] += 1
                previous_last = self.user_product_last_order[user_id].get(product_id, -1)
                if order_number > previous_last:
                    self.user_product_last_order[user_id][product_id] = order_number

        self.rule_predictor.fit(all_product_lists, product_names=self.product_names)
        self._fitted = True
        return self

    def predict(self, user_id: int, order_number: int, context: list[int], top_k: int = 3) -> list[PersonalizedPrediction]:
        if not self._fitted:
            raise RuntimeError("PersonalizedBasketPredictor must be fitted before prediction.")

        context_set = set(int(product_id) for product_id in context)
        candidate_scores: Counter[int] = Counter()
        candidate_reasons: dict[int, list[str]] = defaultdict(list)

        history_counts = self.user_product_counts.get(user_id, Counter())
        if history_counts:
            max_count = max(history_counts.values())
            for product_id, count in history_counts.items():
                if product_id in context_set:
                    continue
                last_order = self.user_product_last_order[user_id].get(product_id, order_number)
                order_gap = max(order_number - last_order, 0)
                recency_bonus = 1.0 / (1.0 + order_gap)
                history_score = self.history_weight * ((count / max_count) + recency_bonus)
                candidate_scores[product_id] += history_score
                product_name = self.product_names.get(product_id, f"product_{product_id}")
                candidate_reasons[product_id].append(
                    f"{product_name} appears {count} times in this user's history"
                )

        rule_predictions = self.rule_predictor.predict(context, top_k=25)
        for prediction in rule_predictions:
            if prediction.product_id in context_set:
                continue
            rule_score = self.rule_weight * prediction.score
            candidate_scores[prediction.product_id] += rule_score
            candidate_reasons[prediction.product_id].append(prediction.reason)

        ranked = sorted(
            candidate_scores.items(),
            key=lambda item: (-item[1], item[0]),
        )

        predictions: list[PersonalizedPrediction] = []
        for product_id, score in ranked[:top_k]:
            reason_parts = candidate_reasons.get(product_id, [])
            if not reason_parts:
                product_name = self.product_names.get(product_id, f"product_{product_id}")
                reason = f"{product_name}: fallback candidate"
            else:
                reason = "; ".join(reason_parts[:2])
            predictions.append(
                PersonalizedPrediction(
                    product_id=product_id,
                    score=round(float(score), 4),
                    reason=reason,
                )
            )
        return predictions
