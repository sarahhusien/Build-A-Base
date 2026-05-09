import json
import re
from hashlib import sha1
from typing import Any

from openai import OpenAI
from sqlalchemy import or_

from .compatibility import feedback_counts_for_product, routine_compatibility
from .config import get_settings
from .database import Product, SessionLocal
from .schemas import AgentRequest, AgentResponse, DISCLAIMER, ToolCallResult
from .tools import (
    analyze_skin_tone_tool,
    infer_skin_type_tool,
    look_recreator_tool,
    makeup_problem_solver_tool,
    match_foundation_tool,
    routine_generator_tool,
)


MEDICAL_TERMS = [
    "eczema",
    "psoriasis",
    "rash",
    "infection",
    "bleeding",
    "painful",
    "hives",
    "melasma",
    "rosacea",
    "acne diagnosis",
]

ROUTINE_BRAND_QUESTION = (
    "Do you have any particular brands you want me to prioritize or avoid? "
    "If not, I can keep choosing the best fits for your skin type, finish, coverage, and budget."
)

ROUTINE_SLOT_LABELS = {
    "primer": "Primer",
    "base": "Foundation or Skin Tint",
    "powder_blush": "Powder Blush",
    "liquid_blush": "Liquid Blush",
    "powder_contour_or_bronzer": "Powder Contour or Bronzer",
    "cream_or_liquid_contour_bronzer": "Cream or Liquid Contour",
    "concealer": "Concealer",
    "pressed_setting_powder": "Pressed Setting Powder",
    "loose_setting_powder": "Loose Setting Powder",
    "setting_sprays": "Setting Sprays",
}

KNOWN_BRANDS = [
    "maybelline",
    "l'oreal",
    "loreal",
    "nyx",
    "e.l.f",
    "elf",
    "cerave",
    "rare beauty",
    "milani",
    "fenty",
    "laura mercier",
    "charlotte tilbury",
    "urban decay",
]

SKIN_TYPES = ["dry", "oily", "combination", "balanced"]
UNDERTONES = ["cool", "neutral", "warm", "olive"]
DEPTHS = ["fair", "light", "medium", "tan", "deep", "rich"]
PRICE_TIERS = ["drugstore", "mid_range", "premium"]
PROBLEM_WORDS = ["cakiness", "cakey", "dryness", "oxidation", "oxidize", "separation", "separating", "separates", "separated", "oiliness", "gets oily", "shiny", "flaking", "flaky", "patchy", "pilling"]
FULL_FACE_TRIGGERS = ["full glam", "glam", "makeup look", "full face", "routine", "complete look"]
FULL_FACE_CATEGORIES = [
    "primer",
    "foundation",
    "concealer",
    "powder blush",
    "liquid blush",
    "powder bronzer",
    "cream contour",
    "pressed setting powder",
    "loose setting powder",
    "setting spray",
]
PRODUCT_TYPE_ALIASES = {
    "primer": "primer",
    "foundation": "foundation",
    "base": "foundation",
    "skin tint": "skin tint",
    "tinted moisturizer": "skin tint",
    "concealer": "concealer",
    "powder": "setting powder",
    "setting powder": "setting powder",
    "pressed powder": "pressed setting powder",
    "loose powder": "loose setting powder",
    "setting spray": "setting spray",
    "spray": "setting spray",
    "blush": "liquid blush",
    "bronzer": "powder bronzer",
    "contour": "cream contour",
}
PROBLEM_CATEGORIES = {
    "cakey": ["primer", "foundation", "pressed setting powder", "setting spray"],
    "cakiness": ["primer", "foundation", "pressed setting powder", "setting spray"],
    "patchy": ["primer", "foundation", "setting spray"],
    "dryness": ["primer", "skin tint", "setting spray"],
    "flaking": ["primer", "skin tint"],
    "flaky": ["primer", "skin tint"],
    "oxidation": ["foundation", "setting powder"],
    "oxidize": ["foundation", "setting powder"],
    "separation": ["primer", "foundation", "setting powder"],
    "separating": ["primer", "foundation", "setting powder"],
    "separates": ["primer", "foundation", "setting powder"],
    "separated": ["primer", "foundation", "setting powder"],
    "oiliness": ["primer", "foundation", "loose setting powder", "setting spray"],
    "gets oily": ["primer", "foundation", "loose setting powder", "setting spray"],
    "shiny": ["primer", "foundation", "loose setting powder", "setting spray"],
    "pilling": ["primer", "skin tint"],
}


