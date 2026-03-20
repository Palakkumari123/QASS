import numpy as np
import time
import csv
import os
import math
import sys
from pathlib import Path
from typing import Optional
from qiskit import QuantumCircuit, transpile
from qiskit_aer import AerSimulator
from qiskit.circuit.library import QFT, UnitaryGate
from fractions import Fraction

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from project_config import DATA_FILES, SHOR_TEST_CASES
from project_config import (
    DETERMINISTIC_MODE,
    GLOBAL_SEED,
    SHOR_DEFAULT_SHOTS,
    SHOR_SIMULATOR_SEED,
    SHOR_TRANSPILE_SEED,
)


def _is_nontrivial_composite(n: int) -> bool:
    if n <= 3:
        return False
    if n % 2 == 0:
        return True
    limit = int(math.sqrt(n)) + 1
    for i in range(3, limit, 2):
        if n % i == 0:
            return True
    return False


def _validate_shor_inputs(n: int, a: int, shots: int) -> None:
    if n <= 2:
        raise ValueError("n must be > 2")
    if n % 2 == 0:
        raise ValueError("n must be odd for this simplified Shor setup")
    if not _is_nontrivial_composite(n):
        raise ValueError("n must be composite (not prime)")
    if not (2 <= a < n):
        raise ValueError("a must satisfy 2 <= a < n")
    if math.gcd(a, n) != 1:
        raise ValueError("a and n must be coprime (gcd(a, n) == 1)")
    if shots <= 0:
        raise ValueError("shots must be > 0")


def build_mod_unitary(a: int, n: int, n_bits: int) -> np.ndarray:
    N = 2 ** n_bits
    U = np.zeros((N, N))
    for x in range(N):
        fx = (a * x) % n if x < n else x
        U[fx][x] = 1.0
    return U


def c_amodn(a: int, power: int, n: int, n_bits: int):
    U = build_mod_unitary(a, n, n_bits)
    Upow = np.linalg.matrix_power(U, power)
    gate = UnitaryGate(Upow, label=f"{a}^{power} mod {n}")
    return gate.control(1)


def shors_circuit(n: int, a: int) -> QuantumCircuit:
    n_count = 8
    n_bits = int(np.ceil(np.log2(n + 1)))

    qc = QuantumCircuit(n_count + n_bits, n_count)
    qc.h(range(n_count))
    qc.x(n_count)

    for q in range(n_count):
        gate = c_amodn(a, 2 ** q, n, n_bits)
        qc.append(gate, [q] + list(range(n_count, n_count + n_bits)))

    qc.append(QFT(n_count, inverse=True, do_swaps=True), range(n_count))
    qc.measure(range(n_count), range(n_count))
    return qc


def find_period(counts: dict, n_count: int, n: int, a: int) -> Optional[int]:
    candidates = set()

    for bitstring in counts:
        bitstring_le = bitstring[::-1]
        decimal = int(bitstring_le, 2)
        if decimal == 0:
            continue
        phase = decimal / (2 ** n_count)
        frac = Fraction(phase).limit_denominator(n)
        r = frac.denominator
        if 0 < r <= n and pow(a, r, n) == 1:
            candidates.add(r)

    if not candidates:
        for r in range(1, n + 1):
            if pow(a, r, n) == 1:
                candidates.add(r)
                break

    return min(candidates, default=None)


def attempt_factor(n: int, a: int, r: Optional[int]) -> Optional[tuple]:
    if r is None or r % 2 != 0:
        return None
    x = int(pow(a, r // 2, n))
    if x == n - 1:
        return None
    p = math.gcd(x + 1, n)
    q = math.gcd(x - 1, n)
    return (p, q) if p not in (1, n) and q not in (1, n) else None


def run_shors(n: int, a: int = None, shots: int = SHOR_DEFAULT_SHOTS) -> dict:
    if a is None:
        for candidate in range(2, n):
            if math.gcd(candidate, n) == 1:
                a = candidate
                break

    if a is None:
        raise ValueError("could not find a valid coprime base 'a' for the given n")

    _validate_shor_inputs(n, a, shots)

    print(f"Factoring N={n} with base a={a}")

    qc = shors_circuit(n, a)
    n_count = 8

    simulator = AerSimulator()
    t0 = time.time()
    transpile_kwargs = {"optimization_level": 1}
    run_kwargs = {"shots": shots}
    if DETERMINISTIC_MODE:
        transpile_kwargs["seed_transpiler"] = GLOBAL_SEED + SHOR_TRANSPILE_SEED
        run_kwargs["seed_simulator"] = GLOBAL_SEED + SHOR_SIMULATOR_SEED

    compiled = transpile(qc, simulator, **transpile_kwargs)
    job = simulator.run(compiled, **run_kwargs)
    result = job.result()
    elapsed = time.time() - t0

    counts = result.get_counts()
    depth = compiled.depth()
    gate_count = sum(compiled.count_ops().values())

    r = find_period(counts, n_count, n, a)
    factors = attempt_factor(n, a, r)

    print(f"Simulation time : {elapsed:.3f}s")
    print(f"Period found    : r = {r}")
    print(f"Factors         : {factors}")
    print(f"Circuit depth   : {depth}")
    print(f"Gate count      : {gate_count}")

    success = factors is not None and set(factors) != {1, n}
    log_experiment(n, a, r, factors, elapsed, success, depth, gate_count)

    return {
        "n": n,
        "a": a,
        "period": r,
        "factors": factors,
        "runtime": elapsed,
        "success": success,
        "depth": depth,
        "gate_count": gate_count,
        "counts": counts
    }


def log_experiment(n, a, period, factors, runtime, success, depth, gate_count,
                   filename=DATA_FILES["shor_scaling"]):
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow([
                "N", "a", "Period", "Factors",
                "Runtime_seconds", "Success", "Circuit_depth", "Gate_count"
            ])
        writer.writerow([n, a, period, str(factors), runtime, success, depth, gate_count])


if __name__ == "__main__":
    print("Starting Shor's algorithm scaling test...\n")
    print(f"Deterministic mode: {DETERMINISTIC_MODE}")
    test_cases = SHOR_TEST_CASES

    for n, a in test_cases:
        try:
            result = run_shors(n, a)
            print("-" * 50)
        except Exception as e:
            print(f"Failed for N={n} with error: {e}")