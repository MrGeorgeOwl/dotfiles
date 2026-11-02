---
name: test-sanitization
description: Review and simplify tests related to the current branch diff against its base. Group related tests and remove tests with no value.
---

# Test Sanitization

Apply the edits. Follow repository instructions.
Preserve user changes. Do not change production behavior.

## Scope

1. Inspect the branch and working tree.
2. Select the base from the user request, PR target, repository guidance, or remote default, in that order.
   Ask if the base is unclear.
3. Read `git diff <base>...HEAD`.
4. Review tests for the changed behavior, including unchanged test files.
   Read the relevant code and fixtures.
   Do not clean up unrelated tests.

## Clean up

1. **Remove tests with no value.**
   Remove tests that still pass when the behavior they claim to check is broken.
   Remove tests that add no coverage over the retained ones, including duplicates.
   Replace tests of private helpers or implementation details with tests through the public interface.
   Tests must survive a refactor that keeps behavior.
   Keep distinct boundary, error, and regression cases.
   Keep a test if its value is uncertain.
2. **Merge equivalent tests.**
   Use `pytest.mark.parametrize` when the call and assertion are the same and only fixtures or inputs differ.
   Preserve each distinct case, fixture behavior, and test mark.
   Do not add branches to combine different behaviors.
3. **Group related tests.**
   Put tests for the same class or idea in one test class.
   Reuse an existing class when it fits.
   Preserve test isolation.
4. **Shorten names.**
   Review all remaining test names in scope.
   Let the class name state the subject.
   Let the test name state the behavior.
   For example, use `TestInvoiceParser.test_rejects_empty_input`.
   Keep names clear and unique.
5. **Prefer fixtures over helpers.**
   Turn setup helper functions into fixtures.
   Use `@pytest.mark.usefixtures` when a test needs only a fixture's side effect.
   Fold a fixture into the fixture that is its only user.
6. **Snapshot whole outputs.**
   Replace piecewise assertions on one output, such as a generated query, with a snapshot of the whole output.
   Use the project's snapshot tool. Regenerate snapshots with it and never edit them by hand.
7. **Mirror the source layout.**
   Test `src/foo/bar.py` in `tests/foo/test_bar.py`.
   Move shared fixtures to the nearest common `conftest.py`.
8. **Fix test hygiene.**
   Make tests fast, independent, repeatable, and self-validating.
   Assert results instead of leaving anything to check by hand.
   Replace real app ids, campaign ids, and app names with fake ones.

## Verify and report

1. Check the diff for lost coverage and unrelated edits.
   Confirm that risky logic in the branch diff, such as thresholds, fallbacks, and escaping, has a test that fails without it.
   Add the test if it is missing.
2. Run the project's test and lint recipes for the changed test files.
   Include affected tests when shared fixtures or helpers change.
   Use the full recipe if file selection is not supported.
3. Confirm that moved and parameterized tests are collected.
4. Fix failures caused by these edits.
   Run the checks again after fixes.
5. Report what was removed, merged, grouped, renamed, moved, and added.
   Give reasons for removals.
   Name the retained tests for duplicates.
6. List check commands and results.
   Report failures and skipped checks clearly.
