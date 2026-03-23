import csv
import os
import statistics
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


THREAT_LEVELS = {
    0: "CLEAR",
    1: "WARNING",
    2: "ELEVATED",
    3: "CRITICAL",
}


@dataclass
class MonitorSignal:
    name: str
    value: float
    threshold: float
    triggered: bool


@dataclass
class MonitorReport:
    session_id: str
    qber_signal: MonitorSignal
    entropy_signal: MonitorSignal
    timing_signal: MonitorSignal
    threat_level: int
    threat_label: str
    action: str
    monitor_duration_ms: float
    metadata: Dict[str, object]


def bits_entropy_per_bit(bits: np.ndarray) -> float:
    if bits.size == 0:
        return 0.0
    p1 = float(np.mean(bits))
    p0 = 1.0 - p1
    if p0 == 0.0 or p1 == 0.0:
        return 0.0
    return float(-p0 * np.log2(p0) - p1 * np.log2(p1))


def bytes_to_bits(data: bytes) -> np.ndarray:
    if not data:
        return np.array([], dtype=np.int8)
    arr = np.frombuffer(data, dtype=np.uint8)
    return np.unpackbits(arr).astype(np.int8)


def timing_cv(values_ms: Sequence[float]) -> float:
    valid = [float(v) for v in values_ms if float(v) >= 0.0]
    if len(valid) < 2:
        return 0.0
    mean_v = statistics.mean(valid)
    if mean_v == 0.0:
        return 0.0
    std_v = statistics.pstdev(valid)
    return float(std_v / mean_v)


class SecurityMonitor:
    def __init__(
        self,
        qber_threshold: float = 0.11,
        entropy_threshold: float = 0.99,
        timing_cv_threshold: float = 0.10,
    ):
        if qber_threshold <= 0.0:
            raise ValueError("qber_threshold must be > 0")
        if entropy_threshold <= 0.0 or entropy_threshold > 1.0:
            raise ValueError("entropy_threshold must be in (0, 1]")
        if timing_cv_threshold <= 0.0:
            raise ValueError("timing_cv_threshold must be > 0")
        self.qber_threshold = qber_threshold
        self.entropy_threshold = entropy_threshold
        self.timing_cv_threshold = timing_cv_threshold

    def evaluate_session(
        self,
        session_id: str,
        qber: float,
        qrng_data: bytes,
        operation_timings_ms: Sequence[float],
        endpoint_id: Optional[str] = None,
    ) -> MonitorReport:
        if not session_id:
            raise ValueError("session_id must not be empty")
        if qber < 0.0 or qber > 1.0:
            raise ValueError("qber must be in [0,1]")

        t0 = time.perf_counter()
        entropy = bits_entropy_per_bit(bytes_to_bits(qrng_data))
        cv_value = timing_cv(operation_timings_ms)

        qber_signal = MonitorSignal(
            name="qber",
            value=qber,
            threshold=self.qber_threshold,
            triggered=qber > self.qber_threshold,
        )
        entropy_signal = MonitorSignal(
            name="entropy",
            value=entropy,
            threshold=self.entropy_threshold,
            triggered=entropy < self.entropy_threshold,
        )
        timing_signal = MonitorSignal(
            name="timing_cv",
            value=cv_value,
            threshold=self.timing_cv_threshold,
            triggered=cv_value > self.timing_cv_threshold,
        )

        threat_level, action = self._resolve_response(
            qber_signal.triggered,
            entropy_signal.triggered,
            timing_signal.triggered,
            endpoint_id,
        )

        monitor_duration_ms = (time.perf_counter() - t0) * 1000.0
        metadata = {
            "endpoint_id": endpoint_id if endpoint_id is not None else "",
            "timing_samples": len(operation_timings_ms),
            "triggered_count": int(qber_signal.triggered) + int(entropy_signal.triggered) + int(timing_signal.triggered),
        }

        return MonitorReport(
            session_id=session_id,
            qber_signal=qber_signal,
            entropy_signal=entropy_signal,
            timing_signal=timing_signal,
            threat_level=threat_level,
            threat_label=THREAT_LEVELS[threat_level],
            action=action,
            monitor_duration_ms=monitor_duration_ms,
            metadata=metadata,
        )

    def _resolve_response(
        self,
        qber_triggered: bool,
        entropy_triggered: bool,
        timing_triggered: bool,
        endpoint_id: Optional[str],
    ) -> Tuple[int, str]:
        if qber_triggered:
            if endpoint_id:
                return 3, f"ABORT_SESSION_AND_BLACKLIST:{endpoint_id}"
            return 3, "ABORT_SESSION"
        if entropy_triggered and timing_triggered:
            return 2, "ROTATE_SESSION_KEY"
        if entropy_triggered:
            return 1, "ALERT_AND_RESEED_QRNG"
        return (1, "ALERT_SIDE_CHANNEL") if timing_triggered else (0, "NO_ACTION")


def append_layer6_log(csv_path: str, report: MonitorReport) -> None:
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "session_id",
                "qber",
                "qber_threshold",
                "qber_triggered",
                "entropy",
                "entropy_threshold",
                "entropy_triggered",
                "timing_cv",
                "timing_cv_threshold",
                "timing_triggered",
                "threat_level",
                "threat_label",
                "action",
                "monitor_duration_ms",
                "endpoint_id",
                "timing_samples",
                "triggered_count",
            ])
        writer.writerow([
            report.session_id,
            report.qber_signal.value,
            report.qber_signal.threshold,
            report.qber_signal.triggered,
            report.entropy_signal.value,
            report.entropy_signal.threshold,
            report.entropy_signal.triggered,
            report.timing_signal.value,
            report.timing_signal.threshold,
            report.timing_signal.triggered,
            report.threat_level,
            report.threat_label,
            report.action,
            report.monitor_duration_ms,
            report.metadata.get("endpoint_id", ""),
            report.metadata.get("timing_samples", ""),
            report.metadata.get("triggered_count", ""),
        ])


def evaluate_monitor_batch(
    monitor: SecurityMonitor,
    sessions: Sequence[Dict[str, object]],
) -> List[MonitorReport]:
    reports: List[MonitorReport] = []
    for item in sessions:
        report = monitor.evaluate_session(
            session_id=str(item["session_id"]),
            qber=float(item["qber"]),
            qrng_data=bytes(item["qrng_data"]),
            operation_timings_ms=list(item["operation_timings_ms"]),
            endpoint_id=str(item.get("endpoint_id")) if item.get("endpoint_id") is not None else None,
        )
        reports.append(report)
    return reports
