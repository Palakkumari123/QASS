import csv
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from qiskit import QuantumCircuit
from qiskit.compiler import transpile
from qiskit_aer import Aer

from project_config import DETERMINISTIC_MODE, GLOBAL_SEED


BITSTRING_TO_COMBINATION: Dict[str, int] = {
    "001": 0,
    "010": 1,
    "011": 2,
    "100": 3,
    "101": 4,
    "110": 5,
    "111": 6,
}

COMBINATION_TO_SOURCES: Dict[int, Tuple[str, ...]] = {
    0: ("qkd",),
    1: ("kyber",),
    2: ("qrng",),
    3: ("qkd", "kyber"),
    4: ("qkd", "qrng"),
    5: ("kyber", "qrng"),
    6: ("qkd", "kyber", "qrng"),
}


@dataclass
class SelectorResult:
    session_id: str
    seed: int
    raw_bitstring: str
    combination_id: int
    selected_sources: Tuple[str, ...]
    attempts: int
    selector_duration_ms: float
    transpiled_depth: int
    transpiled_ops: Dict[str, int]
    metadata: Dict[str, object]


def _build_selector_circuit() -> QuantumCircuit:
    qc = QuantumCircuit(3, 3)
    qc.h(0)
    qc.h(1)
    qc.h(2)
    qc.cx(0, 1)
    qc.cx(1, 2)
    qc.measure([0, 1, 2], [0, 1, 2])
    return qc


def _run_once(seed: int) -> Tuple[str, int, Dict[str, int]]:
    backend = Aer.get_backend("aer_simulator")
    qc = _build_selector_circuit()
    compiled = transpile(qc, backend, seed_transpiler=seed)
    job = backend.run(compiled, shots=1, seed_simulator=seed)
    counts = job.result().get_counts()
    bitstring = next(iter(counts.keys()))
    return bitstring, int(compiled.depth()), {k: int(v) for k, v in compiled.count_ops().items()}


def select_combination(
    session_id: str,
    shared_seed: Optional[int] = None,
    max_attempts: int = 16,
) -> SelectorResult:
    if not session_id:
        raise ValueError("session_id must not be empty")
    if max_attempts <= 0:
        raise ValueError("max_attempts must be > 0")

    if DETERMINISTIC_MODE:
        base_seed = GLOBAL_SEED if shared_seed is None else int(shared_seed)
    elif shared_seed is None:
        now = int(time.time_ns() & 0x7FFFFFFF)
        base_seed = now
    else:
        base_seed = int(shared_seed)

    t0 = time.perf_counter()
    for attempt in range(1, max_attempts + 1):
        run_seed = base_seed + attempt - 1
        raw_bitstring, depth, ops = _run_once(run_seed)
        if raw_bitstring in BITSTRING_TO_COMBINATION:
            combination_id = BITSTRING_TO_COMBINATION[raw_bitstring]
            selected_sources = COMBINATION_TO_SOURCES[combination_id]
            selector_duration_ms = (time.perf_counter() - t0) * 1000.0
            metadata = {
                "backend": "aer_simulator",
                "valid_outcomes": sorted(BITSTRING_TO_COMBINATION.keys()),
                "max_attempts": max_attempts,
            }
            return SelectorResult(
                session_id=session_id,
                seed=run_seed,
                raw_bitstring=raw_bitstring,
                combination_id=combination_id,
                selected_sources=selected_sources,
                attempts=attempt,
                selector_duration_ms=selector_duration_ms,
                transpiled_depth=depth,
                transpiled_ops=ops,
                metadata=metadata,
            )

    raise RuntimeError("Selector failed to produce a valid non-empty combination within max_attempts")


def append_layer2_log(csv_path: str, result: SelectorResult) -> None:
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "session_id",
                "seed",
                "raw_bitstring",
                "combination_id",
                "selected_sources",
                "attempts",
                "selector_duration_ms",
                "transpiled_depth",
                "transpiled_ops",
            ])
        writer.writerow([
            result.session_id,
            result.seed,
            result.raw_bitstring,
            result.combination_id,
            "+".join(result.selected_sources),
            result.attempts,
            result.selector_duration_ms,
            result.transpiled_depth,
            str(result.transpiled_ops),
        ])