class BeautyAgent:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key) if self.settings.openai_api_key else None

    def run(self, request: AgentRequest) -> AgentResponse:
        if self._contains_medical_request(request):
            return AgentResponse(
                summary="I can help with cosmetic preferences, comfort, and product selection, but not medical skin concerns.",
                tools_used=[],
                recommendations=[
                    "For beauty support, I can suggest gentle-looking makeup finishes, non-medical skin prep, and base product guidance.",
                    "For symptoms such as pain, spreading rash, infection, bleeding, or persistent irritation, please contact a licensed medical professional.",
                ],
                follow_up_questions=[],
                explanation="No beauty tools were used because the request appears to ask for medical skin guidance.",
                disclaimer=DISCLAIMER,
            )

        intent = self._extract_intent(request)
        return self._run_sqlite_only_agent(request, intent)

    def _run_sqlite_only_agent(self, request: AgentRequest, intent: dict[str, Any]) -> AgentResponse:
        database_result = self._agent_database_recommendations(intent)
        tool_results = [
            ToolCallResult(
                tool="sqlite_product_database",
                input_summary="typed-message intent and SQLite product filters",
                output=database_result,
            )
        ]
        recommendations = _recommendations_from_filtered_tools(tool_results)
        summary = _summary_from_intent(intent)
        explanation = _intent_explanation(intent, tool_results)
        debug_info = database_result.get("debug", {})

        print("TYPED USER MESSAGE:", request.text_input)
        print("DETECTED INTENT:", intent)
        print("DETECTED PRICE_TIER:", intent["price_tier"])
        print("DETECTED COVERAGE:", intent["coverage"])
        print("PRODUCTS SENT TO OPENAI:", [])
        print("FINAL PRODUCTS RETURNED:", debug_info.get("final_products", []))

        return AgentResponse(
            summary=summary,
            tools_used=tool_results,
            recommendations=list(dict.fromkeys(recommendations))[:5],
            follow_up_questions=[],
            explanation=explanation,
            disclaimer=DISCLAIMER,
            request_text=request.text_input,
            debug_info={
                "route_used": "/api/agent sqlite_only",
                "user_text": request.text_input,
                "detected_price_tier": intent["price_tier"],
                "detected_coverage": intent["coverage"],
                "candidate_products_before_filter": debug_info.get("candidate_products_before_filter", []),
                "candidate_products_after_filter": debug_info.get("candidate_products_after_filter", []),
                "final_products": debug_info.get("final_products", []),
            },
        )

    def _contains_medical_request(self, request: AgentRequest) -> bool:
        combined = f"{request.goal} {request.text_input} {json.dumps(request.profile)}".lower()
        return any(term in combined for term in MEDICAL_TERMS)

    def _llm_plan(self, request: AgentRequest) -> list[str] | None:
        if not self.client:
            return None

        system = (
            "You are a cosmetic-only AI Beauty Agent planner. Choose tools required to satisfy the user goal. "
            "Available tools: analyze_skin_tone_tool, match_foundation_tool, infer_skin_type_tool, "
            "routine_generator_tool, makeup_problem_solver_tool, look_recreator_tool. "
            "Return JSON only as {\"tools\": [tool names in execution order]}. "
            "Ask for follow-up only by omitting tools that lack required inputs. Do not provide medical diagnosis."
        )
        payload = {
            "goal": request.goal,
            "text_input": request.text_input,
            "has_image": bool(request.image),
            "profile_keys": list(request.profile.keys()),
        }
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(payload)},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            parsed = json.loads(content)
            tools = parsed.get("tools", [])
            return [tool for tool in tools if isinstance(tool, str)]
        except Exception:
            return None

    def _fallback_plan(self, request: AgentRequest) -> list[str]:
        text = f"{request.goal} {request.text_input}".lower()
        tools: list[str] = []
        if request.image or any(word in text for word in ["tone", "undertone", "base match", "selfie"]):
            tools.extend(["analyze_skin_tone_tool", "match_foundation_tool"])
        if request.profile.get("quiz_answers") or "skin type" in text or "quiz" in text:
            tools.append("infer_skin_type_tool")
        if any(word in text for word in ["routine", "skincare", "regimen", "products"]):
            tools.append("routine_generator_tool")
        if any(word in text for word in ["cakey", "patchy", "pilling", "problem", "separating", "separates", "separation", "oxidize"]):
            tools.append("makeup_problem_solver_tool")
        if request.image or self._has_any_word(text, ["recreate", "inspiration"]):
            tools.append("look_recreator_tool")
        return tools or ["infer_skin_type_tool", "routine_generator_tool"]

    def _has_any_word(self, text: str, words: list[str]) -> bool:
        return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)

    def _execute_plan(self, request: AgentRequest, plan: list[str], intent: dict[str, Any] | None = None) -> AgentResponse:
        intent = intent or self._extract_intent(request)
        plan = list(dict.fromkeys(plan))
        if "look_recreator_tool" in plan and not request.image and not self._has_any_word(request.text_input.lower(), ["recreate", "inspiration"]):
            plan.remove("look_recreator_tool")
        if self._needs_database_recommendations(intent, plan):
            plan.append("routine_generator_tool")
        context: dict[str, Any] = {
            "undertone": intent["undertone"],
            "depth": intent["depth"],
            "skin_type": intent["skin_type"],
        }
        tool_results: list[ToolCallResult] = []
        recommendations: list[str] = []
        follow_ups: list[str] = []
        database_result_cache: dict[str, Any] | None = None
        has_routine_tool = "routine_generator_tool" in plan

        for tool_name in plan:
            if tool_name == "analyze_skin_tone_tool":
                result = analyze_skin_tone_tool(request.image)
                context.update({"undertone": result["undertone"], "depth": result["depth"]})
                if result["status"] == "needs_input":
                    follow_ups.append("Upload a clear, natural-light selfie if you want a more specific tone family and complexion range estimate.")
                self._append(tool_results, tool_name, "image input", result)
            elif tool_name == "match_foundation_tool":
                result = match_foundation_tool(context["undertone"], context["depth"])
                recommendations.extend(self._product_recommendation_text(result))
                self._append(tool_results, tool_name, f"{context['undertone']} tone family, {context['depth']} complexion range", result)
            elif tool_name == "infer_skin_type_tool":
                answers = request.profile.get("quiz_answers", {})
                if not answers:
                    follow_ups.append("Answer the skin type quiz questions if you want a more confident routine.")
                result = infer_skin_type_tool(answers)
                context["skin_type"] = result["skin_type"]
                self._append(tool_results, tool_name, "quiz answers", result)
            elif tool_name == "routine_generator_tool":
                database_result_cache = database_result_cache or self._agent_database_recommendations(intent)
                result = database_result_cache
                if not self._has_brand_preference(request):
                    follow_ups.append(ROUTINE_BRAND_QUESTION)
                recommendations.extend(self._routine_recommendation_text(result) or result["morning"][:3])
                self._append(tool_results, tool_name, "typed-message intent and database filters", result)
            elif tool_name == "makeup_problem_solver_tool":
                result = makeup_problem_solver_tool(request.text_input, request.profile.get("product_list", []))
                database_result = database_result_cache or self._agent_database_recommendations(intent)
                database_result_cache = database_result
                result["product_recommendations"] = database_result["product_recommendations"]
                if not has_routine_tool:
                    result["makeup_bag"] = database_result["makeup_bag"]
                result["debug"] = database_result["debug"]
                recommendations.extend(self._product_recommendation_text(result) or result["fixes"][:3])
                self._append(tool_results, tool_name, "problem text and product list", result)
            elif tool_name == "look_recreator_tool":
                result = look_recreator_tool(request.image, {**request.profile, **context})
                recommendations.extend(self._product_recommendation_text(result) or result["steps"][:3])
                self._append(tool_results, tool_name, "inspiration image and user profile", result)

        tool_results = _sanitize_tool_results_for_price_tier(tool_results, intent["price_tier"])
        recommendations = _recommendations_from_filtered_tools(tool_results) or recommendations
        used_names = [result.tool.replace("_tool", "").replace("_", " ") for result in tool_results]
        summary = "I built a cosmetic recommendation using " + ", ".join(used_names) + "."
        explanation = self._explain(tool_results, request)
        print("TYPED USER MESSAGE:", request.text_input)
        print("DETECTED INTENT:", intent)
        print("DETECTED PRICE_TIER:", intent["price_tier"])
        print("PRODUCTS SENT TO OPENAI:", _product_log_tuples_from_tools(tool_results))
        ai_response = self._llm_synthesize(request, tool_results, recommendations, follow_ups, intent)
        if ai_response:
            summary = ai_response.get("summary", summary)
            explanation = ai_response.get("explanation", explanation)
            recommendations = ai_response.get("recommendations", recommendations)
            follow_ups = ai_response.get("follow_up_questions", follow_ups)
        routine_text = self._routine_text_from_results(tool_results)
        if routine_text:
            recommendations = routine_text
            if not self._has_brand_preference(request) and ROUTINE_BRAND_QUESTION not in follow_ups:
                follow_ups.append(ROUTINE_BRAND_QUESTION)
        if any(result.tool in {"routine_generator_tool", "makeup_problem_solver_tool"} for result in tool_results):
            summary = _summary_from_intent(intent)
            explanation = _intent_explanation(intent, tool_results)
            recommendations = _recommendations_from_filtered_tools(tool_results) or recommendations
        recommendations = _filter_recommendation_text_for_price_tier(recommendations, tool_results, intent["price_tier"])
        print("FINAL PRODUCTS RETURNED:", _product_log_tuples_from_tools(tool_results))

        return AgentResponse(
            summary=summary,
            tools_used=tool_results,
            recommendations=list(dict.fromkeys(recommendations))[:5],
            follow_up_questions=list(dict.fromkeys(follow_ups)),
            explanation=explanation,
            disclaimer=DISCLAIMER,
            request_text=request.text_input,
        )

    def _needs_database_recommendations(self, intent: dict[str, Any], plan: list[str]) -> bool:
        if "routine_generator_tool" in plan or "makeup_problem_solver_tool" in plan:
            return False
        return bool(intent["product_type"] or intent["problems"] or intent["raw_text"])

    def _needs_database_backed_agent(self, intent: dict[str, Any]) -> bool:
        return bool(intent["raw_text"] or intent["product_type"] or intent["problems"])

    def _extract_intent(self, request: AgentRequest) -> dict[str, Any]:
        text = f"{request.goal} {request.text_input}".lower()
        profile = request.profile
        skin_type = _first_present(text, SKIN_TYPES) or str(profile.get("skin_type") or "balanced").lower()
        undertone = _first_present(text, UNDERTONES) or str(profile.get("undertone") or "neutral").lower()
        depth = _first_present(text, DEPTHS) or str(profile.get("depth") or "medium").lower()
        coverage = _coverage_from_text(text, str(profile.get("coverage") or ""))
        finish = _finish_from_text(text, str(profile.get("preference") or "natural"))
        price_tier = _price_tier_from_text(text, str(profile.get("budget") or "moderate"))
        product_type = _product_type_from_text(text)
        problems = [word for word in PROBLEM_WORDS if word in text]
        categories = _categories_for_intent(product_type, problems, text)
        intent = {
            "skin_type": skin_type,
            "undertone": undertone,
            "depth": depth,
            "coverage": coverage,
            "finish": finish,
            "price_tier": price_tier,
            "product_type": product_type,
            "problems": problems,
            "categories": categories,
            "raw_text": request.text_input,
        }
        print(f"[Build a Base agent] extracted_intent={intent}")
        return intent

    def _agent_database_recommendations(self, intent: dict[str, Any]) -> dict[str, Any]:
        db = SessionLocal()
        try:
            before_filter_rows: list[Product] = []
            selected: list[dict[str, Any]] = []
            filters_used: list[dict[str, Any]] = []
            sql_used: list[str] = []
            candidate_names: list[str] = []
            for category in intent["categories"]:
                before_filter_rows.extend(_query_agent_candidates_before_price_filter(db, intent, category))
                rows, debug = _query_agent_candidates(db, intent, category)
                filters_used.append(debug["filters"])
                sql_used.extend(debug["sql"])
                candidate_names.extend([f"{row.brand} {row.name}" for row in rows])
                selected.extend(_product_to_agent_dict(row, intent, debug["confidence"]) for row in rows)
        finally:
            db.close()

        candidate_products_before_filter = _dedupe_debug_products(
            _product_debug_dict(row) for row in before_filter_rows
        )
        selected = _apply_feedback_adjustments(_enforce_requested_price_tier(selected, intent["price_tier"]))
        _raise_if_blocked_tier_present(selected, intent["price_tier"], "candidate_products_after_filter")
        candidate_products_after_filter = _debug_products_from_dicts(selected)
        candidate_tuples = [(product.get("brand"), product.get("name"), product.get("price_tier")) for product in selected]
        unique = _dedupe_products(selected)
        ranked = _rank_agent_products(unique, intent)
        final_limit = 10 if _is_full_face_request(intent["raw_text"].lower()) else 5
        final = _enforce_requested_price_tier(_dedupe_products(_diverse_products(ranked, final_limit)), intent["price_tier"])[:final_limit]
        _raise_if_blocked_tier_present(final, intent["price_tier"], "final_products")
        compatibility = routine_compatibility(final, intent["skin_type"])

        ids = [product.get("id") for product in final]
        final_tuples = [(product.get("brand"), product.get("name"), product.get("price_tier")) for product in final]
        print("REQUESTED PRICE TIER:", intent["price_tier"])
        print("CANDIDATES SENT TO AI:", candidate_tuples)
        print("FINAL RESULTS:", final_tuples)
        print(f"[Build a Base agent] user_message={intent['raw_text']!r}")
        print(f"[Build a Base agent] extracted_filters={intent}")
        print(f"[Build a Base agent] sql_or_filtering_logic={sql_used}")
        print(f"[Build a Base agent] candidate_count={len(selected)} unique={len(unique)}")
        print(f"[Build a Base agent] candidate_product_names={candidate_names}")
        print(f"[Build a Base agent] final_product_ids={ids}")

        makeup_bag: dict[str, list[dict[str, Any]]] = {}
        for product in final:
            slot = _slot_for_category(product.get("category", "product"))
            makeup_bag.setdefault(slot, []).append(product)

        return {
            "morning": _routine_steps_for_intent(intent),
            "evening": ["Remove makeup fully", "Cleanse gently", "Moisturize according to your skin type"],
            "budget_tier": intent["price_tier"],
            "base_choice": intent.get("product_type") or "custom",
            "concealer_coverage": intent["coverage"],
            "shopping_priorities": intent["problems"] or [intent["finish"], intent["coverage"]],
            "makeup_bag": makeup_bag,
            "product_recommendations": final,
            "routine_score": compatibility["routine_score"],
            "compatibility_warnings": compatibility["compatibility_warnings"],
            "positive_compatibility_notes": compatibility["positive_compatibility_notes"],
            "debug": {
                "intent": intent,
                "filters_used": filters_used,
                "candidate_product_names": candidate_names,
                "final_product_ids": ids,
                "candidate_products_before_filter": candidate_products_before_filter,
                "candidate_products_after_filter": candidate_products_after_filter,
                "final_products": _debug_products_from_dicts(final),
            },
        }

    def _llm_synthesize(
        self,
        request: AgentRequest,
        tool_results: list[ToolCallResult],
        recommendations: list[str],
        follow_ups: list[str],
        intent: dict[str, Any],
    ) -> dict[str, Any] | None:
        if not self.client:
            return None

        system = (
            "You are Build a Base's AI Beauty Agent. Synthesize cosmetic-only beauty recommendations from tool outputs. "
            "Never diagnose or treat medical skin conditions. Do not invent products outside allowed_candidates. "
            "If allowed_candidates is non-empty, every product name you mention must come from allowed_candidates. "
            "Ask follow-up questions only when the tool outputs show missing required inputs. "
            "Every response must include the exact disclaimer supplied by the app separately, so do not rewrite it. "
            "Return JSON only with summary, recommendations, follow_up_questions, and explanation."
        )
        allowed_candidates = _products_from_tool_results(tool_results)
        payload = {
            "goal": request.goal,
            "text_input": request.text_input,
            "profile": request.profile,
            "detected_intent": intent,
            "allowed_candidates": allowed_candidates,
            "tool_results": [result.model_dump() for result in tool_results],
            "fallback_recommendations": recommendations,
            "fallback_follow_up_questions": follow_ups,
        }
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": json.dumps(payload)},
                ],
                temperature=0.35,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(response.choices[0].message.content or "{}")
            if not isinstance(parsed.get("recommendations"), list):
                return None
            parsed["follow_up_questions"] = parsed.get("follow_up_questions") or []
            return parsed
        except Exception:
            return None

    def _append(self, results: list[ToolCallResult], tool: str, input_summary: str, output: dict[str, Any]) -> None:
        results.append(ToolCallResult(tool=tool, input_summary=input_summary, output=output))

    def _product_recommendation_text(self, result: dict[str, Any]) -> list[str]:
        products = result.get("product_recommendations", [])
        return [
            f"{product['name']} ({product['category']}, {product.get('typical_price', 'price varies')}): {product['why']}"
            for product in products
            if isinstance(product, dict) and product.get("name") and product.get("why")
        ]

    def _routine_text_from_results(self, results: list[ToolCallResult]) -> list[str]:
        for result in results:
            if result.tool == "routine_generator_tool":
                return self._routine_recommendation_text(result.output)
        return []

    def _routine_recommendation_text(self, result: dict[str, Any]) -> list[str]:
        makeup_bag = result.get("makeup_bag", {})
        if not isinstance(makeup_bag, dict):
            return []

        routine: list[str] = []
        for slot, label in ROUTINE_SLOT_LABELS.items():
            products = makeup_bag.get(slot, [])
            if not isinstance(products, list):
                continue
            limit = 2 if slot == "setting_sprays" else 1
            for product in products[:limit]:
                if isinstance(product, dict) and product.get("name"):
                    routine.append(
                        f"{label}: {product['name']} - {product.get('finish', 'finish varies')}, "
                        f"{product.get('coverage') or 'coverage varies'}, {product.get('typical_price', 'price varies')}. "
                        f"Why: {product.get('why', 'It fits your profile.')}"
                    )
        return routine

    def _has_brand_preference(self, request: AgentRequest) -> bool:
        profile = request.profile
        if profile.get("brand_preferences") or profile.get("preferred_brands") or profile.get("avoid_brands"):
            return True
        text = f"{request.goal} {request.text_input}".lower()
        return "brand" in text or any(brand in text for brand in KNOWN_BRANDS)

    def _explain(self, results: list[ToolCallResult], request: AgentRequest) -> str:
        inputs = []
        if request.image:
            inputs.append("uploaded image")
        if request.profile.get("quiz_answers"):
            inputs.append("quiz answers")
        if request.text_input:
            inputs.append("text input")
        if request.profile:
            inputs.append("profile")
        input_text = ", ".join(inputs) if inputs else "your request"
        actions = [result.tool.replace("_tool", "").replace("_", " ") for result in results]
        domains = []
        if "analyze skin tone" in actions or "match foundation" in actions:
            domains.append("tone family and base product guidance")
        if "infer skin type" in actions:
            domains.append("skin-type inference")
        if "routine generator" in actions:
            domains.append("routine planning")
        if "makeup problem solver" in actions:
            domains.append("makeup troubleshooting")
        if "look recreator" in actions:
            domains.append("look recreation")
        return f"Based on your {input_text}, I used {', '.join(actions)} to combine {', '.join(domains)}."


