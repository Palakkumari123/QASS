import csv
import os
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from cryptography.hazmat.primitives import hashes, hmac, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

from Quantum_layer_verification.QRNG import quantum_rng


CIPHER_CHAIN = ["AES-256-GCM", "ChaCha20-Poly1305", "AES-256-CBC-HMAC"]


@dataclass
class EncryptionResult:
    cipher: str
    nonce: bytes
    ciphertext: bytes
    tag: bytes
    associated_data: bytes
    encrypt_duration_ms: float
    metadata: Dict[str, object]


@dataclass
class DecryptionResult:
    cipher: str
    plaintext: bytes
    decrypt_duration_ms: float
    metadata: Dict[str, object]


def _require_length(key: bytes, expected: int, label: str) -> None:
    if len(key) != expected:
        raise ValueError(f"{label} must be {expected} bytes")


def _qrng_bytes(num_bytes: int) -> bytes:
    if num_bytes <= 0:
        raise ValueError("num_bytes must be > 0")
    bits = quantum_rng(num_bytes * 8)
    return bytes(int("".join(str(int(b)) for b in bits[i:i + 8]), 2) for i in range(0, len(bits), 8))


def _encrypt_aes_gcm(key: bytes, plaintext: bytes, associated_data: bytes, nonce: Optional[bytes]) -> Tuple[bytes, bytes, bytes]:
    _require_length(key, 32, "AES-256-GCM key")
    n = nonce if nonce is not None else _qrng_bytes(12)
    if len(n) != 12:
        raise ValueError("AES-256-GCM nonce must be 12 bytes")
    aesgcm = AESGCM(key)
    ct_and_tag = aesgcm.encrypt(n, plaintext, associated_data)
    return n, ct_and_tag[:-16], ct_and_tag[-16:]


def _decrypt_aes_gcm(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, associated_data: bytes) -> bytes:
    _require_length(key, 32, "AES-256-GCM key")
    if len(nonce) != 12:
        raise ValueError("AES-256-GCM nonce must be 12 bytes")
    if len(tag) != 16:
        raise ValueError("AES-256-GCM tag must be 16 bytes")
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext + tag, associated_data)


def _encrypt_chacha20_poly1305(key: bytes, plaintext: bytes, associated_data: bytes, nonce: Optional[bytes]) -> Tuple[bytes, bytes, bytes]:
    _require_length(key, 32, "ChaCha20-Poly1305 key")
    n = nonce if nonce is not None else _qrng_bytes(12)
    if len(n) != 12:
        raise ValueError("ChaCha20-Poly1305 nonce must be 12 bytes")
    chacha = ChaCha20Poly1305(key)
    ct_and_tag = chacha.encrypt(n, plaintext, associated_data)
    return n, ct_and_tag[:-16], ct_and_tag[-16:]


def _decrypt_chacha20_poly1305(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, associated_data: bytes) -> bytes:
    _require_length(key, 32, "ChaCha20-Poly1305 key")
    if len(nonce) != 12:
        raise ValueError("ChaCha20-Poly1305 nonce must be 12 bytes")
    if len(tag) != 16:
        raise ValueError("ChaCha20-Poly1305 tag must be 16 bytes")
    chacha = ChaCha20Poly1305(key)
    return chacha.decrypt(nonce, ciphertext + tag, associated_data)


