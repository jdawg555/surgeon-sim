"""
Core data structures for Dragonfly Fusion Planning.
Lumbar fusion logistics: pedicle screws, rods, tray optimization.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class SpineLevel(str, Enum):
    """Fusion-relevant spinal levels (disc-space naming)."""
    C3_C4 = "C3-C4"
    C4_C5 = "C4-C5"
    C5_C6 = "C5-C6"
    C6_C7 = "C6-C7"
    L1_L2 = "L1-L2"
    L2_L3 = "L2-L3"
    L3_L4 = "L3-L4"
    L4_L5 = "L4-L5"
    L5_S1 = "L5-S1"

    @property
    def is_cervical(self) -> bool:
        return self.value.startswith("C")

    @property
    def is_lumbar(self) -> bool:
        return self.value.startswith("L") or self.value.startswith("S")


class SessionState(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    SEGMENTING = "segmenting"
    PREDICTING = "predicting"
    PLAN_READY = "plan_ready"
    REPORT_READY = "report_ready"
    ERROR = "error"


@dataclass
class PatientInfo:
    name: str = ""
    patient_id: str = ""
    date_of_birth: str = ""
    study_date: str = ""
    referring_physician: str = ""
    institution: str = ""
    notes: str = ""
    sex: str = ""  # "M" | "F" | ""


@dataclass
class PatientSession:
    """Complete state for one patient fusion planning session."""
    session_id: str
    patient: PatientInfo
    output_dir: Path
    state: SessionState = SessionState.IDLE

    scan_path: Optional[Path] = None
    stl_path: Optional[Path] = None
    selected_level: Optional[SpineLevel] = None
    fusion_plan: Optional[object] = None       # ImplantPlan from implant_predictor
    tray_config: Optional[object] = None       # TrayConfiguration from tray_optimizer
    report_path: Optional[Path] = None
    api_case_id: str = ""  # mirrors the API case_id once case_sync writes to flywheel
