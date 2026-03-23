import csv
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from Phase_4.layer1_key_sources import KeySourceResult


COMBINATION_MAP: Dict[int, Tuple[str, ...]] = {
    0: ("qkd",),
    1: ("kyber",),
    2: ("qrng",),
    3: ("qkd", "kyber"),
    4: ("qkd", "qrng"),
    5: ("kyber", "qrng"),
    6: ("qkd", "kyber", "qrng"),
}


@dataclass
class DSRKeyResult:
    session_id: str
    combination_id: int
    selected_sources: Tuple[str, ...]
    xor_key: bytes
    master_key: bytes
    xor_duration_ms: float
    hkdf_duration_ms: float
    total_duration_ms: float
    metadata: Dict[str, object]


def validate_combination_id(combination_id: int) -> None:
    if combination_id not in COMBINATION_MAP:
        raise ValueError("combination_id must be one of 0..6")


def validate_pool(pool: Dict[str, KeySourceResult]) -> None:
    required = {"qkd", "kyber", "qrng"}
    if missing := required.difference(set(pool.keys())):
        raise ValueError(f"pool missing required sources: {sorted(missing)}")


def xor_bytes(keys: List[bytes]) -> bytes:
    if not keys:
        raise ValueError("keys must not be empty")
    length = len(keys[0])
    if length == 0:
        raise ValueError("keys must not contain empty bytes")
    if any(len(k) != length for k in keys):
        raise ValueError("all keys must have same length")
    output = bytearray(length)
    for k in keys:
        for i, b in enumerate(k):
            output[i] ^= b
    return bytes(output)


def hkdf_sha256(input_key: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    if length <= 0:
        raise ValueError("length must be > 0")
    return HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        info=info,
    ).derive(input_key)


def derive_master_key(
    session_id: str,
    combination_id: int,
    pool: Dict[str, KeySourceResult],
    qrng_salt: Optional[bytes] = None,
    output_bytes: int = 32,
) -> DSRKeyResult:
    if not session_id:
        raise ValueError("session_id must not be empty")
    if output_bytes <= 0:
        raise ValueError("output_bytes must be > 0")
    validate_combination_id(combination_id)
    validate_pool(pool)

    selected_sources = COMBINATION_MAP[combination_id]
    selected_keys = [pool[name].key_material for name in selected_sources]

    t0 = time.perf_counter()
    tx = time.perf_counter()
    xor_key = xor_bytes(selected_keys)
    xor_duration_ms = (time.perf_counter() - tx) * 1000.0

    salt = qrng_salt if qrng_salt is not None else pool["qrng"].key_material
    if len(salt) == 0:
        raise ValueError("qrng_salt must not be empty")

    info = session_id.encode("utf-8") + combination_id.to_bytes(1, "big")

    th = time.perf_counter()
    master_key = hkdf_sha256(xor_key, salt=salt, info=info, length=output_bytes)
    hkdf_duration_ms = (time.perf_counter() - th) * 1000.0
    total_duration_ms = (time.perf_counter() - t0) * 1000.0

    metadata = {
        "salt_bytes": len(salt),
        "output_bytes": output_bytes,
        "selected_key_bytes": len(selected_keys[0]),
        "info_hex": info.hex(),
    }

    return DSRKeyResult(
        session_id=session_id,
        combination_id=combination_id,
        selected_sources=selected_sources,
        xor_key=xor_key,
        master_key=master_key,
        xor_duration_ms=xor_duration_ms,
        hkdf_duration_ms=hkdf_duration_ms,
        total_duration_ms=total_duration_ms,
        metadata=metadata,
    )


def append_layer3_log(csv_path: str, result: DSRKeyResult) -> None:
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "session_id",
                "combination_id",
                "selected_sources",
                "xor_duration_ms",
                "hkdf_duration_ms",
                "total_duration_ms",
                "master_key_bytes",
                "salt_bytes",
                "output_bytes",
            ])
        writer.writerow([
            result.session_id,
            result.combination_id,
            "+".join(result.selected_sources),
            result.xor_duration_ms,
            result.hkdf_duration_ms,
            result.total_duration_ms,
            len(result.master_key),
            result.metadata.get("salt_bytes", ""),
            result.metadata.get("output_bytes", ""),
        ])
