from __future__ import annotations

import json
from pathlib import Path
import pickle
from typing import Any, Optional

from backend.schemas import (
    PredictionItem,
    PredictionResponse,
    ProductItem,
    SampleUser,
)

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts"


class ShoppingAssistantService:
    def __init__(self) -> None:
        self.predictor: Any = None
        self.products: list[dict[str, Any]] = []
        self.product_map: dict[int, str] = {}
        self.sample_users: list[dict[str, Any]] = []
        self.is_loaded = False

    def load_artifacts(self) -> None:
        if self.is_loaded:
            return

        model_path = ARTIFACT_DIR / "predictor.pkl"
        catalog_path = ARTIFACT_DIR / "products_catalog.json"
        users_path = ARTIFACT_DIR / "sample_users.json"

        if not model_path.exists():
            raise FileNotFoundError(
                f"Model artifact not found at {model_path}. Please run export_model_artifact.py first."
            )

        with open(model_path, "rb") as f:
            self.predictor = pickle.load(f)

        if catalog_path.exists():
            self.products = json.loads(catalog_path.read_text(encoding="utf-8"))
            self.product_map = {int(p["product_id"]): str(p["product_name"]) for p in self.products}
        elif hasattr(self.predictor, "product_names"):
            self.product_map = dict(self.predictor.product_names)
            self.products = [
                {"product_id": pid, "product_name": name}
                for pid, name in sorted(self.product_map.items(), key=lambda x: x[1])
            ]

        if users_path.exists():
            self.sample_users = json.loads(users_path.read_text(encoding="utf-8"))

        self.is_loaded = True

    def search_products(self, query: str = "", limit: int = 15) -> list[ProductItem]:
        if not self.is_loaded:
            self.load_artifacts()

        q = query.strip().lower()
        if not q:
            # return popular/first few products
            return [
                ProductItem(product_id=p["product_id"], product_name=p["product_name"])
                for p in self.products[:limit]
            ]

        results = []
        for p in self.products:
            if q in p["product_name"].lower():
                results.append(ProductItem(product_id=p["product_id"], product_name=p["product_name"]))
                if len(results) >= limit:
                    break
        return results

    def get_sample_users(self) -> list[SampleUser]:
        if not self.is_loaded:
            self.load_artifacts()
        return [SampleUser(**user) for user in self.sample_users]

    def predict(
        self,
        context_product_ids: list[int],
        user_id: Optional[int] = None,
        order_number: int = 10,
        top_k: int = 3,
    ) -> PredictionResponse:
        if not self.is_loaded:
            self.load_artifacts()

        context_names = [
            self.product_map.get(pid, f"Product {pid}")
            for pid in context_product_ids
        ]

        if user_id is not None and hasattr(self.predictor, "predict") and "user_id" in self.predictor.predict.__code__.co_varnames:
            raw_predictions = self.predictor.predict(
                user_id=user_id,
                order_number=order_number,
                context=context_product_ids,
                top_k=top_k,
            )
        else:
            # Fallback or rule predictor
            if hasattr(self.predictor, "predict"):
                try:
                    raw_predictions = self.predictor.predict(
                        context=context_product_ids,
                        top_k=top_k,
                    )
                except TypeError:
                    raw_predictions = self.predictor.predict(
                        user_id=0,
                        order_number=order_number,
                        context=context_product_ids,
                        top_k=top_k,
                    )
            else:
                raw_predictions = []

        prediction_items: list[PredictionItem] = []
        for pred in raw_predictions:
            pname = self.product_map.get(pred.product_id, getattr(pred, "product_name", f"Product {pred.product_id}"))
            prediction_items.append(
                PredictionItem(
                    product_id=pred.product_id,
                    product_name=pname,
                    score=float(pred.score),
                    reason=str(pred.reason),
                )
            )

        return PredictionResponse(
            predictions=prediction_items,
            user_id=user_id,
            context_product_ids=context_product_ids,
            context_product_names=context_names,
        )


_service_instance: Optional[ShoppingAssistantService] = None


def get_service() -> ShoppingAssistantService:
    global _service_instance
    if _service_instance is None:
        _service_instance = ShoppingAssistantService()
        _service_instance.load_artifacts()
    return _service_instance
