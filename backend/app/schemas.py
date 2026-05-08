from typing import Any, Literal

from pydantic import BaseModel, Field


DISCLAIMER = (
    "ShadeSync provides cosmetic and beauty recommendations only. It does not diagnose, "
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
