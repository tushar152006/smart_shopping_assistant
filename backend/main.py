from __future__ import annotations

from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import (
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
    ProductItem,
    SampleUser,
)
from backend.service import get_service

app = FastAPI(
    title="Smart Shopping Assistant API",
    description="Explainable forgotten-item prediction engine powered by association rules and user history",
    version="1.0.0",
)

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        service = get_service()
        return HealthResponse(
            status="healthy",
            model="PersonalizedBasketPredictor",
            total_products=len(service.products),
            sample_users_count=len(service.sample_users),
        )
    except Exception as exc:
        return HealthResponse(
            status=f"degraded: {str(exc)}",
            model="unknown",
            total_products=0,
            sample_users_count=0,
        )


@app.get("/api/products/search", response_model=list[ProductItem])
def search_products(
    q: str = Query("", description="Product search query substring"),
    limit: int = Query(15, ge=1, le=50, description="Max products to return"),
) -> list[ProductItem]:
    service = get_service()
    return service.search_products(query=q, limit=limit)


@app.get("/api/users/sample", response_model=list[SampleUser])
def get_sample_users() -> list[SampleUser]:
    service = get_service()
    return service.get_sample_users()


@app.post("/api/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    if not request.context_product_ids:
        raise HTTPException(
            status_code=400,
            detail="context_product_ids list cannot be empty. Please provide at least one item in the basket.",
        )

    service = get_service()
    return service.predict(
        context_product_ids=request.context_product_ids,
        user_id=request.user_id,
        order_number=request.order_number,
        top_k=request.top_k,
    )
