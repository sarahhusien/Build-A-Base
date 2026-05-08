import json
import re
from typing import Any

from openai import OpenAI

from .config import get_settings
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
                    "For beauty support, I can suggest gentle-looking makeup finishes, non-medical skin prep, and shade matching.",
                    "For symptoms such as pain, spreading rash, infection, bleeding, or persistent irritation, please contact a licensed medical professional.",
                ],
                follow_up_questions=[],
                explanation="No beauty tools were used because the request appears to ask for medical skin guidance.",
                disclaimer=DISCLAIMER,
            )

        plan = self._llm_plan(request) or self._fallback_plan(request)
        return self._execute_plan(request, plan)

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
        if request.image or any(word in text for word in ["tone", "undertone", "shade", "foundation", "selfie"]):
            tools.extend(["analyze_skin_tone_tool", "match_foundation_tool"])
        if request.profile.get("quiz_answers") or "skin type" in text or "quiz" in text:
            tools.append("infer_skin_type_tool")
        if any(word in text for word in ["routine", "skincare", "regimen", "products"]):
            tools.append("routine_generator_tool")
        if any(word in text for word in ["cakey", "patchy", "pilling", "problem", "separating", "oxidize"]):
            tools.append("makeup_problem_solver_tool")
        if self._has_any_word(text, ["recreate", "look", "inspiration", "glam"]):
            tools.append("look_recreator_tool")
        return tools or ["infer_skin_type_tool", "routine_generator_tool"]

    def _has_any_word(self, text: str, words: list[str]) -> bool:
        return any(re.search(rf"\b{re.escape(word)}\b", text) for word in words)

    def _execute_plan(self, request: AgentRequest, plan: list[str]) -> AgentResponse:
        context: dict[str, Any] = {
            "undertone": request.profile.get("undertone", "neutral"),
            "depth": request.profile.get("depth", "medium"),
            "skin_type": request.profile.get("skin_type", "balanced"),
        }
        tool_results: list[ToolCallResult] = []
        recommendations: list[str] = []
        follow_ups: list[str] = []

        for tool_name in dict.fromkeys(plan):
            if tool_name == "analyze_skin_tone_tool":
                result = analyze_skin_tone_tool(request.image)
                context.update({"undertone": result["undertone"], "depth": result["depth"]})
                if result["status"] == "needs_input":
                    follow_ups.append("Upload a clear, natural-light selfie if you want a more specific undertone and depth estimate.")
                self._append(tool_results, tool_name, "image input", result)
            elif tool_name == "match_foundation_tool":
                result = match_foundation_tool(context["undertone"], context["depth"])
                recommendations.extend(result["matches"])
                self._append(tool_results, tool_name, f"{context['undertone']} undertone, {context['depth']} depth", result)
            elif tool_name == "infer_skin_type_tool":
                answers = request.profile.get("quiz_answers", {})
                if not answers:
                    follow_ups.append("Answer the skin type quiz questions if you want a more confident routine.")
                result = infer_skin_type_tool(answers)
                context["skin_type"] = result["skin_type"]
                self._append(tool_results, tool_name, "quiz answers", result)
            elif tool_name == "routine_generator_tool":
                result = routine_generator_tool(
                    context["skin_type"],
                    context["undertone"],
                    context["depth"],
                    request.profile.get("preference", "natural"),
                    request.profile.get("budget", "moderate"),
                )
                recommendations.extend(result["morning"][:3])
                self._append(tool_results, tool_name, "skin type, tone profile, preference, budget", result)
            elif tool_name == "makeup_problem_solver_tool":
                result = makeup_problem_solver_tool(request.text_input, request.profile.get("product_list", []))
                recommendations.extend(result["fixes"][:3])
                self._append(tool_results, tool_name, "problem text and product list", result)
            elif tool_name == "look_recreator_tool":
                result = look_recreator_tool(request.image, {**request.profile, **context})
                recommendations.extend(result["steps"][:3])
                self._append(tool_results, tool_name, "inspiration image and user profile", result)

        used_names = [result.tool.replace("_tool", "").replace("_", " ") for result in tool_results]
        summary = "I built a cosmetic recommendation using " + ", ".join(used_names) + "."
        explanation = self._explain(tool_results, request)
        ai_response = self._llm_synthesize(request, tool_results, recommendations, follow_ups)
        if ai_response:
            summary = ai_response.get("summary", summary)
            explanation = ai_response.get("explanation", explanation)
            recommendations = ai_response.get("recommendations", recommendations)
            follow_ups = ai_response.get("follow_up_questions", follow_ups)

        return AgentResponse(
            summary=summary,
            tools_used=tool_results,
            recommendations=list(dict.fromkeys(recommendations))[:8],
            follow_up_questions=list(dict.fromkeys(follow_ups)),
            explanation=explanation,
            disclaimer=DISCLAIMER,
        )

    def _llm_synthesize(
        self,
        request: AgentRequest,
        tool_results: list[ToolCallResult],
        recommendations: list[str],
        follow_ups: list[str],
    ) -> dict[str, Any] | None:
        if not self.client:
            return None

        system = (
            "You are ShadeSync's AI Beauty Agent. Synthesize cosmetic-only beauty recommendations from tool outputs. "
            "Never diagnose or treat medical skin conditions. Do not invent products the tools did not imply. "
            "Ask follow-up questions only when the tool outputs show missing required inputs. "
            "Every response must include the exact disclaimer supplied by the app separately, so do not rewrite it. "
            "Return JSON only with summary, recommendations, follow_up_questions, and explanation."
        )
        payload = {
            "goal": request.goal,
            "text_input": request.text_input,
            "profile": request.profile,
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
            domains.append("tone and shade matching")
        if "infer skin type" in actions:
            domains.append("skin-type inference")
        if "routine generator" in actions:
            domains.append("routine planning")
        if "makeup problem solver" in actions:
            domains.append("makeup troubleshooting")
        if "look recreator" in actions:
            domains.append("look recreation")
        return f"Based on your {input_text}, I used {', '.join(actions)} to combine {', '.join(domains)}."
