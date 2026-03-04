import numpy as np
import matplotlib.pyplot as plt

qubits = np.array([10,12,14,16,18,20])
runtime = np.array([
    0.112974,
    0.142474,
    0.274912,
    0.434131,
    1.952265,
    21.531514
])

log_runtime = np.log(runtime)

coeffs = np.polyfit(qubits, log_runtime, 1)
b, c = coeffs
a = np.exp(c)

print(f"Fitted model:")   # calculating the value of b(growth rate) and a (scaling factor)
print(f"T(n) = {a:.6f} * exp({b:.4f} * n)")

plt.figure()
plt.scatter(qubits, runtime, label="Measured")
plt.plot(qubits, a * np.exp(b * qubits), label="Exp Fit")
plt.yscale("log")
plt.xlabel("Qubits")
plt.ylabel("Runtime (log scale)")
plt.legend()
plt.title("Exponential Runtime Scaling")
plt.show()