def _first_present(text: str, values: list[str]) -> str | None:
    return next((value for value in values if re.search(rf"\b{re.escape(value)}\b", text)), None)


def _coverage_from_text(text: str, fallback: str) -> str:
    if any(word in text for word in ["full coverage", "full glam", "cover everything", "high coverage"]):
        return "full"
    if any(word in text for word in ["light coverage", "sheer", "skin tint", "tinted moisturizer"]):
        return "light"
    if "medium" in text:
        return "medium"
    return fallback or "medium"


def _finish_from_text(text: str, fallback: str) -> str:
    words = []
    for word in ["matte", "dewy", "radiant", "glowy", "natural", "satin", "soft-focus"]:
        if word in text:
            words.append("glow" if word == "glowy" else word)
    return " ".join(words) or fallback or "natural"


def _price_tier_from_text(text: str, fallback: str) -> str:
    if any(word in text for word in ["drugstore", "affordable", "cheap", "budget"]):
        return "drugstore"
    if any(word in text for word in ["premium", "luxury", "high end", "high-end", "sephora", "full glam"]):
        return "premium"
    if any(word in text for word in ["mid range", "mid-range", "moderate"]):
        return "mid_range"
    return "mid_range" if fallback in {"moderate", "mid range", "mid-range"} else fallback or "mid_range"


