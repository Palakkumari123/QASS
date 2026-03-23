# Results and Discussion (Phase 4)

## 1. Overview
Phase 4 evaluates the QASS hybrid architecture across six operational layers with end-to-end integration, statistical validation, and ablation-based contribution analysis. The main objective is to test whether Dynamic Source Randomization and the Quantum Ratchet can jointly reduce attack-surface predictability while preserving cryptographic correctness and agility.

## 2. End-to-End System Validation
All five integration demonstrations executed successfully through the full Layer 1 to Layer 6 pipeline. In all demonstrated sessions, encryption and decryption completed correctly, and algorithm/cipher swaps were performed without changing core orchestration logic.

Key integration evidence is recorded in [qass_integration_log.csv](qass_integration_log.csv), with per-layer traces in [layer1_log.csv](layer1_log.csv), [layer2_log.csv](layer2_log.csv), [layer3_log.csv](layer3_log.csv), [layer4_log.csv](layer4_log.csv), [layer5_log.csv](layer5_log.csv), and [layer6_log.csv](layer6_log.csv).

## 3. Dynamic Source Randomization Behavior
The selector produced all seven non-empty source combinations with reproducible seeds, confirming full state coverage for the DSR policy space. Coverage evidence is provided in [dsr_combo_coverage.csv](dsr_combo_coverage.csv).

Selector statistical behavior was assessed over 400 sessions:
- Chi-square statistic: 9.745000
- p-value: 0.135810
- Total variation distance from uniform: 0.068571

These results provide no strong statistical evidence against near-uniform combination usage under the tested setting. Statistical outputs are reported in [statistical_validation_report.md](statistical_validation_report.md) and [statistical_validation.csv](statistical_validation.csv).

## 4. Quantum Ratchet Independence and Key Evolution
Ratchet analysis showed strong inter-session divergence:
- Mean absolute consecutive-key correlation: 0.058572
- Maximum absolute consecutive-key correlation: 0.161200
- Mean consecutive-key Hamming rate: 0.502979
- 95% CI for Hamming rate: [0.494281, 0.511677]
- All tested ratchet keys were unique

A Hamming rate near 0.5 indicates that consecutive session keys behave close to independent random bitstrings in practice under the tested setup. Supporting artifacts include [statistical_validation_report.md](statistical_validation_report.md) and [qass_ratchet_key_divergence.png](qass_ratchet_key_divergence.png).

## 5. Cryptographic Agility and Correctness
Reliability tests over 150 trials per cipher yielded:
- AES-256-GCM success rate: 1.000000, 95% CI [0.975030, 1.000000]
- ChaCha20-Poly1305 success rate: 1.000000, 95% CI [0.975030, 1.000000]

This confirms that agility-layer swaps preserve functional correctness. Timing and scalability comparisons are shown in [qass_cipher_comparison.png](qass_cipher_comparison.png).

## 6. Security Monitoring Effectiveness
Under synthetic benign and attack conditions over 200 trials:
- Benign clear rate: 1.000000, 95% CI [0.981155, 1.000000]
- Attack detection rate: 1.000000, 95% CI [0.981155, 1.000000]

Operationally, this indicates robust separation between normal operation and strong attack signatures in the tested distributions. Monitoring evidence is captured in [layer6_log.csv](layer6_log.csv) and visualized in [qass_security_monitor_dashboard.png](qass_security_monitor_dashboard.png).

## 7. Ablation Findings
Ablation experiments compared four modes: baseline full stack, no Layer 2, no Layer 4, and single-source Kyber.

Notable effects from [ablation_report.md](ablation_report.md):
- Baseline full stack: unique combination count = 6, predictability rate = 0.25
- No Layer 2 fixed combo: unique combination count = 1, predictability rate = 1.0
- Single-source Kyber: unique combination count = 1, predictability rate = 1.0

These results show that disabling DSR collapses source-combination diversity and makes the attack surface maximally predictable. Ablation traces are in [ablation_results.csv](ablation_results.csv), with visualization in [qass_ablation_plot.png](qass_ablation_plot.png).

## 8. Discussion of Novelty
The contribution is architectural rather than a new low-level primitive. The novelty lies in composition:
- Quantum-driven source-combination randomization at session granularity
- Multi-source XOR+HKDF key synthesis tied to selected source subsets
- Ratcheted forward evolution using fresh randomness material each session
- Configurable cryptographic agility integrated with continuous security monitoring

This integrated design shifts the attacker model from targeting a fixed key path to coping with session-varying key-source topologies.

## 9. Limitations
The present implementation remains simulator-first and empirical:
- Layer 2 selector and QRNG workflows are validated primarily under local simulation conditions
- Statistical conclusions depend on tested sample sizes and synthetic attack distributions
- Formal composable proofs remain future work

The formal assumptions and threat model are documented in [security_model.md](security_model.md).

## 10. Conclusion
Phase 4 results support the core thesis that a quantum-agile, multi-layer architecture can be implemented with measurable diversity, correctness, and monitoring efficacy. DSR improves attack-surface variability, the ratchet improves key-state evolution properties, and agility mechanisms preserve operational continuity during algorithm transitions.

For publication packaging, this section should be cited alongside [phase4_claim_evidence_map.md](phase4_claim_evidence_map.md), which maps each claim to concrete logs and figures.
