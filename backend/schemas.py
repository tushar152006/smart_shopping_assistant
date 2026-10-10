from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    context_product_ids: list[int] = Field(
        ...,
        description="List of product IDs currently in the user's shopping basket",
    )
    user_id: Optional[int] = Field(
        None,
        description="Optional user ID to provide personalized recommendations based on past purchases",
    )
    order_number: int = Field(
        10,
        description="Current order number index for calculating purchase recency bonuses",
    )
    top_k: int = Field(
        3,
        ge=1,
        le=20,
        description="Number of forgotten item recommendations to return",
    )


class PredictionItem(BaseModel):
    product_id: int
    product_name: str
    score: float
    reason: str


class PredictionResponse(BaseModel):
    predictions: list[PredictionItem]
    user_id: Optional[int]
    context_product_ids: list[int]
    context_product_names: list[str]


class ProductItem(BaseModel):
    product_id: int
    product_name: str


class SampleUser(BaseModel):
    user_id: int
    order_count: int
    total_purchased_items: int
    top_favorites: list[str]


class HealthResponse(BaseModel):
    status: str
    model: str
    total_products: int
    sample_users_count: int
