# QKD Simulator - Model Assumptions

This document catalogues all modelling assumptions embedded in the QKD simulator codebase (`qkd_sim/`), which currently implements the BB84, B92, and E91 protocols. Assumptions are grouped by category; file references are included for traceability.

---

## 1. Photon / Qubit Assumptions

| Assumption | Detail | File / Lines |
|---|---|---|
| Single-qubit encoding | Each transmission encodes exactly one qubit (`QuantumCircuit(1,1)`). No multi-photon or continuous-variable QKD. | `protocol.py:149` |
| Ideal photon source | Alice's preparation is perfect - no spontaneous emission, no pulse splitting, no timing jitter. | `protocol.py:164–179` |
| 100% detector efficiency | Every qubit that reaches Bob's apparatus produces a definite outcome (`shots=1`). No detection failures or missed counts. | `protocol.py:203–208` |
| No dark counts | Detectors never fire without an incoming photon. Real APD detectors have 100–10 000 cps dark count rates. | (implicit throughout) |
| No detector dead time | Detectors can measure every transmitted qubit without recovery delays. Real detectors have 100–1000 ns dead time. | (implicit throughout) |
| No transmission loss | All qubits prepared by Alice reach Bob. Real fibre has ~0.2 dB/km loss; satellites have 10–30 dB total loss. | (implicit throughout) |
| No pulse structure | Each transmission is a pure, single-mode qubit. Real optical pulses have spectral width, temporal wings, and mode structure. | (implicit throughout) |

---

## 2. Basis Choice & Encoding

| Assumption | Detail | File / Lines |
|---|---|---|
| Two bases only (Z and X) | Rectilinear (Z/computational) and diagonal (X/Hadamard) bases. No other bases used. | `protocol.py:154–157` |
| Uniform basis probability | Alice and Bob each choose their basis uniformly at random (p = 0.5 each). No biased basis protocols. | `protocol.py:164–165, 192` |
| Uniform bit probability | Alice's secret bits are uniformly random (p = 0.5 for 0 or 1). | `protocol.py:164` |
| BB84 four-state encoding | `bit=0, Z` → \|0⟩; `bit=1, Z` → \|1⟩; `bit=0, X` → \|+⟩; `bit=1, X` → \|−⟩ | `protocol.py:154–179` |

---

## 3. Quantum Channel Noise Models

### 3.1 Channel-Only Noise Architecture

Noise is applied **exclusively** to the identity gate (`qc.id(0)`) channel marker. Alice's state preparation and Bob's measurement apparatus are treated as noiseless. This is a deliberate design choice, not a physical claim.

- `noise.py:37–39` - `CHANNEL_GATE = ['id']`
- `protocol.py:181–183` - identity gate inserted after Alice's preparation

### 3.2 Supported Noise Types

| Noise Model | Physical Meaning | Mathematical Model | Theoretical QBER | File / Lines |
|---|---|---|---|---|
| **None** (ideal) | Perfect channel | Identity | 0 | `noise.py:42–45` |
| **Depolarizing** | Uniform Pauli errors (e.g. photon scattering) | E(ρ) = (1−p)ρ + p·I/2; each Pauli (X,Y,Z) applied with prob p/4 | p/2 | `noise.py:75–78`, `plotter.py:131` |
| **Bit-flip** | Spontaneous X-type errors | X applied with prob p | p/2 | `noise.py:80–83`, `plotter.py:135` |
| **Phase-flip** | Dephasing / Z-type errors | Z applied with prob p | p/2 | `noise.py:85–88`, `plotter.py:138` |
| **Amplitude damping** | Energy loss / T₁ relaxation (e.g. fibre absorption) | Kraus operators for \|1⟩ → \|0⟩ with prob γ | (p + 1 − √(1−p)) / 4 | `noise.py:90–93`, `plotter.py:144` |
| **Phase damping** | Pure dephasing / T₂ decoherence (no energy loss) | Off-diagonal decay: ρ₀₁ → √(1−γ) ρ₀₁ | (1 − √(1−p)) / 4 | `noise.py:95–98`, `plotter.py:148` |

**Per-protocol QBER under depolarising noise** (the only channel for which closed forms are committed for all three protocols):

