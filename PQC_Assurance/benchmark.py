import time
import csv
import os
import statistics
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from kyber_py.kyber import Kyber512, Kyber768, Kyber1024
# functional correctness test and constant-time analysis.

RUNS = 1000
VARIANTS = {
    "Kyber512": Kyber512,
    "Kyber768": Kyber768,
    "Kyber1024": Kyber1024
}


def verify_functional_correctness(name: str, variant) -> dict:
    print(f"Functional correctness test: {name}")
    passed = 0
    failed = 0
    failures = []

    for i in range(RUNS):
        pk, sk = variant.keygen()
        ss_enc, ct = variant.encaps(pk)
        ss_dec = variant.decaps(sk, ct)

        if ss_enc == ss_dec:
            passed += 1
        else:
            failed += 1
            failures.append(i)

    pass_rate = passed / RUNS * 100
    print(f"  Passed: {passed}/{RUNS} ({pass_rate:.2f}%)")
    if failures:
        print(f"  Failed at runs: {failures[:5]}")

    return {
        "algorithm": name,
        "runs": RUNS,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "functionally_correct": failed == 0
    }


def verify_constant_time(name: str, variant) -> dict:
    print(f"Constant-time test: {name}")
    timings = []

    pk, sk = variant.keygen()

    for _ in range(RUNS):
        _, ct = variant.encaps(pk)
        t0 = time.perf_counter()
        variant.decaps(sk, ct)
        timings.append((time.perf_counter() - t0) * 1000)

    mean = statistics.mean(timings)
    std = statistics.stdev(timings)
    cv = (std / mean) * 100
    min_t = min(timings)
    max_t = max(timings)

    print(f"  Mean: {mean:.4f}ms | Std: {std:.4f}ms | CV: {cv:.2f}%")
    print(f"  Min: {min_t:.4f}ms | Max: {max_t:.4f}ms")

    return {
        "algorithm": name,
        "mean_ms": mean,
        "std_ms": std,
        "cv_percent": cv,
        "min_ms": min_t,
        "max_ms": max_t,
        "timings": timings,
        "constant_time": cv < 10.0
    }


def log_correctness_results(results: list, filename="formal_verification_correctness.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Algorithm", "Runs", "Passed", "Failed",
                "Pass_Rate", "Functionally_Correct"
            ])
        for r in results:
            writer.writerow([
                r["algorithm"], r["runs"], r["passed"], r["failed"],
                r["pass_rate"], r["functionally_correct"]
            ])


def log_timing_results(results: list, filename="formal_verification_timing.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Algorithm", "Mean_ms", "Std_ms", "CV_percent",
                "Min_ms", "Max_ms", "Constant_Time"
            ])
        for r in results:
            writer.writerow([
                r["algorithm"], r["mean_ms"], r["std_ms"], r["cv_percent"],
                r["min_ms"], r["max_ms"], r["constant_time"]
            ])


def plot_correctness(results: list):
    algorithms = [r["algorithm"] for r in results]
    pass_rates = [r["pass_rate"] for r in results]
    colors = ['#2ecc71' if r["functionally_correct"] else '#e74c3c' for r in results]

    plt.figure(figsize=(8, 5))
    plt.bar(algorithms, pass_rates, color=colors)
    plt.ylim(0, 105)
    plt.xlabel("Algorithm")
    plt.ylabel("Pass Rate (%)")
    plt.title("Functional Correctness: Shared Secret Match Rate")
    plt.grid(True, linestyle="--", linewidth=0.5, axis='y')
    plt.legend(handles=[
        Patch(color='#2ecc71', label='100% Correct'),
        Patch(color='#e74c3c', label='Failures Detected'),
    ])
    plt.tight_layout()
    plt.savefig("fv_correctness.png", dpi=300)
    plt.show()


def plot_timing_subplot(ax, result: dict):
    ax.hist(result["timings"], bins=50, color='#3498db', edgecolor='white')
    ax.axvline(result["mean_ms"], color='#e74c3c', linestyle='--', label=f'Mean: {result["mean_ms"]:.3f}ms')
    ax.set_title(f'{result["algorithm"]} Decaps Timing\nCV={result["cv_percent"]:.2f}%')
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Frequency")
    ax.legend()
    ax.grid(True, linestyle="--", linewidth=0.5)


def plot_timing_distribution(results: list):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    for ax, r in zip(axes, results):
        plot_timing_subplot(ax, r)

    plt.suptitle("Constant-Time Analysis: Decapsulation Timing Distribution", y=1.02)
    plt.tight_layout()
    plt.savefig("fv_timing_distribution.png", dpi=300)
    plt.show()


def plot_timing_summary(results: list):
    algorithms = [r["algorithm"] for r in results]
    means = [r["mean_ms"] for r in results]
    stds = [r["std_ms"] for r in results]
    colors = ['#2ecc71' if r["constant_time"] else '#e74c3c' for r in results]

    plt.figure(figsize=(8, 5))
    plt.bar(algorithms, means, yerr=stds, color=colors, capsize=8)
    plt.xlabel("Algorithm")
    plt.ylabel("Decapsulation Time (ms)")
    plt.title("Constant-Time Analysis: Mean Decapsulation Time ± Std Dev")
    plt.grid(True, linestyle="--", linewidth=0.5, axis='y')
    plt.legend(handles=[
        Patch(color='#2ecc71', label='CV < 10% (Constant-Time)'),
        Patch(color='#e74c3c', label='CV ≥ 10% (Not Constant-Time)'),
    ])
    plt.tight_layout()
    plt.savefig("fv_timing_summary.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    print("=" * 50)
    print("PART 1: Functional Correctness")
    print("=" * 50)
    correctness_results = []
    for name, variant in VARIANTS.items():
        correctness_results.append(verify_functional_correctness(name, variant))
        print()

    print("=" * 50)
    print("PART 2: Constant-Time Analysis")
    print("=" * 50)
    timing_results = []
    for name, variant in VARIANTS.items():
        timing_results.append(verify_constant_time(name, variant))
        print()

    log_correctness_results(correctness_results)
    log_timing_results(timing_results)
    plot_correctness(correctness_results)
    plot_timing_distribution(timing_results)
    plot_timing_summary(timing_results)

    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"{'Algorithm':<12} {'Correct':<10} {'Pass Rate':<12} {'CV%':<10} Const-Time")
    print("-" * 55)
    for c, t in zip(correctness_results, timing_results):
        print(f"{c['algorithm']:<12} {str(c['functionally_correct']):<10} "
              f"{c['pass_rate']:<12.2f} {t['cv_percent']:<10.2f} {t['constant_time']}")