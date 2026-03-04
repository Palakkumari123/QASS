import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
import csv
import os


def grover_circuit(n: int, target_state: str, num_iterations: int = None) -> QuantumCircuit:
    if len(target_state) != n:
        raise ValueError(f"target_state length {len(target_state)} must equal n={n}")

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


def run_grover(n: int, target_state: str, shots: int = 1024) -> dict:
    num_iterations = max(1, round((np.pi / 4) * np.sqrt(2 ** n)))
    print(f"Qubits: {n} | Target: {target_state} | Iterations: {num_iterations}")

    qc = grover_circuit(n, target_state, num_iterations)

    simulator = AerSimulator()
    t0 = time.time()
    compiled = transpile(qc, simulator)
    job = simulator.run(compiled, shots=shots)
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
                   filename="grover_scaling_data.csv"):
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
    for n in [4,6,8,10, 12, 14, 16, 18, 20]:
        try:
            TARGET = "1" * n
            counts = run_grover(n, TARGET)
            print("-" * 50)
        except Exception as e:
            print(f"Failed at n={n} with error: {e}")
            break