def _product_type_from_text(text: str) -> str:
    for phrase, product_type in PRODUCT_TYPE_ALIASES.items():
        if phrase in text:
            return product_type
    return ""


def _categories_for_intent(product_type: str, problems: list[str], text: str) -> list[str]:
    if _is_full_face_request(text):
        categories = list(FULL_FACE_CATEGORIES)
    elif product_type:
        categories = [product_type]
    else:
        categories = []
    for problem in problems:
        categories.extend(PROBLEM_CATEGORIES.get(problem, []))
    if any(word in text for word in ["routine", "steps", "whole face", "base routine"]):
        categories.extend(["primer", "foundation", "concealer", "loose setting powder", "setting spray"])
    if not categories:
        categories = ["foundation", "concealer", "setting powder"]
    return list(dict.fromkeys(categories))


def _is_full_face_request(text: str) -> bool:
    return any(trigger in text for trigger in FULL_FACE_TRIGGERS)


def _summary_from_intent(intent: dict[str, Any]) -> str:
    category_text = ", ".join(intent["categories"])
    problem_text = f" for {', '.join(intent['problems'])}" if intent["problems"] else ""
    return (
        f"{intent['price_tier'].replace('_', ' ').title()} {intent['coverage']} coverage picks"
        f"{problem_text}: {category_text}."
    )


