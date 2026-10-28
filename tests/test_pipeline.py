"""Run after `python scripts/run_all.py`.  pytest -q"""
import hashlib
import subprocess
import sys
from pathlib import Path
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"


def _check_sums(sumfile: Path):
    for line in sumfile.read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        if not (sumfile.parent / name.strip()).exists():
            continue
        assert hashlib.sha256((sumfile.parent / name.strip()).read_bytes()).hexdigest() == digest, name


@pytest.mark.skipif(not (ROOT / "data/raw/Oman_Layer1_Clean_EN_v2.xlsx").exists(),
                    reason="raw workbooks are not distributed (derived-only mode)")
def test_raw_inputs_unchanged():
    _check_sums(ROOT / "data/raw/checksums.sha256")


def test_external_snapshots_unchanged():
    _check_sums(ROOT / "data/external/checksums.sha256")


def test_every_chapter_figure_behaves_as_documented():
    rep = pd.read_csv(OUT / "claims_report.csv")
    assert len(rep) >= 140
    assert not rep.result.str.startswith("FAIL").any(), rep[rep.result.str.startswith("FAIL")]


def test_no_discrepancies_between_chapter_and_pipeline():
    rep = pd.read_csv(OUT / "claims_report.csv")
    assert (rep.result == "OK").all(), rep[rep.result != "OK"]


def test_panel_shape_and_ban_coding():
    p = pd.read_csv(OUT / "bose_replication_panel.csv")
    assert list(p.year) == list(range(2000, 2025))
    assert p.loc[p.year >= 2011, "D_BAN"].eq(1).all() and p.loc[p.year < 2011, "D_BAN"].eq(0).all()


def test_network_size():
    assert len(pd.read_csv(OUT / "layer2_nodes.csv")) == 8
    assert len(pd.read_csv(OUT / "layer2_edges.csv")) == 13


def test_claims_script_exit_code():
    rc = subprocess.run([sys.executable, str(ROOT / "scripts/07_verify_chapter_claims.py")], cwd=ROOT).returncode
    assert rc == 0


NEW_OUTPUTS = ["layer3_regime_split.csv", "layer3_unit_roots.csv", "layer3_residual_tests.csv",
               "layer3_break_scan.csv", "layer3_placebo.csv", "layer3_pct_effect.csv",
               "layer2_reweight_summary.csv", "layer2_leave_one_out.csv", "layer2_unweighted.csv",
               "layer2_node_merge.csv", "layer2_eig_vs_degree.csv"]


@pytest.mark.parametrize("name", NEW_OUTPUTS)
def test_review_outputs_exist_and_are_non_empty(name):
    """03b and 04b outputs added in response to peer review (docs/DEVIATIONS.md, Section C)."""
    assert (OUT / name).exists(), name
    assert len(pd.read_csv(OUT / name)) > 0, name
