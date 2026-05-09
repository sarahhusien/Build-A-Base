from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from .database import Feedback, Product


FEEDBACK_PENALTIES = {
    "too dry": ["matte", "powder", "soft matte"],
    "too cakey": ["full", "matte", "powder"],
    "too orange": ["warm"],
    "too oily": ["dewy", "radiant", "glow"],
}


def product_formula_base(product: Product | dict[str, Any]) -> str:
    value = _get(product, "formula_base")
    if value:
        return value
    text = " ".join(
        str(_get(product, key) or "")
        for key in ["product_type", "category", "finish", "coverage", "good_for", "notes", "why"]
    ).lower()
    if "primer" in text and any(word in text for word in ["grip", "hydro", "hydrating", "dewy"]):
        return "water-based"
    if any(word in text for word in ["matte", "blur", "pore", "longwear", "long wear", "soft-focus"]):
        return "silicone-heavy"
    if any(word in text for word in ["dewy", "radiant", "glow", "hydrating"]):
        return "water-based"
    if "powder" in text:
        return "powder"
    return "balanced"


def compatibility_profile(product: Product | dict[str, Any]) -> dict[str, str]:
    return {
        "formula_base": product_formula_base(product),
        "best_for": _get(product, "best_for") or _get(product, "good_for") or "",
        "avoid_pairing_with": _get(product, "avoid_pairing_with") or "",
        "compatibility_notes": _get(product, "compatibility_notes") or "",
    }


def score_product_for_profile(
    product: Product,
    skin_type: str,
    undertone: str = "",
    finish_look: str = "",
    feedback_counts: dict[str, int] | None = None,
) -> tuple[int, list[str], list[str]]:
    score = 62
    positives: list[str] = []
    downsides: list[str] = []
    text = _product_text(product)

    if skin_type and skin_type.lower() in product.skin_type_match.lower():
        score += 12
        positives.append(f"skin type compatibility: {skin_type}")
    if undertone and (undertone.lower() in product.undertone.lower() or not product.undertone):
        score += 6
        positives.append(f"undertone: {undertone}")
    finish_text = f"{product.finish} {product.coverage} {product.good_for} {product.notes}".lower()
    look_words = _finish_look_words(finish_look)
    if look_words and any(word in finish_text for word in look_words):
        score += 10
        positives.append(f"finish look: {finish_look}")

    if skin_type == "dry" and any(word in text for word in ["hydrating", "dewy", "radiant", "glow", "cream"]):
        score += 8
        positives.append("hydrating or glow-friendly for dry skin")
    if skin_type == "dry" and any(word in text for word in ["matte", "powder"]):
        score -= 8
        downsides.append("may emphasize dryness if skin is not well prepped")
    if skin_type == "oily" and any(word in text for word in ["matte", "oil", "powder", "long wear", "longwear"]):
        score += 8
        positives.append("helps control shine for oily skin")
    if skin_type == "oily" and any(word in text for word in ["dewy", "radiant", "glow"]):
        score -= 7
        downsides.append("could get shiny faster on oily skin")

    for feedback_type, count in (feedback_counts or {}).items():
        penalty_words = FEEDBACK_PENALTIES.get(feedback_type, [])
        if any(word in text for word in penalty_words):
            score -= min(10, 3 * count)
            downsides.append(f"adjusted down from feedback: {feedback_type}")
    if (feedback_counts or {}).get("wrong budget"):
        score -= min(8, 2 * (feedback_counts or {}).get("wrong budget", 0))

    return max(35, min(98, score)), positives, downsides


def _finish_look_words(finish_look: str) -> list[str]:
    text = finish_look.lower()
    if any(word in text for word in ["full glam", "glam"]):
        return ["full", "matte", "long wear", "longwear", "glam"]
    if any(word in text for word in ["natural", "neutral", "everyday"]):
        return ["natural", "satin", "medium", "skinlike"]
    if any(word in text for word in ["dewy", "radiant", "glowy", "glow"]):
        return ["dewy", "radiant", "glow", "glowy"]
    if "matte" in text:
        return ["matte", "soft matte"]
    return [word for word in text.split() if word]


def routine_compatibility(
    products: list[dict[str, Any]],
    skin_type: str,
) -> dict[str, Any]:
    warnings: list[str] = []
    positives: list[str] = []
    score = 86
    primer = _first_type(products, "primer")
    foundations = [product for product in products if _category(product) in {"foundation", "skin tint"}]
    powders = [product for product in products if "powder" in _category(product)]

    if primer and foundations:
        primer_base = product_formula_base(primer)
        for foundation in foundations:
            foundation_base = product_formula_base(foundation)
            if primer_base == "water-based" and foundation_base == "silicone-heavy":
                warnings.append("Water-based primer with a silicone-heavy foundation can separate. Use thin layers and let primer set first.")
                score -= 10
            elif primer_base == foundation_base:
                positives.append("Primer and base have similar formula behavior, which can improve wear.")
                score += 3

    if skin_type == "dry":
        matte_base = any("matte" in str(product.get("finish", "")).lower() for product in foundations)
        if matte_base:
            warnings.append("Matte base on dry or flaky skin can increase cakiness without hydrating prep.")
            score -= 8
        if len(powders) > 1:
            warnings.append("Using both pressed and loose powder on dry skin can look cakey. Apply only where needed.")
            score -= 8
        if primer and any(word in _product_text(primer) for word in ["hydro", "hydrating", "dewy", "grip"]):
            positives.append("Hydrating/gripping primer supports dry skin and helps base sit smoother.")
            score += 6

    if skin_type == "oily":
        if primer and any(word in _product_text(primer) for word in ["matte", "blur", "pore", "oil"]):
            positives.append("Oil-control primer supports oily skin and helps reduce separation.")
            score += 6
        if powders:
            positives.append("Setting powder helps control shine and lock in the base.")
            score += 4

    if not warnings:
        positives.append("No major formula conflicts detected in this routine.")

    return {
        "routine_score": max(35, min(98, score)),
        "compatibility_warnings": _unique_notes(warnings),
        "positive_compatibility_notes": _unique_notes(positives),
    }


def feedback_counts_for_product(db: Session, product_id: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    rows = db.query(Feedback).filter(Feedback.product_id == product_id).all()
    for row in rows:
        counts[row.feedback_type] = counts.get(row.feedback_type, 0) + 1
    return counts


def _first_type(products: list[dict[str, Any]], product_type: str) -> dict[str, Any] | None:
    return next((product for product in products if product_type in _category(product)), None)


def _category(product: dict[str, Any]) -> str:
    return str(product.get("category") or product.get("product_type") or "").lower()


def _product_text(product: Product | dict[str, Any]) -> str:
    fields = ["name", "product_type", "category", "finish", "coverage", "good_for", "notes", "why"]
    return " ".join(str(_get(product, field) or "") for field in fields).lower()


def _get(product: Product | dict[str, Any], field: str) -> Any:
    if isinstance(product, dict):
        return product.get(field)
    return getattr(product, field, "")


def _unique_notes(notes: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for note in notes:
        key = note.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(note)
    return unique
