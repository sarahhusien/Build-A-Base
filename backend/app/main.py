import json

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .agent import BeautyAgent
from .database import SavedResult, get_db, init_db
from .schemas import (
    AgentRequest,
    AgentResponse,
    FoundationRequest,
    LookRequest,
    ProblemRequest,
    QuizRequest,
    RoutineRequest,
    SavedResultCreate,
    SavedResultRead,
)
from .tools import (
    infer_skin_type_tool,
    look_recreator_tool,
    makeup_problem_solver_tool,
    match_foundation_tool,
    routine_generator_tool,
)


app = FastAPI(title="ShadeSync API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/agent", response_model=AgentResponse)
def agent(request: AgentRequest) -> AgentResponse:
    return BeautyAgent().run(request)


@app.post("/api/foundation")
def foundation(request: FoundationRequest) -> dict:
    return match_foundation_tool(request.undertone, request.depth)


@app.post("/api/skin-type")
def skin_type(request: QuizRequest) -> dict:
    return infer_skin_type_tool(request.answers)


@app.post("/api/routine")
def routine(request: RoutineRequest) -> dict:
    return routine_generator_tool(
        request.skin_type,
        request.undertone,
        request.depth,
        request.preference,
        request.budget,
    )


@app.post("/api/problem-solver")
def problem_solver(request: ProblemRequest) -> dict:
    return makeup_problem_solver_tool(request.problem_text, request.product_list)


@app.post("/api/look-recreator")
def look_recreator(request: LookRequest) -> dict:
    return look_recreator_tool(request.inspiration_image, request.user_profile)


@app.post("/api/saved-results", response_model=SavedResultRead)
def create_saved_result(request: SavedResultCreate, db: Session = Depends(get_db)) -> SavedResultRead:
    saved = SavedResult(
        title=request.title,
        category=request.category,
        payload_json=json.dumps(request.payload),
    )
    db.add(saved)
    db.commit()
    db.refresh(saved)
    return _read_saved(saved)


@app.get("/api/saved-results", response_model=list[SavedResultRead])
def list_saved_results(db: Session = Depends(get_db)) -> list[SavedResultRead]:
    rows = db.query(SavedResult).order_by(SavedResult.created_at.desc()).all()
    return [_read_saved(row) for row in rows]


def _read_saved(row: SavedResult) -> SavedResultRead:
    return SavedResultRead(
        id=row.id,
        title=row.title,
        category=row.category,
        payload=json.loads(row.payload_json),
        created_at=row.created_at.isoformat(),
    )
