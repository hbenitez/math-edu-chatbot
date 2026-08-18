# Approach 1 — Implementation Plan (LangGraph)

**Goal:** turn the failing single-call Socratic tutor into a **LangGraph agentic
pipeline** where the small model (`llama3.2`) never does arithmetic, a
deterministic tool owns the math, and a guardrail prevents answer-leaks and
sycophantic reversals.

This plan implements **Approach 1** from
[socratic-tutor-improvement-approaches.md](socratic-tutor-improvement-approaches.md).
All components run **fully offline** on the teacher's laptop (Windows 11, i7,
40 GB) via Ollama, consistent with the
[Classroom Cloud deployment guide](deployment-classroom-cloud.md).

---

## 1. Why LangGraph

The current `text.py` makes **one** `llm.invoke(messages)` call and asks the 3B
model to plan, compute, grade, and self-censor at once. LangGraph lets us express
the tutor as a **stateful graph** of small, single-responsibility nodes with
explicit, inspectable transitions:

- **Typed shared state** carried across turns (the hidden lesson plan, the verified
  ground truth, the current step, grading history).
- **Conditional edges** to route on the grader's verdict (correct → advance,
  wrong → hint, push-back → hold).
- **Checkpointing** so a multi-turn tutoring session survives across Gradio
  requests without us hand-rolling history reconstruction.
- Each node is a **narrow** prompt or a pure Python function — exactly what a 3B
  can handle reliably.

---

## 2. Target architecture

```
                    ┌─────────────────────────────────────────────┐
   student photo ──►│ intake_vision  (qwen2.5vl:7b, optional)      │
   or text        ─►│  → normalized problem text                    │
                    └───────────────────────┬─────────────────────┘
                                            ▼
                    ┌─────────────────────────────────────────────┐
   (once per        │ solve  (SymPy tool — NO LLM)                  │
    problem)        │  → final_answer + canonical_steps[]           │
                    └───────────────────────┬─────────────────────┘
                                            ▼
                    ┌─────────────────────────────────────────────┐
                    │ plan  (llama3.2, 1 call)                      │
                    │  verified steps → hidden socratic_questions[] │
                    └───────────────────────┬─────────────────────┘
                                            ▼
             ┌───────────────────  per student turn  ───────────────────┐
             │                                                            │
             ▼                                                            │
   ┌───────────────────────┐   verdict=correct   ┌──────────────────┐    │
   │ grade  (llama3.2 +     │───────────────────►│ advance_step      │    │
   │ deterministic compare) │                    └─────────┬────────┘    │
   │  → correct / partial / │   verdict=wrong              │             │
   │    wrong / pushback    │──────────┐                   ▼             │
   └───────────┬───────────┘          │         ┌──────────────────┐     │
               │ pushback             ▼         │ tutor  (llama3.2)  │     │
               ▼             ┌──────────────┐   │ phrase next Q/hint │     │
   ┌───────────────────────┐ │ hint         │──►│ from stored plan   │─────┘
   │ guardrail             │ │ (llama3.2)   │   └──────────────────┘   → reply
   │ hold ground truth,    │ └──────────────┘
   │ re-guide, no reversal │
   └───────────────────────┘
```

**Key invariant:** `solve` (SymPy) is the *only* source of numerical truth. Every
LLM node consumes the stored truth; none recomputes it.

---

## 3. Shared state (`TutorState`)

```python
from typing import TypedDict, Literal, Optional
from langgraph.graph import MessagesState

class TutorState(TypedDict, total=False):
    # --- problem (set once) ---
    raw_input: str                 # student text, or OCR output
    problem_text: str              # normalized statement
    problem_type: str              # e.g. "fraction_division", "linear_equation"

    # --- ground truth from the SymPy tool (set once) ---
    final_answer: str              # canonical answer, e.g. "8/3"
    canonical_steps: list[str]     # verified solution steps
    solver_ok: bool                # did SymPy parse+solve successfully?

    # --- hidden lesson plan (set once) ---
    socratic_questions: list[str]  # ordered guiding questions
    step_index: int                # which step the student is on

    # --- per-turn ---
    student_msg: str
    verdict: Literal["correct", "partial", "wrong", "pushback", "offtopic"]
    attempts_on_step: int
    reply: str                     # text shown to the student

    # multi-turn history (LangGraph MessagesState add-on)
    messages: list
```

