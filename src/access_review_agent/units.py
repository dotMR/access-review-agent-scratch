"""Per-system detection units: SPEC.md §3's isolation boundary, built as a
structural property of the code rather than a documented convention.

A SystemDetectionUnit is constructed once per Information System, with its
system_name and data_dir fixed at construction time. Its only public
method, detect_all(), takes no arguments — there is no parameter through
which a caller could point it at a different system's access file.

The isolation is proven, not just asserted: Milestone 4's
registry-inspection check (scripts/run_milestone4.py) runs a unit against
a data_dir holding *only* that unit's own access file plus HRIS — the
other four systems' files aren't present at all, not just unused — and
confirms detect_all() still succeeds and produces identical findings. If
the unit's code ever referenced another system's file, that run would
raise FileNotFoundError, not just "happen not to" read it.

Per SPEC.md §3, a unit only ever detects — it never writes. Only the
orchestrator (the main agent, orchestrator.py) holds open_issue.
"""

from pathlib import Path
from typing import Any

from access_review_agent.detection.dormant_ad_hoc import detect_dormant_ad_hoc
from access_review_agent.detection.dormant_admin import detect_dormant_admin
from access_review_agent.detection.drift import detect_drift
from access_review_agent.detection.orphaned import detect_orphaned
from access_review_agent.detection.unapproved import detect_unapproved

SYSTEMS = ("aws", "github", "salesforce", "finance_erp", "vpn")


class SystemDetectionUnit:
    """Pre-bound to one system at construction time. `system_name` is
    private; `detect_all()` exposes no parameter that could override it.
    """

    def __init__(self, system_name: str, data_dir: Path):
        if system_name not in SYSTEMS:
            raise ValueError(f"Unknown system_name={system_name!r}, expected one of {SYSTEMS}")
        self._system_name = system_name
        self._data_dir = data_dir

    @property
    def system_name(self) -> str:
        return self._system_name

    def detect_all(self) -> list[dict[str, Any]]:
        """Run every Tier 1 (deterministic) category for this unit's own
        system only, synchronously - Identity resolution (Milestone 6,
        the one v1 Core category needing a real Agent SDK call) is
        deliberately NOT run here. It's added one level up, by
        orchestrator.run_full_reconciliation (async), which is what lets
        this unit and its detect_all() contract stay plain, synchronous
        Python - ADR-0006's Tier 1/Tier 2 split point, drawn at the
        orchestrator layer rather than inside every unit.
        """
        findings: list[dict[str, Any]] = []
        findings += detect_orphaned(self._data_dir, self._system_name)["findings"]
        findings += detect_dormant_admin(self._data_dir, self._system_name)["findings"]
        findings += detect_dormant_ad_hoc(self._data_dir, self._system_name)["findings"]
        findings += detect_unapproved(self._data_dir, self._system_name)["findings"]
        findings += detect_drift(self._data_dir, self._system_name)["findings"]
        return findings
