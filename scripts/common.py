"""Shared paths and parameters. Every script imports this; nothing else hard-codes a path."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((ROOT / "config" / "config.yaml").read_text(encoding="utf-8"))
RAW = ROOT / CFG["paths"]["raw"]
EXT = ROOT / CFG["paths"]["external"]
OUT = ROOT / CFG["paths"]["outputs"]
FIG = ROOT / CFG["paths"]["figures"]
SEED = int(CFG["seed"])
IN = CFG["inputs"]
for _d in (OUT, FIG):
    _d.mkdir(parents=True, exist_ok=True)
