All GitHub interactions must be done using the official `gh` CLI tool.

- Use `gh` for all GitHub operations: issues, pull requests, releases, repos, gists, etc.
- Never use raw API calls, curl, or other HTTP clients to interact with GitHub.
- Assume `gh` is already installed and authenticated.

Examples:
- View a PR: `gh pr view <number>`
- List issues: `gh issue list`
- Create a PR: `gh pr create`
- Check CI status: `gh run list`
- Access the API: `gh api <endpoint>`
