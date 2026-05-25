---
name: concilium
description: Ask one Codex agent for a read-only second opinion on a question, then synthesize its response with your own judgment. Use /concilium followed by a prompt.
---

# Concilium: Codex Discussion

Invoke one Codex agent in read-only mode to discuss a question, then produce a final answer.

## Usage

When this skill is invoked with a prompt:

1. **Dispatch one Codex agent** in READ-ONLY mode:

   ```bash
   codex exec --full-auto -m gpt-5.5 --reasoning-effort medium "READ-ONLY: Do not edit, write, or create any files. Only research and respond. <prompt>"
   ```

2. **Collect result**: Wait for the Codex agent to complete.
3. **Synthesize**: Compare the agent response with your own reasoning and create a unified answer that:
   - Identifies the agent's strongest points
   - Adds your own judgment and missing context
   - Resolves weak assumptions
   - Presents a cohesive, actionable response

## Prompt Template

Use the user's original question exactly. Do not modify or paraphrase it.

## Output Format

Present the final synthesized response directly. Do not show the individual Codex response unless the user asks for it.

If the Codex agent fails or times out, answer directly and note that the discussion agent was unavailable.

## Example

User: /concilium Should we refactor this service now or after the release?

1. Dispatch one read-only Codex agent with the prompt
2. Collect its response
3. Synthesize with your own judgment into one final recommendation

## Options

- `--verbose` or `-v`: Show the Codex agent response before synthesis
- `--timeout <seconds>`: Set custom timeout, default 120 seconds
