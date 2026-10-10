import logging
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from backend.schemas import (
    HealthResponse,
    PredictionRequest,
    PredictionResponse,
    ProductItem,
    SampleUser,
)
from backend.service import get_service

logger = logging.getLogger("shopping_assistant")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="Smart Shopping Assistant API",
    description="Explainable forgotten-item prediction engine powered by association rules and user history",
    version="1.0.0",
)

# Parse allowed origins safely from environment or default to local dev ports
env_origins = os.getenv("ALLOWED_ORIGINS", "")
if env_origins.strip():
    allowed_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    allow_credentials = "*" not in allowed_origins
else:
    allowed_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    allow_credentials = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


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
        logger.error("Health check degradation: %s", exc)
        return HealthResponse(
            status=f"degraded: {str(exc)}",
            model="unknown",
            total_products=0,
            sample_users_count=0,
        )


@app.get("/api/products/search", response_model=list[ProductItem])
def search_products(
    q: str = Query("", max_length=100, description="Product search query substring (max 100 chars)"),
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
