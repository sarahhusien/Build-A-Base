import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { ArrowLeft, ArrowRight, Bookmark, Check, Info, Send, Sparkles } from "lucide-react";
import "./styles.css";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? "http://localhost:8000" : "/_/backend");

type AnyRecord = Record<string, unknown>;

type Product = {
  id?: number | string;
  name: string;
  brand?: string;
  category: string;
  shade_name?: string;
  budget: string;
  finish: string;
  coverage?: string;
  why: string;
  shade_note?: string;
  typical_price?: string;
  image_url?: string;
  shopping_link?: string;
  source?: string;
  price_tier?: string;
  good_for?: string;
  avoid_if?: string;
  possible_downside?: string;
  matched_answers?: string;
  match_percentage?: string;
  why_recommended?: string;
  formula_base?: string;
  best_for?: string;
  avoid_pairing_with?: string;
  compatibility_notes?: string;
};

type DbProduct = {
  id: number;
  name: string;
  brand: string;
  product_type: string;
  shade_name: string;
  shade_depth?: string;
  undertone: string;
  depth: string;
  skin_type_match: string;
  coverage: string;
  finish: string;
  price_tier: string;
  price: number;
  good_for: string;
  avoid_if: string;
  notes: string;
  formula_base?: string;
  best_for?: string;
  avoid_pairing_with?: string;
  compatibility_notes?: string;
};

type RecommendResponse = {
  summary: string;
  makeup_bag: Record<string, Product[]>;
  product_recommendations: Product[];
  explanation: string;
  disclaimer: string;
  routine_score?: number;
  compatibility_warnings?: string[];
  positive_compatibility_notes?: string[];
};

type AgentResponse = {
  summary: string;
  recommendations: string[];
  explanation: string;
  follow_up_questions: string[];
  disclaimer: string;
  request_text?: string;
  tools_used?: { tool?: string; output: AnyRecord }[];
};

type CompareResponse = {
  product_a: DbProduct;
  product_b: DbProduct;
  product_a_score: number;
  product_b_score: number;
  winner: string;
  explanation: string;
  comparison_points: string[];
};

type QuizAnswer = {
  skin_type: string;
  undertone: string;
  depth: string;
  preference: string;
  coverage: string;
  budget: string;
};

const INITIAL_ANSWERS: QuizAnswer = {
  skin_type: "combination",
  undertone: "neutral",
  depth: "medium",
  preference: "natural matte",
  coverage: "medium",
  budget: "drugstore",
};

const PRODUCT_SECTION_LABELS: Record<string, string> = {
  primer: "Primer",
  base: "Foundation or Skin Tint",
  concealer: "Concealer",
  cream_or_liquid_contour_bronzer: "Cream Contour or Bronzer",
  liquid_blush: "Liquid Blush",
  powder_blush: "Powder Blush",
  powder_contour_or_bronzer: "Powder Bronzer",
  pressed_setting_powder: "Pressed Setting Powder",
  loose_setting_powder: "Loose Setting Powder",
  setting_sprays: "Setting Sprays",
};

const QUIZ_STEPS: {
  key: keyof QuizAnswer;
  eyebrow: string;
  title: string;
  helper: string;
  tip: string;
  options: { value: string; label: string; detail: string }[];
}[] = [
  {
    key: "skin_type",
    eyebrow: "Skin profile",
    title: "How does your skin usually behave by midday?",
    helper: "This helps us avoid formulas that slip, cling, or flatten your finish.",
    tip: "To check your skin type, wash your face and allow it to dry without applying products. After 30 to 60 minutes, notice whether your skin feels tight, oily, comfortable, or a bit of both.",
    options: [
      { value: "dry", label: "Dry", detail: "Tight, flaky, or needs richer prep" },
      { value: "balanced", label: "Balanced", detail: "Comfortable with minimal shine" },
      { value: "combination", label: "Combination", detail: "Shiny T-zone, normal or dry cheeks" },
      { value: "oily", label: "Oily", detail: "Shine comes through quickly" },
    ],
  },
  {
    key: "undertone",
    eyebrow: "Tone family",
    title: "Which tone family feels closest?",
    helper: "Choose the tone family that usually looks most balanced with your neck and chest.",
    tip: "To check tone family, look at your wrist veins in natural light. Green-looking veins can suggest warm or olive tones, blue or purple veins can suggest cool tones, and a mix of blue and green can suggest neutral tones.",
    options: [
      { value: "cool", label: "Cool", detail: "Rosy, pink, or blue-leaning" },
      { value: "neutral", label: "Neutral", detail: "Neither very pink nor golden" },
      { value: "warm", label: "Warm", detail: "Golden, peach, or yellow-leaning" },
      { value: "olive", label: "Olive", detail: "Green-gold or muted neutral" },
    ],
  },
  {
    key: "preference",
    eyebrow: "Finish",
    title: "What finish are you shopping for?",
    helper: "We’ll use this to choose between tint, natural foundation, matte base, and glam products.",
    tip: "To choose a finish, think about the look you want after a few hours of wear: matte controls shine, radiant adds glow, skin tint looks sheer, and full glam looks more perfected.",
    options: [
      { value: "natural matte", label: "Natural Matte", detail: "Soft-focus, not flat" },
      { value: "skin tint sheer dewy", label: "Sheer Dewy", detail: "Fresh skin tint energy" },
      { value: "soft radiant", label: "Soft Radiant", detail: "Glow without heavy shimmer" },
      { value: "full glam matte", label: "Full Glam", detail: "Long-wear and more perfected" },
    ],
  },
  {
    key: "coverage",
    eyebrow: "Coverage",
    title: "How much coverage do you want from concealer/base?",
    helper: "This changes whether your routine leans medium, tint-like, or full coverage.",
    tip: "To check coverage preference, decide whether you want freckles and natural texture to show through. Medium coverage softens unevenness, while full coverage hides more discoloration and lasts better for glam looks.",
    options: [
      { value: "medium", label: "Medium", detail: "Everyday coverage that still looks like skin" },
      { value: "full", label: "Full", detail: "More correction and longer-wear glam" },
    ],
  },
  {
    key: "budget",
    eyebrow: "Budget",
    title: "Where should we keep the product picks?",
    helper: "The database comparison prioritizes products in your budget tier.",
    tip: "Choose drugstore for lower-cost products first, moderate for a mix, or premium if you are open to higher-end formulas when they fit better.",
    options: [
      { value: "drugstore", label: "Drugstore", detail: "Affordable picks first" },
      { value: "moderate", label: "Moderate", detail: "Mix of accessible and elevated" },
      { value: "premium", label: "Premium", detail: "Higher-end formulas included" },
    ],
  },
];

