# Learning Notes — Module 3: AI Orchestration (Kestra)

**Cohort:** LLM Zoomcamp 2026 · **Module:** 3 — Orchestration
A working wiki entry: what the module covers, what I actually observed running
the flows, and where it connects to enterprise delivery and certification.

---

## 1. What Kestra is and why it exists

**Kestra** is an open-source orchestration platform. You declare workflows
("flows") in **YAML**: a flow has `inputs`, an ordered list of `tasks`, and
reusable `pluginDefaults`. Everything is versioned, governed, and auditable,
and it runs the same way every time.

**Why it exists:** as soon as an LLM app is more than a single call, you have a
*pipeline* — fetch data, embed, retrieve, call a model, parse, log, branch on
the result. Doing that in an ad-hoc script gives you no retries, no history, no
audit trail, and no separation between "what runs" and "the secrets it needs."
An orchestrator gives you:

- **Declarative structure** — the flow *is* the documentation of what happens.
- **Observability** — every execution has logs, timing, and per-task output.
- **Secrets management** — keys come from env vars (`SECRET_*`, base64), never
  committed to Git.
- **Reproducibility** — same flow + same inputs → same steps.

Kestra's philosophy is "start simple and grow as needed": a basic flow takes
minutes; you add Python, Docker, branching, or AI tasks only when the problem
demands it.

Core AI building block in this module: `io.kestra.plugin.ai.agent.AIAgent`,
backed by a provider (here `GoogleGemini`, `gemini-2.5-flash`).

---

## 2. RAG vs no-RAG (with observed output)

The module contrasts `1_chat_without_rag.yaml` and `2_chat_with_rag.yaml`,
asking each about **Kestra 1.1 features**.

- **No-RAG** — the model answers from training data alone. For a release it
  never saw, the response is **vague, generic, or fabricated** — it guesses.
- **RAG** — the release notes are retrieved and injected into the prompt, so
  the answer is **specific and accurate, grounded in the documentation**.

This is also the mechanism behind **Q1's** result: Kestra's AI Copilot beats
raw ChatGPT at writing flows not because it is a bigger model, but because it
retrieves the **current plugin documentation** into context. Same principle,
two surfaces.

**Takeaway:** RAG is context engineering. The model's quality ceiling on
factual, fast-moving topics is set by *what you put in the context window*, not
by the base weights.

---

## 3. AI agents vs traditional workflows — when to use each

An **AI agent** (`AIAgent`) is given a system message, a prompt, and optionally
**tools**, and it *decides autonomously* which tools to call and when. That was
the point of the agent flows: the workflow designer does **not** hard-code the
tool order in YAML — the agent chooses based on the prompt and system message.

| | Traditional task workflow | AI agent |
|---|---|---|
| Control flow | Explicit, authored in YAML | Model decides at runtime |
| Determinism | High — same steps every run | Low — path can vary |
| Auditability | Strong | Weaker (non-deterministic) |
| Best for | Compliance, ETL, reporting | Open-ended, adaptive tasks |

**Decision rule (this is Q6):** for deterministic, repeatable, compliance-heavy
work (financial reporting, regulated industries) → **traditional task-based
workflows**. Reach for agents when the task is genuinely open-ended and the
adaptivity is worth giving up repeatability. Many real systems are **hybrid**:
deterministic orchestration on the outside, a bounded agent step on the inside.

---

## 4. Token usage and cost monitoring

Every `AIAgent` output exposes `tokenUsage` with
`inputTokenCount` / `outputTokenCount` / `totalTokenCount`. The
`4_simple_agent.yaml` flow logs these in a `log_token_usage` task — a simple,
powerful habit: **make cost observable inside the pipeline itself.**

Observed on actual runs (`gemini-2.5-flash`):

| Run | Agent | Output tokens |
|-----|-------|---------------|
| `summary_length = short` | multilingual_agent | 89 |
| `summary_length = long` | multilingual_agent | 194 (**2.18x** short) |
| `english_brevity`, 1 sentence | english_brevity | 42 |
| `english_brevity`, 3 sentences | english_brevity | 99 (**2.36x**) |