| Protocol | Channel topology | Visibility | QBER | |S| (E91 only) |
|---|---|---|---|---|
| BB84 | single-channel `id(0)` | V = 1 − p | p/2 | n/a |
| B92 | single-channel `id(0)` | V = 1 − p | p/2 (post-sift) | n/a |
| E91 | two-sided `id(0); id(1)` (default) | V² = (1 − p)² | **p − p²/2** | 2√2·(1 − p)² |
| E91 | single-sided `id(1)` only | V = 1 − p | p/2 | 2√2·(1 − p) |

The two-sided E91 QBER is **NOT** `p/2`. Independent depolarising noise on both qubits of the singlet pair gives a Werner state with squared visibility, hence QBER = (1 − V²)/2 = p − p²/2. Closed forms for non-depolarising channels under E91 are deferred to a future version.

### 3.3 IID (Independent and Identically Distributed) Noise

- Each qubit experiences noise independently; no burst errors or correlated noise.
- No environmental drift across a simulation run.

---

## 4. Eavesdropping / Attack Model

| Assumption | Detail | File / Lines |
|---|---|---|
| Intercept-resend attack only | Eve performs the simplest active attack: measure and re-prepare. No collective attacks, no entangling probes, no quantum memory across rounds. | `eve.py:38–76` |
| Ideal Eve equipment | Eve's measurement apparatus uses a noiseless `AerSimulator()` with no noise model applied. Eve introduces errors only from basis mismatch, not from equipment imperfections. | `eve.py:22–36` |
| Uniform random Eve basis | Eve chooses Z or X at random with equal probability (p = 0.5). No strategic basis selection or learning from previous bits. | `eve.py:63–64` |
| Partial interception rate | Eve intercepts each qubit independently with probability `interception_rate` ∈ [0, 1]. | `eve.py:27–32, 59` |
| Non-intercepted qubits unmodified | Qubits not selected for interception pass through to Bob unchanged (they still traverse the noise channel). | `eve.py:73–75` |
| Theoretical QBER from Eve | Expected QBER contribution = `rate × 0.25`, derived as P(wrong basis) × P(error \| wrong basis) = 0.5 × 0.5 = 0.25. | `eve.py:118–120` |

---

## 5. Sifting & Classical Communication

| Assumption | Detail | File / Lines |
|---|---|---|
| Basis sifting only | Qubits where Alice's and Bob's bases match are kept; all others discarded. No error amplification correction during sifting. | `protocol.py:210–218` |
| 50% expected sifting rate | With uniform random basis selection, P(bases match) = 0.5, giving key_rate ≈ 0.5. | `protocol.py:228–229` |
| Exact basis matching | Bases must match exactly; no fuzzy or probabilistic sifting. | `protocol.py:213` |
| Perfect classical channel | Basis announcements, error syndromes, and protocol messages are transmitted without loss, delay, or modification. Authenticated but unauthenticated in code. | (implicit throughout) |
| Instantaneous basis announcement | No propagation delay between Alice and Bob's classical communication. | (implicit throughout) |
| No classical channel overhead in key rate | Authentication and error syndrome transmission costs are not subtracted from the final key rate. | (implicit throughout) |

---

## 6. Security Model & Privacy Amplification

| Assumption | Detail | File / Lines |
|---|---|---|
| Shor-Preskill asymptotic bound | Secure key rate = `key_rate × max(0, 1 − h(e) − f_ec × h(e))` where h is binary entropy. | `protocol.py:63–83` |
| Binary entropy function | h(x) = −x log₂(x) − (1−x) log₂(1−x); clipped at 1×10⁻¹⁵ to avoid log(0). | `protocol.py:63–67`, `plotter.py:163–166` |
| Default f_ec = 1.16 (CASCADE) | Error correction efficiency factor representing CASCADE protocol overhead (~16% above Shannon limit). | `protocol.py:40`, `benchmark.py:107`, `main.py:235,247` |
| f_ec = 1.0 as Shannon limit option | Perfect theoretical error correction used as an alternative in run.py config. | `run.py:69` |
| Security threshold ≈ 11.06% QBER | For f_ec = 1.16, QBER above ~11.06% yields zero secure key rate. Computed via 64-iteration binary search. | `plotter.py:92–112` |
| Information-theoretic security | Security holds against computationally unbounded adversaries; no computational hardness assumptions needed. | (design intent) |
| No finite-size effects | The Shor-Preskill bound is asymptotic; finite-key effects (statistical fluctuations at small n) are ignored. | (design intent) |
| No composable security | Security is not proven in the composable framework; no composability penalty applied. | (design intent) |
| No advantage distillation | No post-processing beyond the Shor-Preskill bound is applied. | (design intent) |

