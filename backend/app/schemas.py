from typing import Any, Literal

from pydantic import BaseModel, Field


DISCLAIMER = (
    "Build a Base provides cosmetic and beauty recommendations only. It does not diagnose, "
    "treat, or advise on medical skin conditions. For painful, severe, spreading, infected, "
    "or persistent skin concerns, consult a licensed medical professional."
)


class AgentRequest(BaseModel):
    goal: str = Field(min_length=2)
    text_input: str = ""
    image: str | None = None
    profile: dict[str, Any] = Field(default_factory=dict)


class ToolCallResult(BaseModel):
    tool: str
    input_summary: str
    output: dict[str, Any]


class AgentResponse(BaseModel):
    summary: str
    tools_used: list[ToolCallResult]
    recommendations: list[str]
    follow_up_questions: list[str] = Field(default_factory=list)
    explanation: str
    disclaimer: str = DISCLAIMER
    request_text: str = ""
    debug_info: dict[str, Any] = Field(default_factory=dict)


class FoundationRequest(BaseModel):
    undertone: str
    depth: str


class QuizRequest(BaseModel):
    answers: dict[str, Any]


class RoutineRequest(BaseModel):
    skin_type: str
    undertone: str = "neutral"
    depth: str = "medium"
    preference: str = "natural"
    budget: str = "moderate"


class RecommendRequest(BaseModel):
    skin_type: str = "balanced"
    undertone: str = "neutral"
    depth: str = "medium"
    preference: str = "natural"
    budget: str = "moderate"
    coverage: str = ""
    goal: str = "Build a makeup routine"


class ProblemRequest(BaseModel):
    problem_text: str
    product_list: list[str] = Field(default_factory=list)


class LookRequest(BaseModel):
    inspiration_image: str | None = None
    user_profile: dict[str, Any] = Field(default_factory=dict)


class SavedResultCreate(BaseModel):
    title: str
    category: Literal["agent", "foundation", "quiz", "routine", "problem", "look"]
    payload: dict[str, Any]


class SavedResultRead(SavedResultCreate):
    id: int
    created_at: str


class ProductRead(BaseModel):
    id: int
    name: str
    brand: str
    product_type: str
    shade_name: str
    shade_depth: str
    undertone: str
    depth: str
    skin_type_match: str
    coverage: str
    finish: str
    price_tier: str
    price: float
    good_for: str
    avoid_if: str
    notes: str
    image_url: str
    shopping_link: str
    formula_base: str = ""
    best_for: str = ""
    avoid_pairing_with: str = ""
    compatibility_notes: str = ""


class RecommendedProduct(BaseModel):
    id: int
    name: str
    brand: str
    category: str
    shade_name: str = ""
    budget: str
    price_tier: str = ""
    finish: str
    coverage: str
    why: str
    shade_note: str
    typical_price: str
    image_url: str
    price_note: str
    shopping_link: str = ""
    source: str = "sqlite_products"
    good_for: str = ""
    avoid_if: str = ""
    possible_downside: str = ""
    matched_answers: str = ""
    match_percentage: str = ""
    why_recommended: str = ""
    formula_base: str = ""
    best_for: str = ""
    avoid_pairing_with: str = ""
    compatibility_notes: str = ""


class RecommendResponse(BaseModel):
    summary: str
    makeup_bag: dict[str, list[RecommendedProduct]]
    product_recommendations: list[RecommendedProduct]
    explanation: str
    disclaimer: str = DISCLAIMER
    routine_score: int = 0
    compatibility_warnings: list[str] = Field(default_factory=list)
    positive_compatibility_notes: list[str] = Field(default_factory=list)


class CompareProductsRequest(BaseModel):
    skin_type: str = "balanced"
    undertone: str = "neutral"
    finish_look: str = "natural"
    product_a_id: int
    product_b_id: int


class CompareProductsResponse(BaseModel):
    product_a: ProductRead
    product_b: ProductRead
    product_a_score: int
    product_b_score: int
    winner: str
    explanation: str
    comparison_points: list[str]


class FeedbackRequest(BaseModel):
    product_id: int
    feedback_type: str
    context: str = ""


class FeedbackResponse(BaseModel):
    id: int
    product_id: int
    feedback_type: str
    context: str
    created_at: str
