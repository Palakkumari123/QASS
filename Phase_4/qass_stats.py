import argparse
import csv
import math
import os
import secrets
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from scipy.stats import chisquare, norm

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from Phase_4.layer1_key_sources import generate_key_material_pool
from Phase_4.layer2_superposition import select_combination
from Phase_4.layer3_dsr_engine import derive_master_key
from Phase_4.layer4_ratchet import QuantumRatchet
from Phase_4.layer5_encryption import decrypt_message, encrypt_message
from Phase_4.layer6_monitor import SecurityMonitor

BASE_DIR = os.path.dirname(__file__)
CSV_PATH = os.path.join(BASE_DIR, "statistical_validation.csv")
REPORT_PATH = os.path.join(BASE_DIR, "statistical_validation_report.md")


def _normal_ci(mean: float, stdev: float, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    if n <= 1:
        return mean, mean
    z = float(norm.ppf(1.0 - alpha / 2.0))
    margin = z * (stdev / math.sqrt(float(n)))
    return mean - margin, mean + margin


def _wilson_ci(successes: int, n: int, alpha: float = 0.05) -> Tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z = float(norm.ppf(1.0 - alpha / 2.0))
    p = successes / float(n)
    denom = 1.0 + (z ** 2) / n
    center = (p + (z ** 2) / (2.0 * n)) / denom
    margin = (z * math.sqrt((p * (1.0 - p) / n) + ((z ** 2) / (4.0 * n ** 2)))) / denom
    return center - margin, center + margin


def _bytes_to_bits(data: bytes) -> np.ndarray:
    arr = np.frombuffer(data, dtype=np.uint8)
    return np.unpackbits(arr).astype(np.int8)


def selector_uniformity_test(num_sessions: int) -> Dict[str, object]:
    counts = np.zeros(7, dtype=int)
    for i in range(num_sessions):
        result = select_combination(session_id=f"stats_selector_{i}", shared_seed=300000 + i)
        counts[result.combination_id] += 1
    expected = np.full(7, num_sessions / 7.0)
    chi_stat, p_value = chisquare(counts, expected)
    probs = counts / float(num_sessions)
    uniform = 1.0 / 7.0
    tv_distance = 0.5 * float(np.sum(np.abs(probs - uniform)))
    return {
        "num_sessions": num_sessions,
        "counts": counts.tolist(),
        "chi_square_stat": float(chi_stat),
        "p_value": float(p_value),
        "tv_distance": tv_distance,
    }


def ratchet_independence_test(num_sessions: int, use_quantum_ratchet_randomness: bool) -> Dict[str, object]:
    pool = generate_key_material_pool(
        kyber_variant="Kyber1024",
        qrng_backend_mode="simulator",
        output_bytes=32,
        session_seed=707,
        qkd_distance_km=10.0,
        qkd_eavesdrop=False,
    )
    selector = select_combination(session_id="stats_ratchet_seed", shared_seed=707)
    dsr = derive_master_key("stats_ratchet_seed", selector.combination_id, pool, output_bytes=32)
    ratchet = QuantumRatchet(initial_key=dsr.master_key, output_bytes=32)

    keys: List[bytes] = []
    for _ in range(num_sessions):
        if use_quantum_ratchet_randomness:
            step = ratchet.advance()
        else:
            step = ratchet.advance(qrng_override=secrets.token_bytes(32))
        keys.append(step.session_key)

    correlations: List[float] = []
    hamming_rates: List[float] = []
    for i in range(len(keys) - 1):
        b1 = _bytes_to_bits(keys[i])
        b2 = _bytes_to_bits(keys[i + 1])
        corr = float(np.corrcoef(b1, b2)[0, 1])
        if math.isnan(corr):
            corr = 0.0
        correlations.append(corr)
        hamming = float(np.mean(b1 != b2))
        hamming_rates.append(hamming)

    mean_abs_corr = float(np.mean(np.abs(correlations))) if correlations else 0.0
    max_abs_corr = float(np.max(np.abs(correlations))) if correlations else 0.0
    mean_hamming = float(np.mean(hamming_rates)) if hamming_rates else 0.0
    stdev_hamming = float(np.std(hamming_rates, ddof=1)) if len(hamming_rates) > 1 else 0.0
    h_low, h_high = _normal_ci(mean_hamming, stdev_hamming, len(hamming_rates))

    return {
        "num_sessions": num_sessions,
        "pair_count": len(correlations),
        "mean_abs_corr": mean_abs_corr,
        "max_abs_corr": max_abs_corr,
        "mean_hamming": mean_hamming,
        "hamming_ci_low": h_low,
        "hamming_ci_high": h_high,
        "all_keys_unique": len(set(keys)) == len(keys),
        "use_quantum_ratchet_randomness": use_quantum_ratchet_randomness,
    }


def encryption_reliability_test(num_trials: int) -> Dict[str, object]:
    pool = generate_key_material_pool(
        kyber_variant="Kyber1024",
        qrng_backend_mode="simulator",
        output_bytes=32,
        session_seed=808,
        qkd_distance_km=10.0,
        qkd_eavesdrop=False,
    )
    selector = select_combination(session_id="stats_enc_seed", shared_seed=808)
    master_key = derive_master_key("stats_enc_seed", selector.combination_id, pool, output_bytes=32).master_key

    ciphers = ["AES-256-GCM", "ChaCha20-Poly1305"]
    results: Dict[str, Dict[str, float]] = {}

    for cipher_name in ciphers:
        success = 0
        enc_times: List[float] = []
        dec_times: List[float] = []
        for i in range(num_trials):
            size = int(np.random.choice([64, 256, 1024, 4096]))
            plaintext = secrets.token_bytes(size)
            aad = f"enc_stats_{i}".encode("utf-8")
            enc = encrypt_message(master_key, plaintext, associated_data=aad, cipher=cipher_name)
            dec = decrypt_message(master_key, cipher_name, enc.nonce, enc.ciphertext, enc.tag, associated_data=aad)
            if dec.plaintext == plaintext:
                success += 1
            enc_times.append(enc.encrypt_duration_ms)
            dec_times.append(dec.decrypt_duration_ms)

        rate = success / float(num_trials)
        low, high = _wilson_ci(success, num_trials)
        results[cipher_name] = {
            "success_rate": rate,
            "ci_low": low,
            "ci_high": high,
            "enc_mean_ms": float(statistics.mean(enc_times)),
            "dec_mean_ms": float(statistics.mean(dec_times)),
        }

    return {
        "num_trials": num_trials,
        "cipher_results": results,
    }


def monitor_quality_test(num_trials: int) -> Dict[str, object]:
    monitor = SecurityMonitor(qber_threshold=0.11, entropy_threshold=0.99, timing_cv_threshold=0.10)

    benign_correct = 0
    attack_detected = 0

    for i in range(num_trials):
        benign_qber = float(np.random.uniform(0.0, 0.03))
        benign_qrng = bytes([0xAA, 0x55] * 32)
        benign_timings = [float(np.random.normal(1.0, 0.02)) for _ in range(5)]
        benign = monitor.evaluate_session(
            session_id=f"benign_{i}",
            qber=benign_qber,
            qrng_data=benign_qrng,
            operation_timings_ms=benign_timings,
            endpoint_id="node_benign",
        )
        if benign.threat_level == 0:
            benign_correct += 1

        attack_qber = float(np.random.uniform(0.18, 0.35))
        attack_qrng = bytes([0x00] * 64)
        attack_timings = [float(v) for v in np.abs(np.random.normal(1.0, 0.6, size=5))]
        attack = monitor.evaluate_session(
            session_id=f"attack_{i}",
            qber=attack_qber,
            qrng_data=attack_qrng,
            operation_timings_ms=attack_timings,
            endpoint_id="node_attack",
        )
        if attack.threat_level >= 2:
            attack_detected += 1

    benign_rate = benign_correct / float(num_trials)
    attack_rate = attack_detected / float(num_trials)
    b_low, b_high = _wilson_ci(benign_correct, num_trials)
    a_low, a_high = _wilson_ci(attack_detected, num_trials)

    return {
        "num_trials": num_trials,
        "benign_clear_rate": benign_rate,
        "benign_ci_low": b_low,
        "benign_ci_high": b_high,
        "attack_detection_rate": attack_rate,
        "attack_ci_low": a_low,
        "attack_ci_high": a_high,
    }


def write_csv(metrics: Dict[str, object]) -> None:
    rows: List[Tuple[str, str, str]] = [
        (
            "selector_uniformity",
            "num_sessions",
            str(metrics["selector_uniformity"]["num_sessions"]),
        ),
        ("selector_uniformity", "counts", str(metrics["selector_uniformity"]["counts"])),
        (
            "selector_uniformity",
            "chi_square_stat",
            str(metrics["selector_uniformity"]["chi_square_stat"]),
        ),
        ("selector_uniformity", "p_value", str(metrics["selector_uniformity"]["p_value"])),
        (
            "selector_uniformity",
            "tv_distance",
            str(metrics["selector_uniformity"]["tv_distance"]),
        ),
    ]

    ratchet = metrics["ratchet_independence"]
    rows.extend([
        ("ratchet_independence", "num_sessions", str(ratchet["num_sessions"])),
        ("ratchet_independence", "pair_count", str(ratchet["pair_count"])),
        ("ratchet_independence", "mean_abs_corr", str(ratchet["mean_abs_corr"])),
        ("ratchet_independence", "max_abs_corr", str(ratchet["max_abs_corr"])),
        ("ratchet_independence", "mean_hamming", str(ratchet["mean_hamming"])),
        ("ratchet_independence", "hamming_ci_low", str(ratchet["hamming_ci_low"])),
        ("ratchet_independence", "hamming_ci_high", str(ratchet["hamming_ci_high"])),
        ("ratchet_independence", "all_keys_unique", str(ratchet["all_keys_unique"])),
        ("ratchet_independence", "use_quantum_ratchet_randomness", str(ratchet["use_quantum_ratchet_randomness"])),
    ])

    enc = metrics["encryption_reliability"]
    rows.extend([
        ("encryption_reliability", "num_trials", str(enc["num_trials"])),
    ])
    for cipher_name, values in enc["cipher_results"].items():
        rows.extend([
            (f"encryption_{cipher_name}", "success_rate", str(values["success_rate"])),
            (f"encryption_{cipher_name}", "ci_low", str(values["ci_low"])),
            (f"encryption_{cipher_name}", "ci_high", str(values["ci_high"])),
            (f"encryption_{cipher_name}", "enc_mean_ms", str(values["enc_mean_ms"])),
            (f"encryption_{cipher_name}", "dec_mean_ms", str(values["dec_mean_ms"])),
        ])

    mon = metrics["monitor_quality"]
    rows.extend([
        ("monitor_quality", "num_trials", str(mon["num_trials"])),
        ("monitor_quality", "benign_clear_rate", str(mon["benign_clear_rate"])),
        ("monitor_quality", "benign_ci_low", str(mon["benign_ci_low"])),
        ("monitor_quality", "benign_ci_high", str(mon["benign_ci_high"])),
        ("monitor_quality", "attack_detection_rate", str(mon["attack_detection_rate"])),
        ("monitor_quality", "attack_ci_low", str(mon["attack_ci_low"])),
        ("monitor_quality", "attack_ci_high", str(mon["attack_ci_high"])),
    ])

    with open(CSV_PATH, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["section", "metric", "value"])
        for row in rows:
            writer.writerow(row)


def write_report(metrics: Dict[str, object]) -> None:
    selector = metrics["selector_uniformity"]
    ratchet = metrics["ratchet_independence"]
    enc = metrics["encryption_reliability"]
    mon = metrics["monitor_quality"]

    lines: List[str] = [
        "# Statistical Validation Report",
        "",
        "## 1. Selector Uniformity",
        f"- Sessions: {selector['num_sessions']}",
        f"- Counts (combo 0..6): {selector['counts']}",
        f"- Chi-square statistic: {selector['chi_square_stat']:.6f}",
        f"- p-value: {selector['p_value']:.6f}",
        f"- Total variation distance from uniform: {selector['tv_distance']:.6f}",
        "",
        "## 2. Ratchet Independence",
        f"- Sessions: {ratchet['num_sessions']}",
        f"- Consecutive pairs: {ratchet['pair_count']}",
        f"- Mean absolute bit-correlation: {ratchet['mean_abs_corr']:.6f}",
        f"- Max absolute bit-correlation: {ratchet['max_abs_corr']:.6f}",
        f"- Mean Hamming distance rate: {ratchet['mean_hamming']:.6f}",
        f"- 95% CI for Hamming rate: [{ratchet['hamming_ci_low']:.6f}, {ratchet['hamming_ci_high']:.6f}]",
        f"- All keys unique: {ratchet['all_keys_unique']}",
        f"- Quantum randomness used in ratchet test: {ratchet['use_quantum_ratchet_randomness']}",
        "",
        "## 3. Encryption Reliability",
        f"- Trials per cipher: {enc['num_trials']}",
    ]
    for cipher_name, values in enc["cipher_results"].items():
        lines.extend([
            f"- {cipher_name} success rate: {values['success_rate']:.6f} (95% CI [{values['ci_low']:.6f}, {values['ci_high']:.6f}])",
            f"- {cipher_name} mean encrypt ms: {values['enc_mean_ms']:.6f}",
            f"- {cipher_name} mean decrypt ms: {values['dec_mean_ms']:.6f}",
        ])
    lines.extend([
        "",
        "## 4. Monitor Quality",
        f"- Trials: {mon['num_trials']}",
        f"- Benign clear rate: {mon['benign_clear_rate']:.6f} (95% CI [{mon['benign_ci_low']:.6f}, {mon['benign_ci_high']:.6f}])",
        f"- Attack detection rate: {mon['attack_detection_rate']:.6f} (95% CI [{mon['attack_ci_low']:.6f}, {mon['attack_ci_high']:.6f}])",
        "",
        "## 5. Interpretation",
        "- High selector p-value indicates no strong evidence against near-uniform combination usage under tested sessions.",
        "- Near-zero consecutive key correlations and near-0.5 Hamming rate support ratchet key divergence.",
        "- Encryption reliability near 1.0 indicates correctness of agility modes under repeated trials.",
        "- Strong attack detection with high benign-clear rate supports monitoring efficacy under tested synthetic conditions.",
    ])

    with open(REPORT_PATH, mode="w", newline="") as f:
        f.write("\n".join(lines) + "\n")


def run_all(
    selector_sessions: int,
    ratchet_sessions: int,
    encryption_trials: int,
    monitor_trials: int,
    use_quantum_ratchet_randomness: bool,
) -> Dict[str, object]:
    selector = selector_uniformity_test(selector_sessions)
    ratchet = ratchet_independence_test(ratchet_sessions, use_quantum_ratchet_randomness)
    encryption = encryption_reliability_test(encryption_trials)
    monitor = monitor_quality_test(monitor_trials)
    metrics = {
        "selector_uniformity": selector,
        "ratchet_independence": ratchet,
        "encryption_reliability": encryption,
        "monitor_quality": monitor,
    }
    write_csv(metrics)
    write_report(metrics)
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selector-sessions", type=int, default=1200)
    parser.add_argument("--ratchet-sessions", type=int, default=80)
    parser.add_argument("--encryption-trials", type=int, default=200)
    parser.add_argument("--monitor-trials", type=int, default=300)
    parser.add_argument("--quantum-ratchet", action="store_true")
    args = parser.parse_args()

    metrics = run_all(
        selector_sessions=args.selector_sessions,
        ratchet_sessions=args.ratchet_sessions,
        encryption_trials=args.encryption_trials,
        monitor_trials=args.monitor_trials,
        use_quantum_ratchet_randomness=args.quantum_ratchet,
    )

    print("selector_p_value", metrics["selector_uniformity"]["p_value"])
    print("selector_tv_distance", metrics["selector_uniformity"]["tv_distance"])
    print("ratchet_mean_abs_corr", metrics["ratchet_independence"]["mean_abs_corr"])
    print("ratchet_mean_hamming", metrics["ratchet_independence"]["mean_hamming"])
    print("aes_success", metrics["encryption_reliability"]["cipher_results"]["AES-256-GCM"]["success_rate"])
    print("chacha_success", metrics["encryption_reliability"]["cipher_results"]["ChaCha20-Poly1305"]["success_rate"])
    print("benign_clear", metrics["monitor_quality"]["benign_clear_rate"])
    print("attack_detect", metrics["monitor_quality"]["attack_detection_rate"])
    print("csv", CSV_PATH)
    print("report", REPORT_PATH)


if __name__ == "__main__":
    main()
