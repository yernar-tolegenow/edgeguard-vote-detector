"""Command-line interface.

    edgeguard demo                     run on built-in synthetic data and print scores
    edgeguard run data.csv --column kw run on your own CSV and write a result CSV
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

from . import __version__
from .metrics import scores
from .pipeline import PipelineConfig, run_pipeline
from .synthetic import make_utility_stream


def _config_from_args(args: argparse.Namespace) -> PipelineConfig:
    return PipelineConfig(window=args.window, k=args.k, seed=args.seed)


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--window", type=int, default=96, help="history length in samples (default 96)")
    p.add_argument("--k", type=int, default=2, help="detectors that must agree (default 2)")
    p.add_argument("--seed", type=int, default=42, help="random seed (default 42)")


def read_column(path: Path, column: str) -> np.ndarray:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or column not in reader.fieldnames:
            raise ValueError(f"column '{column}' not found in {path}")
        return np.array([float(row[column]) for row in reader])


def cmd_demo(args: argparse.Namespace) -> int:
    stream = make_utility_stream(n=args.n, seed=args.seed)
    result = run_pipeline(stream.values, stream.train_size, _config_from_args(args))
    test = slice(stream.train_size, None)
    report = {name: scores(stream.labels[test], f[test]) for name, f in result.flags.items()}
    report["vote_2_of_3"] = scores(stream.labels[test], result.alarm[test])
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{'method':<18}{'precision':>10}{'recall':>9}{'f1':>8}{'FAR':>9}")
        for name, s in report.items():
            print(
                f"{name:<18}{s['precision']:>10.3f}{s['recall']:>9.3f}"
                f"{s['f1']:>8.3f}{s['false_alarm_rate']:>9.4f}"
            )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    values = read_column(Path(args.input), args.column)
    train = args.train if args.train else len(values) // 3
    result = run_pipeline(values, train, _config_from_args(args))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["index", "value", *result.flags.keys(), "alarm", "state", "action"])
        for i, v in enumerate(values):
            w.writerow(
                [
                    i,
                    v,
                    *(int(f[i]) for f in result.flags.values()),
                    int(result.alarm[i]),
                    result.states[i].value,
                    result.actions[i].value,
                ]
            )
    print(f"wrote {len(values)} rows to {out} ({int(result.alarm.sum())} alarms)")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="edgeguard", description=__doc__.splitlines()[0])
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="run on synthetic data and print scores")
    demo.add_argument("--n", type=int, default=3000, help="number of samples (default 3000)")
    demo.add_argument("--json", action="store_true", help="print scores as JSON")
    _add_common(demo)
    demo.set_defaults(func=cmd_demo)

    run = sub.add_parser("run", help="run on a CSV file")
    run.add_argument("input", help="input CSV file")
    run.add_argument("--column", required=True, help="name of the numeric column")
    run.add_argument("--train", type=int, default=0, help="attack-free samples at the start")
    run.add_argument("--output", default="results/output.csv", help="where to write results")
    _add_common(run)
    run.set_defaults(func=cmd_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ValueError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
