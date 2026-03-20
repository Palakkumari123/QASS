import numpy as np
import matplotlib.pyplot as plt
import csv
import importlib
import os
import sys
from pathlib import Path
from scipy.stats import chisquare
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit.compiler import transpile

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from project_config import DATA_FILES, QRNG_BATCH_SIZE, QRNG_NUM_BITS, QRNG_TRIALS
from project_config import (
    DETERMINISTIC_MODE,
    GLOBAL_SEED,
    QRNG_BACKEND_MODE,
    QRNG_DEBIAS_METHOD,
    QRNG_HARDWARE_MAX_ATTEMPTS,
    QRNG_HARDWARE_SHOTS,
    QRNG_IBM_BACKEND,
    QRNG_IBM_CHANNEL,
    QRNG_IBM_INSTANCE,
    QRNG_SIMULATOR_SEED,
    QRNG_TRANSPILE_SEED,
)


NUM_BITS = QRNG_NUM_BITS
RUNS = QRNG_TRIALS
BATCH_SIZE = QRNG_BATCH_SIZE


def _validate_backend_mode(mode: str) -> str:
    mode = mode.strip().lower()
    if mode not in {"simulator", "hardware"}:
        raise ValueError("mode must be 'simulator' or 'hardware'")
    return mode


def _validate_debias_method(method: str) -> str:
    method = method.strip().lower()
    if method not in {"none", "von_neumann"}:
        raise ValueError("debias_method must be 'none' or 'von_neumann'")
    return method


def _von_neumann_extract(raw_bits: np.ndarray) -> np.ndarray:
    if len(raw_bits) < 2:
        return np.array([], dtype=int)
    pairs = raw_bits[: len(raw_bits) - (len(raw_bits) % 2)].reshape(-1, 2)
    kept = pairs[pairs[:, 0] != pairs[:, 1]]
    return kept[:, 0].astype(int)


def _apply_debias(raw_bits: np.ndarray, method: str) -> np.ndarray:
    return raw_bits if method == "none" else _von_neumann_extract(raw_bits)


def classical_prng(num_bits: int, seed: int = 42) -> np.ndarray:
    if num_bits <= 0:
        raise ValueError("num_bits must be > 0")
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, num_bits)


