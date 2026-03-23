# QASS Phase 4 Security Model

## 1. System Entities
1. Alice and Bob execute identical QASS Layer 1 through Layer 6 workflows.
2. Both parties share synchronized session context and selector seed material.
3. An adversary may observe traffic, inject interference, and attempt adaptive targeting.

## 2. Session State
1. Layer 1 outputs source keys $K_{qkd}$, $K_{kyber}$, $K_{qrng}$.
2. Layer 2 selects a non-empty subset $S \subseteq \{qkd, kyber, qrng\}$ with $|S| \in \{1,2,3\}$.
3. Layer 3 computes:
$$
K_{xor} = \bigoplus_{i \in S} K_i,
$$
$$
K_{master} = HKDF_{SHA256}(K_{xor}, salt, info).
$$
4. Layer 4 ratchet computes:
$$
K_{t+1} = HKDF_{SHA256}(K_t \oplus R_t, \text{info}=ratchet_t),
$$
where $R_t$ is fresh randomness material.
5. Layer 5 encrypts with an AEAD cipher selected by configuration.
6. Layer 6 evaluates QBER, entropy, and timing-CV signals and emits response levels.

## 3. Adversary Model
1. The adversary can passively observe ciphertext, metadata, and timing.
2. The adversary can actively induce BB84 disturbance, producing elevated QBER.
3. The adversary can attempt partial key-source compromise.
4. The adversary cannot simultaneously and perfectly compromise all selected key sources in a session.
5. The adversary cannot invert HKDF-SHA256 under standard preimage resistance assumptions.

## 4. Security Games

### Game A: DSR Source-Uncertainty
1. Challenger samples a selector outcome $S$ and derives session key material with Layer 3.
2. Adversary receives public transcript and oracle access excluding full source internals.
3. Adversary outputs guess $\hat{S}$.
4. Security target: adversary advantage over random guessing remains bounded by negligible terms plus source-leakage assumptions.

### Game B: Partial-Compromise Resistance
1. Challenger reveals any strict subset of selected source inputs.
2. Adversary attempts to distinguish $K_{master}$ from random.
3. Security target: without all selected source contributions, adversary advantage remains negligible under XOR masking and HKDF extraction assumptions.

### Game C: Ratchet Forward/Backward Secrecy
1. Challenger runs ratchet chain $K_1, K_2, ..., K_T$.
2. Adversary compromises one internal key $K_j$.
3. Adversary attempts to recover $K_{j-1}$ or $K_{j+1}$.
4. Security target: recovery probability remains negligible under one-wayness of HKDF and unpredictability of ratchet randomness inputs.

## 5. Monitoring Security Objectives
1. If QBER exceeds configured threshold, system enters critical response and session abort path.
2. If entropy falls below threshold, system raises warning/elevated responses and reseed guidance.
3. If timing CV exceeds threshold, system raises side-channel anomaly signal.

## 6. Claim Boundaries
1. Current evidence establishes implementation-level empirical behavior, not universal composability proofs.
2. Current validation uses simulator-first execution with explicit future path to hardware-backed entropy and selector execution.
3. Stronger formal guarantees require adaptive game proofs and composable models in future work.

## 7. Assumptions Summary
1. HKDF-SHA256 behaves as a secure extractor and KDF.
2. At least one selected source contribution remains unknown to the adversary per secure session.
3. Session IDs and selector context are unique enough to avoid derivation collisions.
4. Monitoring thresholds are deployment-tuned and correctly instrumented.