**Lessons:**
- Output length is driven by the **prompt's format instructions** ("1 sentence"
  vs "3 sentences"; "short" vs "long"), and cost scales roughly linearly with
  it.
- Output tokens are usually the expensive side of the bill — controlling
  verbosity is a direct cost lever.
- Logging token usage per task turns cost from an end-of-month surprise into a
  per-execution metric you can alert on.

---

## 5. Multi-agent patterns

`6_multi_agent_research.yaml` shows the **agent-as-tool** pattern:

- **Main agent (Analyst)** — orchestrates, synthesizes findings, and emits a
  structured JSON report.
- **Research agent (Tool)** — a specialized agent exposed to the main agent as
  a *tool* (`io.kestra.plugin.ai.tool.AIAgent`), using Tavily web search to
  gather current company data.

The main agent **delegates** the research subtask to the research agent, which
returns concise factual data; the main agent then structures the output. This
gives **modularity and separation of concerns** — each agent has one job, a
focused system message, and its own provider config.

**Pattern vocabulary:** orchestrator/worker (a.k.a. supervisor + sub-agents),
tool-use delegation, structured-output contract (the analyst is forced to emit
valid JSON only). These generalize far beyond Kestra.

---

## 6. SA Connection — orchestration in enterprise AI delivery

How this shows up when architecting AI for enterprise customers:

- **Orchestration is the productionization story.** Notebooks demo; pipelines
  ship. Retries, scheduling, secrets, lineage, and audit logs are what move a
  RAG/agent prototype into a governed production system.
- **Governance & compliance by design.** Declarative YAML + versioning + secret
  injection + per-task logs is exactly what security and audit teams ask for.
  The Q6 lesson — deterministic workflows for regulated work — is a
  conversation SAs have constantly.
- **Cost transparency.** Per-task token logging maps directly to FinOps /
  unit-economics questions ("what does one run of this cost, and where?").
- **Hybrid architectures.** The credible enterprise pattern is deterministic
  orchestration wrapping bounded agent/LLM steps — not "agents everywhere."
  Being able to draw that line is core SA judgment.
- **Vendor-neutral framing.** The provider here is Gemini, but the pattern
  (agent + tools + retrieval + structured output + observability) is identical
  when the model behind it is Claude. Orchestration is where model choice
  becomes a swappable configuration detail.

---

## 7. Certification relevance — Anthropic Claude Architect

Flags for topics in this module that map to Claude Architect-style competencies
(verify against the current official exam guide before relying on these):

- 🟢 **Agents & tool use** — when to give a model tools vs author explicit
  steps; how autonomous tool selection works. *(High relevance.)*
- 🟢 **Context engineering / RAG** — grounding answers in retrieved docs;
  why retrieval beats a bigger model for fresh facts. *(High relevance.)*
- 🟢 **Deterministic vs agentic design** — choosing predictable workflows for
  compliance-critical use cases. *(High relevance — recurring architecture
  judgment.)*
- 🟡 **Multi-agent orchestration** — orchestrator/worker, agent-as-tool,
  structured-output contracts. *(Medium — pattern literacy.)*
- 🟡 **Cost & token monitoring** — reasoning about input/output token economics
  and observability. *(Medium — operational maturity.)*
- ⚪ **Tool specifics (Kestra/Gemini)** — the *platform* is unlikely to be
  tested; the *transferable patterns* above are what matter. Re-map each to
  Claude's tool-use / MCP / agent SDK equivalents when studying.

---

## Quick reference

- Flow anatomy: `inputs` → `tasks` → `pluginDefaults`; secrets via
  `{{ secret('NAME') }}` from `SECRET_*` env vars (base64).
- AI task: `io.kestra.plugin.ai.agent.AIAgent` with `systemMessage`, `prompt`,
  optional `tools`, and a `provider`.
- Token usage: `outputs.<task>.tokenUsage.{input,output,total}TokenCount`.
- Golden rule: deterministic where you must, agentic where it pays off.
