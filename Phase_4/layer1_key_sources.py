import csv
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
from kyber_py.kyber import Kyber512, Kyber768, Kyber1024

from project_config import (
	BB84_ATTENUATION_DB_PER_KM,
	BB84_NOISE_RATE,
	BB84_RANDOM_SOURCE,
	DETERMINISTIC_MODE,
	GLOBAL_SEED,
)
from Quantum_layer_verification.QRNG import quantum_rng


def photon_survival_prob(distance_km: float, attenuation_db_per_km: float = BB84_ATTENUATION_DB_PER_KM) -> float:
	return 10 ** (-attenuation_db_per_km * distance_km / 10)


def bits_to_bytes(bits: np.ndarray, output_bytes: int) -> bytes:
	if output_bytes <= 0:
		raise ValueError("output_bytes must be > 0")
	if bits.size == 0:
		raise ValueError("bits must not be empty")
	needed = output_bytes * 8
	if bits.size < needed:
		repeats = (needed + bits.size - 1) // bits.size
		bits = np.tile(bits, repeats)
	packed = np.packbits(bits[:needed].astype(np.uint8))
	return bytes(packed.tolist())


def shannon_entropy_per_bit(bits: np.ndarray) -> float:
	if bits.size == 0:
		return 0.0
	p1 = float(np.mean(bits))
	p0 = 1.0 - p1
	if p0 == 0.0 or p1 == 0.0:
		return 0.0
	return float(-p0 * np.log2(p0) - p1 * np.log2(p1))


def _generate_bits(rng: np.random.Generator, num_bits: int, random_source: str) -> np.ndarray:
	source = random_source.strip().lower()
	if source == "classical":
		return rng.integers(0, 2, num_bits, dtype=np.int8)
	if source == "qrng":
		return quantum_rng(num_bits).astype(np.int8)
	raise ValueError("random_source must be 'classical' or 'qrng'")


def bb84_generate_sifted_key(
	num_bits: int,
	distance_km: float,
	noise_rate: float,
	eavesdrop: bool,
	random_source: str,
	seed: Optional[int],
) -> Dict[str, object]:
	if num_bits <= 0:
		raise ValueError("num_bits must be > 0")
	rng = np.random.default_rng(seed)

	alice_bits = _generate_bits(rng, num_bits, random_source)
	alice_bases = _generate_bits(rng, num_bits, random_source)

	survival = photon_survival_prob(distance_km)
	survived = rng.random(num_bits) < survival
	alice_bits_recv = alice_bits[survived]
	alice_bases_recv = alice_bases[survived]

	if alice_bits_recv.size == 0:
		return {
			"sifted_bits": np.array([], dtype=np.int8),
			"qber": 1.0,
			"key_rate": 0.0,
			"secure": False,
			"num_bits_received": 0,
			"sifted_key_length": 0,
		}

	if eavesdrop:
		eve_bases = rng.integers(0, 2, alice_bits_recv.size, dtype=np.int8)
		eve_wrong = eve_bases != alice_bases_recv
		eve_bits = alice_bits_recv.copy()
		wrong_count = int(np.sum(eve_wrong))
		if wrong_count > 0:
			eve_bits[eve_wrong] = rng.integers(0, 2, wrong_count, dtype=np.int8)
		transmitted_bits = eve_bits
	else:
		transmitted_bits = alice_bits_recv

	bob_bases = _generate_bits(rng, alice_bits_recv.size, random_source)
	bob_bits = transmitted_bits.copy()

	noise_mask = rng.random(alice_bits_recv.size) < noise_rate
	bob_bits[noise_mask] = 1 - bob_bits[noise_mask]

	if eavesdrop:
		eve_disturbed = eve_bases != alice_bases_recv
		disturbed_count = int(np.sum(eve_disturbed))
		if disturbed_count > 0:
			bob_bits[eve_disturbed] = rng.integers(0, 2, disturbed_count, dtype=np.int8)

	matching_bases = bob_bases == alice_bases_recv
	sifted_alice = alice_bits_recv[matching_bases]
	sifted_bob = bob_bits[matching_bases]
	sifted_len = int(sifted_alice.size)

	if sifted_len == 0:
		qber = 1.0
		secure = False
	else:
		qber = float(np.mean(sifted_alice != sifted_bob))
		secure = qber < 0.11

	key_rate = float(sifted_len / num_bits)

	return {
		"sifted_bits": sifted_bob.astype(np.int8),
		"qber": qber,
		"key_rate": key_rate,
		"secure": secure,
		"num_bits_received": int(alice_bits_recv.size),
		"sifted_key_length": sifted_len,
	}


@dataclass
class KeySourceResult:
	source_name: str
	key_material: bytes
	duration_ms: float
	metadata: Dict[str, object]


