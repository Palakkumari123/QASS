import csv
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from Quantum_layer_verification.QRNG import quantum_rng


@dataclass
class RatchetStepResult:
    session_index: int
    previous_key: bytes
    qrng_bytes: bytes
    xored_material: bytes
    session_key: bytes
    advance_duration_ms: float
    metadata: Dict[str, object]


def _bits_to_bytes(bits: np.ndarray, output_bytes: int) -> bytes:
    if output_bytes <= 0:
        raise ValueError("output_bytes must be > 0")
    if bits.size == 0:
        raise ValueError("bits must not be empty")
    needed = output_bytes * 8
    if bits.size < needed:
        repeats = (needed + bits.size - 1) // bits.size
        bits = np.tile(bits, repeats)
    packed = np.packbits(bits[:needed].astype(np.uint8))
    return bytes(packed.tolist())


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    if len(a) != len(b):
        raise ValueError("byte arrays must have equal length")
    return bytes(x ^ y for x, y in zip(a, b))


def _hkdf_sha256(input_key: bytes, info: bytes, output_bytes: int) -> bytes:
    if output_bytes <= 0:
        raise ValueError("output_bytes must be > 0")
    return HKDF(
        algorithm=hashes.SHA256(),
        length=output_bytes,
        salt=None,
        info=info,
    ).derive(input_key)


def qrng_random_bytes(num_bytes: int) -> bytes:
    if num_bytes <= 0:
        raise ValueError("num_bytes must be > 0")
    bits = quantum_rng(num_bytes * 8)
    return _bits_to_bytes(bits.astype(np.int8), num_bytes)


class QuantumRatchet:
    def __init__(self, initial_key: bytes, output_bytes: int = 32):
        if not initial_key:
            raise ValueError("initial_key must not be empty")
        if output_bytes <= 0:
            raise ValueError("output_bytes must be > 0")
        if len(initial_key) != output_bytes:
            raise ValueError("initial_key length must match output_bytes")
        self.current_key = initial_key
        self.output_bytes = output_bytes
        self.session_count = 0

    def advance(self, qrng_override: Optional[bytes] = None) -> RatchetStepResult:
        previous_key = self.current_key
        t0 = time.perf_counter()
        qrng_material = qrng_override if qrng_override is not None else qrng_random_bytes(self.output_bytes)
        if len(qrng_material) != self.output_bytes:
            raise ValueError("qrng material length must match output_bytes")
        xored = _xor_bytes(previous_key, qrng_material)
        info = f"ratchet_{self.session_count}".encode("utf-8")
        session_key = _hkdf_sha256(xored, info=info, output_bytes=self.output_bytes)
        self.current_key = session_key
        duration_ms = (time.perf_counter() - t0) * 1000.0

        step = RatchetStepResult(
            session_index=self.session_count,
            previous_key=previous_key,
            qrng_bytes=qrng_material,
            xored_material=xored,
            session_key=session_key,
            advance_duration_ms=duration_ms,
            metadata={
                "info": info.decode("utf-8"),
                "output_bytes": self.output_bytes,
            },
        )
        self.session_count += 1
        return step


def run_ratchet_sessions(initial_key: bytes, sessions: int = 5, output_bytes: int = 32) -> List[RatchetStepResult]:
    if sessions <= 0:
        raise ValueError("sessions must be > 0")
    ratchet = QuantumRatchet(initial_key=initial_key, output_bytes=output_bytes)
    return [ratchet.advance() for _ in range(sessions)]


def append_layer4_log(csv_path: str, session_id: str, step: RatchetStepResult) -> None:
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "session_id",
                "session_index",
                "advance_duration_ms",
                "key_bytes",
                "qrng_bytes",
                "info",
            ])
        writer.writerow([
            session_id,
            step.session_index,
            step.advance_duration_ms,
            len(step.session_key),
            len(step.qrng_bytes),
            step.metadata.get("info", ""),
        ])