---

## 7. Hardcoded Parameters & Defaults

| Parameter | Default Value | Interpretation | File / Lines |
|---|---|---|---|
| `f_ec` | 1.16 | CASCADE error correction overhead | `protocol.py:40` |
| `n_qubits` | 256 | Qubits per simulation run | `run.py:36` |
| `n_trials` | 30 | Independent repetitions per data point | `run.py:37` |
| `noise_strength_min` | 0.0 | Lower bound of noise sweep | `run.py:57` |
| `noise_strength_max` | 0.30 | Upper bound of noise sweep | `run.py:58` |
| `noise_strength_steps` | 21 | Linspace resolution in noise sweep | `run.py:59` |
| `eve_interception_rate` | 0.20 | Default Eve attack rate in examples | `run.py:75` |
| `shots` | 1 | Measurements per qubit (projective) | `protocol.py:204`, `eve.py:92` |
| Binary search iterations | 64 | Precision for QBER threshold search | `plotter.py:105–112` |
| Theory curve interpolation | 200 points | Resolution for continuous theory overlays | `plotter.py:282–290` |
| Output DPI | 300 | Poster-quality figure resolution | `plotter.py:43` |
| Base font size | 20 pt | Readable at 1–2 m (poster display) | `plotter.py:34–44` |

---

## 8. Domain Scenario Assumptions (`scenarios.py`)

Each pre-defined scenario encodes noise parameters intended to represent a real-world deployment context.

| Scenario | Noise Type | Strength | Eve Rate | Expected QBER Range | Physical Context |
|---|---|---|---|---|---|
| Ideal Baseline | none | 0.0 | - | 0.0 | Validation reference |
| Metropolitan Network | depolarizing | 0.02 | - | 1–5% | Urban fibre < 50 km |
| Long-Haul Link | amplitude damping | 0.08 | - | 4–10% | Inter-city fibre 50–100 km |
| Data Centre | phase damping | 0.01 | - | 0.5–2% | In-building, ~1 km |
| Adversarial Test | depolarizing | 0.05 | 0.50 | 15–20% | Channel + 50% Eve attack |
| Full Eavesdropping | none | 0.0 | 1.00 | 25% | Pure intercept-resend worst case |
| High Noise Stress | depolarizing | 0.12 | - | 8–12% | Near security threshold |
| Satellite Downlink | amplitude damping | 0.10 | - | 5–10% | Free-space, ~500 km orbit |
| E91 Ideal Singlet | none | 0.0 | - | 0% (\|S\| ~ 2.828) | Validates singlet preparation and CHSH estimator |
| E91 Depolarising 5% | depolarizing | 0.05 | - | ~4.88% (\|S\| ~ 2.55) | Realistic noisy channel, two-sided topology |
| E91 CHSH Violation Lost | depolarizing | 0.16 | - | ~14.7% (\|S\| ~ 2.0) | Werner V² < 1/√2 boundary; security from Bell test lost |

---

## 9. Statistical Assumptions

| Assumption | Detail | File / Lines |
|---|---|---|
| Normal distribution (CLT) | n_trials = 30 is assumed sufficient for the Central Limit Theorem to apply to QBER and key rate distributions. | `benchmark.py:58–90` |
| Standard Error of Mean (SEM) for error bars | Error bars = std / √n_trials; no Bessel correction (population std, not sample std). | `benchmark.py:159–162` |
| IID trials | Each trial is an independent simulation; no temporal correlation assumed. | (design intent) |

---

## 10. Simplifications vs. Real-World QKD (Summary)