def _encrypt_aes_cbc_hmac(key: bytes, plaintext: bytes, associated_data: bytes, nonce: Optional[bytes]) -> Tuple[bytes, bytes, bytes]:
    _require_length(key, 32, "AES-256-CBC-HMAC key")
    enc_key = key[:16] + key[16:32]
    mac_key = key
    iv = nonce if nonce is not None else _qrng_bytes(16)
    if len(iv) != 16:
        raise ValueError("AES-256-CBC-HMAC IV must be 16 bytes")

    padder = padding.PKCS7(128).padder()
    padded = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(enc_key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    mac = hmac.HMAC(mac_key, hashes.SHA256())
    mac.update(associated_data)
    mac.update(iv)
    mac.update(ciphertext)
    tag = mac.finalize()
    return iv, ciphertext, tag


def _decrypt_aes_cbc_hmac(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, associated_data: bytes) -> bytes:
    _require_length(key, 32, "AES-256-CBC-HMAC key")
    if len(nonce) != 16:
        raise ValueError("AES-256-CBC-HMAC IV must be 16 bytes")
    if len(tag) != 32:
        raise ValueError("AES-256-CBC-HMAC tag must be 32 bytes")

    enc_key = key[:16] + key[16:32]
    mac_key = key

    mac = hmac.HMAC(mac_key, hashes.SHA256())
    mac.update(associated_data)
    mac.update(nonce)
    mac.update(ciphertext)
    mac.verify(tag)

    cipher = Cipher(algorithms.AES(enc_key), modes.CBC(nonce))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize()


def encrypt_message(
    session_key: bytes,
    plaintext: bytes,
    associated_data: Optional[bytes] = None,
    cipher: str = "AES-256-GCM",
    nonce: Optional[bytes] = None,
) -> EncryptionResult:
    if not isinstance(plaintext, bytes):
        raise ValueError("plaintext must be bytes")
    aad = associated_data if associated_data is not None else b""
    c = cipher.strip()
    if c not in CIPHER_CHAIN:
        raise ValueError(f"cipher must be one of: {CIPHER_CHAIN}")

    t0 = time.perf_counter()
    if c == "AES-256-GCM":
        used_nonce, ciphertext, tag = _encrypt_aes_gcm(session_key, plaintext, aad, nonce)
    elif c == "ChaCha20-Poly1305":
        used_nonce, ciphertext, tag = _encrypt_chacha20_poly1305(session_key, plaintext, aad, nonce)
    else:
        used_nonce, ciphertext, tag = _encrypt_aes_cbc_hmac(session_key, plaintext, aad, nonce)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    metadata = {
        "nonce_bytes": len(used_nonce),
        "ciphertext_bytes": len(ciphertext),
        "tag_bytes": len(tag),
        "plaintext_bytes": len(plaintext),
    }
    return EncryptionResult(
        cipher=c,
        nonce=used_nonce,
        ciphertext=ciphertext,
        tag=tag,
        associated_data=aad,
        encrypt_duration_ms=duration_ms,
        metadata=metadata,
    )


def decrypt_message(
    session_key: bytes,
    cipher: str,
    nonce: bytes,
    ciphertext: bytes,
    tag: bytes,
    associated_data: Optional[bytes] = None,
) -> DecryptionResult:
    c = cipher.strip()
    if c not in CIPHER_CHAIN:
        raise ValueError(f"cipher must be one of: {CIPHER_CHAIN}")
    aad = associated_data if associated_data is not None else b""

    t0 = time.perf_counter()
    if c == "AES-256-GCM":
        plaintext = _decrypt_aes_gcm(session_key, nonce, ciphertext, tag, aad)
    elif c == "ChaCha20-Poly1305":
        plaintext = _decrypt_chacha20_poly1305(session_key, nonce, ciphertext, tag, aad)
    else:
        plaintext = _decrypt_aes_cbc_hmac(session_key, nonce, ciphertext, tag, aad)
    duration_ms = (time.perf_counter() - t0) * 1000.0

    metadata = {
        "nonce_bytes": len(nonce),
        "ciphertext_bytes": len(ciphertext),
        "tag_bytes": len(tag),
        "plaintext_bytes": len(plaintext),
    }
    return DecryptionResult(cipher=c, plaintext=plaintext, decrypt_duration_ms=duration_ms, metadata=metadata)


def append_layer5_log(csv_path: str, session_id: str, enc: EncryptionResult, dec: Optional[DecryptionResult]) -> None:
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "session_id",
                "cipher",
                "encrypt_duration_ms",
                "decrypt_duration_ms",
                "nonce_bytes",
                "ciphertext_bytes",
                "tag_bytes",
                "plaintext_bytes",
                "decrypt_ok",
            ])
        writer.writerow([
            session_id,
            enc.cipher,
            enc.encrypt_duration_ms,
            dec.decrypt_duration_ms if dec is not None else "",
            enc.metadata.get("nonce_bytes", ""),
            enc.metadata.get("ciphertext_bytes", ""),
            enc.metadata.get("tag_bytes", ""),
            enc.metadata.get("plaintext_bytes", ""),
            dec is not None,
        ])
