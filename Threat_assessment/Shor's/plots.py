import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
	sys.path.append(str(ROOT_DIR))

from project_config import DATA_FILES


filename = DATA_FILES["shor_scaling"]
data = pd.read_csv(filename)
data = data.dropna()
data = data.sort_values("N")

N = data["N"]
runtime = data["Runtime_seconds"]
depth = data["Circuit_depth"]
gate_count = data["Gate_count"]
period = data["Period"]

plt.style.use("default")

plt.figure(figsize=(8, 5))
plt.plot(N, runtime, marker='o')
plt.xlabel("Number to Factor (N)")
plt.ylabel("Runtime (seconds)")
plt.title("Shor's Algorithm Runtime Scaling")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig("shors_runtime_scaling.png", dpi=300)
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(N, depth, marker='o')
plt.xlabel("Number to Factor (N)")
plt.ylabel("Circuit Depth")
plt.title("Shor's Algorithm Circuit Depth Scaling")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig("shors_depth_scaling.png", dpi=300)
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(N, gate_count, marker='o')
plt.xlabel("Number to Factor (N)")
plt.ylabel("Total Gate Count")
plt.title("Shor's Algorithm Gate Count Scaling")
plt.grid(True, linestyle="--", linewidth=0.5)
plt.tight_layout()
plt.savefig("shors_gate_scaling.png", dpi=300)
plt.show()

plt.figure(figsize=(8, 5))
plt.bar([str(int(x)) for x in N], period, color='#3498db')
plt.xlabel("Number to Factor (N)")
plt.ylabel("Period (r)")
plt.title("Period Found by Shor's Algorithm")
plt.grid(True, linestyle="--", linewidth=0.5, axis='y')
plt.tight_layout()
plt.savefig("shors_period.png", dpi=300)
plt.show()