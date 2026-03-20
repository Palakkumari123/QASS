 # Quantum-Assurance Security Suite

This repository compares post-quantum cryptography, quantum communication behavior, and quantum attack scaling under simulation.

## Setup

Install dependencies from repository root:

`pip install -r requirements.txt`

## Project Layout

- `PQC_Assurance/`
  - `Kyber_bench.py`: Benchmarks RSA/ECC/AES/Kyber and logs throughput, latency, and size metrics.
  - `benchmark.py`: Verifies Kyber functional correctness and timing-variance stability.
  - `pqc_plots.py`: Builds plots from PQC benchmark CSV.
- `Quantum_layer_verification/`
  - `BB84.py`: Simulates BB84 with attenuation, noise, and eavesdropping scenarios.
  - `QRNG.py`: Compares classical PRNG vs simulated QRNG entropy and randomness metrics.
- `Threat_assessment/`
  - `Grover/Grover.py`: Runs Grover scaling experiments and logs runtime/depth/gate growth.
  - `Grover/plots.py`: Visualizes Grover scaling metrics.
  - `Shor's/shor.py`: Runs Shor period-finding based factorization tests.
  - `Shor's/plots.py`: Visualizes Shor scaling metrics.
- `project_config.py`: Shared configuration for run counts, seeds, test cases, and CSV filenames.

## Deterministic Mode

Deterministic mode is enabled by default and controls seeds used in BB84, QRNG, Grover, and Shor simulation paths.

- Enable/disable: `QASS_DETERMINISTIC=true|false`
- Override global seed: `QASS_GLOBAL_SEED=<int>`

Example:

`QASS_DETERMINISTIC=false python Quantum_layer_verification/QRNG.py`

QRNG backend and debias controls:

- `QASS_QRNG_BACKEND=simulator|hardware`
- `QASS_QRNG_DEBIAS=none|von_neumann`
- `QASS_QRNG_HARDWARE_SHOTS=<int>`
- `QASS_QRNG_HARDWARE_MAX_ATTEMPTS=<int>`
- `QASS_IBM_CHANNEL=<value>`
- `QASS_IBM_INSTANCE=<value>`
- `QASS_IBM_BACKEND=<backend_name>` (optional)
- `IBM_QUANTUM_TOKEN=<your_token>` (required for hardware mode)

BB84 random source control:

- `QASS_BB84_RANDOM_SOURCE=classical|qrng`

## Run Order

Run from repository root (`/home/samaksh/Desktop/qass`) in this order:

1. `python PQC_Assurance/Kyber_bench.py`
2. `python PQC_Assurance/benchmark.py`
3. `python Quantum_layer_verification/BB84.py`
4. `python Quantum_layer_verification/QRNG.py`
5. `python Threat_assessment/Grover/Grover.py`
6. `python Threat_assessment/Shor's/shor.py`
7. Generate plots:
   - `python PQC_Assurance/pqc_plots.py`
   - `python Threat_assessment/Grover/plots.py`
   - `python Threat_assessment/Shor's/plots.py`

## Expected CSV Outputs

Configured in `project_config.py`:

- `pqc_benchmark_data.csv`
- `formal_verification_correctness.csv`
- `formal_verification_timing.csv`
- `bb84_simulation_data.csv`
- `qrng_entropy_data.csv`
- `grover_scaling_data.csv`
- `shors_scaling_data.csv`

## Notes

- `pqc_plots.py` keeps a compatibility fallback to `kyber_bench_data.csv` if the new canonical file is not present.
- Most scripts append to CSV logs by default; clear files manually if you want a fresh run.
