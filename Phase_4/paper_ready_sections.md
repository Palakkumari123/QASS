# Paper-Ready Sections (Abstract, Results, Discussion, Conclusion)

## Abstract
Quantum-era migration requires cryptographic systems that are both post-quantum secure and operationally agile. This work presents QASS (Quantum-Agile Security System), a six-layer hybrid architecture integrating multi-source key generation, quantum-guided source selection, hybrid key derivation, ratcheted session evolution, agility-enabled encryption, and runtime monitoring. The central mechanism is Dynamic Source Randomization (DSR), where active key-source combinations vary per session to reduce fixed attack surfaces. A complementary Quantum Ratchet advances key state with fresh randomness material and one-way derivation.

Phase 4 was implemented and validated end to end. Integration demos confirmed correct operation under normal sessions, eavesdropping-triggered critical response, cipher migration, and post-quantum algorithm swapping. Statistical evaluation showed near-uniform selector behavior in tested runs and strong ratchet key divergence, while repeated-trial encryption tests confirmed high correctness across agility modes. Ablation results showed that disabling DSR collapses combination diversity and maximizes predictability, supporting the architectural role of session-varying source selection. These results indicate that QASS is a practical pathway for cryptographic agility during quantum transition, with formal composable proofs and hardware-backed entropy integration as next-step assurance upgrades.

## Results
### End-to-End Validation
All five required integration demonstrations completed successfully through Layer 1 to Layer 6. Decryption correctness was preserved across baseline and swapped configurations. Evidence is captured in [qass_integration_log.csv](qass_integration_log.csv) and per-layer logs [layer1_log.csv](layer1_log.csv), [layer2_log.csv](layer2_log.csv), [layer3_log.csv](layer3_log.csv), [layer4_log.csv](layer4_log.csv), [layer5_log.csv](layer5_log.csv), and [layer6_log.csv](layer6_log.csv).

### DSR and Selector Behavior
All seven non-empty source combinations were demonstrated with reproducible seeds in [dsr_combo_coverage.csv](dsr_combo_coverage.csv). Statistical selector testing over 400 sessions produced chi-square 9.745000 and p-value 0.135810, with total variation distance 0.068571 from uniform. Results are reported in [statistical_validation_report.md](statistical_validation_report.md) and [statistical_validation.csv](statistical_validation.csv).

### Ratchet Divergence
Ratchet validation showed mean absolute consecutive-key correlation 0.058572, maximum 0.161200, and mean consecutive-key Hamming rate 0.502979 with 95% CI [0.494281, 0.511677]. All tested ratchet keys were unique. Supporting artifacts: [statistical_validation_report.md](statistical_validation_report.md) and [qass_ratchet_key_divergence.png](qass_ratchet_key_divergence.png).

### Agility Correctness
Across 150 trials per cipher, AES-256-GCM and ChaCha20-Poly1305 each achieved success rate 1.000000 with 95% CI [0.975030, 1.000000]. Cipher timing comparison is provided in [qass_cipher_comparison.png](qass_cipher_comparison.png).

### Monitoring Performance
Over 200 synthetic trials, benign clear rate was 1.000000 (95% CI [0.981155, 1.000000]) and attack detection rate was 1.000000 (95% CI [0.981155, 1.000000]). Evidence is in [layer6_log.csv](layer6_log.csv) and [qass_security_monitor_dashboard.png](qass_security_monitor_dashboard.png).

### Ablation
Ablation modes in [ablation_report.md](ablation_report.md) and [ablation_results.csv](ablation_results.csv) showed:
- Baseline full stack: unique combinations 6, predictability 0.25
- No Layer 2 fixed combination: unique combinations 1, predictability 1.0
- Single-source Kyber: unique combinations 1, predictability 1.0

This indicates that disabling DSR removes source diversity and yields a maximally predictable attack surface.

## Discussion
The contribution is architectural composition rather than a new standalone primitive. The key novelty is combining session-level source randomization, multi-source derivation, ratcheted key evolution, and modular agility controls into one operational pipeline with measurable outputs. Empirical evidence supports the claim that DSR increases source-path diversity and that ratcheting improves inter-session key-state separation in the tested setting.

The system also demonstrates deployment relevance: algorithm transitions were performed through configuration-level changes without redesigning core orchestration. This aligns with cryptographic-agility requirements for long-lived infrastructures.

Limitations remain. Current validation is simulator-first, and statistical findings are conditioned on tested sample sizes and synthetic attack distributions. Stronger guarantees require formal adaptive/composable proofs and hardware-backed entropy paths. Formal assumptions and adversary framing are documented in [security_model.md](security_model.md), and claim traceability is consolidated in [phase4_claim_evidence_map.md](phase4_claim_evidence_map.md).

## Conclusion
Phase 4 demonstrates that a quantum-agile hybrid security architecture can be implemented, instrumented, and empirically validated as an integrated system. DSR provides measurable attack-surface variability, ratcheting supports key-state divergence across sessions, and agility mechanisms preserve correctness under cipher and PQC source changes. Monitoring logic provides practical runtime response hooks for threat-aware operation.

Overall, QASS provides a credible transition architecture for post-quantum deployment planning. Future work should prioritize hardware-backed entropy integration, larger real-channel validation, and formal composable security proofs to further strengthen assurance at publication and deployment levels.
