---
name: george-code-review
description: Review a branch, PR, or diff against George's code review checklist, mostly for Python backend. Use when George asks for a review. Tests are out of scope; use test-sanitization for them.
---
# George's code review

Review only. Never edit, commit or push unless George asks. Tests are NOT reviewed here.

## 1. Scope
1. Diff the branch against its merge-base (include untracked files). Use that same diff throughout.
2. State the branch intent and what's out of scope in 1–2 sentences. If unclear, ask.
3. Read repo rules: CLAUDE.md, AGENTS.md, Makefile/justfile.
4. Run lint, type check and tests first; note what already fails.

## 2. Read
5. Read the whole diff plus surrounding code. Follow callers, API contracts, DB columns, templates, config (blast radius).
6. Find the one fact that makes the change safe and prove it by running something.

## 3. Checks

**Correctness**
- Intended case works; callers still work; code matches intent.
- Fix targets the root cause. No guard, retry, swallowed error or clamp hiding a bug; every copy of the bug is fixed.
- Missing key/required value raises; never silently `return None`. Optional steps fall back to the old behaviour. Validate at boundaries, trust the inside.

**Scope (Boy Scout rule)**
- Every hunk serves the branch's purpose.
- Leave code the branch touches cleaner than you found it: small tidy-ups (a bad name, dead line, flattened branch) inside touched functions/files are welcome.
- Wider refactors or unrelated fixes go to a separate PR, listed as follow-ups.
- Small commits, one concern each.

**Simplicity: do less**
- No dead code, speculative guards, options-for-later, one-use aliases or wrappers, dirty hacks.
- Nothing re-implements what the repo or stdlib already has.
- All cases go through one path; no special branch for one case. Grow a data structure, not an if/else chain.
- Flat control flow: guard clauses, no chained inline if/else, no dense boolean one-liners, light template logic. Related logic stays together.
- Inline functions and constants used once. A value derived from an object is a property on that object, not a separate helper.
- Remove abstractions with a single implementation unless a second implementation is actually planned or a test needs a fake. Re-adding later is cheap.

**Naming**
- Functions/methods start with a verb; classes, properties, constants, data are nouns.
- Plain words, no jargon, no needless prefixes, nothing called `helper`/`utils`, no near-duplicate names for different things.

**Types**
- No data packed into strings to parse later, no bare tuples, no parallel fields that must stay in sync: use NamedTuple, pydantic model, or Enum. Keep raw values instead of flattening to float/bool.
- Enum for a fixed set of values shared across modules.
- A constant used by only one class is a class attribute.
- Parse external data into types at the boundary.

**Architecture**
- Logic sits in the layer that owns it: validation in the entity or its own validator, business logic in the service/domain layer, not the web layer. Separate concepts are separate entities (SRP, dependency rule).
- One source of truth; no second endpoint or state copy that needs syncing.
- Explicit contracts; no flag arguments switching behaviour.
- Absolute imports; key casing matches the surrounding payload.

**Comments**
- Delete comments that restate code; prefer renaming/reshaping over explaining. Keep license text, outside-constraint notes, public API contracts, issue links.
- Docstrings hold only what the schema/signature can't express.

**Cost and security**
- No added user latency or cost without a measured reason.
- No tokens or secrets in logs; no real IDs or user data in prompts or examples.

## 4. Report
- Verify every finding against the source, ideally by running something; drop what you can't prove. Raise style only when it breaks a rule above.
- Severity: P0/P1 blocker (intended case fails, data loss, security), P2 should-fix (real bug or clear rule violation), P3 nit.
- Each finding: priority, `file:line`, one-sentence problem, failure scenario or rule broken, smallest fix (prefer deleting or narrowing). Sort by priority.
- Sections: **Blocked on me / Changed / Found**. No praise, no restating the PR, plain prose.
- The review must not make the PR bigger; out-of-scope items go under follow-ups.

Optional deep mode: when George asks for a "swarm", run parallel reviewers on different angles, then verify and merge findings.
