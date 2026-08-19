# Open-Source Release Plan — MathBot (MIT)

**Goal:** extract `mathbot/` into its own independent GitHub repository and prepare
it for public release under the **MIT license**, following software-engineering
best practices for commits, documentation, code structure, and **reproducibility**,
so that other developers can install, run, and contribute to MathBot easily.

This plan builds on the extraction options already discussed (fresh vs.
history-preserving). The recommendation here assumes a **clean initial history**
(fresh start), which is the cleanest base for a public v0.1.0.

---

## 1. Target repository structure

```
mathbot/
├── .github/
│   ├── workflows/ci.yml            # lint + test on push/PR
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── docs/                           # keep the existing guides
│   ├── deployment-classroom-cloud.md
│   ├── socratic-tutor-improvement-approaches.md
│   └── approach1-langgraph-implementation-plan.md
├── src/mathbot/                    # the code becomes a real package
│   ├── __init__.py                 # __version__
│   ├── config.py                   # models + ports from env (no hardcoding)
│   ├── prompts.py                  # the Socratic SYSTEM_PROMPTs (shared)
│   ├── llm.py                      # ollama/langchain helpers + latex cleanup
│   ├── text_app.py                 # was text.py  (exposes main())
│   └── visual_app.py               # was visual.py (exposes main())
├── tests/
│   ├── test_prompts.py
│   └── test_latex.py               # pure-function tests, no Ollama needed
├── .gitignore                      # NEW — .venv/, .gradio/, __pycache__/
├── .python-version                 # pin the interpreter (e.g. 3.11)
├── CHANGELOG.md                    # Keep a Changelog format
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE                         # MIT
├── README.md                       # developer front door
├── pyproject.toml                  # deps + entry points + ruff/pytest config
└── uv.lock                         # already present
```

> **Why `src/` layout:** it prevents accidental imports from the working directory,
> makes the install path identical to what users get, and is the modern Python
> packaging default.

---

## 2. Phase 1 — Minimum for a credible MIT release

1. **`LICENSE`** — standard MIT text with `Copyright (c) 2026 <holder>`. Declare it
   in `pyproject.toml` as `license = "MIT"` + `license-files = ["LICENSE"]`
   (PEP 639) and add an SPDX / OSI classifier so the license is machine-readable,
   not just a file.
2. **Developer-facing `README.md`** — replace the thin blurb with: one-line
   description, a short *what / why*, **badges** (CI, license, Python, uv), a
   **60-second quickstart**, usage, configuration, links into `docs/`, and license.
3. **Own `.gitignore`** — **critical**: the `.venv/` / `.gradio/` rules currently
   live in the *parent* repo and will **not** travel with the extraction.
4. **`.python-version`** — pin the interpreter so `uv` selects the same one
   everywhere.
5. **`CHANGELOG.md`** + git tag **`v0.1.0`** + a **GitHub Release** — a citable,
   versioned starting point.

**Exit criterion:** a stranger can clone, `uv sync`, `uv run`, and see the license,
changelog, and a working quickstart.

---

## 3. Phase 2 — Code structure for reuse

The current `text.py` and `visual.py` **duplicate** the Socratic prompt and chat
plumbing, and **hardcode** model names (`llama3.2`, `qwen2.5vl:7b`) and port `7860`.

- **Move to a `src/mathbot/` package** and factor out shared pieces:
  - `prompts.py` — the system prompts.
  - `llm.py` — `limpiar_latex`, `pil_a_bytes`, and the Ollama / LangChain calls.
  - `config.py` — models and ports read from **environment variables** with sane
    defaults.
- **Add console entry points** in `pyproject.toml`:

  ```toml
  [project.scripts]
  mathbot-text   = "mathbot.text_app:main"
  mathbot-visual = "mathbot.visual_app:main"
  ```

  so anyone can `uv run mathbot-text` or `uv tool install` / `pipx install` it.
- **Packaging tradeoff:** entry points require this to be a **real package**, so
  replace the current `[tool.uv] package = false` with a build backend
  (`hatchling`). This is the right move for "others can use it."
- **Make models/ports configurable** (env vars or CLI flags) instead of hardcoded —
  the single biggest usability win for other deployments.

