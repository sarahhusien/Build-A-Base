import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Bot,
  Brush,
  ClipboardList,
  Droplet,
  Heart,
  Image,
  Save,
  Search,
  Sparkles,
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type AnyRecord = Record<string, unknown>;

type AgentResponse = {
  summary: string;
  explanation: string;
  recommendations: string[];
  follow_up_questions: string[];
  tools_used: { tool: string; input_summary: string; output: AnyRecord }[];
  disclaimer: string;
};

function App() {
  const [active, setActive] = useState("agent");
  const [result, setResult] = useState<AnyRecord | AgentResponse | null>(null);
  const [saved, setSaved] = useState<AnyRecord[]>([]);

  useEffect(() => {
    fetchSaved().catch(() => undefined);
  }, []);

  async function api(path: string, body?: AnyRecord) {
    const response = await fetch(`${API_BASE}${path}`, {
      method: body ? "POST" : "GET",
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return response.json();
  }

  async function fetchSaved() {
    setSaved(await api("/api/saved-results"));
  }

  async function saveCurrent(category: string) {
    if (!result) return;
    await api("/api/saved-results", {
      title: `${category} result`,
      category,
      payload: result as AnyRecord,
    });
    await fetchSaved();
  }

  const tabs = [
    ["agent", Bot, "Agent"],
    ["foundation", Droplet, "Foundation"],
    ["quiz", ClipboardList, "Skin Quiz"],
    ["routine", Sparkles, "Routine"],
    ["problem", Brush, "Fix Makeup"],
    ["look", Image, "Recreate"],
    ["saved", Heart, "Saved"],
  ] as const;

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">SS</span>
          <div>
            <h1>ShadeSync</h1>
            <p>Cosmetic AI beauty studio</p>
          </div>
        </div>
        <nav className="tabs">
          {tabs.map(([id, Icon, label]) => (
            <button
              key={id}
              className={active === id ? "active" : ""}
              onClick={() => {
                setActive(id);
                setResult(null);
              }}
              title={label}
            >
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <section className="workspace">
        {active === "agent" && <AgentPanel run={api} setResult={setResult} />}
        {active === "foundation" && <FoundationPanel run={api} setResult={setResult} />}
        {active === "quiz" && <QuizPanel run={api} setResult={setResult} />}
        {active === "routine" && <RoutinePanel run={api} setResult={setResult} />}
        {active === "problem" && <ProblemPanel run={api} setResult={setResult} />}
        {active === "look" && <LookPanel run={api} setResult={setResult} />}
        {active === "saved" && <SavedPanel saved={saved} />}
        {active !== "saved" && result && (
          <ResultPanel result={result} onSave={() => saveCurrent(active)} />
        )}
      </section>
    </main>
  );
}

function AgentPanel({ run, setResult }: PanelProps) {
  const [goal, setGoal] = useState("Match my foundation, infer my skin type, and build a budget routine.");
  const [text, setText] = useState("My makeup gets patchy around my nose. I like natural finishes.");
  const [image, setImage] = useState("");
  const [budget, setBudget] = useState("drugstore");
  const [preference, setPreference] = useState("natural finish");

  async function submit() {
    setResult(
      await run("/api/agent", {
        goal,
        text_input: text,
        image: image || null,
        profile: {
          budget,
          preference,
          quiz_answers: {
            after_washing: "tight cheeks, shiny T-zone",
            midday: "oily t-zone",
          },
          product_list: ["hydrating primer", "matte foundation", "setting powder"],
        },
      }),
    );
  }

  return (
    <section className="panel">
      <PanelTitle icon={<Bot />} title="AI Beauty Agent" />
      <label>Goal<textarea value={goal} onChange={(e) => setGoal(e.target.value)} /></label>
      <label>Text input<textarea value={text} onChange={(e) => setText(e.target.value)} /></label>
      <div className="grid two">
        <label>Optional image URL or base64<input value={image} onChange={(e) => setImage(e.target.value)} /></label>
        <label>Budget<select value={budget} onChange={(e) => setBudget(e.target.value)}><option>drugstore</option><option>moderate</option><option>premium</option></select></label>
      </div>
      <label>Preference<input value={preference} onChange={(e) => setPreference(e.target.value)} /></label>
      <button className="primary" onClick={submit}><Search size={18} /> Run Agent</button>
    </section>
  );
}

type PanelProps = {
  run: (path: string, body?: AnyRecord) => Promise<AnyRecord>;
  setResult: (result: AnyRecord | AgentResponse) => void;
};

function FoundationPanel({ run, setResult }: PanelProps) {
  const [undertone, setUndertone] = useState("neutral");
  const [depth, setDepth] = useState("medium");
  return (
    <section className="panel">
      <PanelTitle icon={<Droplet />} title="Foundation Shade Matcher" />
      <div className="grid two">
        <label>Undertone<select value={undertone} onChange={(e) => setUndertone(e.target.value)}><option>cool</option><option>neutral</option><option>warm</option><option>olive</option></select></label>
        <label>Depth<select value={depth} onChange={(e) => setDepth(e.target.value)}><option>fair</option><option>light</option><option>medium</option><option>tan</option><option>deep</option><option>rich</option></select></label>
      </div>
      <button className="primary" onClick={async () => setResult(await run("/api/foundation", { undertone, depth }))}>Match Shade</button>
    </section>
  );
}

function QuizPanel({ run, setResult }: PanelProps) {
  const [after, setAfter] = useState("tight cheeks, shiny T-zone");
  const [midday, setMidday] = useState("oily around nose");
  return (
    <section className="panel">
      <PanelTitle icon={<ClipboardList />} title="Skin Type Quiz" />
      <label>After washing<input value={after} onChange={(e) => setAfter(e.target.value)} /></label>
      <label>Midday skin feel<input value={midday} onChange={(e) => setMidday(e.target.value)} /></label>
      <button className="primary" onClick={async () => setResult(await run("/api/skin-type", { answers: { after_washing: after, midday } }))}>Infer Skin Type</button>
    </section>
  );
}

function RoutinePanel({ run, setResult }: PanelProps) {
  const [skinType, setSkinType] = useState("combination");
  const [undertone, setUndertone] = useState("neutral");
  const [depth, setDepth] = useState("medium");
  const [preference, setPreference] = useState("natural");
  const [budget, setBudget] = useState("drugstore");
  return (
    <section className="panel">
      <PanelTitle icon={<Sparkles />} title="Routine Generator" />
      <div className="grid two">
        <label>Skin type<input value={skinType} onChange={(e) => setSkinType(e.target.value)} /></label>
        <label>Undertone<input value={undertone} onChange={(e) => setUndertone(e.target.value)} /></label>
        <label>Depth<input value={depth} onChange={(e) => setDepth(e.target.value)} /></label>
        <label>Budget<input value={budget} onChange={(e) => setBudget(e.target.value)} /></label>
      </div>
      <label>Preference<input value={preference} onChange={(e) => setPreference(e.target.value)} /></label>
      <button className="primary" onClick={async () => setResult(await run("/api/routine", { skin_type: skinType, undertone, depth, preference, budget }))}>Generate Routine</button>
    </section>
  );
}

function ProblemPanel({ run, setResult }: PanelProps) {
  const [problem, setProblem] = useState("My foundation gets cakey and separates around my nose.");
  const [products, setProducts] = useState("primer, serum foundation, setting powder");
  return (
    <section className="panel">
      <PanelTitle icon={<Brush />} title="Makeup Problem Solver" />
      <label>Problem<textarea value={problem} onChange={(e) => setProblem(e.target.value)} /></label>
      <label>Products<input value={products} onChange={(e) => setProducts(e.target.value)} /></label>
      <button className="primary" onClick={async () => setResult(await run("/api/problem-solver", { problem_text: problem, product_list: products.split(",").map((item) => item.trim()) }))}>Solve Problem</button>
    </section>
  );
}

function LookPanel({ run, setResult }: PanelProps) {
  const [image, setImage] = useState("");
  const [style, setStyle] = useState("soft glam");
  return (
    <section className="panel">
      <PanelTitle icon={<Image />} title="Makeup Look Recreator" />
      <label>Inspiration image URL or base64<input value={image} onChange={(e) => setImage(e.target.value)} /></label>
      <label>Style<input value={style} onChange={(e) => setStyle(e.target.value)} /></label>
      <button className="primary" onClick={async () => setResult(await run("/api/look-recreator", { inspiration_image: image || null, user_profile: { style } }))}>Recreate Look</button>
    </section>
  );
}

function SavedPanel({ saved }: { saved: AnyRecord[] }) {
  return (
    <section className="panel">
      <PanelTitle icon={<Heart />} title="Saved Results" />
      <div className="saved-list">
        {saved.length === 0 && <p className="muted">No saved results yet.</p>}
        {saved.map((item) => (
          <article className="result-card" key={String(item.id)}>
            <strong>{String(item.title)}</strong>
            <span>{String(item.category)} · {String(item.created_at)}</span>
            <pre>{JSON.stringify(item.payload, null, 2)}</pre>
          </article>
        ))}
      </div>
    </section>
  );
}

function ResultPanel({ result, onSave }: { result: AnyRecord | AgentResponse; onSave: () => void }) {
  const agent = result as AgentResponse;
  return (
    <section className="result">
      <div className="result-header">
        <h2>Result</h2>
        <button onClick={onSave} title="Save result"><Save size={18} /></button>
      </div>
      {"recommendations" in result && (
        <div className="recommendations">
          <p>{agent.summary}</p>
          <ul>{agent.recommendations.map((item) => <li key={item}>{item}</li>)}</ul>
          <p className="muted">{agent.explanation}</p>
          {agent.follow_up_questions.length > 0 && <p className="follow">Follow-up: {agent.follow_up_questions.join(" ")}</p>}
          <p className="disclaimer">{agent.disclaimer}</p>
        </div>
      )}
      <pre>{JSON.stringify(result, null, 2)}</pre>
    </section>
  );
}

function PanelTitle({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <div className="panel-title">
      {icon}
      <h2>{title}</h2>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