State is persisted with a **checkpointer** keyed by conversation id, so each
Gradio request resumes the same session.

---

## 4. Nodes

| Node | Type | Model | Responsibility |
|------|------|-------|----------------|
| `intake_vision` | LLM | `qwen2.5vl:7b` | OCR a photo → problem text (skipped for text-only input) |
| `classify` | LLM (constrained) | `llama3.2` | Label `problem_type`; extract a machine-parseable expression |
| `solve` | **pure Python** | — | SymPy solves → `final_answer`, `canonical_steps`; sets `solver_ok` |
| `plan` | LLM | `llama3.2` | Turn verified steps into ordered `socratic_questions` |
| `grade` | LLM + Python | `llama3.2` | Compare `student_msg` to the expected step; emit `verdict` |
| `advance_step` | pure Python | — | `step_index += 1`; reset `attempts_on_step` |
| `hint` | LLM | `llama3.2` | Produce a nudge for the current step (never the answer) |
| `guardrail` | LLM + Python | `llama3.2` | On push-back, hold the verified answer and re-guide; block leaks |
| `tutor` | LLM | `llama3.2` | Phrase the next question/hint in kid-friendly Spanish + LaTeX |

### Node design notes

- **`solve` (the linchpin).** Parse the student's problem into a SymPy expression
  and solve deterministically. Handles the failure cases directly:
  `8 ÷ 6 → Rational(4,3)`, `8 ÷ Rational(1,2) → 16`. Sets `solver_ok=False` if it
  cannot parse, which routes to a graceful fallback (ask the student to restate).
- **`grade`.** Where possible, compare **numerically/symbolically** (SymPy
  `simplify(a-b)==0`), not by LLM opinion — this fixes the "¡Casi!/¡Excelente!"
  miscalibration. The LLM is only used to map free-text answers to a candidate
  value; the *judgement* is deterministic.
- **`guardrail`.** Detects "pushback" (student asserts a value). It re-checks the
  student's claim against `final_answer` with SymPy: if the student is wrong, it
  **does not** reverse — it re-guides. This directly kills the sycophancy failure.
- **`tutor`.** The only node that owns tone/format (Socratic, one step at a time,
  LaTeX in `$…$`). It receives the exact content to convey, so it cannot invent
  math.

---

## 5. Graph wiring

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

g = StateGraph(TutorState)

g.add_node("intake_vision", intake_vision)
g.add_node("classify", classify)
g.add_node("solve", solve)
g.add_node("plan", plan)
g.add_node("grade", grade)
g.add_node("advance_step", advance_step)
g.add_node("hint", hint)
g.add_node("guardrail", guardrail)
g.add_node("tutor", tutor)

# First turn: build the problem + plan.
g.add_conditional_edges(START, has_image, {"image": "intake_vision", "text": "classify"})
g.add_edge("intake_vision", "classify")
g.add_edge("classify", "solve")
g.add_conditional_edges("solve", solver_router,
                        {"ok": "plan", "unparseable": "tutor"})   # fallback: ask to restate
g.add_edge("plan", "tutor")

# Subsequent turns enter at `grade`.
g.add_conditional_edges("grade", grade_router, {
    "correct":  "advance_step",
    "partial":  "hint",
    "wrong":    "hint",
    "pushback": "guardrail",
})
g.add_conditional_edges("advance_step", finished_router,
                        {"more": "tutor", "done": "tutor"})  # tutor congratulates on done
g.add_edge("hint", "tutor")
g.add_edge("guardrail", "tutor")
g.add_edge("tutor", END)

