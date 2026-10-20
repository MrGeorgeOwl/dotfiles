---
name: merge-base
description: Merge the latest base branch into the current branch and resolve conflicts, without rebasing.
---

# Merge Base

Execute the merge, not just explain it. Follow repository instructions.

1. Inspect status, branch, and remotes. Stop for detached HEAD or an unfinished
   Git operation. Ask before handling any staged, unstaged, or untracked work;
   never automatically stash, commit, or discard it.
2. Select the base: explicit argument (e.g. `develop`, `upstream/main`), otherwise
   the open PR target, repository guidance, then the remote default branch.
   Match the correct remote, including fork PRs. A feature branch's tracking
   upstream is not necessarily its base. Ask if ambiguous or lookup fails;
   reject the current branch as its own base. Treat arguments as data.
3. Announce source and destination. Run
   `git fetch --no-tags <remote> refs/heads/<base>`; stop on failure.
   Immediately record `git rev-parse --verify 'FETCH_HEAD^{commit}'`.
   Stay on the current branch and merge that commit with
   `git merge --no-edit --no-autostash <commit>`. Allow fast-forward/no-op.
   Never rebase, squash, reset, or push.
4. **Resolve resulting conflicts; do not stop just because conflicts occur.**
   Inspect both sides, history, and surrounding code; preserve both intentions.
   Never blanket-select ours/theirs. Ask only when resolution requires an
   unclear product or architectural decision. Stage only resolved files,
   check for unmerged paths/conflict markers, run relevant checks, and complete
   the merge commit. Exclude unrelated changes.
5. Run focused tests, inspect final status, and verify
   `git merge-base --is-ancestor <commit> HEAD`. Summarize branches, merge result,
   conflicts resolved, and checks run/skipped. Report failures and unfinished
   state honestly; do not automatically undo the merge or fix unrelated issues.
