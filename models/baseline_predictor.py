from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Prediction:
    product_id: int
    score: float
    reason: str


class BasketBaselinePredictor:
    def __init__(self) -> None:
        self.global_counts: Counter[int] = Counter()
        self.cooccurrence_counts: dict[int, Counter[int]] = defaultdict(Counter)
        self.product_names: dict[int, str] = {}
        self._fitted = False

    def fit(
        self,
        contexts: Iterable[list[int]],
        targets: Iterable[int],
        product_names: dict[int, str] | None = None,
    ) -> "BasketBaselinePredictor":
        if product_names:
            self.product_names.update(product_names)

        for context, target in zip(contexts, targets):
            self.global_counts[target] += 1
            context_set = set(context)
            for product_id in context_set:
                if product_id == target:
                    continue
                self.cooccurrence_counts[product_id][target] += 1

        self._fitted = True
        return self

    def predict(self, context: list[int], top_k: int = 3) -> list[Prediction]:
        if not self._fitted:
            raise RuntimeError("BasketBaselinePredictor must be fitted before prediction.")

        context_set = set(context)
        candidate_scores: Counter[int] = Counter()

        for product_id in context_set:
            candidate_scores.update(self.cooccurrence_counts.get(product_id, {}))

        if not candidate_scores:
            candidate_scores.update(self.global_counts)

        ranked_candidates = sorted(
            (
                (candidate_id, score)
                for candidate_id, score in candidate_scores.items()
                if candidate_id not in context_set
            ),
            key=lambda item: (-item[1], -self.global_counts[item[0]], item[0]),
        )

        predictions: list[Prediction] = []
        for candidate_id, score in ranked_candidates[:top_k]:
            product_name = self.product_names.get(candidate_id, f"product_{candidate_id}")
            reason = self._build_reason(candidate_id, context_set)
            predictions.append(
                Prediction(
                    product_id=candidate_id,
                    score=float(score),
                    reason=f"{product_name}: {reason}",
                )
            )
        return predictions

    def _build_reason(self, candidate_id: int, context_set: set[int]) -> str:
        supporting_items: list[tuple[int, int]] = []
        for product_id in context_set:
            support = self.cooccurrence_counts.get(product_id, {}).get(candidate_id, 0)
            if support > 0:
                supporting_items.append((product_id, support))

        if supporting_items:
            supporting_items.sort(key=lambda item: (-item[1], item[0]))
            top_supporters = supporting_items[:2]
            supporter_names = [
                self.product_names.get(product_id, f"product_{product_id}")
                for product_id, _ in top_supporters
            ]
            return (
                f"co-occurs with {', '.join(supporter_names)} in historical baskets"
            )

        return "popular across the training baskets"
