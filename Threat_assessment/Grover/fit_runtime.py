import numpy as np
import matplotlib.pyplot as plt

qubits = np.array([4, 6, 8, 10, 12, 14, 16, 18, 20])
runtime = np.array([
    0.1723918914794922,
0.1566472053527832,
0.11134076118469238,
0.12466835975646973,
0.14531254768371582,
0.2710103988647461,
0.7124321460723877,
4.089721918106079,
56.55517339706421
])

log_runtime = np.log(runtime)

coeffs = np.polyfit(qubits, log_runtime, 1)
b, c = coeffs
a = np.exp(c)

print("Fitted model:")
print(f"T(n) = {a:.6f} * exp({b:.4f} * n)")

plt.figure(figsize=(8, 5))
plt.scatter(qubits, runtime, label="Measured")
plt.plot(qubits, a * np.exp(b * qubits), label="Exp Fit")
plt.yscale("log")
plt.xlabel("Number of Qubits (n)")
plt.ylabel("Runtime (seconds, log scale)")
plt.legend()
plt.title("Exponential Runtime Scaling")
plt.grid(True, which="both", linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig("runtime_exponential_fit.png", dpi=300)
plt.show()