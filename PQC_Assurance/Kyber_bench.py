import time
import csv
import os
import statistics
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from kyber_py.kyber import Kyber512, Kyber768, Kyber1024

RUNS = 100
MESSAGE = b"benchmark message for encryption test"


def benchmark_rsa(key_size: int) -> dict:
    keygen_times, enc_times, dec_times = [], [], []

    for _ in range(RUNS):
        t0 = time.perf_counter()
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
            backend=default_backend()
        )
        keygen_times.append(time.perf_counter() - t0)

        public_key = private_key.public_key()

        t0 = time.perf_counter()
        ciphertext = public_key.encrypt(
            MESSAGE,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        enc_times.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        dec_times.append(time.perf_counter() - t0)

    pub_bytes = public_key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return {
        "algorithm": f"RSA-{key_size}",
        "keygen_ms": statistics.mean(keygen_times) * 1000,
        "enc_ms": statistics.mean(enc_times) * 1000,
        "dec_ms": statistics.mean(dec_times) * 1000,
        "public_key_bytes": len(pub_bytes),
        "ciphertext_bytes": len(ciphertext),
        "quantum_safe": False
    }


def benchmark_ecc() -> dict:
    keygen_times, sign_times, verify_times = [], [], []

    for _ in range(RUNS):
        t0 = time.perf_counter()
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        keygen_times.append(time.perf_counter() - t0)

        public_key = private_key.public_key()

        t0 = time.perf_counter()
        signature = private_key.sign(MESSAGE, ec.ECDSA(hashes.SHA256()))
        sign_times.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        public_key.verify(signature, MESSAGE, ec.ECDSA(hashes.SHA256()))
        verify_times.append(time.perf_counter() - t0)

    pub_bytes = public_key.public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo
    )

    return {
        "algorithm": "ECC-256",
        "keygen_ms": statistics.mean(keygen_times) * 1000,
        "enc_ms": statistics.mean(sign_times) * 1000,
        "dec_ms": statistics.mean(verify_times) * 1000,
        "public_key_bytes": len(pub_bytes),
        "ciphertext_bytes": len(signature),
        "quantum_safe": False
    }


def benchmark_aes(key_size: int) -> dict:
    keygen_times, enc_times, dec_times = [], [], []

    for _ in range(RUNS):
        t0 = time.perf_counter()
        key = get_random_bytes(key_size // 8)
        keygen_times.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(MESSAGE)
        nonce = cipher.nonce
        enc_times.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        cipher_dec = AES.new(key, AES.MODE_GCM, nonce=nonce)
        cipher_dec.decrypt_and_verify(ciphertext, tag)
        dec_times.append(time.perf_counter() - t0)

    return {
        "algorithm": f"AES-{key_size}",
        "keygen_ms": statistics.mean(keygen_times) * 1000,
        "enc_ms": statistics.mean(enc_times) * 1000,
        "dec_ms": statistics.mean(dec_times) * 1000,
        "public_key_bytes": key_size // 8,
        "ciphertext_bytes": len(ciphertext),
        "quantum_safe": False
    }


def benchmark_kyber(variant) -> dict:
    name = {Kyber512: "Kyber512", Kyber768: "Kyber768", Kyber1024: "Kyber1024"}[variant]
    keygen_times, enc_times, dec_times = [], [], []

    for _ in range(RUNS):
        t0 = time.perf_counter()
        public_key, private_key = variant.keygen()
        keygen_times.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        shared_secret_enc, ciphertext = variant.encaps(public_key)
        enc_times.append(time.perf_counter() - t0)

        t0 = time.perf_counter()
        variant.decaps(private_key, ciphertext)
        dec_times.append(time.perf_counter() - t0)

    return {
        "algorithm": name,
        "keygen_ms": statistics.mean(keygen_times) * 1000,
        "enc_ms": statistics.mean(enc_times) * 1000,
        "dec_ms": statistics.mean(dec_times) * 1000,
        "public_key_bytes": len(public_key),
        "ciphertext_bytes": len(ciphertext),
        "quantum_safe": True
    }


def log_results(results: list, filename="pqc_benchmark_data.csv"):
    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "Algorithm", "Keygen_ms", "Enc_ms", "Dec_ms",
                "PublicKey_bytes", "Ciphertext_bytes", "Quantum_Safe"
            ])
        for r in results:
            writer.writerow([
                r["algorithm"], r["keygen_ms"], r["enc_ms"], r["dec_ms"],
                r["public_key_bytes"], r["ciphertext_bytes"], r["quantum_safe"]
            ])


if __name__ == "__main__":
    results = []

    print("Benchmarking RSA-2048...")
    results.append(benchmark_rsa(2048))
    print("Benchmarking RSA-3072...")
    results.append(benchmark_rsa(3072))
    print("Benchmarking ECC-256...")
    results.append(benchmark_ecc())
    print("Benchmarking AES-128...")
    results.append(benchmark_aes(128))
    print("Benchmarking AES-256...")
    results.append(benchmark_aes(256))
    print("Benchmarking Kyber512...")
    results.append(benchmark_kyber(Kyber512))
    print("Benchmarking Kyber768...")
    results.append(benchmark_kyber(Kyber768))
    print("Benchmarking Kyber1024...")
    results.append(benchmark_kyber(Kyber1024))

    log_results(results)

    print("\nResults:")
    print(f"{'Algorithm':<12} {'Keygen(ms)':<12} {'Enc(ms)':<10} {'Dec(ms)':<10} {'PubKey(B)':<12} {'CT(B)':<8} {'QSafe'}")
    print("-" * 75)
    for r in results:
        print(f"{r['algorithm']:<12} {r['keygen_ms']:<12.4f} {r['enc_ms']:<10.4f} {r['dec_ms']:<10.4f} {r['public_key_bytes']:<12} {r['ciphertext_bytes']:<8} {r['quantum_safe']}")