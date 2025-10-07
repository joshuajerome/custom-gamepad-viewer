# Repository Guidelines

## Project Structure & Module Organization
- `app.py` builds the FastAPI application, mounts static assets, and wires storage/state helpers.
- `server/` contains API routers (`server/api`), request handlers, and supporting services.
- `core/` hosts backend logic such as theme discovery/validation and shared utilities.
- `ui/` provides HTML, JS, and CSS under `pages/`, `scripts/`, and `styles/`; `controller_css/` exposes layout and dynamic variables.
- `themes/` ships reference skins; `data/` is created at runtime for persisted config and slot files.
- `tests/` mirrors the Python modules with `pytest` suites; use this layout when adding coverage.
- `scripts/setup.sh` / `scripts/setup.ps1` perform first-time environment bootstrap.

## Build, Test, and Development Commands
- `./scripts/setup.sh --build` (macOS/Linux) or `powershell -File .\scripts\setup.ps1 -build` (Windows) creates the virtual environment and installs dependencies.
- `uv run python app.py` starts the auto-reloading dev server on `http://127.0.0.1:8000`.
- `uv run pytest` executes the backend test suite; add `-k pattern` to target specific cases.
- `uv run ruff check` and `uv run mypy .` run linting and type checks expected before submitting a PR.

## Coding Style & Naming Conventions
- Write Python with 4-space indentation, keep lines ≤100 chars (configured via Ruff), and favour type hints on function boundaries.
- Use `snake_case` for modules, functions, and tests; reserve `PascalCase` for classes and `SCREAMING_SNAKE_CASE` for constants.
- Front-end assets should follow lowercase-hyphen names (`ui/scripts/theme-picker.js`) and co-locate CSS/JS per page.
- Let Ruff auto-fix trivial issues (`uv run ruff check --fix`) and ensure `pytest.ini` markers stay in sync with new suites.

## Testing Guidelines
- Add tests under `tests/` mirroring the module path (e.g., `core/themes/...` ⇒ `tests/core/...`).
- Name files `test_*.py` and individual cases `test_*` to enable automatic discovery.
- Prefer fast tests that assert HTTP responses (via `httpx.AsyncClient`) and state changes in `FileStore` / `AppState`.
- Run `uv run pytest` before each push; add theme fixtures under `tests/data` only when required.

## Commit & Pull Request Guidelines
- Follow the existing history format: optional release tag in square brackets, concise scope, and, when applicable, the tracking issue (e.g., `[0.1] Phase 3: UI & Dynamic Styling Integration (#9)`).
- Squash related changes into coherent commits; avoid WIP messages.
- Pull requests should summarise the change, link issues or tasks, and attach UI screenshots or theme previews when front-end assets change.
- Confirm lint, type check, and tests pass before requesting review; mention any follow-up todos explicitly in the PR body.
