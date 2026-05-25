---
name: mcp-building
description: Use when designing, implementing, reviewing, or securing Model Context Protocol servers and tools, especially acquire-mcp-server. Applies MCP tool-interface design, validation, observability, security, tenant isolation, and maintainability practices.
---

# MCP Building

Use this skill when building or reviewing MCP servers, MCP tools, or MCP client integrations.

## Core principles

- Treat MCP as a production API boundary rather than only an agent convenience layer.
- Design tools for model reliability: obvious names, narrow scopes, explicit parameters, examples, and clear failure messages.
- Keep tool schemas easy for models to satisfy. Avoid needless nesting, escaping-heavy payloads, ambiguous unions, and parameters that require hidden counting or inference.
- Validate all inputs server-side. Preserve tenant scope, permissions, metric names, IDs, date ranges, and limits in server-controlled code.
- Prefer read-only and idempotent tools by default. Add dry-run and explicit confirmation semantics for writes or high-risk actions.
- Keep authentication, authorization, rate limits, and organization scoping outside model control.
- Treat negative call/exposure/query instructions as advisory only. Enforce forbidden actions in server-side code, schemas, allowlists, and authorization checks.
- Log enough to debug tool usage without leaking secrets or customer data.
- Test with real MCP clients and direct protocol calls. Add regression tests for both schema compatibility and business behavior.

## Security checklist

- Threat-model prompt injection, tool poisoning, credential leakage, confused-deputy behavior, cross-tenant data access, over-broad tools, and unsafe defaults.
- Inspect tool descriptions as an attack surface. Keep them limited to reviewed tool-use guidance and exclude hidden instructions, unrelated policy, and unreviewed text from external sources.
- Keep credentials scoped to the minimum required resources. Expose only narrow capability-specific handles to tools.
- Enforce allowlists for metrics, dimensions, filters, ordering fields, and operations.
- Cap result size, date range, query cost, concurrency, and execution time.
- Normalize and validate paths/URLs/IDs if tools touch external resources.
- Return structured errors that help the agent recover without exposing internals.
- Convert every critical negative instruction into a hard control: unavailable tool, denied permission, rejected parameter, constrained output schema, deterministic validator, or human approval gate.
- Add static analysis and MCP-specific checks where possible; traditional vulnerability scans miss MCP-specific issues such as tool poisoning.
- Review open-source MCP servers before adopting them. Research found both traditional vulnerabilities and MCP-specific vulnerabilities in public MCP servers.

## Tool design checklist

- Tool name is verb+noun and maps to one user intention.
- Description says when the tool fits and which adjacent cases belong elsewhere.
- Each parameter has a type, constraints, and business meaning.
- Defaults are documented and safe.
- Output contract is stable and minimal.
- Errors are typed or consistently shaped.
- Examples use fake IDs and placeholders, with real customer/app/campaign data kept out of static docs and tests.
- Pagination or limits are explicit for list-like tools.
- Time handling is explicit: timezone, date format, inclusive/exclusive boundaries.
- Tests cover schema, validation, normal output, empty output, unauthorized access, bad filters, bad dates, and result limits.
- Tests include adversarial calls that ask the model/tool to violate prohibitions, such as unauthorized tenant access, unregistered metrics, excessive date ranges, hidden/debug fields, and raw SQL.

## acquire-mcp-server guidance

Use these defaults in `acquire-mcp-server`:

- Preserve organization scoping as a hard middleware/service concern. Derive tenant scope from authenticated context.
- Keep StarRocks access behind query builders and typed parameter/metric/filter registries. Expose narrow business tools instead of raw SQL.
- Prefer explicit allowlists for campaign metrics, keyword metrics, filter fields, ordering fields, operators, and granularities.
- Keep tool outputs compact: return only requested metrics and needed metadata. Avoid dumping entire rows or debug internals.
- Use fake IDs and placeholder names in docs, tests, and tool examples.
- Keep date defaults safe and visible, such as bounded recent windows, and reject unbounded expensive queries.
- For top-N time series, keep the two-step pattern: total query identifies IDs, granulated query filters by those IDs.
- Preserve Gemini-compatible schemas when acquire tools are consumed by market-research-agent: avoid `anyOf`, `oneOf`, and array-typed `type`.
- Add unit tests for query object generation and tool tests for MCP-visible behavior. Snapshot SQL only when stable and intentionally reviewed.
- Add negative/adversarial tests for business invariants: unknown metric, duplicate metric, unsupported operator, invalid ordering field, cross-org app ID, over-limit result request, excessive date range, and attempts to request internal/debug fields.
- Run the project checks appropriate to the change: `uv run ruff`, `uv run mypy`, `uv run pytest`, or the repository `just`/`make` equivalents when present.
- Use `mcpsnag` or direct MCP protocol calls to verify tools/list and tools/call behavior after schema or transport changes.
- Monitor Sentry/Logfire/Prometheus-style signals for tool latency, errors, result sizes, auth failures, and database failures.

## Preferred alternatives

- Build narrow business tools rather than generic SQL execution tools for business users or agents.
- Split broad multi-mode tools into separate narrow tools when that improves clarity.
- Accept metric/filter names only after registry validation.
- Return bounded, task-shaped result sets.
- Represent security and tenant boundaries in server-side code, with tool-description text as supporting documentation.
- Put business logic in validators, query builders, or service code.
- Review source, dependencies, permissions, and tool descriptions before adopting third-party MCP servers.

## Sources

- Anthropic, "Building effective agents": https://www.anthropic.com/engineering/building-effective-agents
- OpenAI, "A practical guide to building agents": https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/
- Jang et al., "Can Large Language Models Truly Understand Prompts? A Case Study with Negated Prompts": https://arxiv.org/abs/2209.12711
- Zhou et al., "Instruction-Following Evaluation for Large Language Models": https://arxiv.org/abs/2311.07911
- Geng et al., "JSONSchemaBench: A Rigorous Benchmark of Structured Outputs for Language Models": https://arxiv.org/abs/2501.10868
- Narajala and Habler, "Enterprise-Grade Security for the Model Context Protocol": https://arxiv.org/abs/2504.08623
- Hasan et al., "Model Context Protocol (MCP) at First Glance": https://arxiv.org/abs/2506.13538
