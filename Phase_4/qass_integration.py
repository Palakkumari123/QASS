import csv
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from Phase_4.layer1_key_sources import append_layer1_log, generate_key_material_pool
from Phase_4.layer2_superposition import append_layer2_log, select_combination
from Phase_4.layer3_dsr_engine import append_layer3_log, derive_master_key
from Phase_4.layer4_ratchet import QuantumRatchet, append_layer4_log
from Phase_4.layer5_encryption import append_layer5_log, decrypt_message, encrypt_message
from Phase_4.layer6_monitor import SecurityMonitor, append_layer6_log


BASE_DIR = os.path.dirname(__file__)
INTEGRATION_CSV = os.path.join(BASE_DIR, "qass_integration_log.csv")
LAYER1_CSV = os.path.join(BASE_DIR, "layer1_log.csv")
LAYER2_CSV = os.path.join(BASE_DIR, "layer2_log.csv")
LAYER3_CSV = os.path.join(BASE_DIR, "layer3_log.csv")
LAYER4_CSV = os.path.join(BASE_DIR, "layer4_log.csv")
LAYER5_CSV = os.path.join(BASE_DIR, "layer5_log.csv")
LAYER6_CSV = os.path.join(BASE_DIR, "layer6_log.csv")


CONFIG = {
    "qkd_source": "bb84_simulated",
    "pqc_source": "Kyber1024",
    "qrng_source": "simulator",
    "selector_mode": "quantum_superposition",
    "combiner": "xor_hkdf",
    "ratchet_hash": "hkdf_sha256",
    "cipher": "AES-256-GCM",
    "monitoring": True,
    "qber_threshold": 0.11,
    "entropy_threshold": 0.99,
    "timing_cv_threshold": 0.10,
}


@dataclass
class SessionArtifacts:
    session_id: str
    selected_combo_id: int
    selected_sources: str
    plaintext: bytes
    decrypted: bytes
    decrypt_ok: bool
    qber: float
    threat_level: int
    threat_label: str
    action: str
    timings: Dict[str, float]


def _append_integration_log(row: Dict[str, object]) -> None:
    file_exists = os.path.isfile(INTEGRATION_CSV)
    with open(INTEGRATION_CSV, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "session_id",
                "demo",
                "combo_id",
                "sources",
                "cipher",
                "kyber_variant",
                "decrypt_ok",
                "qber",
                "threat_level",
                "threat_label",
                "action",
                "l1_ms",
                "l2_ms",
                "l3_ms",
                "l4_ms",
                "l5_enc_ms",
                "l5_dec_ms",
                "l6_ms",
            ])
        writer.writerow([
            row.get("session_id", ""),
            row.get("demo", ""),
            row.get("combo_id", ""),
            row.get("sources", ""),
            row.get("cipher", ""),
            row.get("kyber_variant", ""),
            row.get("decrypt_ok", ""),
            row.get("qber", ""),
            row.get("threat_level", ""),
            row.get("threat_label", ""),
            row.get("action", ""),
            row.get("l1_ms", ""),
            row.get("l2_ms", ""),
            row.get("l3_ms", ""),
            row.get("l4_ms", ""),
            row.get("l5_enc_ms", ""),
            row.get("l5_dec_ms", ""),
            row.get("l6_ms", ""),
        ])


