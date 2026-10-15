# Engineering Rules

Adapted from poteto's pstack principles
(<https://github.com/cursor/plugins/tree/main/pstack>).

1. **Prove it works.** Verify against the real artifact: run it, read the actual value, inspect the diff. "It compiles" is not proof.
2. **Fix root causes.** Reproduce the bug first, then trace it to its cause. Do not add nil checks or guards that silence a crash.
3. **Test behavior, not implementation.** Call code the way its users do and assert literal expected values. If a test would still pass with every import returning undefined, rewrite or delete it.
4. **Keep boundary discipline.** Validate input at system boundaries, then trust internal types.
5. **Make operations idempotent.** Retries must converge on the same end state.
6. **Subtract before you add.** Remove dead weight before building on top of it.
7. **Encode lessons in structure.** Advice given twice becomes a lint, a check, or a script.
