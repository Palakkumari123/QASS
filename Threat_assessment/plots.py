import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

filename = "grover_scaling_data.csv"
data = pd.read_csv(filename)
data = data.dropna()
data = data.sort_values("Qubits")

qubits = data["Qubits"]
runtime = data["Runtime_seconds"]
depth = data["Circuit_depth"]
gate_count = data["Gate_count"]
success_prob = data["Success_probability"]
iterations = data["Iterations"]

plt.style.use("default")

plt.figure(figsize=(8, 5))
plt.plot(qubits, runtime, marker='o')
plt.yscale("log")
plt.xlabel("Number of Qubits (n)")
plt.ylabel("Runtime (seconds, log scale)")
plt.title("Grover Simulation Runtime Scaling")
plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig("runtime_log_scaling.png", dpi=300)
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(qubits, depth, marker='o')
plt.xlabel("Number of Qubits (n)")
plt.ylabel("Circuit Depth")
plt.title("Circuit Depth Scaling with Qubits")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig("depth_scaling.png", dpi=300)
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(qubits, gate_count, marker='o')
plt.xlabel("Number of Qubits (n)")
plt.ylabel("Total Gate Count")
plt.title("Gate Count Scaling with Qubits")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig("gate_scaling.png", dpi=300)
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(qubits, success_prob * 100, marker='o')
plt.xlabel("Number of Qubits (n)")
plt.ylabel("Success Probability (%)")
plt.title("Grover Success Probability vs Qubits")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig("success_probability.png", dpi=300)
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(qubits, iterations, marker='o')
plt.xlabel("Number of Qubits (n)")
plt.ylabel("Grover Iterations")
plt.title("Optimal Iterations vs Qubits")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig("iterations_scaling.png", dpi=300)
plt.show()