# Technology choices

| Choice | Why | Alternatives considered |
|---|---|---|
| Python 3.10+ | The thesis notebooks are in Python. It has the best science libraries and is easy to read. | R (weaker for systems code), C++ (fast but slow to write and test) |
| NumPy | Fast arrays for the rolling features. Small and stable. | pandas (heavier, not needed for one column) |
| scikit-learn | Ready, well-tested Isolation Forest with a fixed random seed. | PyOD (more methods, more dependencies) |
| Standard library `csv` and `argparse` | No extra dependencies for input, output and the command line. | pandas, Click |
| pytest + pytest-cov | Short tests, clear failure messages, coverage report. | unittest (more boilerplate) |
| ruff | One fast tool for linting and formatting. | flake8 + black + isort (three tools) |
| setuptools + `pyproject.toml` | Standard packaging, builds a wheel that installs the `edgeguard` command. | Poetry (extra tool to learn) |
| Git + GitHub | Required by the assignment; issues, releases and Actions in one place. | GitLab (also good, has its own CI) |
| GitHub Actions | Free for public repositories, lives next to the code, easy YAML. | GitLab CI, Jenkins (needs its own server) |
| MIT license | Short and permissive; others can reuse the code with credit. | Apache-2.0, GPL-3.0 |

Rule used: pick the smallest set of mature tools that the thesis already uses,
so the module stays light enough for an edge gateway (thesis requirement NFR3).
