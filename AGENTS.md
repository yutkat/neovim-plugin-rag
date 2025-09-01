# Repository Guidelines

## Project Structure & Module Organization
- `scripts/`: Python and Bash utilities for ingest, classification, and PR editing (`fetch_rss.py`, `search.py`, `predict_category.py`, `embedding.py`, `edit_pluginlist.sh`).
- `data/`: Working artifacts (RSS dumps, PR bodies, CSVs) and a checkout of `yutkat/my-neovim-pluginlist/` during CI.
- `chroma_db/`: ChromaDB SQLite store for plugin embeddings.
- `.github/workflows/`: CI for daily discovery, vector DB refresh, and category verification.
- `pyproject.toml`: Python package metadata and dependencies.

## Build, Test, and Development Commands
- Install deps (uses uv): `pip install uv && uv sync`.
- Run RSS fetch: `uv run scripts/fetch_rss.py data/latest_rss.json`.
- Classify candidates: `jq -r '.[].title' data/latest_rss.json | sed 's#^#https://github.com/#' | xargs -I{} uv run scripts/search.py {}`.
- Generate PR body: `cat data/search.json | uv run scripts/predict_category.py > data/pr.md`.
- Create/update embeddings: `uv run scripts/embedding.py data/neovim-plugin-category.csv`.
- Local env vars required: `OPENAI_API_KEY`, `GITHUB_TOKEN`.
- GitHub operations use a GitHub App (no PAT). Configure secrets `APP_ID` and `APP_PRIVATE_KEY` for workflows (Secret names must not start with `GITHUB_`).

## Coding Style & Naming Conventions
- Python 3.12+ targeted; prefer 4‑space indent, type hints, and small, single‑purpose functions under `scripts/`.
- Filenames: snake_case for Python (`predict_category.py`), kebab/snake for shell (`edit_pluginlist.sh`).
- Keep pure functions where feasible; isolate I/O and network calls.

## Testing Guidelines
- No formal test suite yet. Use script‑level checks with small fixtures in `data/` and dry‑runs (`echo | script` pattern).
- When adding tests, prefer `pytest` with `tests/test_*.py`; name tests after script behavior (e.g., `test_search_returns_top_k`).

## Commit & Pull Request Guidelines
- Style: Conventional Commits preferred (e.g., `feat:`, `fix:`, `chore:`). The history includes `chore: update chroma_db data`—match this pattern for data refreshes.
- PRs: include purpose, sample command outputs, and links to related issues. For categorization changes, attach the rendered table (`data/pr-with-header.md`).

## Security & Configuration Tips
- Never commit tokens. Export secrets locally: `export OPENAI_API_KEY=... GITHUB_TOKEN=...`.
- Large artifacts live under `data/` and `chroma_db/`; avoid manual edits—regenerate via scripts.
- CI uses Ubuntu runners; verify locally with `uv run ...` before opening PRs.