**Exit criterion:** `uv run mathbot-text` / `mathbot-visual` work; models and ports
are configurable; no duplicated prompt/plumbing.

---

## 4. Phase 3 — Quality & reproducibility

- **Ruff** for lint + format (config in `pyproject.toml`); remove `# type: ignore`
  noise where feasible.
- **Pytest** covering the pure functions (`limpiar_latex`, prompt assembly), with
  `ollama` / `ChatOllama` **mocked** so CI needs **no models**.
- **GitHub Actions CI** (`ci.yml`): `uv sync` → `ruff check` → `pytest` on every
  push / PR. Green checks are a strong trust signal.
- **pre-commit** hooks (ruff) so contributors are auto-formatted.
- **Reproducibility specifics:**
  - `uv.lock` is already committed ✓.
  - Add a **"Models" note** documenting the exact Ollama tags (optionally their
    digests, e.g. `qwen2.5vl:7b@sha256:…`) so readers pull the *same* weights.
  - A `justfile` / `Makefile` with `sync` / `run` / `test` / `lint` targets.

**Exit criterion:** CI is green on a clean machine; tests pass without Ollama;
model versions are documented.

---

## 5. Phase 4 — Community & discoverability

- **`CONTRIBUTING.md`** (uv setup, running tests, commit style),
  **`CODE_OF_CONDUCT.md`** (Contributor Covenant), issue / PR templates.
- **GitHub repo metadata:** clear description + **topics**
  (`ollama`, `gradio`, `langchain`, `education`, `math`, `socratic`, `llm`,
  `offline`).
- Optional **`SECURITY.md`** noting the LAN / `share=True` exposure (already covered
  in the deployment guide).

---

## 6. Commit strategy for the first public push

- **Keep Conventional Commits** (already in use: `docs:`, `build:`) — this enables
  automated changelogs / releases later.
- For v0.1.0, **do not carry the messy extraction history**. Make a small set of
  clean, logical commits that tell the story, then tag:

  ```
  feat: core text & visual Socratic tutors
  refactor: extract shared prompts/llm/config
  build: uv packaging + entry points
  docs: deployment, approaches, and LangGraph plan
  chore: MIT license, CI, tests, community files
  # then:
  git tag v0.1.0
  ```

- This yields a readable history and sidesteps the extraction artifacts (including
  the `.gitignore` commit that a subdirectory history-filter would drop).

---

## 7. Reproducibility summary (what guarantees a clean re-run)

| Concern | Mechanism |
|---------|-----------|
| Same Python | `.python-version` + `requires-python` |
| Same packages | `pyproject.toml` + committed `uv.lock` (`uv sync`) |
| Same models | documented Ollama tags / digests in README |
| Same commands | `uv run mathbot-text` / `mathbot-visual`; `justfile` targets |
| Same checks | GitHub Actions CI (lint + test, no models needed) |
| Runtime deps | Ollama documented as an external prerequisite |

> **Note:** the repo is *source*-reproducible, but Ollama and the model weights
> (~8 GB) remain **external runtime prerequisites** — they are not vendored.

---

## 8. Open decisions

1. **README / docs language** — app + user docs are Spanish (rural-school audience).
   Recommended: **English README** (developer front door) while **keeping the
   Spanish deployment / user guides**, or a bilingual README.
2. **Scope of v0.1.0** — do Phase 1 + Phase 2 together (recommended, makes it
   genuinely reusable) vs. ship Phase 1 with the flat scripts and refactor in
   v0.2.0.
3. **Repo name & visibility** — e.g. `mathbot`, **public** (required for an MIT
   project to be shareable / useful).
4. **Copyright holder** for the LICENSE.

**Recommended path:** extract with a **clean history**, then land **Phase 1 + Phase
2** as the initial **v0.1.0**, with **Phase 3–4** as fast follow-ups.

---

## 9. Related documents

- Deployment: [Classroom Cloud offline deployment guide](deployment-classroom-cloud.md)
- Improvement analysis: [Three approaches to better Socratic tutoring](socratic-tutor-improvement-approaches.md)
- Implementation: [Approach 1 — LangGraph plan](approach1-langgraph-implementation-plan.md)