| Aspect | This Simulator | Real-World QKD |
|---|---|---|
| Detector efficiency | 100% | 40–95% (APD / SNSPD) |
| Dark count rate | 0 | 100–10 000 cps |
| Detector dead time | 0 ns | 100–1 000 ns |
| Transmission loss | None modelled | 0.2 dB/km (fibre); 10–30 dB (satellite) |
| Clock synchronisation | Perfect | ±1–10 ns jitter |
| Photon source | Ideal single photon | Attenuated laser (Poissonian) |
| Photon-number splitting (PNS) attack | Not modelled | Relevant for coherent sources |
| Error correction | Shannon-like Shor-Preskill bound, f_ec = 1.16 | Protocol-dependent (1.0–2.0×) |
| Privacy amplification | Shor-Preskill formula only | Toeplitz hashing, etc. |
| Classical channel auth. overhead | Not subtracted | Reduces final key rate |
| Eve attack model | Intercept-resend only | Collective, coherent, or side-channel attacks also possible |
| Finite-key effects | Ignored (asymptotic) | Significant at small n (< 10⁶ qubits) |
| Composable security | Not modelled | Required for real deployments |

---

## 11. E91 Protocol-Specific Assumptions

The E91 (Ekert 1991) protocol is the entanglement-based QKD plug-in implemented in `qkd_sim/protocols/e91.py`. Unlike BB84 and B92, which are prepare-and-measure protocols, E91 distributes one half of an EPR pair to each party and uses CHSH-inequality violation as a security indicator. The list below documents the additional assumptions and conventions specific to this protocol.

### 11.1 Singlet state preparation
Target state: **|Ψ⁻⟩ = (|01⟩ − |10⟩) / √2** (perfectly anti-correlated on every shared measurement axis).

Verified gate sequence (`e91.py:_prepare_pairs`):
```
qc.h(0)        # |00> -> (|00> + |10>)/sqrt(2)
qc.cx(0, 1)    # -> (|00> + |11>)/sqrt(2) = |Phi+>
qc.x(0)        # -> (|10> + |01>)/sqrt(2) = |Psi+>
qc.z(0)        # -> (-|10> + |01>)/sqrt(2) = (|01> - |10>)/sqrt(2) = |Psi->
```
Validated by `tests/test_e91.py::test_singlet_preparation` (statevector check, tolerant of global phase).

### 11.2 Three measurement angles (Ekert 1991 convention)

Angles in the XZ-plane of the Bloch sphere:

| Party | Angle 1 | Angle 2 | Angle 3 |
|---|---|---|---|
| Alice | a₁ = 0 | a₂ = π/4 | a₃ = π/2 |
| Bob   | b₁ = π/4 | b₂ = π/2 | b₃ = 3π/4 |

Each party chooses an angle uniformly at random per round (P = 1/3 each).

Implementation: to measure σ_n at angle θ in the XZ-plane, apply `qc.ry(-theta, qubit)` to rotate the eigenbasis of σ_n into the computational Z-basis. Qiskit's `qc.ry(angle)` already implements `exp(-i·angle·Y/2)`, so the Bloch-sphere rotation is by `angle` radians directly — there is **no factor of 2**.

### 11.3 Sifting table

Table of categories indexed by (Alice angle, Bob angle):

| Alice \ Bob | b₁ (π/4) | b₂ (π/2) | b₃ (3π/4) |
|---|---|---|---|
| **a₁ (0)**    | CHSH | discard | CHSH |
| **a₂ (π/4)**  | **KEY** | discard | discard |
| **a₃ (π/2)**  | CHSH | **KEY** | CHSH |

Sifting probabilities (independent uniform 1/3 angle choices):
- P(key)     = 2/9 ≈ 0.2222
- P(CHSH)    = 4/9 ≈ 0.4444
- P(discard) = 3/9 ≈ 0.3333

For the two key pairs (a₂, b₁) and (a₃, b₂), the measurement axes coincide. The singlet gives perfect anti-correlation (E = −1) so Bob inverts his bit (`sifted_key_bob = 1 − bob_outcome`) before computing QBER.

### 11.4 CHSH parameter and security indicator

S = E(a₁,b₁) − E(a₁,b₃) + E(a₃,b₁) + E(a₃,b₃)

For an ideal singlet at the chosen angles, **S = −2√2 ≈ −2.828**. The simulator stores the signed value as `result.s_value` and exposes `abs_s` and `chsh_violation` (`|S| > 2`) as derived properties. Classical local-hidden-variable theories obey `|S| ≤ 2`; the Tsirelson bound is `|S| ≤ 2√2`.

