---
name: agents-building
description: "Use when designing, implementing, reviewing, or improving AI agents and agentic workflows, especially market-research-agent features. Applies Anthropic/OpenAI guidance: start simple, choose workflow patterns before autonomy, design tools carefully, add evals, tracing, guardrails, and human checkpoints."
---

# Agents Building

Use this skill when building or reviewing agent systems. Prefer production reliability over impressive autonomy.

## Core principles

- Start with the simplest useful system: single model call, then retrieval/context, then tools, then workflow, then autonomous agent loop only when simpler designs fail.
- Distinguish workflows from agents:
  - Workflow: predefined code path that orchestrates LLM calls and tools.
  - Agent: model dynamically chooses process and tool use over multiple steps.
- Add complexity only when evals or real traces show it improves task success enough to justify latency, cost, and failure surface.
- Keep prompts, tool calls, intermediate outputs, traces, and final decisions inspectable. Avoid framework abstractions that hide model inputs/outputs.
- Treat tool and schema design as product/API design. Tool descriptions, parameter names, examples, constraints, and failure modes are part of the prompt.
- Design every agent around ground-truth feedback: tool result, database result, test result, trace, user confirmation, or explicit failure.
- Treat negative instructions as soft guidance rather than enforcement. Convert prohibitions into positive allowed behavior plus mechanical checks whenever the rule is important.

## Pattern selection

Use the lightest pattern that fits:

- Single call: classification, extraction, rewriting, simple Q&A, or advice with enough context.
- Prompt chain: fixed stages such as plan -> draft -> validate -> final.
- Routing: clear request categories, model routing, domain/scenario dispatch, or permission paths.
- Parallelization: independent subtasks, multiple reviewers, safety checks, or multi-source research.
- Orchestrator-workers: subtasks cannot be predicted ahead of time, such as coding or open-ended research.
- Evaluator-optimizer: output can be improved by explicit critique and criteria are measurable.
- Autonomous agent loop: task is open-ended, tool feedback is available, there are stopping conditions, and the environment is trusted or sandboxed.

## Implementation checklist

- Define the user's success criteria before choosing the architecture.
- Define task boundaries: allowed data, allowed tools, max turns, max cost, max time, and escalation conditions.
- Keep instructions structured and explicit: role, task, context, constraints, output contract, examples, and refusal/escalation rules.
- Use typed, narrow tools with validation at the boundary. Prefer enums, constrained ranges, explicit IDs, dry-run flags, and idempotent operations.
- Add guardrails in layers: input validation, retrieval/content filtering, tool authorization, output validation, and human approval for high-risk actions.
- Add observability before broad rollout: model, prompt version, tool calls, tool results, latency, token/cost, branch taken, errors, and final outcome.
- Build evals from real traces. Include happy paths, ambiguous requests, tool failure, missing context, prompt injection, permission failures, and high-risk actions.
- Prefer deterministic checks where possible. Use LLM-as-judge only with clear rubrics and spot-check against human review.
- Plan for human intervention when failure thresholds are exceeded or actions are high-risk, sensitive, irreversible, or externally visible.

## Negative instructions and hard constraints

LLMs can miss, invert, or forget negated instructions, especially in long agent contexts with many tools and competing goals. Use negative wording only as explanatory text; depend on code, schemas, validators, and tool design for safety, permissions, data boundaries, output format, and business invariants.

Prefer this hierarchy:

- Remove forbidden actions from the action space when possible.
- Enforce authorization, tenant scope, billing limits, and destructive-action checks in code.
- Use typed schemas, enums, grammar/constrained decoding, and deterministic validators for structure and lexical constraints.
- Rephrase important prohibitions as positive contracts: "Only use claims supported by tool results" is better than a generic anti-hallucination warning.
- Place critical constraints close to the active decision point; a long system prompt alone is too weak.
- Add verifier steps for constraints that cannot be made deterministic, and escalate after repeated violations.

Examples:

- Private metrics: make the tool return them only after server-side authorization.
- JSON validity: use structured output, schema validation, and retry/failover.
- Supported claims: require an evidence field per claim and reject outputs with missing evidence.
- Static examples: lint prompts/examples or review tests so they contain fake app IDs and placeholders.

## Market Research Agent guidance

Use these defaults in `market-research-agent` and related market-research projects:

- Preserve the existing Plan -> Execute -> Finalize workflow unless the task explicitly requires a different architecture.
- Prefer scenario agents for simple, single-purpose requests; use domain agents for multi-domain analysis; use finalizer synthesis for complex user-facing reports.
- Keep domain boundaries crisp: market, ASO, ads, trends, and account should have distinct prompts, tool filters, and output expectations.
- Route based on user intent and required data sources rather than vague topic similarity.
- Use parallel domain execution only when domains are independent enough that merging results is safer than serial reasoning.
- Make every report cite or explain the data/tool evidence behind conclusions. Avoid unsupported market claims.
- Use fake app IDs and placeholders in prompts/examples; keep real app IDs, campaign IDs, app names, and customer data out of static prompts.
- Keep user/org authorization and credit/limit checks outside model discretion.
- Treat Slack/Web formatting as finalization concerns; keep domain agents focused on analysis.
- Maintain conversation memory as bounded context. Store durable preferences/facts intentionally as selected memory entries.
- For new tools, test parameter schemas against the active model set. Gemini-compatible schemas must avoid `anyOf`, `oneOf`, and array-typed `type`.
- When changing prompts or routing, add or update autotests with representative market/ASO/ads/account requests.
- For prompt rules phrased as prohibitions, decide whether each rule needs a matching code/schema/test enforcement path. If yes, add the enforcement before relying on the prompt.

## Preferred alternatives

- Prefer routing or a workflow before introducing multi-agent systems.
- Use deterministic code for CRUD, simple lookups, and fixed business logic.
- Keep authorization, tenant scope, billing limits, and destructive actions in code-controlled checks.
- Enforce safety, privacy, tool permissions, output shape, and business rules with code/schema/test controls.
- Expose concise plans, tool traces, evidence, and decisions instead of raw chain-of-thought.
- Improve context, instructions, tools, evals, and routing before considering fine-tuning.
- Keep fragile behavior traceable even when a framework is useful.

## Sources

- Anthropic, "Building effective agents": https://www.anthropic.com/engineering/building-effective-agents
- OpenAI, "A practical guide to building agents": https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/
- Jang et al., "Can Large Language Models Truly Understand Prompts? A Case Study with Negated Prompts": https://arxiv.org/abs/2209.12711
- Truong et al., negation benchmark analysis: https://arxiv.org/abs/2306.08189
- Zhou et al., "Instruction-Following Evaluation for Large Language Models": https://arxiv.org/abs/2311.07911
- Qi et al., "AGENTIF: Benchmarking Instruction Following of Large Language Models in Agentic Scenarios": https://arxiv.org/abs/2505.16944
