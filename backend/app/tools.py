from typing import Any

from .product_catalog import recommend_products


DEPTHS = ["fair", "light", "medium", "tan", "deep", "rich"]
UNDERTONES = ["cool", "neutral", "warm", "olive"]


def _contains_any(text: str, words: list[str]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in words)


def analyze_skin_tone_tool(image: str | None) -> dict[str, Any]:
    if not image:
        return {
            "status": "needs_input",
            "undertone": "neutral",
            "depth": "medium",
            "confidence": 0.28,
            "notes": "No image was provided, so a neutral medium placeholder was used.",
        }

    lowered = image.lower()
    undertone = "neutral"
    if _contains_any(lowered, ["warm", "gold", "yellow", "peach"]):
        undertone = "warm"
    elif _contains_any(lowered, ["cool", "pink", "rosy", "blue"]):
        undertone = "cool"
    elif "olive" in lowered:
        undertone = "olive"

    depth = "medium"
    for candidate in DEPTHS:
        if candidate in lowered:
            depth = candidate
            break

    return {
        "status": "estimated",
        "undertone": undertone,
        "depth": depth,
        "confidence": 0.62,
        "notes": "Image input was available. For production-grade color matching, pair this with calibrated lighting guidance.",
    }


def match_foundation_tool(undertone: str, depth: str) -> dict[str, Any]:
    undertone = undertone.lower() if undertone else "neutral"
    depth = depth.lower() if depth else "medium"
    family = f"{depth.title()} {undertone.title()}"
    finish = "natural satin" if undertone in {"neutral", "olive"} else "soft radiant"
    return {
        "shade_family": family,
        "undertone": undertone,
        "depth": depth,
        "matches": [
            f"{family} shade family",
            f"{family} flexible tint family",
            f"{family} longer-wear foundation family",
        ],
        "product_recommendations": recommend_products(
            category="foundation",
            undertone=undertone,
            depth=depth,
            budget="moderate",
            finish_preference=finish,
            limit=3,
        ),
        "application_tip": "Swatch along the jawline and check after 10 minutes in indirect daylight.",
        "finish": finish,
    }


def infer_skin_type_tool(quiz_answers: dict[str, Any]) -> dict[str, Any]:
    joined = " ".join(str(value) for value in quiz_answers.values()).lower()
    oily_score = sum(word in joined for word in ["oily", "shiny", "greasy", "large pores"])
    dry_score = sum(word in joined for word in ["dry", "tight", "flaky", "rough"])
    sensitive_score = sum(word in joined for word in ["sting", "red", "sensitive", "burn"])

    if oily_score and dry_score:
        skin_type = "combination"
    elif oily_score:
        skin_type = "oily"
    elif dry_score:
        skin_type = "dry"
    else:
        skin_type = "balanced"

    return {
        "skin_type": skin_type,
        "signals": {
            "oiliness": oily_score,
            "dryness": dry_score,
            "sensitivity": sensitive_score,
        },
        "notes": "This is a cosmetic skin-type inference from quiz answers, not a diagnosis.",
    }


def routine_generator_tool(
    skin_type: str,
    undertone: str,
    depth: str,
    preference: str,
    budget: str,
) -> dict[str, Any]:
    skin_type = (skin_type or "balanced").lower()
    budget = budget or "moderate"
    preference = preference or "natural"
    preference_text = preference.lower()
    base_category = "skin tint" if any(word in preference_text for word in ["skin tint", "light coverage", "sheer", "dewy"]) else "foundation"
    concealer_coverage = "full" if any(word in preference_text for word in ["full", "glam", "event", "long wear", "long-wear"]) else "medium"

    moisturizer = {
        "oily": "lightweight gel moisturizer",
        "dry": "ceramide-rich cream moisturizer",
        "combination": "gel-cream moisturizer",
        "balanced": "simple lotion moisturizer",
    }.get(skin_type, "simple lotion moisturizer")

    base_products = recommend_products(base_category, skin_type=skin_type, undertone=undertone, depth=depth, budget=budget, finish_preference=preference, limit=1)
    concealer_products = [
        product
        for product in recommend_products("concealer", skin_type=skin_type, undertone=undertone, depth=depth, budget=budget, finish_preference=concealer_coverage, limit=4)
        if product.get("coverage") == concealer_coverage
    ] or recommend_products("concealer", skin_type=skin_type, undertone=undertone, depth=depth, budget=budget, limit=1)

    contour_first = "liquid contour" if budget.lower() == "drugstore" else "cream contour"
    contour_second = "cream contour" if contour_first == "liquid contour" else "liquid contour"

    makeup_bag = {
        "primer": _products_for_slot("primer", skin_type, undertone, depth, preference, budget, "", 1),
        "base": _products_for_slot(base_category, skin_type, undertone, depth, preference, budget, "", 1, base_products),
        "powder_blush": _products_for_slot("powder blush", skin_type, undertone, depth, preference, budget, "", 1),
        "liquid_blush": _products_for_slot("liquid blush", skin_type, undertone, depth, preference, budget, "", 1),
        "powder_contour_or_bronzer": _products_for_slot("powder bronzer", skin_type, undertone, depth, preference, budget, "", 1),
        "cream_or_liquid_contour_bronzer": (
            _products_for_slot(contour_first, skin_type, undertone, depth, preference, budget, "", 1)
            or _products_for_slot(contour_second, skin_type, undertone, depth, preference, budget, "", 1)
        ),
        "concealer": _products_for_slot("concealer", skin_type, undertone, depth, preference, budget, concealer_coverage, 1, concealer_products[:1]),
        "pressed_setting_powder": _products_for_slot("pressed setting powder", skin_type, undertone, depth, preference, budget, "", 1),
        "loose_setting_powder": _products_for_slot("loose setting powder", skin_type, undertone, depth, preference, budget, "", 1),
        "setting_sprays": _products_for_slot("setting spray", skin_type, undertone, depth, preference, budget, "", 2),
    }
    prep_products = recommend_products("moisturizer", skin_type=skin_type, budget=budget, limit=1) + recommend_products("sunscreen", skin_type=skin_type, budget=budget, limit=1)
    product_recommendations = prep_products + [product for products in makeup_bag.values() for product in products]

    return {
        "morning": [
            "Gentle cleanse or water rinse",
            "Hydrating serum if skin feels tight",
            moisturizer,
            "Broad-spectrum SPF 30 or higher",
            f"{preference} base in a {depth} {undertone} family",
        ],
        "evening": [
            "Remove makeup thoroughly",
            "Gentle cleanser",
            moisturizer,
            "Use exfoliating or retinoid-style cosmetics sparingly if already tolerated",
        ],
        "budget_tier": budget,
        "base_choice": base_category,
        "concealer_coverage": concealer_coverage,
        "shopping_priorities": ["SPF", "base formula fit", "barrier-support moisturizer"],
        "makeup_bag": makeup_bag,
        "product_recommendations": product_recommendations,
    }