Correlation function from outcome counts (mapping bit `0 → +1`, `1 → −1`):
```python
a_pm = 1 - 2 * alice_outcomes[mask]
b_pm = 1 - 2 * bob_outcomes[mask]
E    = float(np.mean(a_pm * b_pm))
```
Empty CHSH buckets at small `n_qubits` return correlation `0.0` with a `RuntimeWarning`.

### 11.5 Channel topology — the most subtle physics

The existing `NoiseModelFactory` uses `add_all_qubit_quantum_error(error, ['id'])`, which applies the noise channel to **every** `id` gate the circuit emits. E91 therefore offers two configurable channel topologies via the `channel_topology` constructor argument (default `'both'`):

- **`'both'`** — emits `id(0); id(1)`. Each qubit of the singlet is independently depolarised, giving Werner-state visibility V² = (1 − p)². This is the physically realistic model when both Alice and Bob receive their qubit through a channel.
- **`'bob'`** — emits `id(1)` only. Single-sided noise gives V = (1 − p), which exactly matches BB84's QBER curve. Useful as a sanity-check apples-to-apples comparison.

Closed-form predictions are committed for the depolarising channel only:

| Channel topology | Visibility | QBER | |S| |
|---|---|---|---|
| `both` (default) | V² = (1 − p)² | p − p²/2 | 2√2·(1 − p)² |
| `bob` | V = (1 − p) | p/2 | 2√2·(1 − p) |

**Critical bug to avoid:** writing `p/2` as the depolarising QBER for E91 in `both` mode. Test `tests/test_e91.py::test_depolarizing_qber_two_sided` guards against this regression.

### 11.6 Secure key rate (Shor-Preskill)

E91 uses the inherited Shor-Preskill formula so all three protocols are compared on a fair basis. Combined with sifting rate 2/9:

```
r_E91 = (2/9) · max(0, 1 − (1 + f_ec) · h(QBER))
```

The implementation overrides `theoretical_secure_key_rate` only to thread the `channel_topology` keyword through to `theoretical_qber`; the formula itself is unchanged.

### 11.7 Qiskit memory string ordering (little-endian)

For a 2-qubit, 2-clbit circuit with `measure(0, 0); measure(1, 1)`, `result.get_memory(i)[0]` returns a little-endian bit string: **rightmost char = clbit 0**. The implementation uses `bits[-1]` for Alice (clbit 0) and `bits[-2]` for Bob (clbit 1). This is verified by `tests/test_e91.py::test_clbit_ordering_little_endian` with a deterministic state.

### 11.8 `n_qubits` semantic shift

For E91, the `n_qubits` parameter means **the number of EPR pairs** (each pair is one round of the protocol that consumes one logical "qubit" event). This differs from BB84/B92, where `n_qubits` is the number of single qubits Alice transmits. With sifting fraction 2/9, each EPR pair contributes ~0.222 sifted key bits. Default scenario `n_qubits` for E91 is 400.

### 11.9 What is NOT modelled in v1

| Aspect | Status | Rationale |
|---|---|---|
| Eavesdropper attack model | Deferred to v2 (raises `NotImplementedError`) | The single-qubit intercept-resend `EveInterceptor` is incompatible with two-qubit entanglement circuits. A device-independent / collective-attack model on the EPR source is required for a meaningful E91 Eve treatment. |
| Closed-form QBER for bitflip / phaseflip / amplitude_damping / phase_damping | Returns `None` (plotter handles gracefully) | Numerical curves still work; analytical Werner-state derivations are deferred. |
| Finite-key bounds on the CHSH estimator | Not modelled | Asymptotic-only treatment matches BB84/B92's existing posture. |
| Device-independent (DI-QKD) security bound | Not modelled | The Devetak-Winter / DI bound is more conservative than Shor-Preskill but requires the CHSH-rate estimator to be promoted to a primary metric. |
| Two-way classical post-processing (advantage distillation) | Not modelled | Same posture as BB84/B92. |
| EPR source defects (white noise, asymmetric Werner mixing) | Not modelled — source is treated as a pure singlet upstream of the channel | Defects can be approximated by depolarising noise applied at the source. |
| Detection-loophole / fair-sampling closure | Not modelled | Assumes perfect detectors (consistent with sections 1 and 4). |
