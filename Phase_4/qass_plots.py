import csv
import os
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from Phase_4.layer1_key_sources import generate_key_material_pool
from Phase_4.layer2_superposition import select_combination
from Phase_4.layer3_dsr_engine import derive_master_key
from Phase_4.layer4_ratchet import QuantumRatchet
from Phase_4.layer5_encryption import encrypt_message


BASE_DIR = os.path.dirname(__file__)
INTEGRATION_CSV = os.path.join(BASE_DIR, "qass_integration_log.csv")
LAYER6_CSV = os.path.join(BASE_DIR, "layer6_log.csv")


def _bytes_to_bits(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    return np.unpackbits(arr)


def _entropy_per_bit(data: bytes) -> float:
    bits = _bytes_to_bits(data)
    if bits.size == 0:
        return 0.0
    p1 = float(np.mean(bits))
    p0 = 1.0 - p1
    if p0 == 0.0 or p1 == 0.0:
        return 0.0
    return float(-p0 * np.log2(p0) - p1 * np.log2(p1))


def _read_csv_rows(path: str) -> List[Dict[str, str]]:
    if not os.path.isfile(path):
        return []
    with open(path, mode="r", newline="") as f:
        return list(csv.DictReader(f))


def _build_session_keys(count: int = 20) -> List[bytes]:
    keys: List[bytes] = []
    for i in range(count):
        session_id = f"plot_entropy_{i}"
        seed = 9000 + i
        pool = generate_key_material_pool(
            kyber_variant="Kyber1024",
            qrng_backend_mode="simulator",
            output_bytes=32,
            session_seed=seed,
            qkd_distance_km=10.0,
            qkd_eavesdrop=False,
        )
        selector = select_combination(session_id=session_id, shared_seed=seed)
        dsr = derive_master_key(session_id=session_id, combination_id=selector.combination_id, pool=pool)
        ratchet = QuantumRatchet(dsr.master_key, output_bytes=32)
        step = ratchet.advance()
        keys.append(step.session_key)
    return keys


def plot_session_key_entropy(count: int = 20) -> None:
    keys = _build_session_keys(count=count)
    entropies = [_entropy_per_bit(k) for k in keys]
    x = list(range(1, len(entropies) + 1))
    plt.figure(figsize=(10, 5))
    plt.plot(x, entropies, marker="o", color="#1f77b4")
    plt.ylim(0.95, 1.01)
    plt.xlabel("Session")
    plt.ylabel("Entropy (bits/bit)")
    plt.title("Session Key Entropy Across Sessions")
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "qass_session_key_entropy.png"), dpi=300)
    plt.show()


def plot_combination_distribution(count: int = 100) -> None:
    combo_counts = {i: 0 for i in range(7)}
    for i in range(count):
        selector = select_combination(session_id=f"plot_combo_{i}", shared_seed=10000 + i)
        combo_counts[selector.combination_id] += 1
    x = list(combo_counts.keys())
    y = [combo_counts[i] for i in x]
    plt.figure(figsize=(10, 5))
    plt.bar(x, y, color="#2ca02c")
    plt.xlabel("Combination ID")
    plt.ylabel("Selection Count")
    plt.title("Combination Selection Distribution Across Sessions")
    plt.grid(True, linestyle="--", linewidth=0.5, axis="y")
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "qass_combination_distribution.png"), dpi=300)
    plt.show()


def plot_ratchet_key_divergence(count: int = 20) -> None:
    keys = _build_session_keys(count=count)
    correlations: List[float] = []
    pairs = []
    for i in range(len(keys) - 1):
        b1 = _bytes_to_bits(keys[i])
        b2 = _bytes_to_bits(keys[i + 1])
        corr = float(np.corrcoef(b1, b2)[0, 1])
        if np.isnan(corr):
            corr = 0.0
        correlations.append(corr)
        pairs.append(i + 1)
    plt.figure(figsize=(10, 5))
    plt.plot(pairs, correlations, marker="s", color="#d62728")
    plt.axhline(0.0, linestyle="--", color="black", linewidth=1)
    plt.xlabel("Consecutive Session Pair Index")
    plt.ylabel("Bit Correlation")
    plt.title("Ratchet Key Divergence Across Consecutive Sessions")
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "qass_ratchet_key_divergence.png"), dpi=300)
    plt.show()


