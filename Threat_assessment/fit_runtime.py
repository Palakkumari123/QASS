import numpy as np
import matplotlib.pyplot as plt

qubits = np.array([4, 6, 8, 10, 12, 14, 16, 18, 20])
runtime = np.array([
    0.099003,
    0.090504,
    0.101915,
    0.101581,
    0.140630,
    0.263208,
    0.727339,
    4.120457,
    38.212498
])

log_runtime = np.log(runtime)

coeffs = np.polyfit(qubits, log_runtime, 1)
b, c = coeffs
a = np.exp(c)

print(f"Fitted model:")
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