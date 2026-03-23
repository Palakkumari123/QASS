# QASS Ablation Report

- Run ID: ablation_1774115845
- Sessions per mode: 8

## Metrics
- decrypt_success_rate: correctness under AES-256-GCM
- unique_combo_count: number of distinct source combinations exercised
- combo_entropy: entropy of combination usage
- predictability_rate: frequency of most common combination
- mean_abs_key_corr: average absolute correlation between consecutive keys
- mean_hamming_rate: average consecutive key hamming ratio
- mean_total_ms: average per-session runtime

### baseline_full
- decrypt_success_rate: 1.000000
- unique_combo_count: 6
- combo_entropy: 2.500000
- predictability_rate: 0.250000
- mean_abs_key_corr: 0.063124
- mean_hamming_rate: 0.524554
- mean_total_ms: 2384.213227

### no_layer2_fixed_combo
- decrypt_success_rate: 1.000000
- unique_combo_count: 1
- combo_entropy: -0.000000
- predictability_rate: 1.000000
- mean_abs_key_corr: 0.025121
- mean_hamming_rate: 0.507812
- mean_total_ms: 2272.650618

### no_layer4_no_ratchet
- decrypt_success_rate: 1.000000
- unique_combo_count: 5
- combo_entropy: 2.250000
- predictability_rate: 0.250000
- mean_abs_key_corr: 0.051107
- mean_hamming_rate: 0.520089
- mean_total_ms: 1395.546469

### single_source_kyber
- decrypt_success_rate: 1.000000
- unique_combo_count: 1
- combo_entropy: -0.000000
- predictability_rate: 1.000000
- mean_abs_key_corr: 0.051980
- mean_hamming_rate: 0.511161
- mean_total_ms: 1334.620038

