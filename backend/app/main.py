import json

import httpx
from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .agent import BeautyAgent
from .compatibility import compatibility_profile, feedback_counts_for_product, score_product_for_profile
from .database import Feedback, Product, SavedResult, get_db, init_db
from .recommender import recommend_from_database
from .schemas import (
    AgentRequest,
    AgentResponse,
    CompareProductsRequest,
    CompareProductsResponse,
    FeedbackRequest,
    FeedbackResponse,
    FoundationRequest,
    LookRequest,
    ProblemRequest,
    ProductRead,
    QuizRequest,
    RecommendRequest,
    RecommendResponse,
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


app = FastAPI(title="Build a Base API")

IMAGE_FALLBACK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480" viewBox="0 0 640 480" role="img" aria-label="Product image unavailable">
  <rect width="640" height="480" fill="#f8ebe5"/>
  <rect x="220" y="118" width="200" height="266" rx="24" fill="#fffaf6" stroke="#d8a9a2" stroke-width="8"/>
  <rect x="252" y="84" width="136" height="58" rx="16" fill="#3b241d"/>
  <rect x="258" y="188" width="124" height="88" rx="16" fill="#f4dada"/>
  <path d="M282 312h76" stroke="#a75f65" stroke-width="12" stroke-linecap="round"/>
  <path d="M294 340h52" stroke="#a75f65" stroke-width="10" stroke-linecap="round"/>
</svg>"""

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


@app.get("/products", response_model=list[ProductRead])
@app.get("/api/products", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)) -> list[ProductRead]:
    products = db.query(Product).order_by(Product.product_type, Product.brand, Product.name).all()
    return [_read_product(product) for product in products]


@app.get("/products/{product_id}", response_model=ProductRead)
@app.get("/api/products/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductRead:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return _read_product(product)


@app.get("/api/product-image/{product_id}")
def product_image(product_id: int, db: Session = Depends(get_db)) -> Response:
    product = db.get(Product, product_id)
    if not product or not product.image_url:
        return _fallback_image()

    try:
        remote = httpx.get(
            product.image_url,
            timeout=8,
            follow_redirects=True,
            headers={
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "User-Agent": "Mozilla/5.0",
            },
        )
        content_type = remote.headers.get("content-type", "")
        if remote.status_code >= 400 or "image" not in content_type:
            return _fallback_image()
    except Exception:
        return _fallback_image()

    return Response(
        content=remote.content,
        media_type=content_type.split(";")[0],
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.post("/recommend", response_model=RecommendResponse)
@app.post("/api/recommend", response_model=RecommendResponse)
def recommend(request: RecommendRequest, db: Session = Depends(get_db)) -> RecommendResponse:
    return recommend_from_database(request, db)


@app.post("/api/agent", response_model=AgentResponse)
def agent(request: AgentRequest) -> AgentResponse:
    return BeautyAgent().run(request)


@app.post("/api/compare-products", response_model=CompareProductsResponse)
def compare_products(request: CompareProductsRequest, db: Session = Depends(get_db)) -> CompareProductsResponse:
    product_a = db.get(Product, request.product_a_id)
    product_b = db.get(Product, request.product_b_id)
    if not product_a or not product_b:
        raise HTTPException(status_code=404, detail="One or both products were not found")

    a_score, a_notes, a_downsides = score_product_for_profile(
        product_a,
        request.skin_type,
        request.undertone,
        request.finish_look,
        feedback_counts_for_product(db, product_a.id),
    )
    b_score, b_notes, b_downsides = score_product_for_profile(
        product_b,
        request.skin_type,
        request.undertone,
        request.finish_look,
        feedback_counts_for_product(db, product_b.id),
    )
    winner = "tie"
    if a_score > b_score:
        winner = f"{product_a.brand} {product_a.name}"
    elif b_score > a_score:
        winner = f"{product_b.brand} {product_b.name}"

    return CompareProductsResponse(
        product_a=_read_product(product_a),
        product_b=_read_product(product_b),
        product_a_score=a_score,
        product_b_score=b_score,
        winner=winner,
        explanation=f"{winner} is the better fit for {request.skin_type} skin and a {request.finish_look} look." if winner != "tie" else "Both products are similarly fitted to this profile.",
        comparison_points=[
            f"{product_a.name}: {', '.join(a_notes) or 'general formula fit'}; downsides: {', '.join(a_downsides) or 'none flagged'}",
            f"{product_b.name}: {', '.join(b_notes) or 'general formula fit'}; downsides: {', '.join(b_downsides) or 'none flagged'}",
            f"Desired finish look: {request.finish_look}",
            f"Finish: {product_a.finish} vs {product_b.finish}",
            f"Coverage: {product_a.coverage or 'varies'} vs {product_b.coverage or 'varies'}",
            f"Price tier: {product_a.price_tier} vs {product_b.price_tier}",
        ],
    )


@app.post("/api/feedback", response_model=FeedbackResponse)
def create_feedback(request: FeedbackRequest, db: Session = Depends(get_db)) -> FeedbackResponse:
    product = db.get(Product, request.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    feedback = Feedback(
        product_id=request.product_id,
        feedback_type=request.feedback_type,
        context=request.context,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return FeedbackResponse(
        id=feedback.id,
        product_id=feedback.product_id,
        feedback_type=feedback.feedback_type,
        context=feedback.context,
        created_at=feedback.created_at.isoformat(),
    )


@app.post("/api/foundation")
def foundation(request: FoundationRequest) -> dict:
    return match_foundation_tool(request.undertone, request.depth)


@app.post("/api/skin-type")
def skin_type(request: QuizRequest) -> dict:
    return infer_skin_type_tool(request.answers)


@app.post("/api/routine")
def routine(request: RoutineRequest, db: Session = Depends(get_db)) -> RecommendResponse:
    return recommend_from_database(
        RecommendRequest(
            skin_type=request.skin_type,
            undertone=request.undertone,
            depth=request.depth,
            preference=request.preference,
            budget=request.budget,
            goal="Generate a makeup routine",
        ),
        db,
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


def _fallback_image() -> Response:
    return Response(
        content=IMAGE_FALLBACK_SVG,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )


def _read_product(product: Product) -> ProductRead:
    return ProductRead(
        id=product.id,
        name=product.name,
        brand=product.brand,
        product_type=product.product_type,
        shade_name=product.shade_name,
        shade_depth=product.shade_depth,
        undertone=product.undertone,
        depth=product.depth,
        skin_type_match=product.skin_type_match,
        coverage=product.coverage,
        finish=product.finish,
        price_tier=product.price_tier,
        price=product.price,
        good_for=product.good_for,
        avoid_if=product.avoid_if,
        notes=product.notes,
        image_url=product.image_url,
        shopping_link=product.shopping_link,
        formula_base=product.formula_base,
        best_for=product.best_for,
        avoid_pairing_with=product.avoid_pairing_with,
        compatibility_notes=product.compatibility_notes,
    )