def quantum_rng_simulator(num_bits: int, debias_method: str = QRNG_DEBIAS_METHOD) -> tuple:
    if num_bits <= 0:
        raise ValueError("num_bits must be > 0")
    debias_method = _validate_debias_method(debias_method)

    simulator = Aer.get_backend('aer_simulator')
    raw_bits = []

    transpile_kwargs = {}
    run_kwargs = {"shots": 1}

    if DETERMINISTIC_MODE:
        transpile_kwargs["seed_transpiler"] = GLOBAL_SEED + QRNG_TRANSPILE_SEED
        run_kwargs["seed_simulator"] = GLOBAL_SEED + QRNG_SIMULATOR_SEED

    max_attempts = max(1, num_bits // BATCH_SIZE + 5)
    for _ in range(max_attempts):
        qc = QuantumCircuit(BATCH_SIZE, BATCH_SIZE)
        qc.h(range(BATCH_SIZE))
        qc.measure(range(BATCH_SIZE), range(BATCH_SIZE))
        compiled = transpile(qc, simulator, **transpile_kwargs)
        job = simulator.run(compiled, **run_kwargs)
        result = job.result().get_counts()
        bitstring = list(result.keys())[0]
        raw_bits.extend([int(b) for b in bitstring])

        extracted = _apply_debias(np.array(raw_bits, dtype=int), debias_method)
        if len(extracted) >= num_bits:
            efficiency = len(extracted) / len(raw_bits) if raw_bits else 0.0
            metadata = {
                "backend_mode": "simulator",
                "debias_method": debias_method,
                "raw_bits_generated": len(raw_bits),
                "extractor_efficiency": efficiency,
                "backend_name": "aer_simulator",
                "job_id": "simulator",
            }
            return extracted[:num_bits], metadata

    raise RuntimeError("Simulator QRNG could not generate enough bits with current settings")


def quantum_rng_hardware(num_bits: int, debias_method: str = QRNG_DEBIAS_METHOD) -> tuple:
    if num_bits <= 0:
        raise ValueError("num_bits must be > 0")
    if QRNG_HARDWARE_SHOTS <= 0:
        raise ValueError("QASS_QRNG_HARDWARE_SHOTS must be > 0")

    debias_method = _validate_debias_method(debias_method)
    token = os.getenv("IBM_QUANTUM_TOKEN")
    if not token:
        raise RuntimeError(
            "Hardware QRNG requires IBM_QUANTUM_TOKEN in the environment"
        )

    try:
        runtime = importlib.import_module("qiskit_ibm_runtime")
        QiskitRuntimeService = runtime.QiskitRuntimeService
        Sampler = runtime.SamplerV2
    except ImportError as exc:
        raise RuntimeError(
            "Hardware QRNG requires qiskit-ibm-runtime. Install it with: pip install qiskit-ibm-runtime"
        ) from exc

    service = QiskitRuntimeService(
        channel=QRNG_IBM_CHANNEL,
        token=token,
        instance=QRNG_IBM_INSTANCE,
    )
    backend = (
        service.backend(QRNG_IBM_BACKEND)
        if QRNG_IBM_BACKEND
        else service.least_busy(operational=True, simulator=False)
    )
    sampler = Sampler(mode=backend)

    raw_bits = []
    last_job_id = ""

    for _ in range(QRNG_HARDWARE_MAX_ATTEMPTS):
        qc = QuantumCircuit(BATCH_SIZE, BATCH_SIZE)
        qc.h(range(BATCH_SIZE))
        qc.measure(range(BATCH_SIZE), range(BATCH_SIZE))
        compiled = transpile(qc, backend)
        job = sampler.run([compiled], shots=QRNG_HARDWARE_SHOTS)
        last_job_id = job.job_id()
        result = job.result()
        dist = result[0].data.c.get_counts()
        bitstring = list(dist.keys())[0]
        raw_bits.extend([int(b) for b in bitstring])

        extracted = _apply_debias(np.array(raw_bits, dtype=int), debias_method)
        if len(extracted) >= num_bits:
            efficiency = len(extracted) / len(raw_bits) if raw_bits else 0.0
            metadata = {
                "backend_mode": "hardware",
                "debias_method": debias_method,
                "raw_bits_generated": len(raw_bits),
                "extractor_efficiency": efficiency,
                "backend_name": backend.name,
                "job_id": last_job_id,
            }
            return extracted[:num_bits], metadata

    raise RuntimeError("Hardware QRNG could not generate enough bits before reaching max attempts")


def quantum_rng_with_metadata(
    num_bits: int,
    mode: str = QRNG_BACKEND_MODE,
    debias_method: str = QRNG_DEBIAS_METHOD,
) -> tuple:
    mode = _validate_backend_mode(mode)
    if mode == "hardware":
        return quantum_rng_hardware(num_bits, debias_method=debias_method)
    return quantum_rng_simulator(num_bits, debias_method=debias_method)


def quantum_rng(
    num_bits: int,
    mode: str = QRNG_BACKEND_MODE,
    debias_method: str = QRNG_DEBIAS_METHOD,
) -> np.ndarray:
    bits, _ = quantum_rng_with_metadata(num_bits, mode=mode, debias_method=debias_method)
    return bits


def calculate_entropy(bits: np.ndarray) -> float:
    p1 = np.mean(bits)
    p0 = 1 - p1
    return 0.0 if p0 == 0 or p1 == 0 else -p0 * np.log2(p0) - p1 * np.log2(p1)


def calculate_chi_square(bits: np.ndarray) -> tuple:
    observed = [np.sum(bits == 0), np.sum(bits == 1)]
    expected = [len(bits) / 2, len(bits) / 2]
    stat, p_value = chisquare(observed, expected)
    return stat, p_value


def runs_test(bits: np.ndarray) -> float:
    runs = 1 + sum(bits[i] != bits[i - 1] for i in range(1, len(bits)))
    expected_runs = (2 * np.sum(bits) * np.sum(1 - bits)) / len(bits) + 1
    return abs(runs - expected_runs) / expected_runs * 100


def serial_correlation(bits: np.ndarray) -> float:
    return float(np.corrcoef(bits[:-1], bits[1:])[0, 1])


def analyze_source(name: str, bits: np.ndarray, metadata: dict | None = None) -> dict:
    metadata = metadata or {}
    ent = calculate_entropy(bits)
    chi_stat, p_value = calculate_chi_square(bits)
    runs_dev = runs_test(bits)
    correlation = serial_correlation(bits)
    entropy_efficiency = (ent / 1.0) * 100

    return {
        "source": name,
        "num_bits": len(bits),
        "entropy_bits": ent,
        "max_entropy": 1.0,
        "entropy_efficiency": entropy_efficiency,
        "chi_square_stat": chi_stat,
        "chi_square_p": p_value,
        "runs_deviation": runs_dev,
        "serial_correlation": correlation,
        "passes_uniformity": p_value > 0.05,
        "passes_correlation": abs(correlation) < 0.01,
        "backend_mode": metadata.get("backend_mode", "n/a"),
        "debias_method": metadata.get("debias_method", "none"),
        "raw_bits_generated": metadata.get("raw_bits_generated", len(bits)),
        "extractor_efficiency": metadata.get("extractor_efficiency", 1.0),
        "backend_name": metadata.get("backend_name", "n/a"),
        "job_id": metadata.get("job_id", "n/a"),
    }


def run_multiple_trials(runs: int) -> tuple:
    if runs <= 0:
        raise ValueError("runs must be > 0")

    classical_entropies = []
    quantum_entropies = []
    classical_correlations = []
    quantum_correlations = []

    for i in range(runs):
        print(f"  Trial {i + 1}/{runs}...")
        c_bits = classical_prng(NUM_BITS, seed=i)
        q_bits = quantum_rng(NUM_BITS)

        classical_entropies.append(calculate_entropy(c_bits))
        quantum_entropies.append(calculate_entropy(q_bits))
        classical_correlations.append(abs(serial_correlation(c_bits)))
        quantum_correlations.append(abs(serial_correlation(q_bits)))

    return (classical_entropies, quantum_entropies,
            classical_correlations, quantum_correlations)


def log_results(classical: dict, quantum: dict, filename=DATA_FILES["qrng_entropy"]):
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Source", "Num_Bits", "Entropy_bits", "Entropy_Efficiency",
                "Chi_Square_Stat", "Chi_Square_P", "Runs_Deviation",
                "Serial_Correlation", "Passes_Uniformity", "Passes_Correlation",
                "Backend_Mode", "Debias_Method", "Raw_Bits_Generated",
                "Extractor_Efficiency", "Backend_Name", "Job_ID"
            ])
        for r in [classical, quantum]:
            writer.writerow([
                r["source"], r["num_bits"], r["entropy_bits"],
                r["entropy_efficiency"], r["chi_square_stat"],
                r["chi_square_p"], r["runs_deviation"],
                r["serial_correlation"], r["passes_uniformity"],
                r["passes_correlation"], r["backend_mode"],
                r["debias_method"], r["raw_bits_generated"],
                r["extractor_efficiency"], r["backend_name"], r["job_id"]
            ])


