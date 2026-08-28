---
name: concilium
description: Ask Codex and Claude agents for read-only second opinions on a question, then synthesize their responses with your own judgment. Use /concilium followed by a prompt.
---

# Concilium: Multi-Agent Discussion

Invoke Codex and Claude agents in read-only mode to discuss a question, then produce a final answer.

## Usage

When this skill is invoked with a prompt:

1. **Dispatch Codex and Claude agents** in READ-ONLY mode with the same prompt and highest available effort:

   ```bash
   codex exec --full-auto -m gpt-5.6-terra "READ-ONLY: Do not edit, write, or create any files. Only research and respond. <prompt>"
   ```

   ```bash
   claude -p --permission-mode plan --effort max "READ-ONLY: Do not edit, write, or create any files. Only research and respond. <prompt>"
   ```

   Run them in parallel when possible.

2. **Collect results**: Wait for both agents to complete.
3. **Synthesize**: Compare both agent responses with your own reasoning and create a unified answer that:
   - Identifies each agent's strongest points
   - Uses Claude's thoughts alongside Codex's in future recommendations and changes
   - Adds your own judgment and missing context
   - Resolves weak assumptions or disagreements
   - Presents a cohesive, actionable response

## Prompt Template

Use the user's original question exactly. Do not modify or paraphrase it.

## Output Format

Present the final synthesized response directly. Do not show the individual Codex or Claude responses unless the user asks for them.

If either agent fails or times out, continue with the available responses and your own judgment, and note which discussion agent was unavailable.

## Example

User: /concilium Should we refactor this service now or after the release?

1. Dispatch read-only Codex and Claude agents with the prompt
2. Collect their responses
3. Synthesize both agents' thoughts with your own judgment into one final recommendation

## Options

- `--verbose` or `-v`: Show the Codex and Claude agent responses before synthesis
- `--timeout <seconds>`: Set custom timeout, default 120 seconds
