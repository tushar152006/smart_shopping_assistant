from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import combinations
from math import log1p
from typing import Iterable


@dataclass(frozen=True)
class AssociationRule:
    antecedent: tuple[int, ...]
    consequent: int
    support: float
    confidence: float
    lift: float
    support_count: int


@dataclass(frozen=True)
class RulePrediction:
    product_id: int
    score: float
    reason: str


class AssociationRulePredictor:
    def __init__(
        self,
        max_antecedent_size: int = 2,
        min_antecedent_support: int = 5,
        min_rule_support_count: int = 3,
        min_confidence: float = 0.01,
        max_lift: float = 5.0,
    ) -> None:
        self.max_antecedent_size = max_antecedent_size
        self.min_antecedent_support = min_antecedent_support
        self.min_rule_support_count = min_rule_support_count
        self.min_confidence = min_confidence
        self.max_lift = max_lift
        self.product_names: dict[int, str] = {}
        self.global_counts: Counter[int] = Counter()
        self.rules_by_antecedent: dict[tuple[int, ...], list[AssociationRule]] = defaultdict(list)
        self._fitted = False

    def fit(
        self,
        baskets: Iterable[list[int]],
        product_names: dict[int, str] | None = None,
    ) -> "AssociationRulePredictor":
        if product_names:
            self.product_names.update(product_names)

        basket_list = [sorted(set(int(item) for item in basket)) for basket in baskets]
        basket_count = len(basket_list)

        item_counts: Counter[int] = Counter()
        antecedent_counts: Counter[tuple[int, ...]] = Counter()
        consequent_counts: dict[tuple[int, ...], Counter[int]] = defaultdict(Counter)

        for basket in basket_list:
            basket_set = set(basket)
            for item in basket_set:
                item_counts[item] += 1
                self.global_counts[item] += 1

            max_size = min(self.max_antecedent_size, len(basket_set) - 1)
            for size in range(1, max_size + 1):
                for antecedent in combinations(basket, size):
                    antecedent_counts[antecedent] += 1
                    for consequent in basket:
                        if consequent not in antecedent:
                            consequent_counts[antecedent][consequent] += 1

        for antecedent, total_count in antecedent_counts.items():
            if total_count < self.min_antecedent_support:
                continue

            for consequent, joint_count in consequent_counts[antecedent].items():
                if joint_count < self.min_rule_support_count:
                    continue
                confidence = joint_count / total_count
                if confidence < self.min_confidence:
                    continue

                consequent_support = item_counts[consequent] / basket_count
                lift = confidence / consequent_support if consequent_support else 0.0
                rule = AssociationRule(
                    antecedent=antecedent,
                    consequent=consequent,
                    support=joint_count / basket_count,
                    confidence=confidence,
                    lift=lift,
                    support_count=joint_count,
                )
                self.rules_by_antecedent[antecedent].append(rule)

        for antecedent in self.rules_by_antecedent:
            self.rules_by_antecedent[antecedent].sort(
                key=lambda rule: (-rule.confidence, -rule.lift, -rule.support_count, rule.consequent)
            )

        self._fitted = True
        return self

    def predict(self, context: list[int], top_k: int = 3) -> list[RulePrediction]:
        if not self._fitted:
            raise RuntimeError("AssociationRulePredictor must be fitted before prediction.")

        context_set = set(int(item) for item in context)
        candidate_scores: dict[int, float] = defaultdict(float)
        best_rule: dict[int, AssociationRule] = {}

        sorted_context = sorted(context_set)
        for size in range(min(self.max_antecedent_size, len(sorted_context)), 0, -1):
            for antecedent in combinations(sorted_context, size):
                for rule in self.rules_by_antecedent.get(antecedent, []):
                    if rule.consequent in context_set:
                        continue
                    score = rule.confidence * min(rule.lift, self.max_lift) * log1p(rule.support_count)
                    candidate_scores[rule.consequent] += score
                    current_best = best_rule.get(rule.consequent)
                    if current_best is None or (rule.confidence, rule.lift, rule.support_count) > (
                        current_best.confidence,
                        current_best.lift,
                        current_best.support_count,
                    ):
                        best_rule[rule.consequent] = rule

        if not candidate_scores:
            fallback = self.global_counts.most_common(top_k)
            return [
                RulePrediction(
                    product_id=product_id,
                    score=float(count),
                    reason=f"{self.product_names.get(product_id, f'product_{product_id}')}: popular across sampled baskets",
                )
                for product_id, count in fallback
                if product_id not in context_set
            ][:top_k]

        ranked = sorted(
            candidate_scores.items(),
            key=lambda item: (-item[1], -self.global_counts[item[0]], item[0]),
        )

        predictions: list[RulePrediction] = []
        for product_id, score in ranked[:top_k]:
            rule = best_rule[product_id]
            antecedent_names = [
                self.product_names.get(item, f"product_{item}") for item in rule.antecedent
            ]
            consequent_name = self.product_names.get(product_id, f"product_{product_id}")
            predictions.append(
                RulePrediction(
                    product_id=product_id,
                    score=round(float(score), 4),
                    reason=(
                        f"{consequent_name}: rule {antecedent_names} -> {consequent_name} "
                        f"(confidence={rule.confidence:.3f}, lift={rule.lift:.3f})"
                    ),
                )
            )
        return predictions
