# Contributing

1. Open an issue first to describe the bug or idea.
2. Create a branch from `main`, for example `feature/drift-check`.
3. Install dev tools: `pip install -e ".[dev]"`.
4. Make the change and add a test for it.
5. Check locally: `ruff check .`, `ruff format .`, `pytest`.
6. Open a pull request. CI must be green before merging.

Commit messages: one short line in the imperative mood ("Add drift check"),
then an empty line and more detail if needed.
