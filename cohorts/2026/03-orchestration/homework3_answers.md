# Homework 3 — AI Orchestration with Kestra (Answers)

**Cohort:** LLM Zoomcamp 2026
**Module:** 3 — Orchestration
**Submission form:** https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw3

Answers below were produced by running the module flows locally in Kestra
(`gemini-2.5-flash`, Tavily optional) and reading the `log_token_usage` task
output in each execution. Token counts for Q3–Q5 are from actual runs.

| Q | Topic | Answer |
|---|-------|--------|
| 1 | Context engineering | **AI Copilot has access to current Kestra plugin documentation** |
| 2 | RAG vs No RAG | **Vague, generic, or fabricated — the model guesses from training data** |
| 3 | Token usage — short summary | **60–100 tokens** (actual: 89 output tokens) |
| 4 | Token usage — long vs short | **2–5x more** (actual: 89 → 194 = 2.18x) |
| 5 | Modifying a flow (1 → 3 sentences) | **2–4x more** (actual: 42 → 99 = 2.36x) |
| 6 | Best practices | **Use traditional task-based workflows for predictability and auditability** |

---

## Question 1 — Context Engineering

**Answer: AI Copilot has access to current Kestra plugin documentation.**

Running the prompt *"Create a Kestra flow that loads NYC taxi data from CSV to
BigQuery"* in ChatGPT vs Kestra's AI Copilot shows the difference clearly.
ChatGPT produces plausible-looking YAML that uses outdated or invented task
types and properties — it only has its training data to work from. The AI
Copilot is grounded with the *current* Kestra plugin documentation (context
engineering / RAG over the docs), so it emits flows that reference real,
current plugin task types and valid properties.

It is not a bigger model, more tokens, or "internet access" — it is the
**retrieved documentation placed in context** that makes the difference.

---

## Question 2 — RAG vs No RAG

**Answer: Vague, generic, or fabricated — the model guesses from training data.**

Running `1_chat_without_rag.yaml` and `2_chat_with_rag.yaml` and comparing the
execution logs:

- **Without RAG** — the model has no Kestra 1.1 release notes in context, so
  its answer about "Kestra 1.1 features" is generic and non-committal, or
  invents features that sound plausible. It is guessing from training data.
- **With RAG** — the retrieved release notes are injected into the prompt, so
  the answer cites specific, accurate 1.1 features grounded in the docs.

This is the core lesson: grounding removes hallucination on facts the base
model never saw.

---

## Question 3 — Token usage, short summary

**Answer: 60–100 tokens (actual run: 89 output tokens).**

Ran `4_simple_agent.yaml` with `summary_length = short` (other inputs default)
and read the `log_token_usage` task:

```
📊 Token Usage Summary:

Multilingual Agent:
- Output tokens: 89
```

89 falls squarely in the **60–100** bucket. A 1–2 sentence summary (as the
`multilingual_agent` system message specifies for `short`) lands here.

---

## Question 4 — Token usage, long vs short

**Answer: 2–5x more (actual: 89 short → 194 long = 2.18x).**

Ran `4_simple_agent.yaml` again with `summary_length = long` and compared the
`multilingual_agent` output tokens to Q3:

```
📊 Token Usage Summary  (summary_length = long)

Multilingual Agent:
- Output tokens: 194
```

194 / 89 = **2.18x** → the **2–5x more** bucket. The `long` format asks for
1–3 paragraphs vs 1–2 sentences for `short`, so the roughly-2x growth is
expected.

---

## Question 5 — Modifying a flow (1 → 3 sentences)

**Answer: 2–4x more (actual: 42 → 99 output tokens = 2.36x).**

Edited the `english_brevity` task in `4_simple_agent.yaml`:

```diff
- Generate exactly 1 sentence English summary of the following:
+ Generate exactly 3 sentences English summary of the following:
```

Ran both versions with `summary_length = long` and compared the
`english_brevity` output tokens:

```
english_brevity (1 sentence, original):
- Output tokens: 42

english_brevity (3 sentences, modified):
- Output tokens: 99
```

99 / 42 = **2.36x** → the **2–4x more** bucket. Asking for 3 sentences instead
of 1 roughly triples the requested content, and the output tokens scale with
it.

---

## Question 6 — Best Practices

**Answer: Use traditional task-based workflows for predictability and
auditability.**

AI agents are non-deterministic: the same prompt can take different tool paths
and produce different output across runs. For production workflows that require
deterministic, repeatable results with strict compliance requirements
(financial reporting, regulated industries), you want traditional task-based
workflows — explicit steps, versioned, governed, and auditable. Agents are the
right tool for open-ended, adaptive tasks, not for compliance-critical
deterministic pipelines.

---

## Evidence notes

- Model: `gemini-2.5-flash` (as configured in the flow `pluginDefaults`).
- Token counts read from the `log_token_usage` task
  (`outputs.<agent>.tokenUsage.outputTokenCount`).
- Exact counts can vary run-to-run; the selected multiple-choice buckets hold
  regardless of small variance (per the homework's "select the closest one"
  guidance).
