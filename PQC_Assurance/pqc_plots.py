import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from project_config import DATA_FILES


filename = DATA_FILES["pqc_benchmark"]
if not Path(filename).is_file() and Path("kyber_bench_data.csv").is_file():
    filename = "kyber_bench_data.csv"

data = pd.read_csv(filename)
data = data.dropna()

algorithms = data["Algorithm"]
keygen = data["Keygen_ms"]
enc = data["Enc_ms"]
dec = data["Dec_ms"]
pubkey = data["PublicKey_bytes"]
ciphertext = data["Ciphertext_bytes"]
quantum_safe = data["Quantum_Safe"]

colors = ['#2ecc71' if qs else '#e74c3c' for qs in quantum_safe]

plt.style.use("default")

plt.figure(figsize=(10, 5))
bars = plt.bar(algorithms, keygen, color=colors)
plt.xlabel("Algorithm")
plt.ylabel("Key Generation Time (ms)")
plt.title("Key Generation Time: Classical vs Post-Quantum")
plt.xticks(rotation=45, ha='right')
plt.grid(True, linestyle="--", linewidth=0.5, axis='y')
from matplotlib.patches import Patch
plt.legend(handles=[
    Patch(color='#e74c3c', label='Classical (Quantum Vulnerable)'),
    Patch(color='#2ecc71', label='Post-Quantum Safe'),
])
plt.tight_layout()
plt.savefig("pqc_keygen_time.png", dpi=300)
plt.show()

plt.figure(figsize=(10, 5))
x = np.arange(len(algorithms))
width = 0.35
plt.bar(x - width/2, enc, width, label="Enc/Encaps", color=colors, alpha=0.9)
plt.bar(x + width/2, dec, width, label="Dec/Decaps", color=colors, alpha=0.5)
plt.xlabel("Algorithm")
plt.ylabel("Time (ms)")
plt.title("Encryption vs Decryption Time: Classical vs Post-Quantum")
plt.xticks(x, algorithms, rotation=45, ha='right')
plt.legend()
plt.grid(True, linestyle="--", linewidth=0.5, axis='y')
plt.tight_layout()
plt.savefig("pqc_enc_dec_time.png", dpi=300)
plt.show()

plt.figure(figsize=(10, 5))
plt.bar(algorithms, pubkey, color=colors)
plt.xlabel("Algorithm")
plt.ylabel("Public Key Size (bytes)")
plt.title("Public Key Size: Classical vs Post-Quantum")
plt.xticks(rotation=45, ha='right')
plt.grid(True, linestyle="--", linewidth=0.5, axis='y')
plt.legend(handles=[
    Patch(color='#e74c3c', label='Classical (Quantum Vulnerable)'),
    Patch(color='#2ecc71', label='Post-Quantum Safe'),
])
plt.tight_layout()
plt.savefig("pqc_pubkey_size.png", dpi=300)
plt.show()

plt.figure(figsize=(10, 5))
plt.bar(algorithms, ciphertext, color=colors)
plt.xlabel("Algorithm")
plt.ylabel("Ciphertext Size (bytes)")
plt.title("Ciphertext Size: Classical vs Post-Quantum")
plt.xticks(rotation=45, ha='right')
plt.grid(True, linestyle="--", linewidth=0.5, axis='y')
plt.legend(handles=[
    Patch(color='#e74c3c', label='Classical (Quantum Vulnerable)'),
    Patch(color='#2ecc71', label='Post-Quantum Safe'),
])
plt.tight_layout()
plt.savefig("pqc_ciphertext_size.png", dpi=300)
plt.show()

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
metrics = [keygen, enc, dec]
titles = ["Key Generation (ms)", "Encryption/Encaps (ms)", "Decryption/Decaps (ms)"]

for ax, metric, title in zip(axes, metrics, titles):
    ax.bar(algorithms, metric, color=colors)
    ax.set_title(title)
    ax.set_xlabel("Algorithm")
    ax.set_ylabel("Time (ms)")
    ax.tick_params(axis='x', rotation=45)
    ax.grid(True, linestyle="--", linewidth=0.5, axis='y')

fig.legend(handles=[
    Patch(color='#e74c3c', label='Classical (Quantum Vulnerable)'),
    Patch(color='#2ecc71', label='Post-Quantum Safe'),
], loc='upper center', ncol=2, bbox_to_anchor=(0.5, 1.02))
plt.tight_layout()
plt.savefig("pqc_summary.png", dpi=300)
plt.show()