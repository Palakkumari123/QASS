import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import sys
from pathlib import Path
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import csv
import os

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from project_config import (
    DATA_FILES,
    DETERMINISTIC_MODE,
    GLOBAL_SEED,
    GROVER_DEFAULT_SHOTS,
    GROVER_MAX_QUBITS,
    GROVER_MIN_QUBITS,
    GROVER_QUBIT_SIZES,
    GROVER_SIMULATOR_SEED,
    GROVER_TRANSPILE_SEED,
)


def _validate_grover_inputs(n: int, target_state: str, shots: int) -> None:
    if n < GROVER_MIN_QUBITS:
        raise ValueError(f"n must be >= {GROVER_MIN_QUBITS}")
    if n > GROVER_MAX_QUBITS:
        raise ValueError(f"n must be <= {GROVER_MAX_QUBITS} to avoid simulator blowup")
    if len(target_state) != n:
        raise ValueError(f"target_state length {len(target_state)} must equal n={n}")
    if set(target_state) - {"0", "1"}:
        raise ValueError("target_state must contain only '0' and '1'")
    if shots <= 0:
        raise ValueError("shots must be > 0")


def grover_circuit(n: int, target_state: str, num_iterations: int = None) -> QuantumCircuit:
    _validate_grover_inputs(n, target_state, GROVER_DEFAULT_SHOTS)

    if num_iterations is None:
        num_iterations = max(1, round((np.pi / 4) * np.sqrt(2 ** n)))

    target_le = target_state[::-1]

    qc = QuantumCircuit(n)
    qc.h(range(n))

    for _ in range(num_iterations):
        _apply_oracle(qc, n, target_le)
        _apply_diffusion(qc, n)

    qc.measure_all()
    return qc


def _apply_oracle(qc: QuantumCircuit, n: int, target_le: str) -> None:
    for i, bit in enumerate(target_le):
        if bit == '0':
            qc.x(i)

    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)

    for i, bit in enumerate(target_le):
        if bit == '0':
            qc.x(i)

    qc.barrier()


def _apply_diffusion(qc: QuantumCircuit, n: int) -> None:
    qc.h(range(n))
    qc.x(range(n))

    qc.h(n - 1)
    qc.mcx(list(range(n - 1)), n - 1)
    qc.h(n - 1)

    qc.x(range(n))
    qc.h(range(n))

    qc.barrier()


def run_grover(n: int, target_state: str, shots: int = GROVER_DEFAULT_SHOTS) -> dict:
    _validate_grover_inputs(n, target_state, shots)

    num_iterations = max(1, round((np.pi / 4) * np.sqrt(2 ** n)))
    print(f"Qubits: {n} | Target: {target_state} | Iterations: {num_iterations}")

    qc = grover_circuit(n, target_state, num_iterations)

    simulator = AerSimulator()
    t0 = time.time()
    transpile_kwargs = {}
    run_kwargs = {"shots": shots}
    if DETERMINISTIC_MODE:
        transpile_kwargs["seed_transpiler"] = GLOBAL_SEED + GROVER_TRANSPILE_SEED
        run_kwargs["seed_simulator"] = GLOBAL_SEED + GROVER_SIMULATOR_SEED

    compiled = transpile(qc, simulator, **transpile_kwargs)
    job = simulator.run(compiled, **run_kwargs)
    result = job.result()
    elapsed = time.time() - t0

    counts = result.get_counts()
    success_prob = max(counts.values()) / shots
    print(f"Simulation time: {elapsed:.3f}s")
    print(f"Top result: {max(counts, key=counts.get)} "
          f"({success_prob * 100:.1f}% of shots)")

    depth = compiled.depth()
    gate_count = sum(compiled.count_ops().values())
    log_experiment(n, num_iterations, elapsed, success_prob, depth, gate_count)
    return counts


def plot_results(counts: dict, target_state: str, n: int) -> None:
    top = dict(sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10])
    labels = list(top.keys())
    values = list(top.values())
    colors = ['#e74c3c' if lbl == target_state else '#3498db' for lbl in labels]

    plt.figure(figsize=(10, 5))
    plt.bar(labels, values, color=colors)
    plt.xlabel("Measured State")
    plt.ylabel("Counts")
    plt.title(f"Grover's Algorithm | n={n} qubits | target=|{target_state}⟩")
    plt.xticks(rotation=45, ha='right')
    plt.legend(handles=[
        Patch(color='#e74c3c', label='Target state'),
        Patch(color='#3498db', label='Other states'),
    ])
    plt.tight_layout()
    plt.savefig("grover_results.png", dpi=150)
    plt.show()


def log_experiment(n, iterations, runtime, success_prob, depth, gate_count,
                   filename=DATA_FILES["grover_scaling"]):
    file_exists = os.path.isfile(filename)

    with open(filename, mode="a", newline="") as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([
                "Qubits",
                "Iterations",
                "Runtime_seconds",
                "Success_probability",
                "Circuit_depth",
                "Gate_count"
            ])

        writer.writerow([n, iterations, runtime, success_prob, depth, gate_count])


if __name__ == "__main__":
    print("Starting scaling test...\n")
    print(f"Deterministic mode: {DETERMINISTIC_MODE}")
    for n in GROVER_QUBIT_SIZES:
        try:
            TARGET = "1" * n
            counts = run_grover(n, TARGET)
            print("-" * 50)
        except Exception as e:
            print(f"Failed at n={n} with error: {e}")
            break