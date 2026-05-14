# E91 v1 PRD — Implementation Plan

| Field | Value |
|---|---|
| **Status** | Implemented — commit `321e1e8` on `QKDSim` branch |
| **Approval date** | 2026-04-08 |
| **Scope** | Add Ekert 1991 entanglement-based QKD as a third plug-in protocol alongside BB84 and B92, with CHSH-based security analysis and a multi-protocol benchmarking mode. |
| **Deferred to v2** | Eavesdropper model for E91; closed-form theoretical curves for non-depolarising channels. |

---

# E91 (Ekert 1991) Protocol Implementation Plan

## Context

The QKDSim codebase currently implements BB84 and B92 prepare-and-measure QKD protocols with a clean multi-protocol architecture (`QKDProtocol` ABC, `QKDResult` dataclass, protocol registry, batched circuit execution, YAML config, parameter sweeps, plotting). The PRD explicitly anticipates E91 as a third protocol but has not been implemented yet.

This plan adds the **E91 entanglement-based QKD protocol** as a third plug-in, with first-class support for benchmarking it against BB84 and B92. The implementation must be physically rigorous enough for graduate physics research code: correct singlet preparation, correct Werner-state visibility under noise, correct CHSH parameter computation, and a comprehensive pytest test suite.

**User decisions captured during planning:**
1. **Channel topology:** Configurable (default both qubits get noise; flag to switch to single-channel for direct BB84 comparison).
2. **Eavesdropper:** Defer to v2; ship E91 in v1 with noise channels only.
3. **Comparison mode:** Full multi-protocol comparison infrastructure in v1 (CLI mode, runner method, plotter overlay).
4. **Tests:** Full pytest suite (T1–T11) in a new `tests/` directory.

---

## Theoretical Foundations (must be encoded correctly)

### Singlet state preparation
Target state: **|Ψ⁻⟩ = (|01⟩ − |10⟩) / √2** (anti-correlated on every measurement axis).

**Verified preparation** (produces |Ψ⁻⟩ exactly up to global phase, validated by Statevector test T1):
```python
qc.h(0)
qc.cx(0, 1)
qc.x(0)
qc.z(0)
```
Step-by-step:
- `|00⟩ → H(0) → (|00⟩+|10⟩)/√2 → CX → (|00⟩+|11⟩)/√2 = |Φ⁺⟩`
- `→ X(0) → (|10⟩+|01⟩)/√2 = |Ψ⁺⟩`
- `→ Z(0) → (-|10⟩+|01⟩)/√2 = (|01⟩−|10⟩)/√2 = |Ψ⁻⟩` ✓

**Critical:** must validate via `qiskit.quantum_info.Statevector` in test T1 before trusting it.

### Three measurement angles (Ekert 1991 convention)
Angles in the XZ-plane of the Bloch sphere:
- **Alice:** a₁ = 0,    a₂ = π/4,   a₃ = π/2
- **Bob:**   b₁ = π/4,  b₂ = π/2,   b₃ = 3π/4