def plot_entropy_comparison(classical: dict, quantum: dict):
    sources = ["Classical PRNG", "Quantum RNG"]
    entropies = [classical["entropy_bits"], quantum["entropy_bits"]]
    colors = ['#e74c3c', '#2ecc71']

    plt.figure(figsize=(8, 5))
    bars = plt.bar(sources, entropies, color=colors, width=0.4)
    plt.axhline(y=1.0, color='black', linestyle='--', linewidth=1, label="Max Entropy (1.0 bit)")
    plt.ylim(0.999, 1.0001)
    plt.ylabel("Shannon Entropy (bits per bit)")
    plt.title("Entropy Comparison: Classical PRNG vs Quantum RNG")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5, axis='y')
    for bar, val in zip(bars, entropies):
        plt.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                 f'{val:.8f}', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.savefig("qrng_entropy_comparison.png", dpi=300)
    plt.show()


def plot_entropy_distribution(classical_entropies: list, quantum_entropies: list):
    plt.figure(figsize=(9, 5))
    plt.hist(classical_entropies, bins=20, alpha=0.6, color='#e74c3c',
             label="Classical PRNG", edgecolor='white')
    plt.hist(quantum_entropies, bins=20, alpha=0.6, color='#2ecc71',
             label="Quantum RNG", edgecolor='white')
    plt.axvline(x=1.0, color='black', linestyle='--', linewidth=1, label="Max Entropy")
    plt.xlabel("Shannon Entropy (bits per bit)")
    plt.ylabel("Frequency")
    plt.title(f"Entropy Distribution over {RUNS} Trials")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig("qrng_entropy_distribution.png", dpi=300)
    plt.show()