class QKDSource:
	def __init__(
		self,
		default_num_bits: int = 4096,
		default_distance_km: float = 10.0,
		default_noise_rate: float = BB84_NOISE_RATE,
		random_source: str = BB84_RANDOM_SOURCE,
	):
		self.default_num_bits = default_num_bits
		self.default_distance_km = default_distance_km
		self.default_noise_rate = default_noise_rate
		self.random_source = random_source

	def generate(
		self,
		output_bytes: int = 32,
		num_bits: Optional[int] = None,
		distance_km: Optional[float] = None,
		noise_rate: Optional[float] = None,
		eavesdrop: bool = False,
		session_seed: Optional[int] = None,
	) -> KeySourceResult:
		bits = num_bits if num_bits is not None else self.default_num_bits
		distance = distance_km if distance_km is not None else self.default_distance_km
		noise = noise_rate if noise_rate is not None else self.default_noise_rate
		if DETERMINISTIC_MODE:
			base = GLOBAL_SEED if session_seed is None else session_seed
			seed = int(base)
		else:
			seed = None

		t0 = time.perf_counter()
		result = bb84_generate_sifted_key(
			num_bits=bits,
			distance_km=distance,
			noise_rate=noise,
			eavesdrop=eavesdrop,
			random_source=self.random_source,
			seed=seed,
		)
		sifted_bits = result["sifted_bits"]
		if int(result["sifted_key_length"]) == 0:
			raise RuntimeError("QKD produced empty sifted key")
		key_material = bits_to_bytes(sifted_bits, output_bytes)
		duration_ms = (time.perf_counter() - t0) * 1000.0

		metadata = {
			"qber": result["qber"],
			"key_rate": result["key_rate"],
			"secure": result["secure"],
			"num_bits_received": result["num_bits_received"],
			"sifted_key_length": result["sifted_key_length"],
			"distance_km": distance,
			"noise_rate": noise,
			"eavesdrop": eavesdrop,
			"random_source": self.random_source,
			"entropy": shannon_entropy_per_bit(sifted_bits),
		}
		return KeySourceResult("qkd", key_material, duration_ms, metadata)


class KyberSource:
	def __init__(self, variant: str = "Kyber1024"):
		normalized = variant.strip()
		mapping = {
			"Kyber512": Kyber512,
			"Kyber768": Kyber768,
			"Kyber1024": Kyber1024,
		}
		if normalized not in mapping:
			raise ValueError("variant must be one of: Kyber512, Kyber768, Kyber1024")
		self.variant_name = normalized
		self.variant = mapping[normalized]

	def generate(self, output_bytes: int = 32) -> KeySourceResult:
		t0 = time.perf_counter()
		public_key, private_key = self.variant.keygen()
		shared_secret, ciphertext = self.variant.encaps(public_key)
		recovered = self.variant.decaps(private_key, ciphertext)
		duration_ms = (time.perf_counter() - t0) * 1000.0

		if shared_secret != recovered:
			raise RuntimeError("Kyber decapsulation failed to recover shared secret")

		key_material = shared_secret[:output_bytes]
		if len(key_material) < output_bytes:
			repeats = (output_bytes + len(shared_secret) - 1) // len(shared_secret)
			key_material = (shared_secret * repeats)[:output_bytes]

		metadata = {
			"variant": self.variant_name,
			"public_key_bytes": len(public_key),
			"ciphertext_bytes": len(ciphertext),
			"shared_secret_bytes": len(shared_secret),
			"integrity_ok": shared_secret == recovered,
		}
		return KeySourceResult("kyber", key_material, duration_ms, metadata)


class QRNGSource:
	def __init__(self, backend_mode: str = "simulator"):
		self.backend_mode = backend_mode

	def generate(self, output_bytes: int = 32) -> KeySourceResult:
		if output_bytes <= 0:
			raise ValueError("output_bytes must be > 0")
		t0 = time.perf_counter()
		bits = quantum_rng(output_bytes * 8, mode=self.backend_mode)
		key_material = bits_to_bytes(bits.astype(np.int8), output_bytes)
		duration_ms = (time.perf_counter() - t0) * 1000.0

		metadata = {
			"backend_mode": self.backend_mode,
			"num_bits": int(bits.size),
			"entropy": shannon_entropy_per_bit(bits.astype(np.int8)),
		}
		return KeySourceResult("qrng", key_material, duration_ms, metadata)


def generate_key_material_pool(
	kyber_variant: str = "Kyber1024",
	qrng_backend_mode: str = "simulator",
	output_bytes: int = 32,
	session_seed: Optional[int] = None,
	qkd_distance_km: float = 10.0,
	qkd_noise_rate: float = BB84_NOISE_RATE,
	qkd_eavesdrop: bool = False,
) -> Dict[str, KeySourceResult]:
	qkd = QKDSource().generate(
		output_bytes=output_bytes,
		distance_km=qkd_distance_km,
		noise_rate=qkd_noise_rate,
		eavesdrop=qkd_eavesdrop,
		session_seed=session_seed,
	)
	kyber = KyberSource(variant=kyber_variant).generate(output_bytes=output_bytes)
	qrng = QRNGSource(backend_mode=qrng_backend_mode).generate(output_bytes=output_bytes)
	return {"qkd": qkd, "kyber": kyber, "qrng": qrng}


def append_layer1_log(csv_path: str, session_id: str, pool: Dict[str, KeySourceResult]) -> None:
	file_exists = os.path.isfile(csv_path)
	with open(csv_path, mode="a", newline="") as f:
		writer = csv.writer(f)
		if not file_exists:
			writer.writerow([
				"session_id",
				"source",
				"duration_ms",
				"key_bytes",
				"entropy",
				"qber",
				"secure",
				"variant",
				"backend_mode",
			])
		for source_name, result in pool.items():
			writer.writerow([
				session_id,
				source_name,
				result.duration_ms,
				len(result.key_material),
				result.metadata.get("entropy", ""),
				result.metadata.get("qber", ""),
				result.metadata.get("secure", ""),
				result.metadata.get("variant", ""),
				result.metadata.get("backend_mode", ""),
			])