def _intent_explanation(intent: dict[str, Any], results: list[ToolCallResult]) -> str:
    tools = ", ".join(result.tool.replace("_tool", "").replace("_", " ") for result in results)
    return (
        f"I used {tools} with filters for {intent['price_tier']} price tier, "
        f"{intent['skin_type']} skin, {intent['coverage']} coverage, {intent['finish']} finish, "
        f"and categories: {', '.join(intent['categories'])}."
    )


def _products_from_tool_results(results: list[ToolCallResult]) -> list[dict[str, Any]]:
    products: list[dict[str, Any]] = []
    for result in results:
        output = result.output
        for product in output.get("product_recommendations", []):
            if isinstance(product, dict):
                products.append(product)
        makeup_bag = output.get("makeup_bag", {})
        if isinstance(makeup_bag, dict):
            for bag_products in makeup_bag.values():
                if isinstance(bag_products, list):
                    products.extend(product for product in bag_products if isinstance(product, dict))
    return _dedupe_products(products)


def _sanitize_tool_results_for_price_tier(results: list[ToolCallResult], requested_tier: str) -> list[ToolCallResult]:
    for result in results:
        output = result.output
        if "product_recommendations" in output and isinstance(output["product_recommendations"], list):
            output["product_recommendations"] = _enforce_requested_price_tier(
                [product for product in output["product_recommendations"] if isinstance(product, dict)],
                requested_tier,
            )
        makeup_bag = output.get("makeup_bag")
        if isinstance(makeup_bag, dict):
            filtered_bag: dict[str, list[dict[str, Any]]] = {}
            for slot, products in makeup_bag.items():
                if isinstance(products, list):
                    filtered = _enforce_requested_price_tier(
                        [product for product in products if isinstance(product, dict)],
                        requested_tier,
                    )
                    if filtered:
                        filtered_bag[slot] = filtered
            output["makeup_bag"] = filtered_bag
    return results


def _recommendations_from_filtered_tools(results: list[ToolCallResult]) -> list[str]:
    routine_result = next((result.output for result in results if result.tool == "routine_generator_tool"), None)
    if isinstance(routine_result, dict):
        text = _routine_recommendation_text_from_output(routine_result)
        if text:
            return text
    products = _products_from_tool_results(results)
    return [
        f"{product['name']} ({product.get('category', 'product')}, {product.get('typical_price', 'price varies')}): {product.get('why', 'It fits your request.')}"
        for product in products
        if product.get("name")
    ]