def plot_correlation_comparison(classical: dict, quantum: dict):
    sources = ["Classical PRNG", "Quantum RNG"]
    correlations = [abs(classical["serial_correlation"]), abs(quantum["serial_correlation"])]
    colors = ['#e74c3c', '#2ecc71']

    plt.figure(figsize=(8, 5))
    plt.bar(sources, correlations, color=colors, width=0.4)
    plt.axhline(y=0.01, color='black', linestyle='--', linewidth=1,
                label="Correlation Threshold (0.01)")
    plt.ylabel("Serial Correlation (absolute)")
    plt.title("Serial Correlation: Classical PRNG vs Quantum RNG")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5, axis='y')
    plt.tight_layout()
    plt.savefig("qrng_correlation.png", dpi=300)
    plt.show()


def plot_trial_entropies(classical_entropies: list, quantum_entropies: list):
    trials = list(range(1, RUNS + 1))
    plt.figure(figsize=(10, 5))
    plt.plot(trials, classical_entropies, color='#e74c3c', alpha=0.7,
             marker='o', label="Classical PRNG")
    plt.plot(trials, quantum_entropies, color='#2ecc71', alpha=0.7,
             marker='o', label="Quantum RNG")
    plt.axhline(y=1.0, color='black', linestyle='--', linewidth=1, label="Max Entropy")
    plt.xlabel("Trial")
    plt.ylabel("Shannon Entropy (bits per bit)")
    plt.title(f"Entropy per Trial: Classical PRNG vs Quantum RNG ({RUNS} Trials)")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig("qrng_entropy_per_trial.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    print("Running QRNG Entropy Analysis...\n")
    np.random.seed((GLOBAL_SEED + QRNG_SIMULATOR_SEED) if DETERMINISTIC_MODE else None)
    print(f"Deterministic mode: {DETERMINISTIC_MODE}")
    print(f"QRNG backend mode: {QRNG_BACKEND_MODE}")
    print(f"QRNG debias method: {QRNG_DEBIAS_METHOD}")

    print("Generating bits...")
    c_bits = classical_prng(NUM_BITS)
    q_bits, q_metadata = quantum_rng_with_metadata(NUM_BITS)

    classical_result = analyze_source("Classical PRNG", c_bits, metadata={"backend_mode": "classical"})
    quantum_result = analyze_source("Quantum RNG", q_bits, metadata=q_metadata)

    print(f"{'Metric':<25} {'Classical PRNG':<20} Quantum RNG")
    print("-" * 65)
    print(f"{'Entropy (bits/bit)':<25} {classical_result['entropy_bits']:<20.8f} {quantum_result['entropy_bits']:.8f}")
    print(f"{'Entropy Efficiency':<25} {classical_result['entropy_efficiency']:<20.6f} {quantum_result['entropy_efficiency']:.6f}")
    print(f"{'Chi-Square p-value':<25} {classical_result['chi_square_p']:<20.6f} {quantum_result['chi_square_p']:.6f}")
    print(f"{'Runs Deviation (%)':<25} {classical_result['runs_deviation']:<20.6f} {quantum_result['runs_deviation']:.6f}")
    print(f"{'Serial Correlation':<25} {classical_result['serial_correlation']:<20.8f} {quantum_result['serial_correlation']:.8f}")
    print(f"{'Passes Uniformity':<25} {classical_result['passes_uniformity']:<20} {quantum_result['passes_uniformity']}")
    print(f"{'Passes Correlation':<25} {classical_result['passes_correlation']:<20} {quantum_result['passes_correlation']}")
    print(f"{'QRNG Backend':<25} {'n/a':<20} {quantum_result['backend_name']}")
    print(f"{'QRNG Job ID':<25} {'n/a':<20} {quantum_result['job_id']}")

    log_results(classical_result, quantum_result)

    print("\nRunning multiple trials...")
    c_ents, q_ents, c_corrs, q_corrs = run_multiple_trials(RUNS)
    print(f"Classical entropy mean: {np.mean(c_ents):.8f} ± {np.std(c_ents):.2e}")
    print(f"Quantum entropy mean  : {np.mean(q_ents):.8f} ± {np.std(q_ents):.2e}")

    plot_entropy_comparison(classical_result, quantum_result)
    plot_entropy_distribution(c_ents, q_ents)
    plot_correlation_comparison(classical_result, quantum_result)
    plot_trial_entropies(c_ents, q_ents)

    print("\nAnalysis complete. CSV and plots saved.")