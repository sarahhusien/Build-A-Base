import json
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from .config import get_settings
from .compatibility import routine_compatibility
from .database import Product
from .product_catalog import recommend_products_from_rows
from .schemas import DISCLAIMER, RecommendRequest, RecommendResponse, RecommendedProduct


ROUTINE_ORDER = {
    "primer": ("primer", 1),
    "base": ("skin tint", 3),
    "powder_blush": ("powder blush", 1),
    "liquid_blush": ("liquid blush", 1),
    "powder_contour_or_bronzer": ("powder bronzer", 1),
    "cream_or_liquid_contour_bronzer": ("liquid contour", 1),
    "concealer": ("concealer", 1),
    "pressed_setting_powder": ("pressed setting powder", 1),
    "loose_setting_powder": ("loose setting powder", 1),
    "setting_sprays": ("setting spray", 2),
}


def recommend_from_database(request: RecommendRequest, db: Session) -> RecommendResponse:
    products = db.query(Product).all()
    base_type = _base_type(request.preference)
    coverage = _coverage(request)

    slot_plan = dict(ROUTINE_ORDER)
    slot_plan["base"] = (base_type, 3)

    makeup_bag: dict[str, list[dict[str, str]]] = {}
    for slot, (product_type, limit) in slot_plan.items():
        slot_coverage = coverage if product_type == "concealer" else request.coverage
        candidates = recommend_products_from_rows(
            products,
            category=product_type,
            skin_type=request.skin_type,
            undertone=request.undertone,
            depth=request.depth,
            budget=request.budget,
            finish_preference=f"{request.preference} {slot_coverage}".strip(),
            coverage=slot_coverage,
            limit=max(limit * 4, 4),
        )
        chosen = _ai_choose_products(request, slot, product_type, candidates, limit) or candidates[:limit]
        makeup_bag[slot] = [_normalize_product(product) for product in chosen]

    flat = [product for slot_products in makeup_bag.values() for product in slot_products]
    compatibility = routine_compatibility(flat, request.skin_type)
    top_matches = sorted(flat, key=_match_score, reverse=True)[:5]
    return RecommendResponse(
        summary="I compared your profile against products stored in the SQLite database.",
        makeup_bag={slot: [RecommendedProduct(**product) for product in products] for slot, products in makeup_bag.items()},
        product_recommendations=[RecommendedProduct(**product) for product in top_matches],
        explanation=(
            "Build a Base filters SQLite products by price tier, product type, skin type, coverage, finish, tone family, "
            "and complexion range before any AI ranking happens. OpenAI is used only to choose from those filtered "
            "database candidates when configured; otherwise the same filtered candidates are ranked deterministically."
        ),
        disclaimer=DISCLAIMER,
        routine_score=compatibility["routine_score"],
        compatibility_warnings=compatibility["compatibility_warnings"],
        positive_compatibility_notes=compatibility["positive_compatibility_notes"],
    )


def _ai_choose_products(
    request: RecommendRequest,
    slot: str,
    product_type: str,
    candidates: list[dict[str, str]],
    limit: int,
) -> list[dict[str, str]] | None:
    settings = get_settings()
    if not settings.openai_api_key or not candidates:
        return None

    client = OpenAI(api_key=settings.openai_api_key)
    payload = {
        "user_profile": request.model_dump(),
        "slot": slot,
        "product_type": product_type,
        "limit": limit,
        "database_candidates": candidates,
    }
    system = (
        "You are a cosmetic-only beauty product recommender. Choose only from the provided SQLite database candidates. "
        "Return JSON only as {\"selected\": [{\"id\": \"candidate id\", \"why\": \"short clear reason\"}]}. "
        "Do not diagnose or discuss medical skin conditions."
    )
    try:
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(payload)},
            ],
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        selected = json.loads(response.choices[0].message.content or "{}").get("selected", [])
    except Exception:
        return None

    by_id = {str(product.get("id")): product for product in candidates}
    chosen: list[dict[str, str]] = []
    for item in selected:
        product = by_id.get(str(item.get("id")))
        if product:
            product = {**product, "why": item.get("why") or product["why"]}
            chosen.append(product)
        if len(chosen) >= limit:
            break
    return chosen or None


def _normalize_product(product: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(product.get("id", 0)),
        "name": product.get("name", ""),
        "brand": product.get("brand", ""),
        "category": product.get("category", ""),
        "shade_name": product.get("shade_name", ""),
        "budget": product.get("budget", ""),
        "price_tier": product.get("price_tier", product.get("budget", "")),
        "finish": product.get("finish", ""),
        "coverage": product.get("coverage", ""),
        "why": product.get("why", ""),
        "shade_note": product.get("shade_note", ""),
        "typical_price": product.get("typical_price", "Price varies"),
        "image_url": product.get("image_url", ""),
        "price_note": product.get("price_note", ""),
        "shopping_link": product.get("shopping_link", ""),
        "source": product.get("source", "sqlite_products"),
        "good_for": product.get("good_for", ""),
        "avoid_if": product.get("avoid_if", ""),
        "possible_downside": product.get("possible_downside", ""),
        "matched_answers": product.get("matched_answers", ""),
        "match_percentage": product.get("match_percentage", ""),
        "why_recommended": product.get("why_recommended", product.get("why", "")),
        "formula_base": product.get("formula_base", ""),
        "best_for": product.get("best_for", ""),
        "avoid_pairing_with": product.get("avoid_pairing_with", ""),
        "compatibility_notes": product.get("compatibility_notes", ""),
    }


def _match_score(product: dict[str, Any]) -> int:
    try:
        return int(product.get("match_percentage") or 0)
    except (TypeError, ValueError):
        return 0


def _base_type(preference: str) -> str:
    text = preference.lower()
    if any(word in text for word in ["skin tint", "light coverage", "sheer", "dewy"]):
        return "skin tint"
    return "foundation"


def _coverage(request: RecommendRequest) -> str:
    text = f"{request.preference} {request.coverage} {request.goal}".lower()
    return "full" if any(word in text for word in ["full", "glam", "event", "long wear", "long-wear"]) else "medium"
