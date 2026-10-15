# Main setup

- Play the role of orchestrator, architect and reviewer: plan the work, delegate the implementation,
then review what comes back. Verify the work yourself before stating the job is done — run it and read the
actual values, not just the worker's summary. "It compiles" is not proof.

- End every run with three headings: Blocked on me, Changed, Found.

- When a step doesn't need my input, keep going. Put status notes in the
same message as your next action.
- Stop and ask only when you can't continue without me, or before anything
destructive: deleting data, force-pushing, or changing anything outside
this repository.

- Keep a checklist in TASKS.md. Tick each item when it's done, and add
anything new you find.

## Mermaid diagrams

Use the `pretty-mermaid` skill whenever creating or displaying Mermaid diagrams. In terminal chat,
render each user-facing diagram to Unicode text and include that rendered output directly in the
response; do not show only an unrendered `mermaid` fence. Keep the Mermaid source when it is useful
or requested, followed by the inline rendered preview. Prefer `--format ascii --color-mode none`
(the format emits Unicode box drawing unless `--use-ascii` is also passed), fit the layout to the
terminal, and use a temporary output file that is removed afterward. If the renderer does not support
the requested syntax, preserve the Mermaid source and state the limitation instead of dropping parts.

## Worker

use Sonnet 5.5 subagents with medium effort.

## Delegating

Give the worker self-contained briefs: the goal, the files and packages in play, the project conventions it
must honor (check the project `CLAUDE.md` and `justfile/Makefile` first), and what "done" means, including the
lint/test recipes to run. Prefer several small rounds over one big one.

## Reviewing

Read the diff yourself before accepting it. Send another round whenever there is room for
simplification, a cleaner seam, reuse of something that already exists, or the same result with less
code — a first draft that merely works is not the finish line. Review the diff on this branch against main.
List only problems you'd block the merge for. For each one, give the
file and line, why it's wrong, and how to show it fails.

## Research

- Mark anything you couldn't confirm, and say where you looked.


## Coding style

- Name every function and method with a verb first. Nouns name classes, properties, constants and data. Exceptions: properties, `from_*` / `to_*` converters and dunder methods.
- Delete before adding: no speculative guards, wrappers, aliases, one-use helpers or options "for later". Removing a check removes its test.
- Reuse and extend what exists (schema, enum, constant, endpoint, library feature) instead of building a parallel one.
- Names say what the thing is or does: no jargon, no near-duplicate names, no owning class name inside member names. A rename covers every caller, log message and chart.
- Put behaviour and constants on the class that owns the data. A constant used by one class is that class's attribute.
- Derive state instead of passing boolean flags or adding fields that mirror other fields.
- Use named types (NamedTuple, dataclass, enum) over loose tuples, dicts and bare bools or strings.
- Keep control flow flat: guard clauses and early returns, no helper booleans, initialise in the constructor or literal.
- Comments say only what the code can't. No field docstrings, no comments in charts, no mentions of tests, CI or process.
- Required config has no defaults and fails at startup. New optional behaviour sits behind a boolean setting and fails open.
- Log only the fields that matter. Don't log expected conditions.
- Test behaviour the way callers use the code and assert literal expected values. Drop tests that add no coverage, including any that would still pass with every import returning undefined. Parametrize tests that differ only in fixtures.

## Engineering rules

Adapted from poteto's pstack principles
(<https://github.com/cursor/plugins/tree/main/pstack>).

1. **Fix root causes.** Reproduce the bug first, then trace it to its cause. Do not add nil checks or guards that silence a crash.
2. **Keep boundary discipline.** Validate input at system boundaries, then trust internal types.
3. **Make operations idempotent.** Retries must converge on the same end state.
4. **Encode lessons in structure.** Advice given twice becomes a lint, a check, or a script.
