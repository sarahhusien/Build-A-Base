from typing import Any


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
            f"{family} flexible skin tint",
            f"{family} buildable serum foundation",
            f"{family} long-wear complexion stick",
        ],
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

    moisturizer = {
        "oily": "lightweight gel moisturizer",
        "dry": "ceramide-rich cream moisturizer",
        "combination": "gel-cream moisturizer",
        "balanced": "simple lotion moisturizer",
    }.get(skin_type, "simple lotion moisturizer")

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
        "shopping_priorities": ["SPF", "base shade match", "barrier-support moisturizer"],
    }


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

    return {
        "problem": problem_text,
        "products_reviewed": product_list,
        "likely_cosmetic_causes": ["layering", "formula compatibility", "shade or finish mismatch"],
        "fixes": fixes,
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
    }


TOOL_REGISTRY = {
    "analyze_skin_tone_tool": analyze_skin_tone_tool,
    "match_foundation_tool": match_foundation_tool,
    "infer_skin_type_tool": infer_skin_type_tool,
    "routine_generator_tool": routine_generator_tool,
    "makeup_problem_solver_tool": makeup_problem_solver_tool,
    "look_recreator_tool": look_recreator_tool,
}
