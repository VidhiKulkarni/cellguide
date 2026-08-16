"""Shared pytest setup: put every agent module's own folder on sys.path, matching how each
agent's run.py does it (sys.path.insert(0, ...)) — the pipeline's modules aren't installed as
a package, they're imported by relative folder location, so tests need the same setup."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

for _folder in [
    "agent3_metric_construction",
    "agent6_next_experiment",
    "agent7_provenance",
]:
    path = str(REPO_ROOT / _folder)
    if path not in sys.path:
        sys.path.insert(0, path)
