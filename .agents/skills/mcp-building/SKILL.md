---
name: mcp-building
description: Use when designing, implementing, reviewing, or securing Model Context Protocol servers and tools, especially acquire-mcp-server. Applies MCP tool-interface design, validation, observability, security, tenant isolation, and maintainability practices.
---

# MCP Building

Use this skill when building or reviewing MCP servers, MCP tools, or MCP client integrations.

## Core principles

- Treat MCP as a production API boundary, not only an agent convenience layer.
- Design tools for model reliability: obvious names, narrow scopes, explicit parameters, examples, and clear failure messages.
- Keep tool schemas easy for models to satisfy. Avoid needless nesting, escaping-heavy payloads, ambiguous unions, and parameters that require hidden counting or inference.
- Validate all inputs server-side. Never trust the model or client to preserve tenant scope, permissions, metric names, IDs, date ranges, or limits.
- Prefer read-only and idempotent tools by default. Add dry-run and explicit confirmation semantics for writes or high-risk actions.
- Keep authentication, authorization, rate limits, and organization scoping outside model control.
- Log enough to debug tool usage without leaking secrets or customer data.
- Test with real MCP clients and direct protocol calls. Add regression tests for both schema compatibility and business behavior.

## Security checklist

- Threat-model prompt injection, tool poisoning, credential leakage, confused-deputy behavior, cross-tenant data access, over-broad tools, and unsafe defaults.
- Inspect tool descriptions as an attack surface. They can steer model behavior and should not contain hidden instructions, unrelated policy, or unreviewed text from external sources.
- Keep credentials scoped to the minimum required resources. Do not expose raw secrets, connection strings, or unrestricted SQL to tools.
- Enforce allowlists for metrics, dimensions, filters, ordering fields, and operations.
- Cap result size, date range, query cost, concurrency, and execution time.
- Normalize and validate paths/URLs/IDs if tools touch external resources.
- Return structured errors that help the agent recover without exposing internals.
- Add static analysis and MCP-specific checks where possible; traditional vulnerability scans miss MCP-specific issues such as tool poisoning.
- Review open-source MCP servers before adopting them. Research found both traditional vulnerabilities and MCP-specific vulnerabilities in public MCP servers.

## Tool design checklist

- Tool name is verb+noun and maps to one user intention.
- Description says when to use the tool and when not to use it.
- Each parameter has a type, constraints, and business meaning.
- Defaults are documented and safe.
- Output contract is stable and minimal.
- Errors are typed or consistently shaped.
- Examples use fake IDs and placeholders, never real customer/app/campaign data.
- Pagination or limits are explicit for list-like tools.
- Time handling is explicit: timezone, date format, inclusive/exclusive boundaries.
- Tests cover schema, validation, normal output, empty output, unauthorized access, bad filters, bad dates, and result limits.

## acquire-mcp-server guidance

Use these defaults in `acquire-mcp-server`:

- Preserve organization scoping as a hard middleware/service concern. Never let model-provided arguments choose tenant scope.
- Keep StarRocks access behind query builders and typed parameter/metric/filter registries. Do not expose raw SQL tools.
- Prefer explicit allowlists for campaign metrics, keyword metrics, filter fields, ordering fields, operators, and granularities.
- Keep tool outputs compact: return only requested metrics and needed metadata. Avoid dumping entire rows or debug internals.
- Use fake IDs and placeholder names in docs, tests, and tool examples.
- Keep date defaults safe and visible, such as bounded recent windows, and reject unbounded expensive queries.
- For top-N time series, keep the two-step pattern: total query identifies IDs, granulated query filters by those IDs.
- Preserve Gemini-compatible schemas when acquire tools are consumed by market-research-agent: avoid `anyOf`, `oneOf`, and array-typed `type`.
- Add unit tests for query object generation and tool tests for MCP-visible behavior. Snapshot SQL only when stable and intentionally reviewed.
- Run the project checks appropriate to the change: `uv run ruff`, `uv run mypy`, `uv run pytest`, or the repository `just`/`make` equivalents when present.
- Use `mcpsnag` or direct MCP protocol calls to verify tools/list and tools/call behavior after schema or transport changes.
- Monitor Sentry/Logfire/Prometheus-style signals for tool latency, errors, result sizes, auth failures, and database failures.

## What to avoid

- Do not build a generic SQL execution MCP tool for business users or agents.
- Do not make one tool with many modes when separate narrow tools would be clearer.
- Do not accept model-generated metric/filter names without registry validation.
- Do not return unbounded rows to let the agent "figure it out."
- Do not bury business logic in prompt text when it belongs in validators, query builders, or service code.
- Do not install or trust third-party MCP servers without reviewing source, dependencies, permissions, and tool descriptions.

## Sources

- Anthropic, "Building effective agents": https://www.anthropic.com/engineering/building-effective-agents
- OpenAI, "A practical guide to building agents": https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/
- Narajala and Habler, "Enterprise-Grade Security for the Model Context Protocol": https://arxiv.org/abs/2504.08623
- Hasan et al., "Model Context Protocol (MCP) at First Glance": https://arxiv.org/abs/2506.13538