To measure σ_n at angle θ in XZ-plane, apply **`qc.ry(-theta, qubit)` then `qc.measure`**. (Qiskit's `ry(angle)` already implements `exp(-i·angle·Y/2)`, so the rotation is by `angle` radians on the Bloch sphere — *no factor of 2 needed*.) Verify with a Statevector test before relying on it.

### Sifting table (uniform random angle choice 1/3 each)

| Alice \ Bob | b₁ (π/4) | b₂ (π/2) | b₃ (3π/4) |
|---|---|---|---|
| **a₁ (0)**    | CHSH    | discard | CHSH    |
| **a₂ (π/4)**  | **KEY** | discard | discard |
| **a₃ (π/2)**  | CHSH    | **KEY** | CHSH    |

- P(key)     = 2/9 ≈ 0.2222 → `theoretical_sifting_rate()` returns **2/9**
- P(CHSH)    = 4/9 ≈ 0.4444
- P(discard) = 3/9 ≈ 0.3333

For key pairs (a₂,b₁) and (a₃,b₂): the measurement axes coincide (a−b = 0), so the singlet gives perfect anti-correlation E = −1. Bob inverts his bit (`sifted_key_bob = 1 − bob_outcome`) and keys agree.

### CHSH parameter
S = E(a₁,b₁) − E(a₁,b₃) + E(a₃,b₁) + E(a₃,b₃)

For the singlet at the chosen angles: **S = −2√2**. Use `|S|` in security checks. Classical bound `|S| ≤ 2`; Tsirelson bound `|S| ≤ 2√2`.

Correlation function from outcome counts, mapping bit `0 → +1`, `1 → −1`:
```python
a_pm = 1 - 2*alice_outcomes[mask]
b_pm = 1 - 2*bob_outcomes[mask]
E = float(np.mean(a_pm * b_pm))
```

### Noise channel topology — the most subtle physics

The existing `NoiseModelFactory` uses `add_all_qubit_quantum_error(error, ['id'])`, which applies the noise to **every** `id` gate regardless of qubit index. This means:

- If the circuit contains `id(0); id(1)`, **both** qubits get hit independently → **two-sided** depolarising → Werner visibility V² = (1−p)².
- If the circuit contains only `id(1)`, only Bob's qubit gets hit → **single-sided** → V = (1−p).

We will support **both** via a config flag (user choice). The flag controls whether `_prepare_pairs()` emits one or two `id` gates.

**QBER under depolarising (Qiskit's `depolarizing_error(p,1)` is the "any-error" convention with V = 1−p per qubit):**

| Channel topology | Visibility | QBER on key bases | |S| |
|---|---|---|---|
| `both` (default)  | V² = (1−p)² | (1 − (1−p)²)/2 = **p − p²/2** | 2√2·(1−p)² |
| `bob`             | V = (1−p)   | **p/2** (matches BB84)         | 2√2·(1−p)   |

Closed-form theoretical curves are committed for **`depolarizing` only** in v1. Other channels (bitflip, phaseflip, amplitude_damping, phase_damping) return `None` from `theoretical_qber` — the existing plotter handles `None` cleanly. Closed forms for those channels can be derived later as a follow-up.

**Critical bug to avoid:** writing `p/2` as the depolarising QBER for E91 in `both` mode. The two-sided independent noise gives `p − p²/2`. This is the highest-risk physics bug in the implementation.

### Qiskit memory string ordering
With `QuantumCircuit(2, 2)` and `measure(0, 0); measure(1, 1)`, `result.get_memory(i)[0]` returns a little-endian string: **rightmost char = clbit 0**. So:
```python
bits = result.get_memory(i)[0].replace(' ', '')
alice_out = int(bits[-1])  # clbit 0
bob_out   = int(bits[-2])  # clbit 1
```
Test T9 must verify this with a deterministic state.

### Secure key rate
Use the inherited Shor-Preskill formula via `theoretical_secure_key_rate()` (no override needed). Combined with sifting rate 2/9:
```
r_E91 = (2/9) · max(0, 1 − (1 + f_ec)·h(QBER))
```
This is a fair apples-to-apples comparison with BB84/B92. (A future extension could add a Devetak-Winter or device-independent bound as a supplementary metric.)

---

## File-by-File Implementation

### NEW: `qkd_sim/protocols/e91.py` (~280 lines)

**`E91Result(QKDResult)` dataclass** with extra fields:
- `alice_angles: np.ndarray` — int 0/1/2 indicating which of Alice's three angles
- `bob_angles: np.ndarray`
- `alice_outcomes: np.ndarray` — raw 0/1 measurements (mirrors `alice_bits`)
- `bob_outcomes: np.ndarray` — raw 0/1 (mirrors `bob_results`)
- `chsh_indices: np.ndarray` — indices used in CHSH evaluation
- `correlations: dict[tuple[int,int], float]` — E(aᵢ, bⱼ) per CHSH pair
- `s_value: float` — signed CHSH parameter (raw, not absolute)
- `chsh_pairs_count: int`
- `key_pairs_count: int`
- `channel_topology: str` — `'both'` or `'bob'`, recorded for reproducibility
- Computed property `abs_s -> float`
- Computed property `chsh_violation -> bool` (`abs(s_value) > 2.0`)

**`E91Protocol(QKDProtocol)` class:**

Constants on the class:
```python
ALICE_ANGLES = np.array([0.0, np.pi/4, np.pi/2])
BOB_ANGLES   = np.array([np.pi/4, np.pi/2, 3*np.pi/4])

# Sifting category lookup, indexed [alice_angle_idx, bob_angle_idx]
_SIFT_TABLE = np.array([
    ['chsh',    'discard', 'chsh'   ],   # a1
    ['key',     'discard', 'discard'],   # a2
    ['chsh',    'key',     'chsh'   ],   # a3
])

# CHSH terms in the order they appear in S, with sign
_CHSH_S_TERMS = [
    ((0, 0), +1),   # +E(a1,b1)
    ((0, 2), -1),   # -E(a1,b3)
    ((2, 0), +1),   # +E(a3,b1)
    ((2, 2), +1),   # +E(a3,b3)
]
```

**Constructor signature** mirrors the base class plus a new keyword-only argument:
```python
def __init__(self, n_qubits, backend, eve=None, f_ec=1.16,
             channel_topology: str = 'both'):
```
where `n_qubits` semantically means **number of EPR pairs**. Validate `channel_topology in ('both', 'bob')`.

**`protocol_name()` classmethod** → `"E91"`

**`theoretical_sifting_rate()` classmethod** → `2.0/9.0`

**`theoretical_qber(noise_type, strengths, channel_topology='both')` staticmethod**:
- For `'depolarizing'` with `channel_topology == 'both'`: return `p - p**2/2`
- For `'depolarizing'` with `channel_topology == 'bob'`: return `p / 2`
- All other noise types: return `None` (deferred to v2)

Note: the base class signature is `theoretical_qber(noise_type, strengths)` — to keep compatibility we accept `channel_topology` as a keyword with a default. The plotter calls `protocol_class.theoretical_qber(noise_type, x)` and won't pass it; we get the default `'both'`. To plot the `'bob'` curve, instantiate the result data with that topology and pass it through.

**`theoretical_chsh(noise_type, strengths, channel_topology='both')` staticmethod** — E91-specific:
- For `'depolarizing'` with topology `'both'`: `2*sqrt(2) * (1-p)**2`
- For `'depolarizing'` with topology `'bob'`:  `2*sqrt(2) * (1-p)`
- Otherwise: `None`

**`run() -> E91Result`**: orchestrates `_prepare_pairs → eve (skipped in v1) → _measure → _post_process`. If `self.eve is not None`, raise `NotImplementedError("E91 eavesdropper attack model is deferred to v2")`.

**`_prepare_pairs()`**:
```python
def _prepare_pairs(self) -> List[QuantumCircuit]:
    """Build n_pairs singlet circuits with channel id markers."""
    self._alice_angles = np.random.randint(0, 3, size=self.n_qubits)
    self._bob_angles   = np.random.randint(0, 3, size=self.n_qubits)
    circuits = []
    for _ in range(self.n_qubits):
        qc = QuantumCircuit(2, 2)
        # Singlet |Psi-> = (|01> - |10>)/sqrt(2)
        qc.h(0)
        qc.cx(0, 1)
        qc.x(0)
        qc.z(0)
        qc.barrier()
        # Channel marker(s) -- noise model targets 'id'
        if self.channel_topology == 'both':
            qc.id(0)
            qc.id(1)
        else:  # 'bob'
            qc.id(1)
        circuits.append(qc)
    return circuits
```
The barrier prevents Qiskit from optimising the prep gates away.

**`_measure(circuits)`**:
```python
def _measure(self, circuits):
    self._alice_outcomes = np.zeros(self.n_qubits, dtype=int)
    self._bob_outcomes   = np.zeros(self.n_qubits, dtype=int)
    for i, qc in enumerate(circuits):
        a_theta = self.ALICE_ANGLES[self._alice_angles[i]]
        b_theta = self.BOB_ANGLES[self._bob_angles[i]]
        qc.ry(-a_theta, 0)   # rotate sigma_n eigenbasis into Z
        qc.ry(-b_theta, 1)
        qc.measure(0, 0)
        qc.measure(1, 1)

    job = self.backend.run(circuits, shots=1, memory=True)
    result = job.result()
    for i in range(len(circuits)):
        bits = result.get_memory(i)[0].replace(' ', '')
        # Qiskit memory is little-endian: rightmost char = clbit 0
        self._alice_outcomes[i] = int(bits[-1])  # clbit 0
        self._bob_outcomes[i]   = int(bits[-2])  # clbit 1
```

**`_post_process()`**:
- Look up sift labels via `self._SIFT_TABLE[self._alice_angles, self._bob_angles]`
- Build `key_mask` and `chsh_mask`
- `sifted_indices = np.where(key_mask)[0]`
- `sifted_key_alice = alice_outcomes[sifted_indices]`
- `sifted_key_bob   = 1 - bob_outcomes[sifted_indices]`  ← anti-correlation flip
- Compute QBER as Hamming distance over the sifted key
- For each CHSH pair `(ai, bi)` in `_CHSH_S_TERMS`:
  - Build sub-mask `(alice_angles == ai) & (bob_angles == bi)`
  - Map outcomes to ±1 and compute `E = mean(a_pm * b_pm)`
  - Handle `n_sub == 0` gracefully by setting `corr = 0.0` (and log a warning)
- Sum signed terms to get `s_value`
- Build and return `E91Result` with all fields populated, including `channel_topology=self.channel_topology`

**Bottom of file:**
```python
from ..registry import register_protocol
register_protocol("e91", E91Protocol)
```

### MODIFY: `qkd_sim/protocols/__init__.py`
Add `from . import e91` so the registration runs on package import.

### MODIFY: `qkd_sim/__init__.py`
Add to imports and `__all__`:
```python
from .protocols.e91 import E91Protocol, E91Result
```

### MODIFY: `qkd_sim/benchmark.py`

1. **Extend `BenchmarkData`** with two optional fields:
   ```python
   chsh_mean: Optional[np.ndarray] = None
   chsh_std: Optional[np.ndarray] = None
   ```
   Add a computed property `chsh_sem` mirroring the existing `qber_sem`.

2. **In `run_noise_sweep` and `run_eve_sweep`:** after populating `qber_results[i, j]`, also collect CHSH:
   ```python
   s_val = getattr(result, 's_value', None)
   if s_val is not None:
       if chsh_results is None:
           chsh_results = np.zeros((n_strengths, n_trials))
       chsh_results[i, j] = abs(s_val)
   ```
   Then at the end, set `chsh_mean`/`chsh_std` only if `chsh_results is not None`.

3. **Add `run_protocol_comparison`** method:
   ```python
   def run_protocol_comparison(
       self,
       protocol_classes: List[Type[QKDProtocol]],
       noise_type: NoiseType,
       strengths: np.ndarray,
       n_trials: int = 30,
       n_qubits: int = 100,
       f_ec: float = 1.16,
       protocol_kwargs: Optional[Dict[str, Dict]] = None,
   ) -> Dict[str, BenchmarkData]:
       """Run the same noise sweep on multiple protocols. Returns dict
       keyed by protocol_name(). protocol_kwargs allows per-protocol
       extras such as {'E91': {'channel_topology': 'both'}}.
       """
   ```
   Implementation loops over `protocol_classes` and calls `run_noise_sweep` for each, threading the per-protocol kwargs through to the protocol constructor (we'll need to extend `run_noise_sweep` to accept a `protocol_kwargs: Optional[Dict] = None` argument that gets unpacked into the `protocol_class(...)` call).

### MODIFY: `qkd_sim/plotter.py`

1. **Add `plot_chsh_vs_noise(data, protocol_class=None, channel_topology='both', ...)`**:
   - Skip with a print message if `data.chsh_mean is None`
   - Errorbar plot of `data.chsh_mean ± chsh_sem`
   - Horizontal line at `|S| = 2` (classical bound, dashed, threshold colour)
   - Horizontal line at `|S| = 2*sqrt(2)` (Tsirelson, dotted, gray)
   - If `protocol_class.theoretical_chsh(noise_type, x, channel_topology) is not None`, overlay it
   - Save / show

2. **Add `plot_protocol_comparison(data_dict, kind='qber', ...)`**:
   - `data_dict: Dict[str, BenchmarkData]` keyed by protocol name
   - `kind ∈ {'qber', 'key_rate', 'secure_key_rate'}`
   - Loop over `data_dict.items()`, plot each as errorbar with the protocol's colour/marker from `STYLE.protocol_colours/markers`
   - Y-axis label, title, and legend depend on `kind`
   - Optionally overlay theory curves if all protocols expose `theoretical_*`

3. **Optionally extend `plot_basis_heatmap`** to handle E91 (3×3 angle-pair heatmap with sift category colouring). **Defer to v2 if time-pressed; the existing skip-if-not-applicable behaviour is fine for v1.**

### MODIFY: `qkd_sim/STYLESHEET.py`

Add to `PlotStyle`:
```python
protocol_colours: Dict[str, str] = field(default_factory=lambda: {
    'BB84': '#dd1634',
    'B92':  '#1a5c8a',
    'E91':  '#22a043',
})
protocol_markers: Dict[str, str] = field(default_factory=lambda: {
    'BB84': 's',
    'B92':  '^',
    'E91':  'D',
})
```

### MODIFY: `qkd_sim/__main__.py`

1. **Add `run_protocol_comparison(config)`** dispatcher:
   - Resolve protocol classes via `[get_protocol(name) for name in config.protocols]`
   - Compute `strengths = np.linspace(...)` from sweep config
   - Build `protocol_kwargs` dict — for E91, populate `{'channel_topology': config.e91_channel_topology}`
   - Call `runner.run_protocol_comparison(...)`
   - For each kind in `('qber', 'secure_key_rate')`, call `plotter.plot_protocol_comparison(data_dict, kind=...)`
   - Print summary table

2. **Add the dispatch branch:**
   ```python
   elif config.mode == 'protocol_comparison':
       run_protocol_comparison(config)
   ```

3. **In `run_sweep`, after the existing QBER and key-rate plots, if the protocol is E91 and `data.chsh_mean is not None`:**
   ```python
   plotter.plot_chsh_vs_noise(data, protocol_class=protocol_class,
                              channel_topology=config.e91_channel_topology,
                              save_path=str(out / 'chsh_vs_noise.png'),
                              show=config.show_plots)
   ```

4. **Update the banner** in `_print_banner` to mention E91 and `protocol_comparison` mode.

5. **Update `--list-protocols` output** — already auto-discovers via the registry, so E91 will appear once `register_protocol("e91", ...)` runs at import time. Verify.

### MODIFY: `qkd_sim/config.py`

1. **Add fields to `SimConfig`:**
   ```python
   protocols: Optional[List[str]] = None       # for protocol_comparison mode
   e91_channel_topology: str = 'both'          # 'both' or 'bob'
   ```

2. **Add YAML mappings:**
   ```python
   _YAML_MAPPING['protocols'] = 'protocols'
   _NESTED_MAPPING[('e91', 'channel_topology')] = 'e91_channel_topology'
   ```

3. **Add `protocol_comparison` to `_REQUIRED`:**
   ```python
   'protocol_comparison': ['mode', 'protocols', 'noise_type',
                           'noise_strength_min', 'noise_strength_max',
                           'noise_strength_steps'],
   ```

4. **Validate `e91_channel_topology in ('both', 'bob')`** in `_validate_required` (or a new validator).

### MODIFY: `qkd_sim/scenarios.py`

Add three E91 scenarios:
```python
E91_IDEAL = DomainScenario(
    name="E91 Ideal Singlet",
    description="E91 in a noise-free channel; |S| should approach 2*sqrt(2) ~ 2.828.",
    noise_type='none', noise_strength=0.0, n_qubits=400,
    protocol="e91", eve_rate=None,
    metadata={'expected_qber': 0.0, 'expected_S': 2*np.sqrt(2),
              'channel_topology': 'both'})

E91_DEPOLARISING_LOW = DomainScenario(
    name="E91 Depolarising 5%",
    description="E91 with two-sided depolarising at p=0.05. QBER ~ p - p^2/2.",
    noise_type='depolarizing', noise_strength=0.05, n_qubits=400,
    protocol="e91", eve_rate=None,
    metadata={'expected_qber': 0.05 - 0.05**2/2,
              'expected_S': 2*np.sqrt(2)*(0.95)**2,
              'channel_topology': 'both'})

E91_VIOLATION_LOST = DomainScenario(
    name="E91 CHSH Violation Lost",
    description="E91 at depolarising strength p~0.16 where two-sided visibility "
                "drops below 1/sqrt(2) and CHSH violation is lost.",
    noise_type='depolarizing', noise_strength=0.16, n_qubits=600,
    protocol="e91", eve_rate=None,
    metadata={'expected_S': 2*np.sqrt(2)*(0.84)**2,
              'channel_topology': 'both'})
```
Register them in the `SCENARIOS` dict.

### NEW: `configs/e91_noise_sweep.yaml`
```yaml
mode: sweep
protocol: e91
n_qubits: 400        # 400 EPR pairs; sift fraction 2/9 -> ~89 key bits/trial
n_trials: 30
f_ec: 1.16

noise:
  type: depolarizing

sweep:
  min: 0.0
  max: 0.30
  steps: 21

e91:
  channel_topology: both     # 'both' (default) or 'bob'

eve:
  rate: null

output:
  directory: ./results/e91_noise_sweep
  save_plots: true
  show_plots: false
  format: png
```

### NEW: `configs/protocol_comparison.yaml`
```yaml
mode: protocol_comparison
protocols:
  - bb84
  - b92
  - e91
n_qubits: 400
n_trials: 30
f_ec: 1.16

noise:
  type: depolarizing

sweep:
  min: 0.0
  max: 0.30
  steps: 16

e91:
  channel_topology: both

output:
  directory: ./results/protocol_comparison
  save_plots: true
  show_plots: false
  format: png
```

### NEW: `tests/__init__.py` (empty file)

### NEW: `tests/test_e91.py` (~350 lines)

Pytest-based test suite. Use `numpy.random.seed` per-test for reproducibility.

| ID  | Test                                  | What it catches                                              |
|-----|---------------------------------------|--------------------------------------------------------------|
| T1  | Singlet preparation Statevector       | Wrong gate sequence producing \|Φ⁻⟩ instead of \|Ψ⁻⟩         |
| T2  | Ideal channel: QBER ≈ 0, \|S\| ≈ 2√2  | End-to-end protocol correctness                              |
| T3  | Sifting rate ≈ 2/9 (binomial)         | Sift table errors                                            |
| T4  | CHSH violation flag at ideal/noisy    | `chsh_violation` property logic                              |
| T5  | Depolarising QBER (`both` topology)   | The `p − p²/2` vs `p/2` formula bug                          |
| T6  | Depolarising QBER (`bob` topology)    | Confirms single-sided gives BB84-like `p/2`                  |
| T7  | Depolarising \|S\| degradation        | Werner V² visibility formula                                 |
| T8  | Reproducibility with seeded RNG       | Determinism for dissertation reproducibility                 |
| T9  | Memory string clbit ordering          | Little-endian Qiskit convention; deterministic state test    |
| T10 | Protocol registry                     | `get_protocol('e91') is E91Protocol`                         |
| T11 | E91Result dataclass shape             | All extra fields present and typed correctly                 |

**T1 implementation sketch:**
```python
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
import numpy as np

def test_singlet_preparation():
    qc = QuantumCircuit(2)
    qc.h(0); qc.cx(0, 1); qc.x(0); qc.z(0)
    sv = Statevector(qc)
    expected = np.array([0, 1/np.sqrt(2), -1/np.sqrt(2), 0], dtype=complex)
    # Tolerate global phase
    assert np.allclose(sv.data, expected, atol=1e-9) or \
           np.allclose(sv.data, -expected, atol=1e-9)
```

**T5 implementation sketch:**
```python
def test_depolarizing_qber_two_sided():
    np.random.seed(42)
    runner = BenchmarkRunner(verbose=False)
    strengths = np.array([0.0, 0.05, 0.10, 0.15])
    data = runner.run_noise_sweep(
        protocol_class=E91Protocol,
        noise_type='depolarizing',
        strengths=strengths,
        n_trials=20,
        n_qubits=400,
        f_ec=1.16,
        protocol_kwargs={'channel_topology': 'both'},
    )
    expected = strengths - strengths**2 / 2
    sem = data.qber_sem
    # Within 4 SEM (allows occasional flake)
    assert np.all(np.abs(data.qber_mean - expected) < 4 * np.maximum(sem, 0.005))
```

**T9 implementation sketch:**
```python
def test_clbit_ordering():
    qc = QuantumCircuit(2, 2)
    qc.x(0)               # qubit 0 -> |1>
    qc.measure(0, 0)
    qc.measure(1, 1)
    backend = AerSimulator()
    job = backend.run([qc], shots=1, memory=True)
    bits = job.result().get_memory(0)[0].replace(' ', '')
    # clbit 0 (Alice) is rightmost; should be '1'
    assert bits[-1] == '1'
    assert bits[-2] == '0'
```

Tests are runnable via `python -m pytest tests/ -v`. The `BenchmarkRunner.run_noise_sweep` extension to accept `protocol_kwargs` (described above) is a prerequisite for T5/T6.

### MODIFY: `Model_Assumptions.md`

Add a new section "11. E91 Protocol-Specific Assumptions" documenting:
- Singlet \|Ψ⁻⟩ preparation gate sequence
- Three-angle Ekert convention (XZ-plane)
- Sifting probabilities (2/9 / 4/9 / 3/9)
- Channel topology choice and the V² vs V distinction
- Closed-form formulas for depolarising only; other channels deferred
- Bit-flip on Bob's side after sifting (singlet anti-correlation)
- CHSH parameter as supplementary security indicator (`|S| > 2`)
- `n_qubits` semantically means "EPR pairs" for E91
- What is **not** modelled in v1: eavesdropper, finite-key bounds on the CHSH estimator, device-independent security, two-way classical post-processing, source defects, detection-loophole effects

Update the QBER table in section 3.2 with the E91 row.

### MODIFY: `configs/CONFIG_REFERENCE.md`

- Add a new section documenting `protocol_comparison` mode (required fields, example, output)
- Document the `e91.channel_topology` config field and its effect
- Note that `n_qubits` for E91 means "number of EPR pairs"
- Add E91 scenarios to the scenarios reference table
- Update the "Required Fields Per Mode" table to include the new mode

---

## Verification Plan

Run end-to-end after implementation:

1. **Run the unit tests:**
   ```bash
   python -m pytest tests/ -v
   ```
   All 11 tests should pass. T5 is the highest-value test — if it fails the depolarising formula is wrong.

2. **Run the E91 noise sweep:**
   ```bash
   python -m qkd_sim configs/e91_noise_sweep.yaml
   ```
   Expected: QBER curve following `p − p²/2`, CHSH curve following `2√2(1−p)²`, both with theoretical overlays. Save plots to `results/e91_noise_sweep/`.

3. **Run the multi-protocol comparison:**
   ```bash
   python -m qkd_sim configs/protocol_comparison.yaml
   ```
   Expected: a single QBER plot with three curves (BB84 in red, B92 in blue, E91 in green), and a single secure-key-rate plot with the same three curves. E91 should show lower QBER at `bob` topology (matches BB84) and slightly higher at `both` topology.

4. **Run the BB84 noise sweep** to confirm no regression:
   ```bash
   python -m qkd_sim configs/noise_sweep.yaml
   ```
   QBER should still match `p/2` exactly. Plots should be unchanged from the pre-refactor baseline.

5. **List protocols** to confirm E91 is registered:
   ```bash
   python -m qkd_sim --list-protocols
   ```
   Expected output includes `e91 - E91`.

6. **Run an E91 scenario:**
   ```bash
   python -m qkd_sim --list-scenarios
   python -m qkd_sim configs/scenario.yaml --scenario e91_ideal
   ```
   Expected: ideal-channel QBER ~ 0 and \|S\| ~ 2.828.

7. **Single-trial sanity check** with very small `n_qubits`:
   ```bash
   python -m qkd_sim configs/single_trial.yaml --protocol e91 --n-qubits 50
   ```
   Confirm no crashes with empty CHSH buckets (the warning path).

---

## Critical Risks (ranked) and Mitigations

1. **Wrong depolarising QBER formula (`p/2` vs `p − p²/2`).** Most likely physics bug. **Mitigation:** test T5 + explicit derivation in docstring.
2. **Wrong singlet preparation gate sequence (\|Φ⁻⟩ vs \|Ψ⁻⟩).** **Mitigation:** Statevector test T1 + explicit gate-by-gate derivation in plan + reuse of verified preparation in code.
3. **Wrong Qiskit `Ry` rotation factor of 2.** Easy to mis-derive. **Mitigation:** use `Ry(-theta)` not `Ry(-2*theta)`, document the convention, validate via T2 (ideal CHSH should give ~ -2√2 with no factor of 2 anywhere).
4. **Qiskit memory string endianness.** Wrong indexing silently swaps Alice/Bob. **Mitigation:** test T9 with deterministic state.
5. **Empty CHSH buckets at small `n_qubits`.** Division-by-zero in correlation. **Mitigation:** explicit check returning 0.0 with warning + scenario default `n_qubits = 400`.
6. **`n_qubits` semantic shift confuses the user.** **Mitigation:** docstring + Model_Assumptions.md + CONFIG_REFERENCE.md + scenarios use 400 by default.
7. **Comparison plot legend collisions** when E91 has BB84-like curves under `bob` topology. **Mitigation:** distinct colours/markers in `STYLESHEET.py`.

---

## Critical Files (priority order)

- `qkd_sim/protocols/e91.py` — **NEW** — entire E91 protocol class (~280 lines)
- `tests/test_e91.py` — **NEW** — 11 test cases (~350 lines)
- `qkd_sim/benchmark.py` — **MODIFY** — extend `BenchmarkData` with CHSH stats, add `run_protocol_comparison`, accept `protocol_kwargs` in `run_noise_sweep`
- `qkd_sim/plotter.py` — **MODIFY** — add `plot_chsh_vs_noise`, `plot_protocol_comparison`
- `qkd_sim/__main__.py` — **MODIFY** — `protocol_comparison` dispatcher, CHSH plot in `run_sweep` for E91, banner update
- `qkd_sim/config.py` — **MODIFY** — `protocols` list field, `e91_channel_topology` field, validation, mode entry
- `qkd_sim/scenarios.py` — **MODIFY** — three E91 scenarios
- `qkd_sim/STYLESHEET.py` — **MODIFY** — `protocol_colours`/`protocol_markers`
- `qkd_sim/protocols/__init__.py` — **MODIFY** — import `e91` to trigger registration
- `qkd_sim/__init__.py` — **MODIFY** — export `E91Protocol`, `E91Result`
- `tests/__init__.py` — **NEW** — empty
- `configs/e91_noise_sweep.yaml` — **NEW**
- `configs/protocol_comparison.yaml` — **NEW**
- `Model_Assumptions.md` — **MODIFY** — section 11 on E91 assumptions
- `configs/CONFIG_REFERENCE.md` — **MODIFY** — `protocol_comparison` mode docs, E91 notes

---

## Implementation Order (incremental, each step independently runnable)

1. Singlet prep + T1 Statevector test + T9 clbit-ordering test (smallest possible PR)
2. `E91Protocol.run()` end-to-end ideal channel + T2, T3, T4, T10, T11
3. `theoretical_qber('depolarizing', ..., 'both')` + `theoretical_chsh` + T5, T7
4. Single-sided `'bob'` topology + T6
5. Reproducibility seeding pass + T8
6. Extend `BenchmarkData` + `run_noise_sweep` for CHSH stats; smoke test sweep
7. `plot_chsh_vs_noise` + integrate into `__main__.run_sweep`
8. `STYLESHEET.py` protocol palette
9. `BenchmarkRunner.run_protocol_comparison` + `plot_protocol_comparison`
10. `__main__.run_protocol_comparison` dispatcher + config schema additions
11. E91 scenarios + YAML configs
12. Documentation updates (`Model_Assumptions.md`, `CONFIG_REFERENCE.md`)
13. End-to-end verification per the Verification Plan

(Eve and the non-depolarising closed-form theoretical curves are deferred to a v2 follow-up by user decision.)