def _run_session(
    session_id: str,
    message: bytes,
    kyber_variant: str,
    cipher_name: str,
    eavesdrop: bool,
    shared_seed: int,
    monitor: SecurityMonitor,
    endpoint_id: str,
) -> SessionArtifacts:
    t1 = time.perf_counter()
    pool = generate_key_material_pool(
        kyber_variant=kyber_variant,
        qrng_backend_mode=CONFIG["qrng_source"],
        output_bytes=32,
        session_seed=shared_seed,
        qkd_distance_km=10.0,
        qkd_eavesdrop=eavesdrop,
    )
    l1_ms = (time.perf_counter() - t1) * 1000.0
    append_layer1_log(LAYER1_CSV, session_id, pool)

    selector = select_combination(session_id=session_id, shared_seed=shared_seed)
    append_layer2_log(LAYER2_CSV, selector)

    dsr = derive_master_key(
        session_id=session_id,
        combination_id=selector.combination_id,
        pool=pool,
        output_bytes=32,
    )
    append_layer3_log(LAYER3_CSV, dsr)

    ratchet = QuantumRatchet(initial_key=dsr.master_key, output_bytes=32)
    ratchet_step = ratchet.advance()
    append_layer4_log(LAYER4_CSV, session_id, ratchet_step)

    aad = f"{session_id}|qass".encode("utf-8")
    enc = encrypt_message(ratchet_step.session_key, message, associated_data=aad, cipher=cipher_name)
    dec = decrypt_message(ratchet_step.session_key, enc.cipher, enc.nonce, enc.ciphertext, enc.tag, associated_data=aad)
    append_layer5_log(LAYER5_CSV, session_id, enc, dec)

    timing_samples: List[float] = []
    for _ in range(5):
        trial = encrypt_message(ratchet_step.session_key, message, associated_data=aad, cipher=cipher_name)
        timing_samples.append(trial.encrypt_duration_ms)
    monitor_report = monitor.evaluate_session(
        session_id=session_id,
        qber=float(pool["qkd"].metadata.get("qber", 0.0)),
        qrng_data=pool["qrng"].key_material + ratchet_step.qrng_bytes,
        operation_timings_ms=timing_samples,
        endpoint_id=endpoint_id,
    )
    append_layer6_log(LAYER6_CSV, monitor_report)

    timings = {
        "l1_ms": l1_ms,
        "l2_ms": selector.selector_duration_ms,
        "l3_ms": dsr.total_duration_ms,
        "l4_ms": ratchet_step.advance_duration_ms,
        "l5_enc_ms": enc.encrypt_duration_ms,
        "l5_dec_ms": dec.decrypt_duration_ms,
        "l6_ms": monitor_report.monitor_duration_ms,
    }

    return SessionArtifacts(
        session_id=session_id,
        selected_combo_id=selector.combination_id,
        selected_sources="+".join(selector.selected_sources),
        plaintext=message,
        decrypted=dec.plaintext,
        decrypt_ok=dec.plaintext == message,
        qber=float(pool["qkd"].metadata.get("qber", 0.0)),
        threat_level=monitor_report.threat_level,
        threat_label=monitor_report.threat_label,
        action=monitor_report.action,
        timings=timings,
    )


def demo_1_normal_operation(monitor: SecurityMonitor) -> None:
    print("\n=== Demo 1: Normal Operation ===")
    session = _run_session(
        session_id="demo1_session",
        message=b"Alice to Bob: QASS secure payload",
        kyber_variant=CONFIG["pqc_source"],
        cipher_name=CONFIG["cipher"],
        eavesdrop=False,
        shared_seed=501,
        monitor=monitor,
        endpoint_id="bob_node",
    )
    print("Selected combination:", session.selected_combo_id, session.selected_sources)
    print("Decrypt success:", session.decrypt_ok)
    print("QBER:", round(session.qber, 6))
    print("Threat:", session.threat_label, session.action)
    print("Layer timings (ms):")
    print("L1", round(session.timings["l1_ms"], 6))
    print("L2", round(session.timings["l2_ms"], 6))
    print("L3", round(session.timings["l3_ms"], 6))
    print("L4", round(session.timings["l4_ms"], 6))
    print("L5 enc", round(session.timings["l5_enc_ms"], 6))
    print("L5 dec", round(session.timings["l5_dec_ms"], 6))
    print("L6", round(session.timings["l6_ms"], 6))
    _append_integration_log({
        "session_id": session.session_id,
        "demo": "demo1_normal",
        "combo_id": session.selected_combo_id,
        "sources": session.selected_sources,
        "cipher": CONFIG["cipher"],
        "kyber_variant": CONFIG["pqc_source"],
        "decrypt_ok": session.decrypt_ok,
        "qber": session.qber,
        "threat_level": session.threat_level,
        "threat_label": session.threat_label,
        "action": session.action,
        **session.timings,
    })


