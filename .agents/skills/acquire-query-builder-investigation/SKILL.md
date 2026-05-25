---
name: acquire-query-builder-investigation
description: Investigate acquire-mcp-server metrics and query builders. Use when Codex needs to find where an Acquire metric comes from, explain how campaign/ad group/keyword/search-term/custom-conversion query builders work, map tables and joins, debug missing or oddly shaped metric fields, or implement equivalent metric/query logic.
---

# Acquire Query Builder Investigation

Use this skill for `acquire-mcp-server` and adjacent Acquire metric/query-builder work. Keep it focused on tracing metric definitions, source tables, joins, filters, generated SQL, and MCP-visible outputs.

## Workflow

1. Identify the surface first.

- Determine entity level: account, app, campaign, ad group, keyword, search term, creative set, custom conversion, or another registry-backed surface.
- Locate the tool, schema, metric registry, field/template class, filters, order fields, query builder, service layer, and tests before explaining behavior.
- Prefer `rg` over broad browsing. Search by tool name, metric name, field class, output schema field, table name, and JSON path.

2. Trace the metric end to end.

- Record whether each field is metadata, direct table data, joined table data, calculated expression, JSON extraction, custom conversion, or post-processing.
- For calculated metrics, identify numerator, denominator, null/zero handling, aliases, casts, and any rounding or formatting.
- For settings/inheritance metrics, note the source entity level and whether a keyword-level output is actually inherited from ad group or campaign data.
- Check aliases and external names separately from internal registry keys when the user is debugging unexpected output names.

3. Map joins and filters.

- List every table/subquery used, join type, join keys, tenant/org/app/campaign/adgroup scoping, default date filters, and default status filters.
- Call out two-step query patterns, such as summary query selects IDs and granulated query filters by those IDs.
- Check whether filters apply before or after aggregation.
- For JSON fields, identify the source column and exact JSON path.

4. Validate against implementation artifacts.

- Inspect existing snapshots, query-object tests, tool tests, and schema tests before proposing edits.
- When SQL generation depends on `sqlglot`, use the `sqlglot-ast-inspector` skill to inspect how the StarRocks dialect parses or renders the expression.
- Prefer adding or updating focused tests for metric registration, generated query structure, and MCP-visible output.

5. Produce a concrete artifact.

- For analysis-only requests, return a compact table: metric, source, joins, calculation, filters, tests, and implementation notes.
- For implementation requests, modify the smallest registry/template/query-builder surface that owns the behavior and keep output contracts compatible.
- Use fake IDs/placeholders in docs and tests unless the user provided specific real IDs for local debugging.

## Output Checklist

Include only the sections that fit the request:

- Metric or field inventory.
- Source table/subquery map.
- Join map with join types and keys.
- Calculation details in SQL-like form.
- Default and user-provided filters.
- Relevant tests or missing test coverage.
- Recommended implementation path.
