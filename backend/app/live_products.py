from functools import lru_cache
from typing import Any

import httpx

from .config import get_settings


BUDGET_MAX_PRICE = {
    "drugstore": 20,
    "moderate": 40,
    "premium": 90,
}


def live_product_search_tool(
    category: str,
    budget: str,
    preference: str = "",
    skin_type: str = "",
    undertone: str = "",
    depth: str = "",
    coverage: str = "",
    limit: int = 3,
) -> list[dict[str, str]]:
    settings = get_settings()
    if not settings.serpapi_api_key:
        return []

    query = _build_query(category, budget, preference, skin_type, undertone, depth, coverage)
    return _search_serpapi(
        settings.serpapi_api_key,
        query,
        budget,
        category,
        preference,
        coverage,
        limit,
    )


def _build_query(
    category: str,
    budget: str,
    preference: str,
    skin_type: str,
    undertone: str,
    depth: str,
    coverage: str,
) -> str:
    parts = [budget, coverage, preference, category, "makeup"]
    if category in {"foundation", "skin tint", "concealer"}:
        parts.extend([depth, undertone])
    if skin_type:
        parts.append(f"for {skin_type} skin")
    return " ".join(part for part in parts if part).strip()


@lru_cache(maxsize=256)
def _search_serpapi(
    api_key: str,
    query: str,
    budget: str,
    category: str,
    preference: str,
    coverage: str,
    limit: int,
) -> list[dict[str, str]]:
    params: dict[str, Any] = {
        "engine": "google_shopping",
        "api_key": api_key,
        "q": query,
        "gl": "us",
        "hl": "en",
        "google_domain": "google.com",
    }
    max_price = BUDGET_MAX_PRICE.get(budget.lower())
    if max_price:
        params["max_price"] = max_price

    try:
        response = httpx.get("https://serpapi.com/search.json", params=params, timeout=12)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return []

    raw_results = payload.get("shopping_results") or []
    normalized = [
        _normalize_result(item, category, budget, preference, coverage)
        for item in raw_results
        if isinstance(item, dict)
    ]
    ranked = sorted(
        [item for item in normalized if item],
        key=lambda product: product["score"],
        reverse=True,
    )
    return [_without_score(product) for product in ranked[:limit]]


def _normalize_result(
    item: dict[str, Any],
    category: str,
    budget: str,
    preference: str,
    coverage: str,
) -> dict[str, Any] | None:
    name = str(item.get("title") or "").strip()
    if not name:
        return None

    price = str(item.get("price") or "Price varies")
    source = str(item.get("source") or item.get("seller") or "Google Shopping")
    image_url = str(item.get("thumbnail") or item.get("image") or "")
    link = str(item.get("link") or item.get("product_link") or "")
    rating = item.get("rating")
    reviews = item.get("reviews")

    text = f"{name} {source}".lower()
    score = 0
    for token in category.replace("_", " ").split():
        if token in text:
            score += 3
    for token in preference.lower().split():
        if token in text:
            score += 1
    if coverage and coverage.lower() in text:
        score += 2
    if rating:
        score += 1
    if reviews:
        score += 1
    if any(word in text for word in ["sample", "dupe list", "empty", "case only"]):
        score -= 5

    return {
        "name": name,
        "category": category,
        "budget": budget,
        "finish": preference or "varies",
        "coverage": coverage,
        "why": f"Live Google Shopping result for {category}, selected for fit with your {budget} {preference or 'beauty'} request.",
        "shade_note": "Check shade options and retailer availability before buying." if category in {"foundation", "skin tint", "concealer"} else "No exact shade needed.",
        "typical_price": price,
        "image_url": image_url,
        "price_note": "Live Google Shopping result via SerpApi; price and availability can change.",
        "shopping_link": link,
        "retailer": source,
        "rating": str(rating or ""),
        "reviews": str(reviews or ""),
        "source": "serpapi_google_shopping",
        "score": score,
    }


def _without_score(product: dict[str, Any]) -> dict[str, str]:
    return {key: str(value) for key, value in product.items() if key != "score"}