def _products_for_slot(
    category: str,
    skin_type: str,
    undertone: str,
    depth: str,
    preference: str,
    budget: str,
    coverage: str,
    limit: int,
    fallback: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    return fallback or recommend_products(
        category,
        skin_type=skin_type,
        undertone=undertone,
        depth=depth,
        budget=budget,
        finish_preference=preference,
        limit=limit,
    )


def makeup_problem_solver_tool(problem_text: str, product_list: list[str]) -> dict[str, Any]:
    text = problem_text.lower()
    fixes: list[str] = []

    if _contains_any(text, ["cakey", "texture", "patchy"]):
        fixes.extend([
            "Use less foundation and build only where needed.",
            "Let moisturizer and SPF settle before complexion products.",
            "Mist sponge lightly, then press over textured areas.",
        ])
    if _contains_any(text, ["separate", "pilling", "balls up"]):
        fixes.extend([
            "Avoid layering silicone-heavy and water-gel products too quickly.",
            "Wait 60 seconds between skin prep layers.",
            "Try primer on only one side of the face to compare compatibility.",
        ])
    if _contains_any(text, ["oxidize", "orange", "dark"]):
        fixes.extend([
            "Test a half shade lighter or more neutral undertone.",
            "Set with a translucent powder only where needed.",
        ])
    if not fixes:
        fixes.append("Start with thinner layers, simplify skin prep, and test one product change at a time.")

    product_recommendations = []
    if _contains_any(text, ["cakey", "texture", "patchy"]):
        product_recommendations.extend(recommend_products("primer", budget="drugstore", limit=2))
        product_recommendations.extend(recommend_products("setting powder", budget="drugstore", limit=1))
    if _contains_any(text, ["separate", "pilling", "balls up", "shiny", "oil"]):
        product_recommendations.extend(recommend_products("setting powder", skin_type="oily", budget="moderate", limit=2))

    return {
        "problem": problem_text,
        "products_reviewed": product_list,
        "likely_cosmetic_causes": ["layering", "formula compatibility", "shade or finish mismatch"],
        "fixes": fixes,
        "product_recommendations": product_recommendations[:4],
    }


def look_recreator_tool(inspiration_image: str | None, user_profile: dict[str, Any]) -> dict[str, Any]:
    style_hint = str(user_profile.get("style", "soft glam"))
    undertone = user_profile.get("undertone", "neutral")
    depth = user_profile.get("depth", "medium")
    return {
        "look": style_hint,
        "steps": [
            "Prep with moisturizer and SPF if daytime.",
            f"Use a complexion product matched to {depth} {undertone}.",
            "Place blush high on the cheeks and diffuse edges.",
            "Use a soft brown liner close to the lash line.",
            "Choose a lip shade one step deeper than your natural lip color.",
        ],
        "image_used": bool(inspiration_image),
        "adaptation_notes": "The look is adapted to the provided profile and cosmetic preferences.",
        "product_recommendations": (
            recommend_products("foundation", undertone=undertone, depth=depth, budget=user_profile.get("budget", "moderate"), limit=2)
            + recommend_products("complexion booster", undertone=undertone, depth=depth, budget=user_profile.get("budget", "moderate"), limit=1)
        ),
    }


TOOL_REGISTRY = {
    "analyze_skin_tone_tool": analyze_skin_tone_tool,
    "match_foundation_tool": match_foundation_tool,
    "infer_skin_type_tool": infer_skin_type_tool,
    "routine_generator_tool": routine_generator_tool,
    "makeup_problem_solver_tool": makeup_problem_solver_tool,
    "look_recreator_tool": look_recreator_tool,
}