def _routine_recommendation_text_from_output(result: dict[str, Any]) -> list[str]:
    makeup_bag = result.get("makeup_bag", {})
    if not isinstance(makeup_bag, dict):
        return []

    routine: list[str] = []
    for slot, label in ROUTINE_SLOT_LABELS.items():
        products = makeup_bag.get(slot, [])
        if not isinstance(products, list):
            continue
        limit = 2 if slot == "setting_sprays" else 1
        for product in products[:limit]:
            if isinstance(product, dict) and product.get("name"):
                routine.append(
                    f"{label}: {product['name']} - {product.get('finish', 'finish varies')}, "
                    f"{product.get('coverage') or 'coverage varies'}, {product.get('typical_price', 'price varies')}. "
                    f"Why: {product.get('why', 'It fits your profile.')}"
                )
    return routine


def _filter_recommendation_text_for_price_tier(
    recommendations: list[str],
    results: list[ToolCallResult],
    requested_tier: str,
) -> list[str]:
    if requested_tier not in {"premium", "drugstore"}:
        return recommendations
    allowed_names = {str(product.get("name", "")).lower() for product in _products_from_tool_results(results)}
    filtered = [
        recommendation
        for recommendation in recommendations
        if not _mentions_blocked_price_tier(recommendation, requested_tier)
        and (not allowed_names or any(name and name in recommendation.lower() for name in allowed_names))
    ]
    return filtered or _recommendations_from_filtered_tools(results)


def _mentions_blocked_price_tier(text: str, requested_tier: str) -> bool:
    text = text.lower()
    if requested_tier == "premium":
        return any(word in text for word in ["drugstore", "affordable", "budget", "cheap"])
    if requested_tier == "drugstore":
        return any(word in text for word in ["premium", "luxury", "high-end", "high end"])
    return False


