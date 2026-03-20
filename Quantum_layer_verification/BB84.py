import numpy as np
import csv
import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from project_config import (
    BB84_ATTENUATION_DB_PER_KM,
    BB84_DISTANCES_KM,
    BB84_NOISE_RATE,
    BB84_NUM_BITS,
    BB84_RANDOM_SOURCE,
    BB84_SEED,
    DATA_FILES,
    DETERMINISTIC_MODE,
    GLOBAL_SEED,
)


NUM_BITS = BB84_NUM_BITS
NOISE_RATE = BB84_NOISE_RATE
DISTANCES = list(BB84_DISTANCES_KM)
ATTENUATION = BB84_ATTENUATION_DB_PER_KM


def photon_survival_prob(distance_km: float, attenuation_db_per_km: float = ATTENUATION) -> float:
    return 10 ** (-attenuation_db_per_km * distance_km / 10)


def _generate_bits(num_bits: int, random_source: str) -> np.ndarray:
    source = random_source.strip().lower()
    if source == "classical":
        return np.random.randint(0, 2, num_bits)
    if source == "qrng":
        try:
            from QRNG import quantum_rng
        except ImportError:
            from Quantum_layer_verification.QRNG import quantum_rng
        return quantum_rng(num_bits)
    raise ValueError("random_source must be 'classical' or 'qrng'")


def bb84_simulate(num_bits: int, distance_km: float, noise_rate: float,
                  eavesdrop: bool = False, random_source: str = BB84_RANDOM_SOURCE) -> dict:

    alice_bits = _generate_bits(num_bits, random_source)
    alice_bases = _generate_bits(num_bits, random_source)

    survival_prob = photon_survival_prob(distance_km)
    survived = np.random.random(num_bits) < survival_prob
    num_survived = np.sum(survived)

    alice_bits_recv = alice_bits[survived]
    alice_bases_recv = alice_bases[survived]

    if eavesdrop:
        eve_bases = np.random.randint(0, 2, num_survived)
        eve_wrong = eve_bases != alice_bases_recv
        eve_bits = alice_bits_recv.copy()
        eve_bits[eve_wrong] = np.random.randint(0, 2, np.sum(eve_wrong))
        transmitted_bits = eve_bits
    else:
        transmitted_bits = alice_bits_recv
    
    transmitted_bases = alice_bases_recv

    bob_bases = _generate_bits(num_survived, random_source)
    bob_bits = transmitted_bits.copy()

    noise_mask = np.random.random(num_survived) < noise_rate
    bob_bits[noise_mask] = 1 - bob_bits[noise_mask]

    if eavesdrop:
        eve_disturbed = (eve_bases != alice_bases_recv)
        bob_bits[eve_disturbed] = np.random.randint(0, 2, np.sum(eve_disturbed))

    matching_bases = bob_bases == transmitted_bases
    sifted_alice = alice_bits_recv[matching_bases]
    sifted_bob = bob_bits[matching_bases]
    sifted_key_length = len(sifted_alice)

    errors = np.sum(sifted_alice != sifted_bob)
    qber = errors / sifted_key_length if sifted_key_length > 0 else 1.0

    key_rate = sifted_key_length / num_bits

    secure = qber < 0.11

    return {
        "distance_km": distance_km,
        "eavesdrop": eavesdrop,
        "num_bits_sent": num_bits,
        "num_bits_received": num_survived,
        "photon_survival_prob": survival_prob,
        "sifted_key_length": sifted_key_length,
        "qber": qber,
        "key_rate": key_rate,
        "secure": secure
    }


def log_results(results: list, filename=DATA_FILES["bb84"]):
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Distance_km", "Eavesdrop", "Bits_Sent", "Bits_Received",
                "Photon_Survival_Prob", "Sifted_Key_Length",
                "QBER", "Key_Rate", "Secure"
            ])
        for r in results:
            writer.writerow([
                r["distance_km"], r["eavesdrop"], r["num_bits_sent"],
                r["num_bits_received"], r["photon_survival_prob"],
                r["sifted_key_length"], r["qber"], r["key_rate"], r["secure"]
            ])


def plot_qber_vs_distance(results_no_eve: list, results_eve: list):
    distances = [r["distance_km"] for r in results_no_eve]
    qber_no_eve = [r["qber"] * 100 for r in results_no_eve]
    qber_eve = [r["qber"] * 100 for r in results_eve]

    plt.figure(figsize=(9, 5))
    plt.plot(distances, qber_no_eve, marker='o', color='#2ecc71', label="No Eavesdropping")
    plt.plot(distances, qber_eve, marker='s', color='#e74c3c', label="With Eavesdropping")
    plt.axhline(y=11, color='black', linestyle='--', linewidth=1, label="Security Threshold (11%)")
    plt.xlabel("Distance (km)")
    plt.ylabel("QBER (%)")
    plt.title("Quantum Bit Error Rate vs Distance")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig("bb84_qber_vs_distance.png", dpi=300)
    plt.show()