function App() {
  const [view, setView] = useState<"home" | "quiz" | "results" | "advisor" | "compare" | "saved">("home");
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<QuizAnswer>(INITIAL_ANSWERS);
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [products, setProducts] = useState<DbProduct[]>([]);
  const [saved, setSaved] = useState<AnyRecord[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchProducts().catch(() => undefined);
    fetchSaved().catch(() => undefined);
  }, []);

  async function api(path: string, body?: AnyRecord) {
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}${path}`, {
        method: body ? "POST" : "GET",
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : undefined,
      });
      if (!response.ok) throw new Error(await response.text());
      return response.json();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
      throw caught;
    } finally {
      setLoading(false);
    }
  }

  async function fetchProducts() {
    setProducts(await api("/api/products"));
  }

  async function fetchSaved() {
    setSaved(await api("/api/saved-results"));
  }

  async function runRecommendation(nextAnswers = answers) {
    const response = await api("/api/recommend", {
      ...nextAnswers,
      preference: `${nextAnswers.preference} ${nextAnswers.coverage}`.trim(),
      goal: "Build a base routine with products that fit my skin and finish goals",
    });
    setResult(response);
    setView("results");
  }

  async function saveResult() {
    if (!result) return;
    await api("/api/saved-results", {
      title: "Build a Base routine",
      category: "routine",
      payload: result as unknown as AnyRecord,
    });
    await fetchSaved();
  }

  async function submitFeedback(productId: number | string | undefined, feedbackType: string, context: string) {
    if (!productId) return;
    await api("/api/feedback", {
      product_id: Number(productId),
      feedback_type: feedbackType,
      context,
    });
  }

  return (
    <main className="site-shell">
      <header className="topbar">
        <button className="wordmark" onClick={() => setView("home")}>
          <span>Build a Base</span>
        </button>
        <nav className="topnav">
          <button onClick={() => setView("quiz")}>Base Quiz</button>
          <button onClick={() => setView("advisor")}>Beauty Advisor</button>
          <button onClick={() => setView("compare")}>Compare Products</button>
          <button onClick={() => setView("saved")}>Saved</button>
        </nav>
      </header>

      {view === "home" && (
        <>
          <Hero onStart={() => setView("quiz")} />
          <HowItWorks />
          <RoutineHighlights />
        </>
      )}

      {view === "quiz" && (
        <QuizFlow
          answers={answers}
          step={step}
          loading={loading}
          setStep={setStep}
          setAnswers={setAnswers}
          onSubmit={runRecommendation}
        />
      )}

      {view === "results" && result && (
        <ResultsPage
          result={result}
          skinType={answers.skin_type}
          loading={loading}
          onRetake={() => {
            setStep(0);
            setView("quiz");
          }}
          onSave={saveResult}
          onFeedback={submitFeedback}
        />
      )}

      {view === "advisor" && <BeautyAdvisor api={api} answers={answers} onSaved={fetchSaved} onViewSaved={() => setView("saved")} />}
      {view === "compare" && <CompareProducts api={api} products={products} answers={answers} />}
      {view === "saved" && <SavedResults saved={saved} />}

      {loading && <p className="toast">Building your base routine...</p>}
      {error && <p className="toast error-toast">Backend error: {error}</p>}
    </main>
  );
}

function Hero({ onStart }: { onStart: () => void }) {
  return (
    <section className="hero">
      <div className="hero-copy">
        <p className="eyebrow">Database-powered base routine builder</p>
        <h1>Build a base that fits your skin</h1>
        <p>
          Build a Base compares your skin type, finish goals, coverage, budget,
          and formula needs with real products, then builds a routine in the right order.
        </p>
        <div className="hero-actions">
          <button className="primary" onClick={onStart}>
            Start Base Builder <ArrowRight size={18} />
          </button>
          <span>Cosmetic recommendations only</span>
        </div>
      </div>
      <div className="hero-visual" aria-label="Base routine product preview">
        <div className="routine-preview">
          {[
            ["1", "Prep", "primer"],
            ["2", "Even", "base"],
            ["3", "Set", "powder"],
            ["4", "Lock", "spray"],
          ].map(([step, title, detail]) => (
            <span key={step}>
              <strong>{step}</strong>
              <b>{title}</b>
              <small>{detail}</small>
            </span>
          ))}
        </div>
        <div className="beauty-card floating">
          <span>Routine fit</span>
          <strong>Full base routine</strong>
          <small>Primer · base · powder · spray</small>
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    ["Tell us your skin and finish goals", "Choose skin type, tone family, coverage, finish, and budget."],
    ["We compare product formulas", "Build a Base scores products stored in SQLite, with AI ranking when configured."],
    ["You get a base routine", "Review your products in order, compatibility notes, and why each product fits."],
  ];
  return (
    <section className="how">
      <div className="section-heading">
        <p className="eyebrow">How it works</p>
        <h2>A cleaner path to your base routine</h2>
      </div>
      <div className="how-grid">
        {steps.map(([title, copy], index) => (
          <article key={title}>
            <span>{index + 1}</span>
            <h3>{title}</h3>
            <p>{copy}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function QuizFlow({
  answers,
  step,
  loading,
  setStep,
  setAnswers,
  onSubmit,
}: {
  answers: QuizAnswer;
  step: number;
  loading: boolean;
  setStep: (step: number) => void;
  setAnswers: (answers: QuizAnswer) => void;
  onSubmit: (answers: QuizAnswer) => Promise<void>;
}) {
  const current = QUIZ_STEPS[step];
  const progress = ((step + 1) / QUIZ_STEPS.length) * 100;
  const selected = answers[current.key];
  const [showTip, setShowTip] = useState(false);

  async function next() {
    if (step === QUIZ_STEPS.length - 1) {
      await onSubmit(answers);
      return;
    }
    setStep(step + 1);
  }

  return (
    <section className="quiz-page">
      <div className="quiz-card">
        <div className="progress-row">
          <span>Step {step + 1} of {QUIZ_STEPS.length}</span>
          <div className="progress-track"><div style={{ width: `${progress}%` }} /></div>
        </div>
        <p className="eyebrow">{current.eyebrow}</p>
        <div className="question-title">
          <h2>{current.title}</h2>
          <button
            className="info-button"
            onClick={() => setShowTip(!showTip)}
            aria-label={`How to check ${current.eyebrow.toLowerCase()}`}
            title={`How to check ${current.eyebrow.toLowerCase()}`}
          >
            <Info size={18} />
          </button>
        </div>
        {showTip && <p className="tip-box">{current.tip}</p>}
        <p className="quiz-helper">{current.helper}</p>
        <div className="answer-grid">
          {current.options.map((option) => (
            <button
              key={option.value}
              className={selected === option.value ? "answer selected" : "answer"}
              onClick={() => setAnswers({ ...answers, [current.key]: option.value })}
            >
              <strong>{option.label}</strong>
              <span>{option.detail}</span>
              {selected === option.value && <Check size={18} />}
            </button>
          ))}
        </div>
        <div className="quiz-actions">
          <button className="secondary" onClick={() => setStep(Math.max(step - 1, 0))} disabled={step === 0}>
            <ArrowLeft size={17} /> Back
          </button>
          <button className="primary" onClick={next} disabled={loading}>
            {step === QUIZ_STEPS.length - 1 ? "See My Routine" : "Next"} <ArrowRight size={17} />
          </button>
        </div>
      </div>
    </section>
  );
}

function ResultsPage({
  result,
  skinType,
  loading,
  onRetake,
  onSave,
  onFeedback,
}: {
  result: RecommendResponse;
  skinType: string;
  loading: boolean;
  onRetake: () => void;
  onSave: () => void;
  onFeedback: (productId: number | string | undefined, feedbackType: string, context: string) => Promise<void>;
}) {
  const allSlides = collectProductSlides(result);
  const skinTip = routineSkinTip(skinType, result);
  return (
    <section className="results-page">
      <div className="results-hero">
        <div>
          <p className="eyebrow">Your base routine</p>
          <h2>Your routine</h2>
          <p>{result.summary}</p>
          {result.routine_score ? <strong className="routine-score">{result.routine_score}% routine score</strong> : null}
        </div>
        <div className="results-actions">
          <button className="secondary" onClick={onRetake}>Retake Quiz</button>
          <button className="primary" onClick={onSave} disabled={loading}><Bookmark size={17} /> Save Results</button>
        </div>
      </div>
      <section className="routine-section">
        <div className="section-heading">
          <p className="eyebrow">Application order</p>
          <h2>One pick for each routine step</h2>
          <p className="tip-box">{skinTip}</p>
        </div>
        <div className="routine-strip routine-timeline">
          {allSlides.map(({ section, product, percent }, index) => (
            <ProductCard
              key={`${section}-${product.name}`}
              section={`${index + 1}. ${section}`}
              product={product}
              percent={percent}
              compact
              routineNotes={compatibilityNotesForStep(section, result)}
              onFeedback={onFeedback}
            />
          ))}
        </div>
      </section>
      <p className="disclaimer">{result.disclaimer}</p>
    </section>
  );
}

function ProductCard({
  product,
  section,
  percent,
  compact = false,
  routineNotes = [],
  onFeedback,
}: {
  product: Product;
  section: string;
  percent: number;
  compact?: boolean;
  routineNotes?: { text: string; kind: "positive" | "warning" }[];
  onFeedback?: (productId: number | string | undefined, feedbackType: string, context: string) => Promise<void>;
}) {
  const [expanded, setExpanded] = useState(false);
  return (
    <article className={compact ? "product-card compact" : "product-card"}>
      <div className="product-image">
        <img src={productImageSrc(product)} alt={product.name} onError={useFallbackImage} />
        <span className="match-badge">{percent}% fit</span>
      </div>
      <div className="product-copy">
        <span className="product-role">{section}</span>
        {product.brand && <span className="product-brand">{product.brand}</span>}
        <h3>{product.name}</h3>
        <div className="product-meta">
          <span>Formula: {product.formula_base || "varies"}</span>
          <span>{product.category}</span>
          <span>{product.finish || "finish varies"}</span>
          <span>{product.coverage || "coverage varies"}</span>
          <span>{product.budget}</span>
        </div>
        <p><strong>Why this fits:</strong> {product.why}</p>
        {routineNotes.map((note) => (
          <small key={note.text} className={note.kind === "warning" ? "warning-note" : "positive-note"}>
            {note.text}
          </small>
        ))}
        <button className="text-toggle" onClick={() => setExpanded(!expanded)}>
          {expanded ? "Hide rating details" : "Rate this product"}
        </button>
        {expanded && (
          <div className="product-details">
            {product.why_recommended && <small><strong>Recommended because:</strong> {product.why_recommended}</small>}
            {product.matched_answers && <small><strong>Profile fit:</strong> {product.matched_answers}</small>}
            {product.possible_downside && <small><strong>Possible downside:</strong> {product.possible_downside}</small>}
            {product.compatibility_notes && <small><strong>Compatibility:</strong> {product.compatibility_notes}</small>}
            {product.avoid_pairing_with && <small><strong>Avoid pairing with:</strong> {product.avoid_pairing_with}</small>}
          </div>
        )}
        {onFeedback && <FeedbackButtons product={product} onFeedback={onFeedback} />}
      </div>
    </article>
  );
}

function FeedbackButtons({
  product,
  onFeedback,
}: {
  product: Product;
  onFeedback: (productId: number | string | undefined, feedbackType: string, context: string) => Promise<void>;
}) {
  const [sent, setSent] = useState("");
  const options = ["Loved this", "Too dry", "Too cakey", "Too orange", "Too oily", "Wrong budget"];
  async function submit(option: string) {
    await onFeedback(product.id, option.toLowerCase(), `${product.brand || ""} ${product.name}`.trim());
    setSent(option);
  }
  return (
    <div className="feedback-row">
      {options.map((option) => (
        <button key={option} onClick={() => submit(option)}>{option}</button>
      ))}
      {sent && <small>Saved: {sent}</small>}
    </div>
  );
}

function RoutineHighlights() {
  const highlights = [
    ["Skin prep", "Primer picks that support grip, hydration, or oil control before your base goes on."],
    ["Complexion base", "Foundation or skin tint based on your coverage goal, finish, budget, and skin type."],
    ["Color + shape", "Blush, bronzer, and contour arranged so creams and powders layer in the right order."],
    ["Set + wear", "Pressed powder, loose powder, and setting spray choices that help the routine last."],
  ];
  return (
    <section className="featured">
      <div className="section-heading">
        <p className="eyebrow">What you get</p>
        <h2>A complete base routine, not a random product list</h2>
      </div>
      <div className="featured-grid">
        {highlights.map(([title, copy], index) => (
          <article key={title}>
            <span>{String(index + 1).padStart(2, "0")}</span>
            <h3>{title}</h3>
            <p>{copy}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function CompareProducts({
  api,
  products,
  answers,
}: {
  api: (path: string, body?: AnyRecord) => Promise<AnyRecord>;
  products: DbProduct[];
  answers: QuizAnswer;
}) {
  const [skinType, setSkinType] = useState(answers.skin_type);
  const [undertone, setUndertone] = useState(answers.undertone);
  const [finishLook, setFinishLook] = useState(answers.preference || "natural");
  const [query, setQuery] = useState("");
  const [productA, setProductA] = useState<number | "">(products[0]?.id || "");
  const [productB, setProductB] = useState<number | "">(products[1]?.id || "");
  const [comparison, setComparison] = useState<CompareResponse | null>(null);
  const filtered = products.filter((product) =>
    `${product.brand} ${product.name} ${product.product_type}`.toLowerCase().includes(query.toLowerCase())
  );

  async function compare() {
    if (!productA || !productB) return;
    const response = await api("/api/compare-products", {
      skin_type: skinType,
      undertone,
      finish_look: finishLook,
      product_a_id: productA,
      product_b_id: productB,
    });
    setComparison(response as CompareResponse);
  }

  return (
    <section className="advisor-page">
      <div className="section-heading">
        <p className="eyebrow">Compare Products</p>
        <h2>See which formula fits better</h2>
        <p>Compare two products against your skin type, tone preference, finish look, formula finish, coverage, and feedback-adjusted fit.</p>
      </div>
      <div className="advisor-card compare-card">
        <label>
          Search products
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Brand, product, or category" />
        </label>
        <label>
          Your skin type
          <select value={skinType} onChange={(event) => setSkinType(event.target.value)}>
            {["dry", "balanced", "combination", "oily"].map((value) => <option key={value}>{value}</option>)}
          </select>
        </label>
        <label>
          Tone preference
          <select value={undertone} onChange={(event) => setUndertone(event.target.value)}>
            {["cool", "neutral", "warm", "olive"].map((value) => <option key={value}>{value}</option>)}
          </select>
        </label>
        <label>
          Desired finish/look
          <select value={finishLook} onChange={(event) => setFinishLook(event.target.value)}>
            <option value="natural">Natural</option>
            <option value="neutral everyday">Neutral Everyday</option>
            <option value="soft radiant">Soft Radiant</option>
            <option value="dewy glow">Dewy Glow</option>
            <option value="matte">Matte</option>
            <option value="full glam">Full Glam</option>
          </select>
        </label>
        <label>
          Product A
          <select value={productA} onChange={(event) => setProductA(Number(event.target.value))}>
            <option value="">Choose Product A</option>
            {filtered.map((product) => <option key={product.id} value={product.id}>{product.brand} - {product.name}</option>)}
          </select>
        </label>
        <label>
          Product B
          <select value={productB} onChange={(event) => setProductB(Number(event.target.value))}>
            <option value="">Choose Product B</option>
            {filtered.map((product) => <option key={product.id} value={product.id}>{product.brand} - {product.name}</option>)}
          </select>
        </label>
        <button className="primary" onClick={compare}>Compare Products</button>
      </div>
      {comparison && (
        <div className="advisor-results compare-results">
          <article className="advisor-response">
            <span>Winner</span>
            <h3>{comparison.winner}</h3>
            <p>{comparison.explanation}</p>
            <div className="comparison-grid">
              <ComparisonProduct product={comparison.product_a} score={comparison.product_a_score} />
              <ComparisonProduct product={comparison.product_b} score={comparison.product_b_score} />
            </div>
            <ul>
              {comparison.comparison_points.map((point) => <li key={point}>{point}</li>)}
            </ul>
          </article>
        </div>
      )}
    </section>
  );
}

function ComparisonProduct({ product, score }: { product: DbProduct; score: number }) {
  return (
    <article className="comparison-product">
      <strong>{score}% fit</strong>
      <h3>{product.brand}</h3>
      <p>{product.name}</p>
      <small>{product.product_type} · {product.finish} · {product.coverage || "coverage varies"} · {product.price_tier}</small>
      <small>Skin: {product.skin_type_match}</small>
      <small>Downside: {product.avoid_if || "None flagged"}</small>
      {product.compatibility_notes && <small>Compatibility: {product.compatibility_notes}</small>}
    </article>
  );
}

function BeautyAdvisor({
  api,
  answers,
  onSaved,
  onViewSaved,
}: {
  api: (path: string, body?: AnyRecord) => Promise<AnyRecord>;
  answers: QuizAnswer;
  onSaved: () => Promise<void>;
  onViewSaved: () => void;
}) {
  const [message, setMessage] = useState("I want a natural drugstore routine that will not get patchy.");
  const [responses, setResponses] = useState<AgentResponse[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [savedKeys, setSavedKeys] = useState<Set<string>>(new Set());

  async function submit() {
    if (!message.trim()) return;
    setIsSending(true);
    try {
      const response = await api("/api/agent", {
        goal: "Answer a beauty shopper question and recommend cosmetic products when useful.",
        text_input: message,
        image: null,
        profile: {
          skin_type: answers.skin_type,
          undertone: answers.undertone,
          depth: answers.depth,
          preference: answers.preference,
          budget: answers.budget,
          coverage: answers.coverage,
        },
      });
      setResponses((current) => [response as AgentResponse, ...current]);
      setMessage("");
    } finally {
      setIsSending(false);
    }
  }

  async function saveRoutine(response: AgentResponse) {
    const key = advisorResponseKey(response);
    await api("/api/saved-results", {
      title: response.request_text || "AI advisor routine",
      category: "agent",
      payload: buildAdvisorRoutinePayload(response),
    });
    setSavedKeys((current) => new Set([...current, key]));
    await onSaved();
  }

  async function submitFeedback(productId: number | string | undefined, feedbackType: string, context: string) {
    if (!productId) return;
    await api("/api/feedback", {
      product_id: Number(productId),
      feedback_type: feedbackType,
      context,
    });
  }

  return (
    <section className="advisor-page">
      <div className="section-heading">
        <p className="eyebrow">Beauty Advisor</p>
        <h2>Ask Build a Base for help choosing products</h2>
        <p>Type a routine, finish, budget, formula, or makeup problem question. The advisor uses the backend agent and keeps recommendations cosmetic-only.</p>
      </div>
      <div className="advisor-card">
        <textarea value={message} onChange={(event) => setMessage(event.target.value)} />
        <button className="primary" onClick={submit} disabled={isSending}>
          Ask Advisor <Send size={17} />
        </button>
      </div>
      <div className="advisor-results">
        {responses.map((response, index) => (
          <article className="advisor-response" key={`${response.summary}-${index}`}>
            <span>Advisor response</span>
            <h3>{response.summary}</h3>
            {response.request_text && <small>Asked: {response.request_text}</small>}
            <AdvisorCompatibility response={response} />
            <div className="results-actions">
              <button className="secondary" onClick={() => saveRoutine(response)}>
                {savedKeys.has(advisorResponseKey(response)) ? "Routine saved" : "Save products + routine"}
              </button>
              <button className="secondary" onClick={onViewSaved}>View saved routines</button>
            </div>
            <AdvisorRoutine response={response} onFeedback={submitFeedback} />
            <p>{response.explanation}</p>
            {response.follow_up_questions.length > 0 && <small>{response.follow_up_questions.join(" ")}</small>}
          </article>
        ))}
      </div>
    </section>
  );
}

function AdvisorCompatibility({ response }: { response: AgentResponse }) {
  const output = response.tools_used?.[0]?.output;
  if (!isRecord(output)) return null;
  const score = output.routine_score;
  const warnings = Array.isArray(output.compatibility_warnings) ? output.compatibility_warnings : [];
  const positives = Array.isArray(output.positive_compatibility_notes) ? output.positive_compatibility_notes : [];
  return (
    <div className="compatibility-panel">
      {typeof score === "number" && <strong>{score}% routine compatibility</strong>}
      {warnings.map((warning) => <small className="warning-note" key={String(warning)}>{String(warning)}</small>)}
      {positives.map((note) => <small className="positive-note" key={String(note)}>{String(note)}</small>)}
    </div>
  );
}

function advisorResponseKey(response: AgentResponse) {
  return `${response.request_text || response.summary}-${response.tools_used?.[0]?.tool || "advisor"}`;
}

function buildAdvisorRoutinePayload(response: AgentResponse): AnyRecord {
  const output = response.tools_used?.find((tool) => isRecord(tool.output) && isRecord(tool.output.makeup_bag))?.output;
  if (!isRecord(output)) return response as unknown as AnyRecord;
  return {
    source: "beauty_advisor",
    prompt: response.request_text || "",
    summary: response.summary,
    explanation: response.explanation,
    makeup_bag: output.makeup_bag,
    product_recommendations: output.product_recommendations,
    routine_score: output.routine_score,
    compatibility_warnings: output.compatibility_warnings,
    positive_compatibility_notes: output.positive_compatibility_notes,
    disclaimer: response.disclaimer,
  };
}

function AdvisorRoutine({
  response,
  onFeedback,
}: {
  response: AgentResponse;
  onFeedback: (productId: number | string | undefined, feedbackType: string, context: string) => Promise<void>;
}) {
  const routine = collectAgentRoutine(response);
  if (routine.length === 0) {
    return (
      <ul>
        {response.recommendations.map((item) => <li key={item}>{item}</li>)}
      </ul>
    );
  }

  return (
    <div className="advisor-routine">
      {routine.map(({ section, product }, index) => (
        <div className="advisor-routine-item" key={`${section}-${product.id || product.name}-${product.brand || ""}-${product.shade_name || ""}`}>
          <img src={productImageSrc(product)} alt={product.name} onError={useFallbackImage} />
          <span>{index + 1}. {section}</span>
          <strong>{product.name}</strong>
          <p>{product.finish || "finish varies"} · {product.coverage || "coverage varies"} · {product.typical_price || "price varies"}</p>
          <small>{product.why}</small>
          {product.matched_answers && <small>Profile fit: {product.matched_answers}</small>}
          {product.possible_downside && <small>Downside: {product.possible_downside}</small>}
          {product.compatibility_notes && <small>Compatibility: {product.compatibility_notes}</small>}
          <FeedbackButtons product={product} onFeedback={onFeedback} />
        </div>
      ))}
    </div>
  );
}

function SavedResults({ saved }: { saved: AnyRecord[] }) {
  return (
    <section className="library-page">
      <div className="section-heading">
        <p className="eyebrow">Saved Results</p>
        <h2>Your saved routines</h2>
      </div>
      <div className="saved-list">
        {saved.length === 0 && <p className="muted">No saved results yet.</p>}
        {saved.map((item) => (
          <article className="saved-card" key={String(item.id)}>
            <strong>{String(item.title)}</strong>
            <span>{String(item.category)} · {String(item.created_at)}</span>
            <SavedRoutinePreview item={item} />
          </article>
        ))}
      </div>
    </section>
  );
}

function SavedRoutinePreview({ item }: { item: AnyRecord }) {
  const payload = item.payload;
  if (!isRecord(payload)) return null;
  const routine = collectSavedRoutine(payload);
  if (routine.length === 0) return <small className="muted">Saved item has no routine products.</small>;
  return (
    <div className="saved-routine-preview">
      {routine.map(({ section, product }, index) => (
        <div key={`${section}-${product.id || product.name}-${index}`} className="saved-routine-item">
          <span>{index + 1}. {section}</span>
          <strong>{product.brand ? `${product.brand} ` : ""}{product.name}</strong>
          <small>{product.finish || "finish varies"} · {product.coverage || "coverage varies"} · {product.price_tier || product.budget}</small>
        </div>
      ))}
    </div>
  );
}

function collectSavedRoutine(payload: AnyRecord): { section: string; product: Product }[] {
  if (isRecord(payload.makeup_bag)) {
    return collectRoutineFromBag(payload.makeup_bag);
  }
  const tools = payload.tools_used;
  if (Array.isArray(tools)) {
    for (const tool of tools) {
      if (!isRecord(tool) || !isRecord(tool.output)) continue;
      const routine = collectRoutineFromBag(tool.output.makeup_bag);
      if (routine.length > 0) return routine;
    }
  }
  return [];
}

function collectRoutineFromBag(makeupBag: unknown): { section: string; product: Product }[] {
  if (!isRecord(makeupBag)) return [];
  const routine: { section: string; product: Product }[] = [];
  Object.keys(PRODUCT_SECTION_LABELS).forEach((key) => {
    const products = makeupBag[key];
    if (!Array.isArray(products)) return;
    const limit = key === "setting_sprays" ? 2 : 1;
    products.slice(0, limit).forEach((product) => {
      if (isProduct(product)) routine.push({ section: PRODUCT_SECTION_LABELS[key], product });
    });
  });
  return routine;
}

function collectProductSlides(result: RecommendResponse | null): { section: string; product: Product; percent: number }[] {
  if (!result) return [];
  const slides: { section: string; product: Product; percent: number }[] = [];
  const seen = new Set<string>();
  Object.keys(PRODUCT_SECTION_LABELS).forEach((key, index) => {
    const products = result.makeup_bag[key] || [];
    const limit = key === "setting_sprays" ? 2 : 1;
    products.slice(0, limit).forEach((product, productIndex) => {
      const productKey = `${product.id || ""}-${product.brand || ""}-${product.name}`.toLowerCase();
      if (seen.has(productKey)) return;
      seen.add(productKey);
      slides.push({
        section: PRODUCT_SECTION_LABELS[key],
        product,
        percent: Number(product.match_percentage || Math.max(88, 98 - index - productIndex)),
      });
    });
  });
  return slides;
}

function collectAgentRoutine(response: AgentResponse): { section: string; product: Product }[] {
  const routine: { section: string; product: Product }[] = [];
  const seen = new Set<string>();

  response.tools_used?.forEach((tool) => {
    const makeupBag = tool.output?.makeup_bag;
    if (isRecord(makeupBag)) {
      Object.keys(PRODUCT_SECTION_LABELS).forEach((key) => {
        const products = makeupBag[key];
        if (!Array.isArray(products)) return;
        const limit = key === "setting_sprays" ? 2 : 1;
        products.slice(0, limit).forEach((product) => {
          if (!isProduct(product)) return;
          const productKey = `${key}-${product.id || ""}-${product.brand || ""}-${product.name}-${product.shade_name || ""}`.toLowerCase();
          if (seen.has(productKey)) return;
          seen.add(productKey);
          routine.push({ section: PRODUCT_SECTION_LABELS[key], product });
        });
      });
    }
  });

  if (routine.length > 0) return routine;

  response.tools_used?.forEach((tool) => {
    const directProducts = tool.output?.product_recommendations;
    if (!Array.isArray(directProducts)) return;
    directProducts.forEach((product) => {
      if (!isProduct(product)) return;
      const key = `${product.id || ""}-${product.brand || ""}-${product.name}-${product.shade_name || ""}`.toLowerCase();
      if (seen.has(key)) return;
      seen.add(key);
      routine.push({ section: PRODUCT_SECTION_LABELS[_slotForProduct(product)] || product.category, product });
    });
  });
  return routine;
}

function _slotForProduct(product: Product) {
  const category = product.category.toLowerCase();
  if (category.includes("primer")) return "primer";
  if (category === "foundation" || category === "skin tint") return "base";
  if (category.includes("powder blush")) return "powder_blush";
  if (category.includes("liquid blush")) return "liquid_blush";
  if (category.includes("bronzer")) return "powder_contour_or_bronzer";
  if (category.includes("contour")) return "cream_or_liquid_contour_bronzer";
  if (category.includes("concealer")) return "concealer";
  if (category.includes("pressed")) return "pressed_setting_powder";
  if (category.includes("loose")) return "loose_setting_powder";
  if (category.includes("spray")) return "setting_sprays";
  return category.replaceAll(" ", "_");
}

function compatibilityNotesForStep(section: string, result: RecommendResponse) {
  const sectionText = section.toLowerCase();
  const notes = [
    ...uniqueStrings(result.compatibility_warnings || []).map((text) => ({ text, kind: "warning" as const })),
    ...uniqueStrings(result.positive_compatibility_notes || []).map((text) => ({ text, kind: "positive" as const })),
  ];

  return notes.filter((note) => {
    const text = note.text.toLowerCase();
    if (text.includes("primer") && sectionText.includes("primer")) return true;
    if ((text.includes("base") || text.includes("foundation")) && sectionText.includes("foundation")) return true;
    if (text.includes("powder") && sectionText.includes("powder")) return true;
    if (text.includes("spray") && sectionText.includes("spray")) return true;
    if ((text.includes("dry") || text.includes("cakey")) && sectionText.includes("powder")) return true;
    return false;
  });
}

function routineSkinTip(skinType: string, result: RecommendResponse) {
  const normalized = skinType.toLowerCase();
  const tips: Record<string, string[]> = {
    dry: [
      "Dry-skin tip: keep powder only where you crease or get shiny, then press setting spray over the base so it looks smoother.",
      "Dry-skin tip: let moisturizer and primer settle before foundation so the base grips without clinging to flaky spots.",
      "Dry-skin tip: use thin layers of base and concealer first; add coverage only where you need it to avoid cakiness.",
    ],
    oily: [
      "Oily-skin tip: apply primer mainly through the T-zone, then use powder in thin layers so the base lasts without looking heavy.",
      "Oily-skin tip: let each cream layer set before powder; rushing layers can make shine break through faster.",
      "Oily-skin tip: save setting spray for the final step so powder melts in but your oil-control products still do their job.",
    ],
    combination: [
      "Combination-skin tip: treat zones differently: hydrate cheeks lightly, then use primer and powder mostly through the T-zone.",
      "Combination-skin tip: keep cream products flexible on drier areas and set only the places that crease or get shiny.",
      "Combination-skin tip: use less powder on the cheeks and more around the nose, forehead, and chin for a balanced finish.",
    ],
    balanced: [
      "Balanced-skin tip: use thin, even layers and choose powder placement based on where you want the finish to stay soft.",
      "Balanced-skin tip: let your primer and base settle before adding blush or bronzer so the layers stay smooth.",
      "Balanced-skin tip: finish with setting spray to bring the routine together and soften any powdery edges.",
    ],
  };
  const options = tips[normalized] || tips.balanced;
  const signature = JSON.stringify(result.makeup_bag || {}) + String(result.routine_score || "");
  const index = Array.from(signature).reduce((total, character) => total + character.charCodeAt(0), 0) % options.length;
  return options[index];
}

function uniqueStrings(values: string[]) {
  return Array.from(new Set(values.map((value) => value.trim()).filter(Boolean)));
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isProduct(value: unknown): value is Product {
  return isRecord(value) && typeof value.name === "string" && typeof value.category === "string";
}

const FALLBACK_PRODUCT_IMAGE = "/product-images/fallback-product.jpg";

function productImageSrc(product: Product) {
  return product.image_url || FALLBACK_PRODUCT_IMAGE;
}

function useFallbackImage(event: React.SyntheticEvent<HTMLImageElement>) {
  if (event.currentTarget.src.endsWith(FALLBACK_PRODUCT_IMAGE)) return;
  event.currentTarget.src = FALLBACK_PRODUCT_IMAGE;
}

createRoot(document.getElementById("root")!).render(<App />);
