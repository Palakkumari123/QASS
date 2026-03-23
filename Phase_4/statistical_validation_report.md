# Statistical Validation Report

## 1. Selector Uniformity
- Sessions: 400
- Counts (combo 0..6): [65, 48, 63, 61, 67, 41, 55]
- Chi-square statistic: 9.745000
- p-value: 0.135810
- Total variation distance from uniform: 0.068571

## 2. Ratchet Independence
- Sessions: 60
- Consecutive pairs: 59
- Mean absolute bit-correlation: 0.058572
- Max absolute bit-correlation: 0.161200
- Mean Hamming distance rate: 0.502979
- 95% CI for Hamming rate: [0.494281, 0.511677]
- All keys unique: True
- Quantum randomness used in ratchet test: False

## 3. Encryption Reliability
- Trials per cipher: 150
- AES-256-GCM success rate: 1.000000 (95% CI [0.975030, 1.000000])
- AES-256-GCM mean encrypt ms: 360.620344
- AES-256-GCM mean decrypt ms: 0.008651
- ChaCha20-Poly1305 success rate: 1.000000 (95% CI [0.975030, 1.000000])
- ChaCha20-Poly1305 mean encrypt ms: 362.197334
- ChaCha20-Poly1305 mean decrypt ms: 0.008607

## 4. Monitor Quality
- Trials: 200
- Benign clear rate: 1.000000 (95% CI [0.981155, 1.000000])
- Attack detection rate: 1.000000 (95% CI [0.981155, 1.000000])

## 5. Interpretation
- High selector p-value indicates no strong evidence against near-uniform combination usage under tested sessions.
- Near-zero consecutive key correlations and near-0.5 Hamming rate support ratchet key divergence.
- Encryption reliability near 1.0 indicates correctness of agility modes under repeated trials.
- Strong attack detection with high benign-clear rate supports monitoring efficacy under tested synthetic conditions.
