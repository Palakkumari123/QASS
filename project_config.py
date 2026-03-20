import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None else value.strip()


DATA_FILES = {
    "pqc_benchmark": "pqc_benchmark_data.csv",
    "fv_correctness": "formal_verification_correctness.csv",
    "fv_timing": "formal_verification_timing.csv",
    "bb84": "bb84_simulation_data.csv",
    "qrng_entropy": "qrng_entropy_data.csv",
    "grover_scaling": "grover_scaling_data.csv",
    "shor_scaling": "shors_scaling_data.csv",
}


PQC_BENCHMARK_RUNS = 100
KYBER_VERIFICATION_RUNS = 1000


DETERMINISTIC_MODE = _env_bool("QASS_DETERMINISTIC", True)
GLOBAL_SEED = int(os.getenv("QASS_GLOBAL_SEED", "42"))


BB84_NUM_BITS = 10000
BB84_NOISE_RATE = 0.01
BB84_DISTANCES_KM = (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)
BB84_ATTENUATION_DB_PER_KM = 0.2
BB84_SEED = 42
BB84_RANDOM_SOURCE = _env_str("QASS_BB84_RANDOM_SOURCE", "classical").lower()


QRNG_NUM_BITS = 100000
QRNG_TRIALS = 10
QRNG_BATCH_SIZE = 20
QRNG_SIMULATOR_SEED = 12345
QRNG_TRANSPILE_SEED = 54321
QRNG_BACKEND_MODE = _env_str("QASS_QRNG_BACKEND", "simulator").lower()
QRNG_DEBIAS_METHOD = _env_str("QASS_QRNG_DEBIAS", "none").lower()
QRNG_IBM_CHANNEL = _env_str("QASS_IBM_CHANNEL", "ibm_quantum")
QRNG_IBM_INSTANCE = _env_str("QASS_IBM_INSTANCE", "ibm-q/open/main")
QRNG_IBM_BACKEND = _env_str("QASS_IBM_BACKEND", "")
QRNG_HARDWARE_SHOTS = int(os.getenv("QASS_QRNG_HARDWARE_SHOTS", "1"))
QRNG_HARDWARE_MAX_ATTEMPTS = int(os.getenv("QASS_QRNG_HARDWARE_MAX_ATTEMPTS", "500"))


GROVER_QUBIT_SIZES = (4, 6, 8, 10, 12, 14, 16, 18, 20)
GROVER_MIN_QUBITS = 2
GROVER_MAX_QUBITS = 24
GROVER_DEFAULT_SHOTS = 1024
GROVER_SIMULATOR_SEED = 24680
GROVER_TRANSPILE_SEED = 13579


SHOR_TEST_CASES = ((15, 7), (21, 2), (35, 3))
SHOR_DEFAULT_SHOTS = 4096
SHOR_SIMULATOR_SEED = 97531
SHOR_TRANSPILE_SEED = 86420
