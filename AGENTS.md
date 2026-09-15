# Guidelines and Tips for Agents

## Startup Rule

Read this first. Then read `treaty_docs/next_steps.md` for current work and
`docs/handoff.md` for decisions from the originating conversation. Read
`docs/methods.md` before changing scientific definitions. Do not auto-read every doc.

## Runtime Environment

Python 3.11+. Initial testing uses the existing Conda environment:

```powershell
conda activate sleep_scoring_dash3.0
```

On this machine environments are under `C:\Users\yzhao\miniconda3\envs`.
If activation is unavailable, use `C:\Users\yzhao\miniconda3\condabin\conda.bat`
with `run --no-capture-output -n sleep_scoring_dash3.0` before Python commands.
This borrows installed NumPy/SciPy/pandas/pytest only; never import the scoring app.
For a separate environment, install `python -m pip install -e ".[test]"`.

## Common Tasks

```powershell
python -m pytest --basetemp .pytest_tmp -p no:cacheprovider -q
python scripts/summarize_usable_data.py --help
python scripts/analyze_ne.py --help
treaty validate .
git diff --check
```

Read `git status --short --branch` before edits and preserve user changes.
No automatic commits, pushes, GitHub repository creation, or PRs. Commit only
when requested. Use short behavior-focused commit titles and flat bullets when
multiple requested changes need a body.

## Scientific Invariants

- Final `sleep_scores`: 4 Active Wake, 5 Quiet Wake; one label per second.
- `ne` is processed percentage delta-F/F. Use its saved rate and `start_time`.
- Equal-length windows are for spectra only. NE signal elevation episodes retain natural boundaries.
- Never join disjoint bouts or bridge invalid NE to manufacture usable duration.
- No silent input rewriting, relabeling, normalization, or inverse filtering.
- Keep per-file functions, source audit tables, and pooled per-mouse summaries.
- Pool event rows before medians and weight spectra by window count. No treating
  events/windows as independent mice. Configuration mixtures and duplicate IDs fail.
- Zero counts and missing metrics are different. Missing estimates stay NaN.
- Synthetic tests verify software, not biological validity. Real files are pending.

## When To Update Treaty Docs

After substantive decisions, new reusable evidence, or shared-state changes,
prepend an entry to `treaty_docs/work_log.md` and update `treaty_docs/next_steps.md`.
Verify the local date first. Follow
[work-log discipline](treaty_docs/treaty_conventions.md#work-log-discipline).
Never edit upstream-maintained `treaty_conventions.md` for project customization.

## Branch Handoff Discipline

The new repo starts on local `main`, without a remote. Check current state before
branch work. Keep requested work tested and explicitly delivered or parked; do not
silently switch another repo's branch. See
[branch handoff](treaty_docs/treaty_conventions.md#branch-handoff).

## Updating The Treaty

Installed with `treaty init`, pinned to v0.9.0, with working docs in `treaty_docs/`.
Use `treaty diff`, `treaty update --dry-run`, then `treaty update` when the user asks.
Preserve local guidance and resolve conflicts before committing. This machine has
`C:\Users\yzhao\python_projects\agent_collab_treaty\.venv\Scripts\treaty.exe`.

## Documentation

- `README.md`: setup, inputs, CLI/API usage, output columns.
- `project_overview.md`: architecture and module responsibilities.
- `docs/methods.md`: formulas, exclusions, weighting, units and limitations.
- `docs/handoff.md`: prior agreement, upstream contracts, provisional choices.
- `treaty_docs/next_steps.md`: concrete unfinished work.
- `treaty_docs/work_log.md`: decisions and verified delivery state.
- `treaty_docs/treaty_conventions.md`: generic collaboration mechanics.

## Project-Specific Reminders

No real data are committed. `data/`, `outputs/`, and MAT files are ignored.
Treat IDs as strings; one manifest row per unique recording, no overlapping chunks.
Do not mix conditions into a per-mouse summary without an explicit design.
MAT v7.3 support and graphical event inspection are future work, not current features.
Do not change sibling `sleep_scoring` or MATLAB preprocessing projects for this task.