graph = g.compile(checkpointer=MemorySaver())
```

- **Entry routing per turn:** first message → `START`; later messages →
  `grade` (the runtime uses the checkpointer to resume state). We implement this
  by branching on whether `socratic_questions` already exists.
- `MemorySaver` is fine for a single-process Gradio server; swap for
  `SqliteSaver` if we want sessions to survive a restart — still fully local.

---

## 6. Integration with the existing app

- **New module `graph_tutor.py`** holds the state, nodes, and compiled graph.
- **`text.py`** keeps the Gradio UI but replaces the body of `chat()` with a call
  into the graph:

  ```python
  cfg = {"configurable": {"thread_id": conversation_id}}
  result = graph.invoke({"student_msg": message, "raw_input": message}, cfg)
  return result["reply"]
  ```

- **`visual.py`** routes the uploaded image into `intake_vision` first, then the
  same graph — unifying the text and visual tutors behind one pipeline.
- Ollama access reuses `langchain_ollama.ChatOllama(model="llama3.2")` and a
  vision call to `qwen2.5vl:7b`; no new model downloads.
- The **Socratic rules** currently in the system prompt move into the `tutor`
  (tone/format) and `guardrail` (no-leak, no-reversal) nodes.

---

## 7. Dependencies

Add to `requirements.txt` (installed once, with internet, per the deployment
guide — then runs offline):

```
langgraph>=0.2.0
langchain-ollama>=0.1.0   # already present
sympy>=1.12
```

No GPU and no additional model weights are required.

---

## 8. Milestones

| Phase | Deliverable | Exit criterion |
|-------|-------------|----------------|
| **P0 — Solver core** | `solve` + `grade` over SymPy | Correct answers/steps for fractions, linear eqs, basic geometry; unit-tested |
| **P1 — Minimal graph** | `classify → solve → plan → tutor` (single turn) | Produces a correct first Socratic question grounded in verified steps |
| **P2 — Multi-turn loop** | `grade`/`hint`/`advance_step` + checkpointer | Advances only on correct answers; calibrated praise |
| **P3 — Guardrail** | push-back handling | Does **not** reverse on a wrong student assertion; never leaks the final answer early |
| **P4 — Vision** | `intake_vision` wired in; `visual.py` uses the graph | Photo → OCR → same pipeline |
| **P5 — Hardening** | fallbacks, latency, offline test on Windows | Graceful "please restate" on unparseable input; acceptable per-turn latency |

---

## 9. Testing & evaluation

- **Golden regression set:** encode the screenshot failures as test cases —
  "dividir fracciones", `8 ÷ 1/2`, and the push-back turn ("Pero x es igual a
  8/6") — and assert the new pipeline: (a) computes correctly, (b) stays on the
  concept, (c) holds its ground on push-back.
- **Solver unit tests:** SymPy answers/steps for the target curriculum.
- **Grader tests:** free-text student answers map to the right verdict.
- **No-leak / no-sycophancy assertions:** the `tutor` reply must not contain
  `final_answer` before the last step; `guardrail` must not flip when the student
  is wrong.
- **Offline smoke test** on the Windows server following the deployment guide.

---

## 10. Risks & mitigations

| Risk | Mitigation |
|------|-----------|
| SymPy can't parse messy/natural-language problems | `classify` normalizes to an expression; on failure, route to a "please restate" fallback |
| Extra LLM calls raise per-turn latency | Keep prompts short; cache the plan; only `tutor` runs every turn |
| Curriculum beyond SymPy's easy reach (word problems, proofs) | Start with arithmetic/fractions/linear algebra/geometry; expand coverage incrementally, `log()` uncovered types |
| LangGraph state lost on server restart | Use `SqliteSaver` (local file) instead of `MemorySaver` |
| `qwen2.5vl` OCR errors feed a wrong problem into `solve` | Show the transcribed problem back to the student for confirmation before solving |

---

## 11. Relationship to Approaches 2 & 3

This pipeline is the **foundation**: the SymPy verifier stays in the loop even
after we later distill a better tutor (Approach 3) or apply DPO (Approach 2). The
classroom dialogues this system logs become the **training data** for those
phases. See the roadmap in
[socratic-tutor-improvement-approaches.md](socratic-tutor-improvement-approaches.md).
