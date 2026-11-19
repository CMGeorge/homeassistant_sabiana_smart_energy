# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Issue tracking workflow

- Every bug fix or code change must be tracked by a GitHub issue in this
  repository. Before fixing a problem (including findings from a code review),
  search the existing issues; reuse a matching issue, otherwise create one per
  problem using `.github/ISSUE_TEMPLATE/issue.md` (bugs, label `Bug`) or
  `.github/ISSUE_TEMPLATE/feature_request.md` (features, label
  `Feature Request`).
- Reference the issues in commit messages (`Refs #N`) and close them from the
  pull request description (`Closes #N`), one line per issue. Issues that are
  intentionally not fixed stay open and are listed as `Refs #N` with the reason.
- Call out any change that affects already-configured devices (unique IDs,
  entity states, device names, units, write behavior) in the PR description and
  in the "Upgrade notes" section of `README.md`.

## Checks before committing

- `python3 -m ruff check .` and `python3 -m ruff format --check custom_components tests`
- `python3 -m pytest`
- Keep the string snippets asserted by `tests/test_sensor.py` (two's complement
  handling in `sensor.py` and `number.py`) and `"modbus"` in the manifest
  dependencies (`tests/test_manifest.py`).
