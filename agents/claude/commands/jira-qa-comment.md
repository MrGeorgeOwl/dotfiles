---
description: "Draft and post a QA-focused comment on a Jira ticket describing changes introduced in the current branch. Usage: /jira-qa-comment <TICKET-KEY> [base-branch]"
allowed-tools: Bash, Read, Glob, Grep, mcp__claude_ai_Atlassian__getJiraIssue
---

You will be given a Jira ticket key (e.g. PROJ-123) and optionally a base branch to compare against. If no base branch is provided, use `main` or `master` (whichever exists in the repo).

1. Fetch the Jira issue using the Atlassian MCP tool to understand the task context (summary, description, linked docs). Also read any existing comments on the issue — use them to understand what has already been noted and avoid repeating information already covered.

2. Run `git diff <base-branch>...HEAD --stat` to get an overview of changed files.

3. Explore the key changed files to understand what was added from a user perspective. Look for:
   - New or modified user-facing entry points (API endpoints, CLI commands, MCP tools, UI screens, etc.)
   - Documentation changes that describe new behavior
   - Schema or response shape changes

4. Draft a comment targeted at QA. Focus entirely on user-facing changes — what new functionality is available, how to invoke it, what inputs it accepts, and what the output looks like. Do not mention implementation details, internal refactors, or infrastructure changes. Do not repeat information already covered in existing comments. Adapt the structure to what fits the changes best, for example:
   - Brief intro sentence
   - Feature or endpoint/tool name and description
   - Parameters or inputs
   - Response or output structure
   - Any other information that would be valuable from a QA perspective

5. Show the drafted comment to the user. Do not post it.