def demo_2_quantum_ratchet(monitor: SecurityMonitor) -> None:
    print("\n=== Demo 2: Quantum Ratchet Advancing ===")
    session_id = "demo2_base"
    pool = generate_key_material_pool(
        kyber_variant=CONFIG["pqc_source"],
        qrng_backend_mode=CONFIG["qrng_source"],
        output_bytes=32,
        session_seed=502,
        qkd_distance_km=10.0,
        qkd_eavesdrop=False,
    )
    selector = select_combination(session_id=session_id, shared_seed=502)
    dsr = derive_master_key(session_id=session_id, combination_id=selector.combination_id, pool=pool)
    ratchet = QuantumRatchet(initial_key=dsr.master_key, output_bytes=32)

    keys: List[bytes] = []
    ratchet_timings: List[float] = []
    for i in range(5):
        step = ratchet.advance()
        keys.append(step.session_key)
        ratchet_timings.append(step.advance_duration_ms)
        append_layer4_log(LAYER4_CSV, f"demo2_step_{i}", step)

    unique_keys = len(set(keys))
    print("Ratchet sessions:", len(keys))
    print("Unique session keys:", unique_keys)
    print("All keys distinct:", unique_keys == len(keys))

    k1, k2, k3, k4, k5 = keys
    print("K3 != K1:", k3 != k1)
    print("K3 != K2:", k3 != k2)
    print("K3 != K4:", k3 != k4)
    print("K3 != K5:", k3 != k5)

    monitor_report = monitor.evaluate_session(
        session_id="demo2_monitor",
        qber=float(pool["qkd"].metadata.get("qber", 0.0)),
        qrng_data=pool["qrng"].key_material,
        operation_timings_ms=ratchet_timings,
        endpoint_id="bob_node",
    )
    append_layer6_log(LAYER6_CSV, monitor_report)

    _append_integration_log({
        "session_id": "demo2_base",
        "demo": "demo2_ratchet",
        "combo_id": selector.combination_id,
        "sources": "+".join(selector.selected_sources),
        "cipher": CONFIG["cipher"],
        "kyber_variant": CONFIG["pqc_source"],
        "decrypt_ok": True,
        "qber": float(pool["qkd"].metadata.get("qber", 0.0)),
        "threat_level": monitor_report.threat_level,
        "threat_label": monitor_report.threat_label,
        "action": monitor_report.action,
        "l1_ms": pool["qkd"].duration_ms + pool["kyber"].duration_ms + pool["qrng"].duration_ms,
        "l2_ms": selector.selector_duration_ms,
        "l3_ms": dsr.total_duration_ms,
        "l4_ms": sum(ratchet_timings),
        "l5_enc_ms": 0.0,
        "l5_dec_ms": 0.0,
        "l6_ms": monitor_report.monitor_duration_ms,
    })


def demo_3_eavesdrop_detection(monitor: SecurityMonitor) -> None:
    print("\n=== Demo 3: Eavesdropping Detection ===")
    session = _run_session(
        session_id="demo3_eve",
        message=b"Eavesdrop test payload",
        kyber_variant=CONFIG["pqc_source"],
        cipher_name=CONFIG["cipher"],
        eavesdrop=True,
        shared_seed=503,
        monitor=monitor,
        endpoint_id="eve_path",
    )
    print("QBER under eavesdropping:", round(session.qber, 6))
    print("Threat:", session.threat_label)
    print("Action:", session.action)
    print("Session aborted condition met:", session.threat_level == 3)
    _append_integration_log({
        "session_id": session.session_id,
        "demo": "demo3_eavesdrop",
        "combo_id": session.selected_combo_id,
        "sources": session.selected_sources,
        "cipher": CONFIG["cipher"],
        "kyber_variant": CONFIG["pqc_source"],
        "decrypt_ok": session.decrypt_ok,
        "qber": session.qber,
        "threat_level": session.threat_level,
        "threat_label": session.threat_label,
        "action": session.action,
        **session.timings,
    })


