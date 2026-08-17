# Improving MathBot's Socratic Tutoring — Three Proposed Approaches

**Scope:** how to make MathBot a reliable Socratic math tutor **under the hard
constraint that only small, open-weight models can be used** — specifically
`llama3.2` (≈3B, text, used by `text.py`) and `qwen2.5vl:7b` (vision, used by
`visual.py`) served locally through Ollama.

This report first summarizes the failure that motivates the work, diagnoses its
root cause, and then details three complementary solutions:
**(1) an agentic pipeline with a verifier tool, (2) RLHF / preference
optimization (DPO), and (3) knowledge distillation.**

---

## 1. Motivating evidence

A classroom test of the text tutor (`text.py`, `llama3.2`) was captured in a
series of screenshots. Two runs both started from the same student prompt:

> **Student:** "No entiendo cómo dividir fracciones." *(I don't understand how to divide fractions.)*

### What the tutor produced (Run A)

- Reframed a **fraction-division** question as a **subtraction** word problem
  ("8 slices, give away 2 → 6 left") and dressed it as a fake proportion
  `8/x = 6/1`, which has nothing to do with dividing fractions.
- Made hard arithmetic errors: **8 ÷ 6 = "1 y media"** (it is 1.33…) and
  **8 ÷ (1/2) = 8/1 = 8** (it is 16).
- Contradicted itself ("La respuesta correcta es efectivamente 8/6, **pero no
  exactamente**") and let the value of `x` wander: **8/6 → 8 → 6 → 8/6 → 4/3**.
- Miscalibrated feedback: said **"¡Casi!"** when the student had made no attempt,
  and **"¡Excelente!"** for answers it immediately contradicted.
- **Collapsed sycophantically**: when the student pushed back ("Pero x es igual a
  8/6"), it abandoned its own answer and agreed ("¡Tienes absolutamente razón!").

### Quality summary

| Dimension | Verdict |
|-----------|---------|
| Socratic **form** (asks questions, encourages, withholds the answer) | Present |
| Feedback **calibration** ("¡Casi!" vs "¡Excelente!") | Broken — fires on the wrong turns |
| **Reasoning** induced in the student | Incoherent — leads the student through a wrong model of the concept |
| **Mathematical** correctness | Multiple false facts and self-contradictions |
| **Robustness** to student push-back | Fails — reverses its answer to match the student |

**Net effect:** a student who followed this faithfully would leave *more* confused
about fraction division and would absorb two false arithmetic facts.

---

## 2. Root cause

`llama3.2` (~3B) is being asked to be, **simultaneously and in a single
free-form turn**, four different things:

1. a **calculator** (do correct multi-step arithmetic/algebra),
2. a **lesson planner** (sequence the concept into steps),
3. a **grader** (judge the student's answer and pick the right encouragement),
4. a **guardrail** (don't leak the answer, don't cave to push-back).

A 3B model cannot hold all four at once, so it hallucinates equations,
miscomputes, and capitulates. **Every viable fix must move work *off* the small
model** rather than expect the 3B to "try harder." The three approaches below do
this in three different ways — at inference time, at the reward level, and at the
weight level.

---

## 3. Approach 1 — Agentic pipeline with a verifier tool

**Idea:** decompose the single monolithic LLM call into a small pipeline of
narrow, specialized steps, and **never let the LLM do arithmetic**.

### Architecture

```
 Photo ──►  qwen2.5vl:7b (OCR / intake)  ──►  problem text
                                              │
                                              ▼
                         ┌────────────────────────────────────────┐
                         │  SOLVER = deterministic tool (SymPy)     │  ← ground truth
                         │  → final answer + canonical step list    │    (no LLM math)
                         └───────────────────┬──────────────────────┘
                                             ▼
                         ┌────────────────────────────────────────┐
                         │  PLANNER agent (llama3.2, 1 call)        │
                         │  verified steps → hidden ordered list    │
                         │  of Socratic sub-questions               │
                         └───────────────────┬──────────────────────┘
                                             ▼   (per student turn)
        student answer ──►  ┌──────────────────────────────────────┐
                            │  GRADER + GUARDRAIL agent             │
                            │  • compare answer vs stored truth     │
                            │  • pick "¡Casi!" vs "¡Excelente!"     │
                            │  • block premature answer reveal      │
                            │  • refuse sycophantic reversal        │
                            └───────────────┬──────────────────────┘
                                            ▼
                            ┌──────────────────────────────────────┐
                            │  TUTOR agent (llama3.2, per turn)     │
                            │  only PHRASES the next question/hint  │
                            │  from the stored plan — never derives │
                            └──────────────────────────────────────┘
```

### Why each failure is fixed

| Observed failure | Fixed by |
|------------------|----------|
| 8 ÷ 6 = "1 y media", 8 ÷ ½ = 8 | Deterministic **solver** — the LLM never computes |
| Wandering value of `x`, self-contradiction | Single **stored ground truth**; tutor only phrases it |
| Wrong concept (subtraction instead of division) | Planner works from the **verified canonical steps** |
| "¡Casi!" / "¡Excelente!" on wrong turns | **Grader** classifies the student answer against truth |
| Sycophantic reversal on push-back | **Guardrail** holds the verified answer and re-guides |

### Fit and cost under the constraint

- **Fits the small model:** each call is narrow enough for a 3B; `qwen2.5vl:7b`
  only does OCR; the CAS covers the 8–14 curriculum (fractions, basic algebra,
  geometry).
- **Runs fully offline** on the teacher's laptop — no training, no GPU, no
  internet.
- **Cost:** engineering effort + higher latency (a few local calls per turn) and
  a dependency on a math engine (e.g. SymPy).

### Verdict
**Highest immediate leverage. Recommended first step** — it removes the
arithmetic and sycophancy bugs today with zero training.

---

## 4. Approach 2 — RLHF / preference optimization (DPO)

**Idea:** fine-tune the *behavior* of `llama3.2` so the pathologies above become
low-probability, using preference learning rather than a bigger model.

### Method

- **Build preference pairs** for the same dialogue context: a **chosen** response
  (one step at a time, correct hint, no answer leak, no capitulation, correctly
  calibrated praise) vs a **rejected** response drawn from the observed failure
  modes (wrong arithmetic, answer reversal, misplaced "¡Casi!").
- **Optimize with DPO** (Direct Preference Optimization) — cheaper and more stable
  than PPO-style RLHF, and practical to run on a modest GPU as a **development-time
  step**.
- **Automate the labels with RLAIF / RLVR** (RL from AI feedback / from
  *verifiable* rewards). The reward function combines:
  - a **math-correctness checker** (verifiable reward — reuse the SymPy solver),
  - a **pacing** check (exactly one step / one question per turn),
  - an **answer-leak** penalty (regex/classifier: did it just give the result?),
  - a **sycophancy** penalty (did the answer change *only* because the student
    pushed back?).

### Fit and cost under the constraint

- **Simplest deployment:** inference stays a **single offline model** — no
  pipeline, no tool calls at runtime.
- Training is a **one-time dev cost** (modest GPU + a labeling setup).
- **Honest caveat:** RLHF/DPO improves *style and control* (sycophancy, pacing,
  calibrated praise) far more than raw *capability*. A 3B still will not be a
  reliable calculator, so **pair it with the verifier tool from Approach 1** for
  the actual math.

### Verdict
Best for eliminating the **behavioral** pathologies (sycophancy, pacing, praise)
while keeping the deployment a single model. Not sufficient on its own for math
correctness.

---

## 5. Approach 3 — Knowledge distillation

**Idea:** create a specialized "Socratic math tutor" 3B by **distilling** the
skill from a large, capable teacher model into `llama3.2`.

### Method

1. **Generate ideal dialogues (dev time, with internet):** use a strong frontier
   teacher model to produce thousands of high-quality Socratic tutoring dialogues
   across the exact target curriculum (fractions, basic algebra, geometry for ages
   8–14).
2. **Filter through the verifier:** drop every dialogue whose math does not pass
   the SymPy checker, so no incorrect reasoning enters the training set.
3. **Supervised fine-tune (SFT)** `llama3.2` on the clean corpus:
   - **Sequence-level / rationale distillation** — teach the small model the
     *hidden reasoning* as well as the *surface question* it should ask.
   - **Context distillation** — fold the long, complex Socratic system prompt
     *into the weights*, so the small model follows the pedagogy reliably without
     depending on a large prompt it currently obeys only loosely.

### Fit and cost under the constraint

- **Single small model at inference**, fully offline — cheap to serve.
- A **domain-distilled** 3B markedly outperforms the general-purpose 3B on this
  one narrow task and can approach much larger models within the domain.
- **Caveat:** quality is entirely bounded by teacher-data quality and the verifier
  filtering; requires **teacher access (internet/API) and a GPU during
  development**. Still math-fragile without a runtime checker.

### Verdict
Best for raising the **base capability** of the tutor so it needs less
orchestration — a strong medium-term investment.

---

## 6. Comparison

| | **1. Agentic + verifier** | **2. RLHF / DPO** | **3. Distillation** |
|---|---|---|---|
| Fixes math errors | ✅ guaranteed (CAS) | ⚠️ only with a checker | ⚠️ better base, still needs checker |
| Fixes sycophancy / pacing / praise | ✅ (guardrail + grader) | ✅ (reward targets them) | ✅ (learned from ideal data) |
| Training required | ❌ none | ✅ dev-time (GPU) | ✅ dev-time (GPU + teacher) |
| Internet needed | ❌ never | ❌ (only for optional AI labels) | ✅ once, to query the teacher |
| Runtime shape | multi-call pipeline | single model | single model |
| Runtime latency | higher (several calls/turn) | low | low |
| Time-to-deploy | **shortest** | medium | longest |
| Main risk | engineering complexity | capability ceiling of a 3B | teacher-data quality |

---

## 7. Recommended roadmap

The three approaches are **complementary, not exclusive**. Pragmatic order:

1. **Ship Approach 1 first** — a SymPy-verified agentic pipeline. It removes the
   arithmetic and sycophancy bugs immediately, with no training and no internet.
2. **Add Approach 3** — distill a better tutor base so the prose needs less
   orchestration and the pedagogy is baked into the weights.
3. **Then Approach 2 (DPO)** — polish residual behavior using preference data you
   will naturally collect from classroom logs.

> **Invariant across all three:** keep the **verifier tool in the loop at inference
> time**. No 3B model — trained however you like — should be trusted to do the
> arithmetic unchecked.

---

## 8. References to related project docs

- Deployment: [Classroom Cloud offline deployment guide](deployment-classroom-cloud.md)
- Scripts under evaluation: `../text.py` (`llama3.2`), `../visual.py` (`qwen2.5vl:7b`)