def _apply_feedback_adjustments(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    db = SessionLocal()
    try:
        for product in products:
            try:
                product_id = int(product.get("id", 0))
            except (TypeError, ValueError):
                continue
            counts = feedback_counts_for_product(db, product_id)
            text = f"{product.get('finish', '')} {product.get('coverage', '')} {product.get('category', '')} {product.get('undertone', '')}".lower()
            score = int(product.get("match_percentage") or 0)
            if counts.get("too dry") and any(word in text for word in ["matte", "powder"]):
                score -= min(8, counts["too dry"] * 2)
            if counts.get("too cakey") and any(word in text for word in ["full", "matte", "powder"]):
                score -= min(8, counts["too cakey"] * 2)
            if counts.get("too oily") and any(word in text for word in ["dewy", "radiant", "glow"]):
                score -= min(8, counts["too oily"] * 2)
            if counts.get("too orange") and "warm" in text:
                score -= min(8, counts["too orange"] * 2)
            if counts.get("wrong budget"):
                score -= min(6, counts["wrong budget"] * 2)
            if counts:
                product["match_percentage"] = str(max(35, score))
                product["possible_downside"] = f"{product.get('possible_downside', '')} Feedback-adjusted from prior responses.".strip()
        return products
    finally:
        db.close()


def _product_log_tuples_from_tools(results: list[ToolCallResult]) -> list[tuple[Any, Any, Any]]:
    return [
        (product.get("brand"), product.get("name"), product.get("price_tier") or product.get("budget"))
        for product in _products_from_tool_results(results)
    ]


def _dedupe_products(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen_ids = set()
    seen_names = set()
    unique = []
    for product in products:
        product_id = str(product.get("id", ""))
        name_key = (
            str(product.get("brand", "")).lower(),
            str(product.get("name", "")).lower(),
            str(product.get("shade_name", "")).lower(),
        )
        if product_id and product_id in seen_ids:
            continue
        if name_key in seen_names:
            continue
        if product_id:
            seen_ids.add(product_id)
        seen_names.add(name_key)
        unique.append(product)
    return unique


def _product_allowed_for_requested_tier(product_tier: str, requested_tier: str) -> bool:
    if requested_tier == "premium":
        return product_tier == "premium"
    if requested_tier == "drugstore":
        return product_tier == "drugstore"
    return True


def _enforce_requested_price_tier(products: list[dict[str, Any]], requested_tier: str) -> list[dict[str, Any]]:
    return [
        product
        for product in products
        if _product_allowed_for_requested_tier(str(product.get("price_tier") or product.get("budget") or ""), requested_tier)
    ]


def _raise_if_blocked_tier_present(products: list[dict[str, Any]], requested_tier: str, stage: str) -> None:
    if requested_tier not in {"premium", "drugstore"}:
        return
    blocked = [
        product
        for product in products
        if not _product_allowed_for_requested_tier(str(product.get("price_tier") or product.get("budget") or ""), requested_tier)
    ]
    if blocked:
        names = [(product.get("brand"), product.get("name"), product.get("price_tier") or product.get("budget")) for product in blocked]
        raise RuntimeError(f"{stage} contains products outside requested {requested_tier} tier: {names}")


def _product_debug_dict(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "brand": product.brand,
        "name": product.name,
        "product_type": product.product_type,
        "price_tier": product.price_tier,
        "coverage": product.coverage,
        "finish": product.finish,
    }


def _debug_products_from_dicts(products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return _dedupe_debug_products(
        {
            "id": product.get("id"),
            "brand": product.get("brand"),
            "name": product.get("name"),
            "product_type": product.get("category") or product.get("product_type"),
            "price_tier": product.get("price_tier") or product.get("budget"),
            "coverage": product.get("coverage"),
            "finish": product.get("finish"),
        }
        for product in products
    )


def _dedupe_debug_products(products: Any) -> list[dict[str, Any]]:
    seen = set()
    unique = []
    for product in products:
        key = (
            str(product.get("id", "")),
            str(product.get("brand", "")).lower(),
            str(product.get("name", "")).lower(),
            str(product.get("price_tier", "")).lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(product)
    return unique


def _query_agent_candidates_before_price_filter(db: Any, intent: dict[str, Any], category: str) -> list[Product]:
    query = db.query(Product)
    query = _apply_category_query(query, category)
    if intent["skin_type"]:
        query = query.filter(Product.skin_type_match.ilike(f"%{intent['skin_type']}%"))
    if _shade_specific_category(category):
        query = query.filter(or_(Product.undertone == "", Product.undertone.ilike(f"%{intent['undertone']}%")))
        query = query.filter(or_(Product.shade_depth == "", Product.shade_depth.ilike(f"%{intent['depth']}%")))
    if intent["coverage"] and _coverage_specific_category(category):
        query = query.filter(Product.coverage.ilike(f"%{intent['coverage']}%"))
    finish_words = _finish_words(intent["finish"])
    if finish_words:
        query = query.filter(or_(*[Product.finish.ilike(f"%{word}%") for word in finish_words]))
    rows = query.order_by(Product.product_type, Product.brand, Product.name).all()
    if rows:
        return rows
    return _apply_category_query(db.query(Product), category).order_by(Product.product_type, Product.brand, Product.name).all()


def _query_agent_candidates(db: Any, intent: dict[str, Any], category: str) -> tuple[list[Product], dict[str, Any]]:
    attempts = [
        ("exact", True, True, True, True, True),
        ("relaxed_finish", True, True, True, True, False),
        ("relaxed_formula", True, True, True, False, False),
        ("relaxed_skin", True, False, True, False, False),
        ("relaxed_profile", True, False, False, False, False),
    ]
    if intent["price_tier"] not in {"premium", "drugstore"}:
        attempts.append(("relaxed_price", False, False, False, False, False))
    sql_logs = []
    filters_log = {
        "category": category,
        "price_tier": intent["price_tier"],
        "skin_type": intent["skin_type"],
        "undertone": intent["undertone"],
        "depth": intent["depth"],
        "coverage": intent["coverage"],
        "finish": intent["finish"],
    }

    for confidence, use_price, use_skin, use_tone, use_formula, use_finish in attempts:
        query = db.query(Product)
        query = _apply_category_query(query, category)
        if use_price:
            query = query.filter(Product.price_tier == intent["price_tier"])
        if use_skin and intent["skin_type"]:
            query = query.filter(Product.skin_type_match.ilike(f"%{intent['skin_type']}%"))
        if use_tone and _shade_specific_category(category):
            query = query.filter(or_(Product.undertone == "", Product.undertone.ilike(f"%{intent['undertone']}%")))
            query = query.filter(or_(Product.shade_depth == "", Product.shade_depth.ilike(f"%{intent['depth']}%")))
        if use_formula and intent["coverage"] and _coverage_specific_category(category):
            query = query.filter(Product.coverage.ilike(f"%{intent['coverage']}%"))
        if use_finish:
            finish_words = _finish_words(intent["finish"])
            if finish_words:
                query = query.filter(or_(*[Product.finish.ilike(f"%{word}%") for word in finish_words]))

        sql_logs.append(f"{confidence}: {_compile_query(query)}")
        rows = query.order_by(Product.product_type, Product.brand, Product.name).all()
        rows = [row for row in rows if _product_allowed_for_requested_tier(row.price_tier, intent["price_tier"])]
        if rows:
            return rows, {"confidence": confidence, "filters": {**filters_log, "relaxation": confidence, "found": len(rows)}, "sql": sql_logs}

    return [], {"confidence": "none", "filters": {**filters_log, "relaxation": "none", "found": 0}, "sql": sql_logs}


def _apply_category_query(query: Any, category: str) -> Any:
    category = category.lower()
    if category == "setting powder":
        return query.filter(Product.product_type.in_(["loose setting powder", "pressed setting powder"]))
    if category == "powder":
        return query.filter(Product.product_type.ilike("%powder%"))
    if category == "contour":
        return query.filter(or_(Product.product_type.ilike("%contour%"), Product.product_type.ilike("%bronzer%")))
    return query.filter(Product.product_type.ilike(f"%{category}%"))


def _compile_query(query: Any) -> str:
    try:
        return str(query.statement.compile(compile_kwargs={"literal_binds": True}))
    except Exception:
        return str(query)


def _shade_specific_category(category: str) -> bool:
    return category in {"foundation", "skin tint", "concealer"}


def _coverage_specific_category(category: str) -> bool:
    return category in {"foundation", "skin tint", "concealer"}


def _product_to_agent_dict(product: Product, intent: dict[str, Any], confidence: str) -> dict[str, Any]:
    score = _agent_product_score(product, intent, confidence)
    downside = product.avoid_if or "No major downside based on this profile."
    if confidence != "exact":
        downside = f"Lower-confidence fit ({confidence}); {downside}"
    why = _agent_product_why(product, intent, confidence)
    return {
        "id": str(product.id),
        "name": product.name,
        "brand": product.brand,
        "category": product.product_type,
        "shade_name": product.shade_name,
        "budget": product.price_tier,
        "price_tier": product.price_tier,
        "finish": product.finish,
        "coverage": product.coverage,
        "why": why,
        "shade_note": "No exact color selection is needed for this product." if not _shade_specific_category(product.product_type) else f"Use the {intent['depth']} range and {intent['undertone']} tone family as a starting point, then check it in daylight.",
        "typical_price": f"${product.price:.2f}" if product.price else "Price varies",
        "image_url": product.image_url,
        "price_note": "Typical price; live prices and availability can change.",
        "shopping_link": product.shopping_link,
        "source": "sqlite_products",
        "good_for": product.good_for,
        "avoid_if": product.avoid_if,
        "possible_downside": downside,
        "matched_answers": _matched_agent_answers(product, intent, confidence),
        "match_percentage": str(score),
        "why_recommended": why,
        "formula_base": product.formula_base,
        "best_for": product.best_for,
        "avoid_pairing_with": product.avoid_pairing_with,
        "compatibility_notes": product.compatibility_notes,
    }


def _agent_product_why(product: Product, intent: dict[str, Any], confidence: str) -> str:
    reasons = []
    if product.price_tier == intent["price_tier"]:
        reasons.append(f"it stays in your {intent['price_tier'].replace('_', ' ')} preference")
    if _coverage_specific_category(product.product_type) and intent["coverage"] in product.coverage.lower():
        reasons.append(f"it gives {intent['coverage']} coverage")
    if intent["skin_type"] in product.skin_type_match.lower():
        reasons.append(f"it suits {intent['skin_type']} skin")
    finish_matches = [word for word in _finish_words(intent["finish"]) if word in product.finish.lower()]
    if finish_matches:
        reasons.append(f"it has a {'/'.join(finish_matches)} finish")
    if intent["problems"]:
        reasons.append(f"it supports your {', '.join(intent['problems'])} concern")
    base_note = product.good_for or product.notes
    if reasons:
        return f"Fits this prompt because {', '.join(reasons)}. Product note: {base_note}."
    if confidence != "exact":
        return f"Closest available fit after relaxing filters. Product note: {base_note}."
    return base_note


def _agent_product_score(product: Product, intent: dict[str, Any], confidence: str) -> int:
    score = {
        "exact": 78,
        "relaxed_finish": 70,
        "relaxed_formula": 64,
        "relaxed_skin": 60,
        "relaxed_profile": 56,
        "relaxed_price": 48,
        "none": 45,
    }.get(confidence, 55)
    combined = f"{product.name} {product.product_type} {product.finish} {product.coverage} {product.good_for} {product.notes}".lower()
    if intent["skin_type"] and intent["skin_type"] in product.skin_type_match.lower():
        score += 5
    if intent["undertone"] and intent["undertone"] in product.undertone.lower():
        score += 4
    if intent["depth"] and intent["depth"] in product.shade_depth.lower():
        score += 4
    if intent["coverage"] and intent["coverage"] in product.coverage.lower():
        score += 5
    for word in _finish_words(intent["finish"]):
        if word in product.finish.lower():
            score += 4
    if any(problem in intent["problems"] for problem in ["separation", "separating", "pilling"]) and any(word in combined for word in ["primer", "grip", "long wear", "set"]):
        score += 7
    if any(problem in intent["problems"] for problem in ["oiliness", "oily"]) and any(word in combined for word in ["matte", "oil", "shine", "powder"]):
        score += 7
    if any(problem in intent["problems"] for problem in ["dryness", "flaky", "flaking"]) and any(word in combined for word in ["dewy", "hydrated", "glow", "skin tint"]):
        score += 7
    if any(problem in intent["problems"] for problem in ["cakey", "cakiness", "patchy"]) and any(word in combined for word in ["lightweight", "natural", "smoothing", "spray", "primer"]):
        score += 7
    score += _message_tiebreak(intent["raw_text"], product.id)
    return min(score, 98)


def _message_tiebreak(message: str, product_id: int) -> int:
    digest = sha1(f"{message}:{product_id}".encode()).hexdigest()
    return int(digest[:2], 16) % 5


def _matched_agent_answers(product: Product, intent: dict[str, Any], confidence: str) -> str:
    matches = [f"confidence: {confidence}"]
    if intent["skin_type"] in product.skin_type_match.lower():
        matches.append(f"skin type: {intent['skin_type']}")
    if intent["undertone"] in product.undertone.lower():
        matches.append(f"tone family: {intent['undertone']}")
    if intent["depth"] in product.shade_depth.lower():
        matches.append(f"complexion range: {intent['depth']}")
    if intent["coverage"] and intent["coverage"] in product.coverage.lower():
        matches.append(f"coverage: {intent['coverage']}")
    finish_matches = [word for word in _finish_words(intent["finish"]) if word in product.finish.lower()]
    if finish_matches:
        matches.append(f"finish: {', '.join(finish_matches)}")
    return ", ".join(matches)


def _finish_words(finish: str) -> list[str]:
    words = []
    for word in ["matte", "radiant", "glow", "dewy", "natural", "satin", "soft-focus"]:
        if word in (finish or "").lower():
            words.append(word)
    return words


def _rank_agent_products(products: list[dict[str, Any]], intent: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(products, key=lambda product: int(product.get("match_percentage") or 0), reverse=True)


def _diverse_products(products: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    chosen: list[dict[str, Any]] = []
    seen_slots = set()
    for product in products:
        slot = _slot_for_category(product.get("category", "product"))
        if slot in seen_slots:
            continue
        chosen.append(product)
        seen_slots.add(slot)
        if len(chosen) >= limit:
            return chosen
    for product in products:
        if product in chosen:
            continue
        chosen.append(product)
        if len(chosen) >= limit:
            break
    return chosen


def _slot_for_category(category: str) -> str:
    category = category.lower()
    if "primer" in category:
        return "primer"
    if category in {"foundation", "skin tint"}:
        return "base"
    if "powder blush" in category:
        return "powder_blush"
    if "liquid blush" in category:
        return "liquid_blush"
    if "bronzer" in category:
        return "powder_contour_or_bronzer"
    if "contour" in category:
        return "cream_or_liquid_contour_bronzer"
    if "concealer" in category:
        return "concealer"
    if "pressed" in category:
        return "pressed_setting_powder"
    if "powder" in category:
        return "loose_setting_powder"
    if "spray" in category:
        return "setting_sprays"
    return category.replace(" ", "_")


def _routine_steps_for_intent(intent: dict[str, Any]) -> list[str]:
    steps = ["Prep skin lightly before makeup"]
    if any(problem in intent["problems"] for problem in ["dryness", "flaking", "flaky"]):
        steps.append("Use moisturizer or SPF that fully settles before makeup")
    if any(problem in intent["problems"] for problem in ["oiliness", "oily", "separation"]):
        steps.append("Use thin layers and set oily areas only")
    steps.append(f"Choose {intent['coverage']} coverage with a {intent['finish']} finish")
    return steps
