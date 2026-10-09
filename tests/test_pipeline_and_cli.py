import csv
import json

import pytest

from edgeguard.cli import main
from edgeguard.metrics import confusion, scores
from edgeguard.pipeline import PipelineConfig, run_pipeline
from edgeguard.synthetic import make_utility_stream


def test_metrics_basic_case():
    c = confusion([1, 1, 0, 0], [1, 0, 1, 0])
    assert c == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    s = scores([1, 1, 0, 0], [1, 0, 1, 0])
    assert s["precision"] == 0.5 and s["recall"] == 0.5 and s["f1"] == 0.5
    assert s["false_alarm_rate"] == 0.5


def test_metrics_length_check():
    with pytest.raises(ValueError):
        confusion([1, 0], [1])


def test_synthetic_stream_has_clean_training_part():
    s = make_utility_stream(n=2000, train_size=800, seed=1)
    assert not s.labels[:800].any()
    assert s.labels[800:].any()


def test_vote_keeps_false_alarms_low():
    """The vote should raise fewer false alarms than the noisiest single detector."""
    s = make_utility_stream(seed=42)
    r = run_pipeline(s.values, s.train_size)
    test = slice(s.train_size, None)
    vote = scores(s.labels[test], r.alarm[test])
    worst_single = max(
        scores(s.labels[test], f[test])["false_alarm_rate"] for f in r.flags.values()
    )
    assert vote["false_alarm_rate"] < worst_single
    assert vote["false_alarm_rate"] < 0.02
    assert vote["f1"] > 0.4
    assert len(r.states) == len(s.values)


def test_pipeline_checks_train_size():
    s = make_utility_stream()
    with pytest.raises(ValueError):
        run_pipeline(s.values, train_size=10, config=PipelineConfig(window=96))


def test_cli_demo_json(capsys):
    assert main(["demo", "--n", "1600", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert "vote_2_of_3" in report


def test_cli_run_writes_csv(tmp_path):
    s = make_utility_stream(n=1600, train_size=700, seed=5)
    src = tmp_path / "in.csv"
    with src.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kw"])
        w.writerows([[v] for v in s.values])
    out = tmp_path / "out.csv"
    assert main(["run", str(src), "--column", "kw", "--train", "700", "--output", str(out)]) == 0
    with out.open() as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 1600
    assert {"alarm", "state", "action"} <= set(rows[0])


def test_cli_reports_missing_column(tmp_path, capsys):
    src = tmp_path / "in.csv"
    src.write_text("a\n1\n2\n")
    assert main(["run", str(src), "--column", "missing"]) == 2
    assert "not found" in capsys.readouterr().err
