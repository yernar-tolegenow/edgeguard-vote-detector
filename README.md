# EdgeGuard Vote Detector

[![CI](https://github.com/yernar-tolegenow/edgeguard-vote-detector/actions/workflows/ci.yml/badge.svg)](https://github.com/yernar-tolegenow/edgeguard-vote-detector/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A small Python tool that finds attacks in smart-city utility readings
(electricity, water, heating) and decides how a gateway should react.

It is a cut-down, testable part of my master's thesis:
*Anomaly Detection and Autonomous Threat Mitigation for Smart City IoT
Infrastructure using Edge Computing* (Astana IT University, 2026).

## How it works

```
readings -> causal features -> 3 detectors -> 2-of-3 vote -> state machine -> action
```

1. **Features** use only past samples (no "future data"), like a real gateway.
2. **Three detectors** look at each reading:
   - *Robust Z-score*: is the reading far from the median of recent readings?
   - *Sudden-change test*: did the reading jump sharply from the previous one?
   - *Isolation Forest*: does the reading look unusual across several features?
3. **2-of-3 vote**: a reading is an alarm only if at least two detectors agree.
   One detector alone cannot raise an alarm, which keeps false alarms low.
4. **State machine** turns alarms into actions:

| State | Action | When |
|---|---|---|
| normal | accept | no recent alarms |
| suspect | accept and monitor | one alarm |
| blocked | temporary block | alarms in a row (default 2) |
| quarantine | quarantine | alarms continue (default 5 in a row) |
| recovery | accept and monitor | quiet for a while after a block |

## Install

Python 3.10 or newer is needed.

```bash
git clone https://github.com/yernar-tolegenow/edgeguard-vote-detector.git
cd edgeguard-vote-detector
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Use

Run on built-in synthetic data and print the scores:

```bash
edgeguard demo
```

Example output (seed 42, 3000 samples, scores on the 2000 test samples):

```
method             precision   recall      f1      FAR
robust_z               0.702    0.471   0.563   0.0089
sudden_change          0.824    0.329   0.471   0.0031
isolation_forest       0.426    0.576   0.490   0.0345
vote_2_of_3            0.784    0.471   0.588   0.0057
```

The vote has the best F1 and a lower false-alarm rate (FAR) than the
Isolation Forest alone. Recall is still under 50%: long "level shift" attacks
are hard for the sudden-change test, so the vote often misses their middle part.

Run on your own CSV file:

```bash
edgeguard run examples/sample_stream.csv --column consumption_kw --train 600 --output results/out.csv
```

`--train` is the number of attack-free samples at the start. The Isolation
Forest learns "normal" from them. The output CSV has one row per reading with
each detector's flag, the alarm, the state and the action.

Use it from Python:

```python
from edgeguard.pipeline import run_pipeline
from edgeguard.synthetic import make_utility_stream

stream = make_utility_stream(seed=1)
result = run_pipeline(stream.values, train_size=stream.train_size)
print(result.alarm.sum(), result.actions[-1])
```

## Project layout

```
src/edgeguard/
  features.py     causal features (rolling median/MAD, EWMA, differences)
  detectors.py    robust Z-score, sudden-change test, Isolation Forest
  voting.py       k-of-n vote
  mitigation.py   five-state response machine
  pipeline.py     runs the whole chain
  synthetic.py    test data with labelled attacks
  metrics.py      precision, recall, F1, false-alarm rate
  cli.py          command-line tool
tests/            pytest tests (27 tests)
examples/         sample CSV
.github/workflows CI and release pipelines
```

## Tests and code style

```bash
pytest --cov=edgeguard     # run tests with coverage
ruff check .               # lint
ruff format --check .      # formatting
```

## CI/CD

- [`ci.yml`](.github/workflows/ci.yml) runs on every push and pull request:
  lint, tests on Python 3.10, 3.11 and 3.12, then builds the package and runs
  the demo. The package, coverage report and demo results are kept as artifacts.
- [`release.yml`](.github/workflows/release.yml) runs when a tag like `v0.1.0`
  is pushed: it tests, builds and publishes a GitHub Release with the package files.

## Why these technologies

See [docs/technology-choices.md](docs/technology-choices.md).

## Limits

- The data here is synthetic. The thesis uses UCI Household Power Consumption
  and Edge-IIoTset, which are not included because of their size and licenses.
- Thresholds are fixed. They are not re-tuned when consumption patterns change.
- Speed and memory have not been measured on real gateway hardware.

## License

MIT, see [LICENSE](LICENSE).

## Author

Yernar Tolegenov, group CSE-2504M, Astana IT University.
