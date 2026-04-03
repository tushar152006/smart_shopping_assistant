from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression

from models.association_rule_predictor import AssociationRulePredictor


@dataclass(frozen=True)
class RankedPrediction:
    product_id: int
    score: float
    reason: str


class FeatureRanker:
    def __init__(self) -> None:
        self.rule_predictor = AssociationRulePredictor()
        self.product_names: dict[int, str] = {}
        self.global_counts: Counter[int] = Counter()
        self.user_product_counts: dict[int, Counter[int]] = defaultdict(Counter)
        self.user_product_last_order: dict[int, dict[int, int]] = defaultdict(dict)
        self.model = LogisticRegression(max_iter=1000, random_state=42, class_weight="balanced")
        self._fitted = False

    def fit(
        self,
        baskets: list[dict[str, object]],
        product_names: dict[int, str] | None = None,
    ) -> "FeatureRanker":
        if product_names:
            self.product_names.update(product_names)

        all_product_lists: list[list[int]] = []
        for basket in baskets:
            user_id = int(basket["user_id"])
            order_number = int(basket["order_number"])
            product_ids = [int(product_id) for product_id in basket["product_ids"]]
            all_product_lists.append(product_ids)

            for product_id in set(product_ids):
                self.global_counts[product_id] += 1
                self.user_product_counts[user_id][product_id] += 1
                previous_last = self.user_product_last_order[user_id].get(product_id, -1)
                if order_number > previous_last:
                    self.user_product_last_order[user_id][product_id] = order_number

        self.rule_predictor.fit(all_product_lists, product_names=self.product_names)
        self._fitted = True
        return self

    def fit_ranker(self, training_rows: list[dict[str, float | int]]) -> "FeatureRanker":
        feature_matrix = np.array(
            [
                [
                    float(row["history_count_norm"]),
                    float(row["recency_bonus"]),
                    float(row["rule_score"]),
                    float(row["global_popularity_norm"]),
                    float(row["context_size_norm"]),
                    float(row["has_history"]),
                    float(row["has_rule_signal"]),
                ]
                for row in training_rows
            ]
        )
        labels = np.array([int(row["label"]) for row in training_rows])
        self.model.fit(feature_matrix, labels)
        return self

    def build_candidate_rows(
        self,
        user_id: int,
        order_number: int,
        context: list[int],
        target_product_id: int | None = None,
        candidate_limit: int = 25,
    ) -> list[dict[str, float | int]]:
        if not self._fitted:
            raise RuntimeError("FeatureRanker must be fitted before building candidate rows.")

        context_set = set(int(product_id) for product_id in context)
        candidate_ids: set[int] = set()

        rule_predictions = self.rule_predictor.predict(context, top_k=candidate_limit)
        rule_scores = {prediction.product_id: prediction.score for prediction in rule_predictions}
        candidate_ids.update(rule_scores.keys())

        history_counts = self.user_product_counts.get(user_id, Counter())
        candidate_ids.update(
            product_id
            for product_id, _ in history_counts.most_common(candidate_limit)
            if product_id not in context_set
        )

        candidate_ids.update(
            product_id
            for product_id, _ in self.global_counts.most_common(candidate_limit)
            if product_id not in context_set
        )

        if target_product_id is not None and target_product_id not in context_set:
            candidate_ids.add(int(target_product_id))

        max_history = max(history_counts.values()) if history_counts else 1
        max_global = max(self.global_counts.values()) if self.global_counts else 1
        context_size_norm = min(len(context) / 20.0, 1.0)

        rows: list[dict[str, float | int]] = []
        for candidate_id in candidate_ids:
            if candidate_id in context_set:
                continue
            count = history_counts.get(candidate_id, 0)
            last_order = self.user_product_last_order.get(user_id, {}).get(candidate_id, order_number)
            order_gap = max(order_number - last_order, 0)
            recency_bonus = 1.0 / (1.0 + order_gap) if count else 0.0
            rows.append(
                {
                    "product_id": candidate_id,
                    "history_count_norm": count / max_history if max_history else 0.0,
                    "recency_bonus": recency_bonus,
                    "rule_score": float(rule_scores.get(candidate_id, 0.0)),
                    "global_popularity_norm": self.global_counts.get(candidate_id, 0) / max_global,
                    "context_size_norm": context_size_norm,
                    "has_history": int(count > 0),
                    "has_rule_signal": int(candidate_id in rule_scores),
                    "label": int(target_product_id is not None and candidate_id == target_product_id),
                }
            )
        return rows

    def predict(
        self,
        user_id: int,
        order_number: int,
        context: list[int],
        top_k: int = 3,
    ) -> list[RankedPrediction]:
        candidate_rows = self.build_candidate_rows(
            user_id=user_id,
            order_number=order_number,
            context=context,
            target_product_id=None,
        )
        if not candidate_rows:
            return []

        feature_matrix = np.array(
            [
                [
                    float(row["history_count_norm"]),
                    float(row["recency_bonus"]),
                    float(row["rule_score"]),
                    float(row["global_popularity_norm"]),
                    float(row["context_size_norm"]),
                    float(row["has_history"]),
                    float(row["has_rule_signal"]),
                ]
                for row in candidate_rows
            ]
        )
        probabilities = self.model.predict_proba(feature_matrix)[:, 1]

        ranked = sorted(
            zip(candidate_rows, probabilities, strict=False),
            key=lambda item: (-item[1], -float(item[0]["rule_score"]), -float(item[0]["history_count_norm"])),
        )

        predictions: list[RankedPrediction] = []
        for row, probability in ranked[:top_k]:
            product_id = int(row["product_id"])
            product_name = self.product_names.get(product_id, f"product_{product_id}")
            reason_parts = []
            if float(row["history_count_norm"]) > 0:
                reason_parts.append("strong user-history match")
            if float(row["rule_score"]) > 0:
                reason_parts.append("supported by basket rules")
            if not reason_parts:
                reason_parts.append("popular fallback candidate")
            predictions.append(
                RankedPrediction(
                    product_id=product_id,
                    score=round(float(probability), 4),
                    reason=f"{product_name}: {', '.join(reason_parts)}",
                )
            )
        return predictions