def plot_layer_timing_breakdown() -> None:
    rows = _read_csv_rows(INTEGRATION_CSV)
    if not rows:
        return
    labels = [r["session_id"] for r in rows]
    l1 = np.array([float(r["l1_ms"]) for r in rows], dtype=float)
    l2 = np.array([float(r["l2_ms"]) for r in rows], dtype=float)
    l3 = np.array([float(r["l3_ms"]) for r in rows], dtype=float)
    l4 = np.array([float(r["l4_ms"]) for r in rows], dtype=float)
    l5e = np.array([float(r["l5_enc_ms"]) for r in rows], dtype=float)
    l5d = np.array([float(r["l5_dec_ms"]) for r in rows], dtype=float)
    l6 = np.array([float(r["l6_ms"]) for r in rows], dtype=float)

    x = np.arange(len(labels))
    plt.figure(figsize=(12, 6))
    plt.bar(x, l1, label="L1")
    plt.bar(x, l2, bottom=l1, label="L2")
    plt.bar(x, l3, bottom=l1 + l2, label="L3")
    plt.bar(x, l4, bottom=l1 + l2 + l3, label="L4")
    plt.bar(x, l5e, bottom=l1 + l2 + l3 + l4, label="L5 enc")
    plt.bar(x, l5d, bottom=l1 + l2 + l3 + l4 + l5e, label="L5 dec")
    plt.bar(x, l6, bottom=l1 + l2 + l3 + l4 + l5e + l5d, label="L6")
    plt.xticks(x, labels, rotation=30, ha="right")
    plt.xlabel("Session")
    plt.ylabel("Total Time (ms)")
    plt.title("Layer Timing Breakdown Per Session")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5, axis="y")
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "qass_layer_timing_breakdown.png"), dpi=300)
    plt.show()


def plot_security_monitoring_dashboard() -> None:
    rows = _read_csv_rows(LAYER6_CSV)
    if not rows:
        return
    sessions = [r["session_id"] for r in rows]
    qber = [float(r["qber"]) for r in rows]
    entropy = [float(r["entropy"]) for r in rows]
    timing_cv = [float(r["timing_cv"]) for r in rows]
    qber_th = float(rows[0]["qber_threshold"])
    entropy_th = float(rows[0]["entropy_threshold"])
    timing_th = float(rows[0]["timing_cv_threshold"])

    fig, axes = plt.subplots(3, 1, figsize=(12, 9), sharex=True)
    axes[0].plot(sessions, qber, marker="o", color="#9467bd")
    axes[0].axhline(qber_th, linestyle="--", color="black", linewidth=1)
    axes[0].set_ylabel("QBER")
    axes[0].set_title("Security Monitoring Dashboard")
    axes[0].grid(True, linestyle="--", linewidth=0.5)

    axes[1].plot(sessions, entropy, marker="s", color="#17becf")
    axes[1].axhline(entropy_th, linestyle="--", color="black", linewidth=1)
    axes[1].set_ylabel("Entropy")
    axes[1].grid(True, linestyle="--", linewidth=0.5)

    axes[2].plot(sessions, timing_cv, marker="^", color="#ff7f0e")
    axes[2].axhline(timing_th, linestyle="--", color="black", linewidth=1)
    axes[2].set_ylabel("Timing CV")
    axes[2].set_xlabel("Session")
    axes[2].grid(True, linestyle="--", linewidth=0.5)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "qass_security_monitor_dashboard.png"), dpi=300)
    plt.show()


def _benchmark_cipher(message_sizes: List[int], cipher_name: str) -> List[float]:
    pool = generate_key_material_pool(
        kyber_variant="Kyber1024",
        qrng_backend_mode="simulator",
        output_bytes=32,
        session_seed=12000,
        qkd_distance_km=10.0,
        qkd_eavesdrop=False,
    )
    selector = select_combination(session_id=f"plot_cipher_{cipher_name}", shared_seed=12000)
    dsr = derive_master_key(session_id=f"plot_cipher_{cipher_name}", combination_id=selector.combination_id, pool=pool)
    ratchet = QuantumRatchet(dsr.master_key, output_bytes=32)
    key = ratchet.advance().session_key

    durations: List[float] = []
    for size in message_sizes:
        plaintext = bytes([size % 256] * size)
        runs = []
        for _ in range(3):
            enc = encrypt_message(key, plaintext, associated_data=b"plot", cipher=cipher_name)
            runs.append(enc.encrypt_duration_ms)
        durations.append(statistics.mean(runs))
    return durations


def plot_cipher_comparison() -> None:
    message_sizes = [64, 256, 1024, 4096, 16384]
    aes_times = _benchmark_cipher(message_sizes, "AES-256-GCM")
    chacha_times = _benchmark_cipher(message_sizes, "ChaCha20-Poly1305")
    plt.figure(figsize=(10, 5))
    plt.plot(message_sizes, aes_times, marker="o", label="AES-256-GCM")
    plt.plot(message_sizes, chacha_times, marker="s", label="ChaCha20-Poly1305")
    plt.xlabel("Message Size (bytes)")
    plt.ylabel("Encryption Time (ms)")
    plt.title("Cipher Comparison for Equal Message Sizes")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(os.path.join(BASE_DIR, "qass_cipher_comparison.png"), dpi=300)
    plt.show()


def run_all_plots() -> None:
    plot_session_key_entropy(count=20)
    plot_combination_distribution(count=100)
    plot_ratchet_key_divergence(count=20)
    plot_layer_timing_breakdown()
    plot_security_monitoring_dashboard()
    plot_cipher_comparison()


if __name__ == "__main__":
    run_all_plots()