def demo_4_cipher_agility(monitor: SecurityMonitor) -> None:
    print("\n=== Demo 4: Cryptographic Agility (Cipher Swap) ===")
    first = _run_session(
        session_id="demo4_aes",
        message=b"Cipher agility message",
        kyber_variant=CONFIG["pqc_source"],
        cipher_name="AES-256-GCM",
        eavesdrop=False,
        shared_seed=504,
        monitor=monitor,
        endpoint_id="bob_node",
    )
    second = _run_session(
        session_id="demo4_chacha",
        message=b"Cipher agility message",
        kyber_variant=CONFIG["pqc_source"],
        cipher_name="ChaCha20-Poly1305",
        eavesdrop=False,
        shared_seed=505,
        monitor=monitor,
        endpoint_id="bob_node",
    )
    print("AES decrypt ok:", first.decrypt_ok)
    print("ChaCha decrypt ok:", second.decrypt_ok)
    print("Layer swap done via cipher config only")
    _append_integration_log({
        "session_id": first.session_id,
        "demo": "demo4_cipher_aes",
        "combo_id": first.selected_combo_id,
        "sources": first.selected_sources,
        "cipher": "AES-256-GCM",
        "kyber_variant": CONFIG["pqc_source"],
        "decrypt_ok": first.decrypt_ok,
        "qber": first.qber,
        "threat_level": first.threat_level,
        "threat_label": first.threat_label,
        "action": first.action,
        **first.timings,
    })
    _append_integration_log({
        "session_id": second.session_id,
        "demo": "demo4_cipher_chacha",
        "combo_id": second.selected_combo_id,
        "sources": second.selected_sources,
        "cipher": "ChaCha20-Poly1305",
        "kyber_variant": CONFIG["pqc_source"],
        "decrypt_ok": second.decrypt_ok,
        "qber": second.qber,
        "threat_level": second.threat_level,
        "threat_label": second.threat_label,
        "action": second.action,
        **second.timings,
    })


def demo_5_algorithm_swapping(monitor: SecurityMonitor) -> None:
    print("\n=== Demo 5: Algorithm Swapping (Kyber1024 -> Kyber768) ===")
    first = _run_session(
        session_id="demo5_kyber1024",
        message=b"Kyber swap message",
        kyber_variant="Kyber1024",
        cipher_name=CONFIG["cipher"],
        eavesdrop=False,
        shared_seed=506,
        monitor=monitor,
        endpoint_id="bob_node",
    )
    second = _run_session(
        session_id="demo5_kyber768",
        message=b"Kyber swap message",
        kyber_variant="Kyber768",
        cipher_name=CONFIG["cipher"],
        eavesdrop=False,
        shared_seed=507,
        monitor=monitor,
        endpoint_id="bob_node",
    )
    print("Kyber1024 decrypt ok:", first.decrypt_ok)
    print("Kyber768 decrypt ok:", second.decrypt_ok)
    print("System remains operational after PQC source swap")
    _append_integration_log({
        "session_id": first.session_id,
        "demo": "demo5_kyber1024",
        "combo_id": first.selected_combo_id,
        "sources": first.selected_sources,
        "cipher": CONFIG["cipher"],
        "kyber_variant": "Kyber1024",
        "decrypt_ok": first.decrypt_ok,
        "qber": first.qber,
        "threat_level": first.threat_level,
        "threat_label": first.threat_label,
        "action": first.action,
        **first.timings,
    })
    _append_integration_log({
        "session_id": second.session_id,
        "demo": "demo5_kyber768",
        "combo_id": second.selected_combo_id,
        "sources": second.selected_sources,
        "cipher": CONFIG["cipher"],
        "kyber_variant": "Kyber768",
        "decrypt_ok": second.decrypt_ok,
        "qber": second.qber,
        "threat_level": second.threat_level,
        "threat_label": second.threat_label,
        "action": second.action,
        **second.timings,
    })


def run_all_demos() -> None:
    monitor = SecurityMonitor(
        qber_threshold=float(CONFIG["qber_threshold"]),
        entropy_threshold=float(CONFIG["entropy_threshold"]),
        timing_cv_threshold=float(CONFIG["timing_cv_threshold"]),
    )
    demo_1_normal_operation(monitor)
    demo_2_quantum_ratchet(monitor)
    demo_3_eavesdrop_detection(monitor)
    demo_4_cipher_agility(monitor)
    demo_5_algorithm_swapping(monitor)
    print("\nIntegration demos complete.")
    print("Logs:")
    print(INTEGRATION_CSV)
    print(LAYER1_CSV)
    print(LAYER2_CSV)
    print(LAYER3_CSV)
    print(LAYER4_CSV)
    print(LAYER5_CSV)
    print(LAYER6_CSV)


if __name__ == "__main__":
    run_all_demos()
