# LLM Zoomcamp 2026 — Homework 3: AI Orchestration with Kestra

Submission form: https://courses.datatalks.club/llm-zoomcamp-2026/homework/hw3

This module is hands-on: the questions are answered by running Kestra flows
locally (Docker) with a Google Gemini API key and reading the execution logs.
Setup follows the module's
[Setup lesson](../../../03-orchestration/lessons/03-setup.md).

## Answers

| Q | Topic | Answer |
|---|-------|--------|
| 1 | Context engineering (ChatGPT vs AI Copilot) | **AI Copilot has access to current Kestra plugin documentation** |
| 2 | RAG vs No RAG | **Vague, generic, or fabricated — the model guesses from training data** |
| 3 | Token usage, short summary (`multilingual_agent` output) | run-dependent — see note below |
| 4 | Token usage, long vs short | run-dependent — see note below |
| 5 | Modifying a flow (1 → 3 sentences) | run-dependent — see note below |
| 6 | Best practices (regulated/deterministic workflows) | **Use traditional task-based workflows for predictability and auditability** |

### Reasoning for the conceptual answers

- **Q1.** ChatGPT writes plausible-but-outdated YAML because it only has its
  training data. Kestra's AI Copilot is grounded with the *current* plugin
  documentation (context engineering / RAG over the docs), so it produces
  flows that use real, current task types and properties.
- **Q2.** Without RAG the model has no Kestra 1.1 release notes in context, so
  it guesses from training data — the answer is vague/generic or fabricated.
  With RAG it cites the actual release notes.
- **Q6.** Agents are non-deterministic. Regulated, audit-heavy workflows
  (financial reporting, etc.) need predictable, repeatable, auditable runs —
  i.e. traditional task-based workflows, not agents.

### Run-dependent answers (Q3–Q5)

These depend on the live Gemini run; read the `log_token_usage` task output.
Note `gemini-2.5-flash` may include reasoning ("thinking") tokens in
`outputTokenCount`, so confirm from your own logs and pick the closest option.

- **Q3** — `4_simple_agent.yaml`, `summary_length = short`. Look at
  `multilingual_agent` **output** tokens. Expected: a 1–2 sentence summary,
  most likely **60–100 tokens** (could land in 200–400 if reasoning tokens are
  counted — check the log).
- **Q4** — same flow, `summary_length = long`, compare `multilingual_agent`
  output tokens to Q3. A 1–3 paragraph summary vs 1–2 sentences → expected
  **2–5x more**.
- **Q5** — using the modified flow in this folder, `english_brevity` now asks
  for **3 sentences** instead of 1. Run with `summary_length = long` and
  compare `english_brevity` output tokens to the original 1-sentence version
  (also `long`). 3 sentences vs 1 → expected **2–4x more**.

## Q5 change

The only code change for this homework is in `english_brevity` inside
[`4_simple_agent.yaml`](./4_simple_agent.yaml):

```diff
- Generate exactly 1 sentence English summary of the following:
+ Generate exactly 3 sentences English summary of the following:
```

## How to reproduce

1. Start Kestra and import the flows from `03-orchestration/flows/`
   (see the Setup lesson). Configure secrets:
   ```bash
   export SECRET_GEMINI_API_KEY=$(echo -n "your-gemini-api-key" | base64)
   ```
2. Q3: run `4_simple_agent.yaml` with `summary_length = short`, read
   `log_token_usage`.
3. Q4: run again with `summary_length = long`, compare.
4. Q5: replace `4_simple_agent.yaml` with the version in this folder (1 → 3
   sentences), run with `summary_length = long`, compare `english_brevity`
   output tokens to the original.
