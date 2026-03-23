import argparse
import csv
import math
import os
import statistics
import sys
import time
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import matplotlib.pyplot as plt
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from Phase_4.layer1_key_sources import generate_key_material_pool
from Phase_4.layer2_superposition import select_combination
from Phase_4.layer3_dsr_engine import derive_master_key
from Phase_4.layer4_ratchet import QuantumRatchet
from Phase_4.layer5_encryption import decrypt_message, encrypt_message

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "ablation_results.csv")
REPORT_PATH = os.path.join(BASE_DIR, "ablation_report.md")
PLOT_PATH = os.path.join(BASE_DIR, "qass_ablation_plot.png")

MODES = [
    "baseline_full",
    "no_layer2_fixed_combo",
    "no_layer4_no_ratchet",
    "single_source_kyber",
]


def _bits_from_bytes(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    return np.unpackbits(arr)


def _mean_abs_corr(keys: Sequence[bytes]) -> float:
    if len(keys) < 2:
        return 0.0
    values: List[float] = []
    for i in range(len(keys) - 1):
        b1 = _bits_from_bytes(keys[i])
        b2 = _bits_from_bytes(keys[i + 1])
        corr = float(np.corrcoef(b1, b2)[0, 1])
        if math.isnan(corr):
            corr = 0.0
        values.append(abs(corr))
    return float(np.mean(values)) if values else 0.0


def _mean_hamming(keys: Sequence[bytes]) -> float:
    if len(keys) < 2:
        return 0.0
    values: List[float] = []
    for i in range(len(keys) - 1):
        b1 = _bits_from_bytes(keys[i])
        b2 = _bits_from_bytes(keys[i + 1])
        values.append(float(np.mean(b1 != b2)))
    return float(np.mean(values)) if values else 0.0


def _combo_entropy(combo_ids: Sequence[int]) -> float:
    if not combo_ids:
        return 0.0
    counts = np.bincount(np.array(combo_ids, dtype=int), minlength=7)
    probs = counts / float(np.sum(counts))
    nonzero = probs[probs > 0.0]
    return -float(np.sum(nonzero * np.log2(nonzero)))


def _predictability_rate(combo_ids: Sequence[int]) -> float:
    if not combo_ids:
        return 0.0
    counts = np.bincount(np.array(combo_ids, dtype=int), minlength=7)
    return float(np.max(counts) / np.sum(counts))


def _run_mode(mode: str, sessions: int, base_seed: int) -> Dict[str, float]:
    keys: List[bytes] = []
    combo_ids: List[int] = []
    decrypt_success = 0
    total_times: List[float] = []

    for i in range(sessions):
        session_seed = base_seed + i
        session_id = f"ablation_{mode}_{i}"

        t0 = time.perf_counter()
        pool = generate_key_material_pool(
            kyber_variant="Kyber1024",
            qrng_backend_mode="simulator",
            output_bytes=32,
            session_seed=session_seed,
            qkd_distance_km=10.0,
            qkd_eavesdrop=False,
        )

        if mode == "baseline_full":
            selector = select_combination(session_id=session_id, shared_seed=session_seed)
            combo_id = selector.combination_id
            master = derive_master_key(session_id, combo_id, pool, output_bytes=32).master_key
            session_key = QuantumRatchet(master, output_bytes=32).advance().session_key
        elif mode == "no_layer2_fixed_combo":
            combo_id = 1
            master = derive_master_key(session_id, combo_id, pool, output_bytes=32).master_key
            session_key = QuantumRatchet(master, output_bytes=32).advance().session_key
        elif mode == "no_layer4_no_ratchet":
            selector = select_combination(session_id=session_id, shared_seed=session_seed)
            combo_id = selector.combination_id
            session_key = derive_master_key(session_id, combo_id, pool, output_bytes=32).master_key
        elif mode == "single_source_kyber":
            combo_id = 1
            session_key = derive_master_key(session_id, combo_id, pool, output_bytes=32).master_key
        else:
            raise ValueError("unsupported mode")

        plaintext = f"ablation_payload_{i}".encode("utf-8")
        aad = f"aad_{mode}".encode("utf-8")
        enc = encrypt_message(session_key, plaintext, associated_data=aad, cipher="AES-256-GCM")
        dec = decrypt_message(session_key, "AES-256-GCM", enc.nonce, enc.ciphertext, enc.tag, associated_data=aad)

        if dec.plaintext == plaintext:
            decrypt_success += 1

        keys.append(session_key)
        combo_ids.append(combo_id)
        total_times.append((time.perf_counter() - t0) * 1000.0)

    return {
        "sessions": float(sessions),
        "decrypt_success_rate": decrypt_success / float(sessions),
        "unique_combo_count": float(len(set(combo_ids))),
        "combo_entropy": _combo_entropy(combo_ids),
        "predictability_rate": _predictability_rate(combo_ids),
        "mean_abs_key_corr": _mean_abs_corr(keys),
        "mean_hamming_rate": _mean_hamming(keys),
        "mean_total_ms": float(statistics.mean(total_times)) if total_times else 0.0,
    }


def append_results(run_id: str, metrics_by_mode: Dict[str, Dict[str, float]]) -> None:
    exists = os.path.isfile(CSV_PATH)
    with open(CSV_PATH, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not exists:
            writer.writerow([
                "run_id",
                "mode",
                "sessions",
                "decrypt_success_rate",
                "unique_combo_count",
                "combo_entropy",
                "predictability_rate",
                "mean_abs_key_corr",
                "mean_hamming_rate",
                "mean_total_ms",
            ])
        for mode, m in metrics_by_mode.items():
            writer.writerow([
                run_id,
                mode,
                m["sessions"],
                m["decrypt_success_rate"],
                m["unique_combo_count"],
                m["combo_entropy"],
                m["predictability_rate"],
                m["mean_abs_key_corr"],
                m["mean_hamming_rate"],
                m["mean_total_ms"],
            ])


def write_report(run_id: str, sessions: int, metrics_by_mode: Dict[str, Dict[str, float]]) -> None:
    lines: List[str] = [
        "# QASS Ablation Report",
        "",
        f"- Run ID: {run_id}",
        f"- Sessions per mode: {sessions}",
        "",
        "## Metrics",
        "- decrypt_success_rate: correctness under AES-256-GCM",
        "- unique_combo_count: number of distinct source combinations exercised",
        "- combo_entropy: entropy of combination usage",
        "- predictability_rate: frequency of most common combination",
        "- mean_abs_key_corr: average absolute correlation between consecutive keys",
        "- mean_hamming_rate: average consecutive key hamming ratio",
        "- mean_total_ms: average per-session runtime",
        "",
    ]
    for mode in MODES:
        m = metrics_by_mode[mode]
        lines.extend([
            f"### {mode}",
            f"- decrypt_success_rate: {m['decrypt_success_rate']:.6f}",
            f"- unique_combo_count: {m['unique_combo_count']:.0f}",
            f"- combo_entropy: {m['combo_entropy']:.6f}",
            f"- predictability_rate: {m['predictability_rate']:.6f}",
            f"- mean_abs_key_corr: {m['mean_abs_key_corr']:.6f}",
            f"- mean_hamming_rate: {m['mean_hamming_rate']:.6f}",
            f"- mean_total_ms: {m['mean_total_ms']:.6f}",
            "",
        ])

    with open(REPORT_PATH, mode="w", newline="") as f:
        f.write("\n".join(lines) + "\n")


def plot_results(metrics_by_mode: Dict[str, Dict[str, float]]) -> None:
    modes = MODES
    x = np.arange(len(modes))

    decrypt = [metrics_by_mode[m]["decrypt_success_rate"] for m in modes]
    predict = [metrics_by_mode[m]["predictability_rate"] for m in modes]
    unique = [metrics_by_mode[m]["unique_combo_count"] for m in modes]
    corr = [metrics_by_mode[m]["mean_abs_key_corr"] for m in modes]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    axes[0, 0].bar(x, decrypt, color="#1f77b4")
    axes[0, 0].set_title("Decrypt Success Rate")
    axes[0, 0].set_xticks(x, modes, rotation=20, ha="right")
    axes[0, 0].set_ylim(0.0, 1.05)

    axes[0, 1].bar(x, predict, color="#ff7f0e")
    axes[0, 1].set_title("Combination Predictability")
    axes[0, 1].set_xticks(x, modes, rotation=20, ha="right")
    axes[0, 1].set_ylim(0.0, 1.05)

    axes[1, 0].bar(x, unique, color="#2ca02c")
    axes[1, 0].set_title("Unique Combination Count")
    axes[1, 0].set_xticks(x, modes, rotation=20, ha="right")

    axes[1, 1].bar(x, corr, color="#d62728")
    axes[1, 1].set_title("Mean Absolute Consecutive Key Correlation")
    axes[1, 1].set_xticks(x, modes, rotation=20, ha="right")

    plt.tight_layout()
    plt.savefig(PLOT_PATH, dpi=300)
    plt.show()


def run(sessions: int, base_seed: int) -> Tuple[str, Dict[str, Dict[str, float]]]:
    run_id = f"ablation_{int(time.time())}"
    metrics_by_mode: Dict[str, Dict[str, float]] = {
        mode: _run_mode(mode=mode, sessions=sessions, base_seed=base_seed + idx * 10000)
        for idx, mode in enumerate(MODES)
    }
    append_results(run_id, metrics_by_mode)
    write_report(run_id, sessions, metrics_by_mode)
    plot_results(metrics_by_mode)
    return run_id, metrics_by_mode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=16)
    parser.add_argument("--base-seed", type=int, default=420000)
    args = parser.parse_args()

    run_id, metrics = run(sessions=args.sessions, base_seed=args.base_seed)
    print("run_id", run_id)
    for mode in MODES:
        m = metrics[mode]
        print(mode, "decrypt", m["decrypt_success_rate"], "predictability", m["predictability_rate"], "corr", m["mean_abs_key_corr"])
    print("csv", CSV_PATH)
    print("report", REPORT_PATH)
    print("plot", PLOT_PATH)


if __name__ == "__main__":
    main()