def plot_key_rate_vs_distance(results_no_eve: list, results_eve: list):
    distances = [r["distance_km"] for r in results_no_eve]
    key_rate_no_eve = [r["key_rate"] * 100 for r in results_no_eve]
    key_rate_eve = [r["key_rate"] * 100 for r in results_eve]

    plt.figure(figsize=(9, 5))
    plt.plot(distances, key_rate_no_eve, marker='o', color='#2ecc71', label="No Eavesdropping")
    plt.plot(distances, key_rate_eve, marker='s', color='#e74c3c', label="With Eavesdropping")
    plt.xlabel("Distance (km)")
    plt.ylabel("Key Generation Rate (%)")
    plt.title("Key Generation Rate vs Distance")
    plt.legend()
    plt.grid(True, linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig("bb84_key_rate_vs_distance.png", dpi=300)
    plt.show()


def plot_photon_survival(results: list):
    distances = [r["distance_km"] for r in results]
    survival = [r["photon_survival_prob"] * 100 for r in results]
    received = [r["num_bits_received"] for r in results]

    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax1.plot(distances, survival, marker='o', color='#3498db', label="Survival Probability (%)")
    ax1.set_xlabel("Distance (km)")
    ax1.set_ylabel("Photon Survival Probability (%)", color='#3498db')
    ax1.tick_params(axis='y', labelcolor='#3498db')

    ax2 = ax1.twinx()
    ax2.bar(distances, received, alpha=0.3, color='#9b59b6', width=4, label="Photons Received")
    ax2.set_ylabel("Photons Received", color='#9b59b6')
    ax2.tick_params(axis='y', labelcolor='#9b59b6')

    plt.title("Photon Loss vs Distance")
    fig.legend(loc='upper right', bbox_to_anchor=(0.88, 0.88))
    plt.tight_layout()
    plt.savefig("bb84_photon_loss.png", dpi=300)
    plt.show()


def plot_sifted_key_length(results_no_eve: list):
    distances = [r["distance_km"] for r in results_no_eve]
    key_lengths = [r["sifted_key_length"] for r in results_no_eve]
    secure = [r["secure"] for r in results_no_eve]
    colors = ['#2ecc71' if s else '#e74c3c' for s in secure]

    plt.figure(figsize=(9, 5))
    plt.bar(distances, key_lengths, color=colors, width=6)
    plt.xlabel("Distance (km)")
    plt.ylabel("Sifted Key Length (bits)")
    plt.title("Sifted Key Length vs Distance")
    plt.legend(handles=[
        Patch(color='#2ecc71', label='Secure (QBER < 11%)'),
        Patch(color='#e74c3c', label='Insecure (QBER ≥ 11%)'),
    ])
    plt.grid(True, linestyle="--", linewidth=0.5, axis='y')
    plt.tight_layout()
    plt.savefig("bb84_sifted_key_length.png", dpi=300)
    plt.show()


if __name__ == "__main__":
    print("Running BB84 QKD Simulation...\n")
    seed = GLOBAL_SEED + BB84_SEED
    np.random.seed(seed if DETERMINISTIC_MODE else None)
    print(f"Deterministic mode: {DETERMINISTIC_MODE}")
    print(f"BB84 random source: {BB84_RANDOM_SOURCE}")

    results_no_eve = []
    results_eve = []

    print(f"{'Distance':<12} {'QBER (no eve)':<18} {'QBER (eve)':<15} {'Key Rate':<12} Secure")
    print("-" * 65)

    for dist in DISTANCES:
        r_no_eve = bb84_simulate(NUM_BITS, dist, NOISE_RATE, eavesdrop=False, random_source=BB84_RANDOM_SOURCE)
        r_eve = bb84_simulate(NUM_BITS, dist, NOISE_RATE, eavesdrop=True, random_source=BB84_RANDOM_SOURCE)
        results_no_eve.append(r_no_eve)
        results_eve.append(r_eve)
        print(f"{dist:<12} {r_no_eve['qber']*100:<18.2f} {r_eve['qber']*100:<15.2f} "
              f"{r_no_eve['key_rate']*100:<12.2f} {r_no_eve['secure']}")

    log_results(results_no_eve + results_eve)

    plot_qber_vs_distance(results_no_eve, results_eve)
    plot_key_rate_vs_distance(results_no_eve, results_eve)
    plot_photon_survival(results_no_eve)
    plot_sifted_key_length(results_no_eve)

    print("\nSimulation complete. CSV and plots saved.")