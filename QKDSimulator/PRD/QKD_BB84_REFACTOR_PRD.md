# PRD: QKD Simulation Platform Refactor

## Context

This is a Python/Qiskit quantum key distribution (QKD) simulation platform for an undergraduate dissertation. It currently implements the BB84 protocol across 9 files (~1,850 lines). The goal of this refactor is to make the architecture multi-protocol (supporting BB84, B92, and optionally E91), introduce YAML-based configuration, and fix several structural issues - all without breaking the working BB84 simulation.

**Constraints:**
- Solo developer, tight deadline (dissertation due ~3 weeks)
- Must remain runnable after each change - no big-bang rewrites
- Python 3.10+, Qiskit SDK, qiskit-aer, numpy, matplotlib, seaborn, tqdm, PyYAML
- All noise is applied via identity gate (`qc.id(0)`) channel markers - this pattern MUST be preserved
- Error correction efficiency `f_ec` (default 1.16 for CASCADE) threads through the entire system

---

## Current File Structure

```
bb84_simulation/
├── __init__.py        # 78 lines  - public API re-exports
├── protocol.py        # 218 lines - BB84Protocol class + BB84Result dataclass
├── noise.py           # 118 lines - NoiseModelFactory + NoiseType Literal alias
├── eve.py             # 115 lines - EveInterceptor (intercept-resend attack)
├── benchmark.py       # 228 lines - BenchmarkRunner + BenchmarkData dataclass
├── plotter.py         # 641 lines - BB84Plotter (all visualisations)
├── scenarios.py       # 186 lines - DomainScenario dataclass + 8 preset scenarios
├── main.py            # 210 lines - argparse CLI (single/sweep/compare/scenario)
└── run.py             # 510 lines - CONFIG dict runner (duplicate of main.py)
```

---

## Target File Structure

```
qkd_sim/
├── __init__.py              # Package exports
├── __main__.py              # Entry point: `python -m qkd_sim config.yaml`
├── config.py                # YAML config loader + SimConfig dataclass
├── base.py                  # QKDProtocol ABC + QKDResult base dataclass
├── registry.py              # Protocol name → class registry
│
├── protocols/
│   ├── __init__.py
│   ├── bb84.py              # BB84Protocol(QKDProtocol) + BB84Result(QKDResult)
│   └── b92.py               # B92Protocol(QKDProtocol) + B92Result(QKDResult)
│
├── noise.py                 # NoiseModelFactory (KEEP AS-IS, already protocol-agnostic)
├── eve.py                   # EveInterceptor (refactored: remove dead param)
├── benchmark.py             # BenchmarkRunner (refactored: protocol-agnostic)
├── plotter.py               # QKDPlotter (renamed, generalised type hints)
├── scenarios.py             # DomainScenario (add protocol field)
│
└── configs/                 # Example YAML config files
    ├── single_trial.yaml
    ├── noise_sweep.yaml
    ├── eve_sweep.yaml
    ├── comparison.yaml
    └── scenario.yaml
```

**Note:** `run.py` is deliberately deleted. `main.py` is replaced by `__main__.py` with YAML config loading.

---

## Task 1: Create Protocol Abstraction Layer

### 1A: Create `base.py`

Create a new file `qkd_sim/base.py` containing:

**`QKDResult` base dataclass:**
```python
@dataclass
class QKDResult:
    """Base result container for any QKD protocol run."""
    protocol_name: str          # e.g. "BB84", "B92"
    n_qubits: int
    alice_bits: np.ndarray
    bob_results: np.ndarray
    sifted_indices: np.ndarray
    sifted_key_alice: np.ndarray
    sifted_key_bob: np.ndarray
    qber: float
    key_rate: float             # sifted bits / transmitted qubits
    f_ec: float = 1.16
    eve_intercepted: Optional[np.ndarray] = None
```

Include these computed `@property` methods on `QKDResult` (move from current `BB84Result`):
- `sifted_length -> int`
- `error_count -> int`
- `_binary_entropy(x) -> float` (static method)
- `secure_key_rate -> float` (Shor-Preskill bound: `key_rate * max(0, 1 - h(e) - f_ec * h(e))`)
- `is_secure -> bool`

**`QKDProtocol` abstract base class:**
```python
from abc import ABC, abstractmethod

class QKDProtocol(ABC):
    """Abstract contract for all QKD protocol implementations."""

    def __init__(self, n_qubits: int, backend: AerSimulator,
                 eve: Optional[EveInterceptor] = None, f_ec: float = 1.16):
        self.n_qubits = n_qubits
        self.backend = backend
        self.eve = eve
        self.f_ec = f_ec

    @abstractmethod
    def run(self) -> QKDResult:
        """Execute the full protocol and return results."""
        ...

    @classmethod
    @abstractmethod
    def protocol_name(cls) -> str:
        """Short identifier, e.g. 'BB84', 'B92'.
        Must be a @classmethod (not @staticmethod) so it can be called on the
        class object retrieved from the registry without instantiation."""
        ...

    @classmethod
    def theoretical_sifting_rate(cls) -> float:
        """Expected fraction of transmitted qubits that survive sifting.

        BB84 default = 0.5 (Alice and Bob basis match with probability 0.5).
        B92 MUST override this to return 0.25 (conclusive event requires
        complementary basis AND outcome 1, so P = 0.5 × 0.5 = 0.25 at zero noise).

        Note: the B92 sifting rate is noise-dependent in practice - noise creates
        spurious conclusive events, raising the rate to (1+p)/4. This method
        returns the noise-free approximation, which is used only for theoretical
        curve overlays, not for results computed from simulation data."""
        return 0.5

    @staticmethod
    def theoretical_qber(noise_type: str, strengths: np.ndarray) -> Optional[np.ndarray]:
        """Analytical QBER prediction for this protocol. Return None if no closed form."""
        return None

    @classmethod
    def theoretical_secure_key_rate(cls, noise_type: str, strengths: np.ndarray, f_ec: float = 1.16) -> Optional[np.ndarray]:
        """Analytical secure key rate using the Shor-Preskill formula.

        Default implementation combines theoretical_qber() and theoretical_sifting_rate().
        Subclasses need only override theoretical_qber() (and theoretical_sifting_rate()
        if their sifting efficiency differs from BB84's 0.5).

        Formula: sifting_rate × max(0, 1 − (1 + f_ec) × h(e))
        where h(e) = binary entropy of the QBER e.
        """
        qber = cls.theoretical_qber(noise_type, strengths)
        if qber is None:
            return None
        sifting = cls.theoretical_sifting_rate()

        def _h(x: np.ndarray) -> np.ndarray:
            x = np.clip(x, 1e-15, 1.0 - 1e-15)
            return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

        return sifting * np.maximum(0.0, 1.0 - (1.0 + f_ec) * _h(qber))
```

The default `theoretical_secure_key_rate` uses `cls.theoretical_sifting_rate()` so that B92
(which overrides `theoretical_sifting_rate()` to 0.25) automatically gets the correct formula.
Subclasses only need to override `theoretical_qber()` in most cases.

### 1B: Refactor `BB84Protocol` to inherit from `QKDProtocol`

Move `protocol.py` → `protocols/bb84.py`. Make these changes:

1. `BB84Result` inherits from `QKDResult`. Add BB84-specific fields:
   - `alice_bases: np.ndarray`
   - `bob_bases: np.ndarray`
   - Keep the `get_basis_matrix()` method here (BB84-specific)

2. `BB84Protocol` inherits from `QKDProtocol`.
   - Implement `protocol_name()` as a `@classmethod` returning `"BB84"` (required by updated ABC)
   - Move current `theoretical_qber` logic from `plotter.py` into `BB84Protocol.theoretical_qber()` as a `@staticmethod`
   - All existing quantum circuit logic (`_alice_prepare`, `_bob_measure`, `_post_process`) stays in this class unchanged

3. The existing protocol logic (Alice prep, identity gate channel marker, Bob measurement, basis sifting) MUST NOT be modified. Only the class hierarchy changes.

4. **`_post_process()` must pass `protocol_name`** when constructing the result. Since `QKDResult` now has `protocol_name: str` as its first field, every call site that builds a result object must supply it. In `BB84Protocol._post_process()`, pass `protocol_name="BB84"` as the first argument to `BB84Result(...)`. Likewise, `B92Protocol._post_process()` must pass `protocol_name="B92"`. Forgetting this will cause a `TypeError` at runtime.

### 1C: Create `registry.py`

Simple dict-based protocol registry:

```python
_REGISTRY: Dict[str, Type[QKDProtocol]] = {}

def register_protocol(name: str, cls: Type[QKDProtocol]):
    _REGISTRY[name.lower()] = cls

def get_protocol(name: str) -> Type[QKDProtocol]:
    if name.lower() not in _REGISTRY:
        available = ', '.join(_REGISTRY.keys())
        raise KeyError(f"Unknown protocol '{name}'. Available: {available}")
    return _REGISTRY[name.lower()]

def list_protocols() -> List[str]:
    return sorted(_REGISTRY.keys())
```

Each protocol file registers itself at module level:
```python
# At bottom of protocols/bb84.py
from qkd_sim.registry import register_protocol
register_protocol("bb84", BB84Protocol)
```

---

## Task 2: YAML Configuration System

### 2A: Create `config.py`

Define a `SimConfig` dataclass that holds all simulation parameters:

```python
@dataclass
class SimConfig:
    """Complete simulation configuration loaded from YAML."""
    # Execution mode
    mode: str                          # "single", "sweep", "eve_sweep", "comparison", "scenario"

    # Protocol selection
    protocol: str = "bb84"             # registry key

    # Basic parameters
    n_qubits: int = 256
    n_trials: int = 30
    f_ec: float = 1.16

    # Noise configuration
    noise_type: str = "none"
    noise_strength: float = 0.0

    # Sweep parameters (used when mode is "sweep" or "comparison")
    noise_strength_min: float = 0.0
    noise_strength_max: float = 0.30        # matches noise_sweep.yaml default
    noise_strength_steps: int = 21

    # Multi-noise comparison list (used when mode is "comparison")
    noise_models: List[str] = field(default_factory=lambda: ["depolarizing"])

    # Eve configuration
    eve_rate: Optional[float] = None   # None = no eavesdropper

    # Eve sweep parameters (used when mode is "eve_sweep")
    eve_rate_min: float = 0.0
    eve_rate_max: float = 1.0
    eve_rate_steps: int = 11

    # Scenario mode
    scenario_name: Optional[str] = None

    # Output configuration
    output_dir: str = "./results"
    save_plots: bool = True
    show_plots: bool = False           # False by default for batch runs
    plot_format: str = "png"
```

**Implement a `load_config(path: str) -> SimConfig` function** that:
1. Reads a YAML file using `yaml.safe_load()`
2. Flattens nested YAML keys into the flat dataclass using the mapping table below
3. Validates required fields based on `mode`
4. Returns a `SimConfig` instance
5. Raises clear error messages for invalid values

**YAML → SimConfig flattening mapping (complete):**

| YAML key | SimConfig field |
|---|---|
| `mode` | `mode` |
| `protocol` | `protocol` |
| `n_qubits` | `n_qubits` |
| `n_trials` | `n_trials` |
| `f_ec` | `f_ec` |
| `noise.type` | `noise_type` |
| `noise.strength` | `noise_strength` |
| `sweep.min` | `noise_strength_min` |
| `sweep.max` | `noise_strength_max` |
| `sweep.steps` | `noise_strength_steps` |
| `noise_models` | `noise_models` |
| `eve.rate` | `eve_rate` |
| `eve_sweep.min` | `eve_rate_min` |
| `eve_sweep.max` | `eve_rate_max` |
| `eve_sweep.steps` | `eve_rate_steps` |
| `scenario_name` | `scenario_name` |
| `output.directory` | `output_dir` |
| `output.save_plots` | `save_plots` |
| `output.show_plots` | `show_plots` |
| `output.format` | `plot_format` |

**Required fields per mode** (missing required fields must raise `ValueError`):

| Mode | Required YAML fields |
|---|---|
| `single` | `mode`, `noise.type`, `noise.strength` |
| `sweep` | `mode`, `noise.type`, `sweep.min`, `sweep.max`, `sweep.steps` |
| `eve_sweep` | `mode`, `eve_sweep.min`, `eve_sweep.max`, `eve_sweep.steps` |
| `comparison` | `mode`, `noise_models`, `sweep.min`, `sweep.max`, `sweep.steps` |
| `scenario` | `mode`, `scenario_name` |

All other fields fall back to `SimConfig` defaults when absent from the YAML. In particular:
- `noise.strength` is **not required** in sweep/comparison/eve_sweep modes (it is unused; the sweep range applies instead)
- `protocol` defaults to `"bb84"` if omitted
- `n_trials` defaults to `30` if omitted

**Also implement `config_to_dict(config: SimConfig) -> dict`** for serialising configs alongside results (reproducibility).

### 2B: YAML Config File Format

The YAML format should use nested structure for readability. Create example configs:

**`configs/single_trial.yaml`:**
```yaml
# Single BB84 trial with depolarising noise
mode: single
protocol: bb84
n_qubits: 256
f_ec: 1.16

noise:
  type: depolarizing
  strength: 0.05

eve:
  rate: null  # No eavesdropper (set to 0.0-1.0 to enable)

output:
  directory: ./results/single
  save_plots: true
  show_plots: true
  format: png
```

**`configs/noise_sweep.yaml`:**
```yaml
# Noise strength parameter sweep
mode: sweep
protocol: bb84
n_qubits: 256
n_trials: 30
f_ec: 1.16

noise:
  type: depolarizing

sweep:
  min: 0.0
  max: 0.30
  steps: 21

eve:
  rate: null

output:
  directory: ./results/depolarising_sweep
  save_plots: true
  show_plots: false
  format: png
```

**`configs/eve_sweep.yaml`:**
```yaml
# Eve interception rate sweep
mode: eve_sweep
protocol: bb84
n_qubits: 256
n_trials: 30
f_ec: 1.16

noise:
  type: none
  strength: 0.0

eve_sweep:
  min: 0.0
  max: 1.0
  steps: 11

output:
  directory: ./results/eve_sweep
  save_plots: true
  format: png
```

**`configs/comparison.yaml`:**
```yaml
# Compare all noise models side by side
mode: comparison
protocol: bb84
n_qubits: 256
n_trials: 30
f_ec: 1.16

noise_models:
  - depolarizing
  - bitflip
  - phaseflip
  - amplitude_damping
  - phase_damping

sweep:
  min: 0.0
  max: 0.20
  steps: 15

output:
  directory: ./results/comparison
  save_plots: true
  format: png
```

**`configs/scenario.yaml`:**
```yaml
# Run a pre-defined deployment scenario
mode: scenario
scenario_name: metropolitan
f_ec: 1.16

output:
  directory: ./results/scenario
  save_plots: true
  format: png
```

### 2C: Create `__main__.py`

Entry point that loads YAML and dispatches execution:

```
Usage:
  python -m qkd_sim configs/sweep.yaml
  python -m qkd_sim configs/sweep.yaml --n-trials 5    # override for quick test
  python -m qkd_sim --list-protocols
  python -m qkd_sim --list-scenarios
```

Implementation:
1. Use `argparse` with a positional `config_file` argument
2. Support optional `--override` flags for common parameters: `--n-trials`, `--n-qubits`, `--protocol`, `--show-plots`
3. Load config via `load_config()`
4. Apply any CLI overrides on top
5. Resolve protocol class from registry via `get_protocol(config.protocol)`
6. Dispatch to the appropriate execution function based on `config.mode`
7. Print a summary of the config before execution
8. Print results after execution

The dispatch functions (`run_single`, `run_sweep`, `run_comparison`, `run_scenario`, `run_eve_sweep`) should live in `__main__.py` and follow the same logic currently in `main.py`'s `cmd_*` functions, but reading from `SimConfig` instead of argparse args.

---

## Task 3: Make Existing Modules Protocol-Agnostic

### 3A: Refactor `benchmark.py`

**Current problem:** `BenchmarkRunner` hardcodes `BB84Protocol` in every method.

**Fix:** Add a `protocol_class` parameter to all runner methods:

```python
def run_noise_sweep(
    self,
    protocol_class: Type[QKDProtocol],   # NEW - was hardcoded BB84Protocol
    noise_type: NoiseType,
    strengths: np.ndarray,
    n_trials: int = 30,
    n_qubits: int = 100,
    with_eve: bool = False,
    eve_rate: float = 0.5,
    f_ec: float = 1.16
) -> BenchmarkData:
```

Inside the loop, change:
```python
# OLD:
protocol = BB84Protocol(n_qubits=n_qubits, backend=backend, eve=eve, f_ec=f_ec)

# NEW:
protocol = protocol_class(n_qubits=n_qubits, backend=backend, eve=eve, f_ec=f_ec)
```

Apply the same change to `run_eve_sweep`, `run_multi_noise_comparison`, and `run_single_config`.

**Also:** Add `protocol_name: str` as a **first-class dataclass field** on `BenchmarkData` (not just stuffed into the `metadata` dict) so results track which protocol generated them. The field should be set by each runner method using `protocol_class.protocol_name()`:

```python
@dataclass
class BenchmarkData:
    protocol_name: str          # NEW - e.g. "BB84", "B92"
    parameter_name: str
    parameter_values: np.ndarray
    # ... rest unchanged
```

**Also:** Change imports from `from protocol import BB84Protocol, BB84Result` to `from .base import QKDProtocol, QKDResult`.

### 3B: Refactor `plotter.py`

1. **Rename class** `BB84Plotter` → `QKDPlotter`
2. **Change type hints** from `BB84Result` → `QKDResult` throughout
3. **Remove `theoretical_qber()` and `theoretical_secure_key_rate()` methods** from the plotter class
4. **Instead**, plotting methods that overlay theory curves should accept an optional `protocol_class` parameter and call `protocol_class.theoretical_qber(noise_type, strengths)`:

```python
def plot_qber_vs_noise(
    self,
    data: BenchmarkData,
    protocol_class: Optional[Type[QKDProtocol]] = None,  # for theory overlay
    ...
) -> plt.Figure:
    # ...
    if show_theory and protocol_class is not None:
        theory_y = protocol_class.theoretical_qber(data.noise_type, theory_x)
        if theory_y is not None:
            ax.plot(theory_x, theory_y, ...)
```

**Unit scaling for secure key rate theory curves:** The ABC's `theoretical_secure_key_rate()` returns a raw fractional rate (e.g. 0.0–0.5). The plotter's y-axis for key rate plots uses "bits per 100 qubits". When overlaying the theory curve in `plot_key_rate_vs_noise()` and `plot_key_rate_comparison()`, the plotter **must multiply** the result of `protocol_class.theoretical_secure_key_rate()` **by 100** before plotting:

```python
theory_y = protocol_class.theoretical_secure_key_rate(data.noise_type, theory_x, f_ec=self.f_ec)
if theory_y is not None:
    ax.plot(theory_x, theory_y * 100, ...)  # scale to per-100 qubits
```

Failing to do this will make theory curves appear 100× too small on the plot.

5. **Keep** the colour palette, marker scheme, font loading, DPI settings, and SEM error bar logic - these are all good
6. **Move** the `draw_bb84_circuit()` function from the deleted `run.py` into `protocols/bb84.py` as a standalone module-level function (not into `QKDPlotter` - it is BB84-specific and does not belong in the protocol-agnostic plotter)
7. The `plot_basis_heatmap` method should accept `QKDResult` but **guard against protocols that lack basis matrices**. `B92Result` has no `alice_bases` field (Alice doesn't choose a basis in B92), so `get_basis_matrix()` is BB84-specific. The plotter must check with `hasattr(result, 'alice_bases')` before calling `get_basis_matrix()`. If the attribute is missing, either skip the heatmap with a log message (`"Basis heatmap not available for {protocol_name}"`) or render an alternative B92-specific visualisation showing Alice's bit-state encoding vs Bob's basis choice. For this refactor, **skipping with a message is sufficient** - a B92-specific heatmap can be added later if needed.

### 3C: Refactor `eve.py`

1. **Remove the unused `channel_backend` parameter** from `EveInterceptor.intercept()`:
```python
# OLD:
def intercept(self, circuits, channel_backend) -> Tuple[...]:

# NEW:
def intercept(self, circuits: List[QuantumCircuit]) -> Tuple[List[QuantumCircuit], np.ndarray]:
```

2. **Update the call site** in `protocols/bb84.py` (`BB84Protocol.run()`) that passes `channel_backend` to no longer pass it. Note: `benchmark.py` does not call `eve.intercept()` directly - it goes through `protocol.run()` - so only the protocol file needs updating.

3. Keep all existing quantum logic unchanged - the intercept-resend implementation is correct.

**Important - Eve on B92:** The existing `EveInterceptor` was designed for BB84's symmetric four-state structure. When applied to B92, it will still execute correctly (Eve randomly picks a Z or X basis, measures, and re-prepares), but the QBER contribution is **not** `rate × 0.25`. In B92, Eve's intercept-resend disturbs the non-orthogonal state space differently; the expected QBER from Eve is higher and basis-dependent. For this refactor, `EveInterceptor` is used as-is for B92 simulation (the circuit-level implementation remains valid), but:
- `B92Protocol.theoretical_qber()` must **not** include an Eve term derived from `rate × 0.25`
- Eve QBER on B92 should be read from simulation data only (no closed-form overlay)
- A code comment in `protocols/b92.py` must flag this limitation

### 3D: Refactor `scenarios.py`

Add a `protocol` field to `DomainScenario`:

```python
@dataclass
class DomainScenario:
    name: str
    description: str
    noise_type: NoiseType
    noise_strength: float
    n_qubits: int
    protocol: str = "bb84"          # NEW - registry key
    eve_rate: Optional[float] = None
    metadata: Dict[str, Any] = None
```

Update all existing scenario instances to include `protocol="bb84"`.

**Protocol precedence in scenario mode:** When `mode=scenario`, the protocol is determined exclusively by `DomainScenario.protocol`. The `SimConfig.protocol` field is **ignored** in this mode (since the scenario defines its own protocol). The dispatcher in `__main__.py` must resolve the protocol class from `scenario.protocol`, not from `config.protocol`, when executing a scenario run. Add a comment in the dispatcher making this precedence explicit.

**Silent override warning:** If `config.protocol` differs from `scenario.protocol`, print a warning so the user isn't surprised:
```python
if config.protocol != scenario.protocol:
    print(f"Note: scenario '{scenario.name}' uses protocol '{scenario.protocol}', "
          f"overriding config protocol '{config.protocol}'.")
```

### 3E: Update `__init__.py`

1. **Remove** the `PassiveEve` import (class doesn't exist, causes ImportError)
2. **Remove** the `run_single_trial` import (function doesn't exist in `protocol.py`, also causes ImportError)
3. **Update** imports to reflect new module locations (`protocols.bb84` instead of `protocol`)
4. **Add** new exports: `QKDProtocol`, `QKDResult`, `SimConfig`, `load_config`, `get_protocol`, `list_protocols`, `QKDPlotter`
5. **Use relative imports** consistently throughout all files

### 3F: Delete `run.py`

Remove `run.py` entirely. Its functionality is superseded by the YAML config system + `__main__.py`.

### 3G: Fix all imports

All internal imports must use relative imports for package consistency:
```python
# CORRECT (relative):
from .base import QKDProtocol, QKDResult
from .noise import NoiseModelFactory, NoiseType
from .eve import EveInterceptor

# WRONG (direct):
from protocol import BB84Protocol
from noise import NoiseModelFactory
```

---

## Task 4: Implement B92 Protocol

### 4A: Create `protocols/b92.py`

Implement `B92Protocol(QKDProtocol)` with the following key differences from BB84:

**State preparation (Alice):**
- Alice uses only 2 non-orthogonal states (not 4):
  - Bit 0 → |0⟩ (Z-basis ground state)
  - Bit 1 → |+⟩ (X-basis, via Hadamard on |0⟩)
- Alice does NOT randomly choose a basis - her bit value fully determines her state.
- Channel marker `qc.id(0)` is appended after preparation (same as BB84, preserving the noise pattern).

**Measurement (Bob):**
- Bob randomly chooses to measure in Z-basis (0) or X-basis (1) with equal probability.
- Bob's measurement is the same circuit pattern: optional Hadamard then measure.

**Sifting - conclusive events and bit assignment (CRITICAL):**

The core B92 insight: two non-orthogonal states can never be distinguished with certainty, but a single specific outcome in the complementary basis is *impossible* unless the correct state was sent. That impossible outcome becoming possible reveals, unambiguously, which state Alice sent.

| Alice sent | Bob's basis | Bob's outcome | Event type | Key bit |
|---|---|---|---|---|
| \|0⟩ (bit 0) | Z (0) | 0 | Inconclusive - discard | - |
| \|0⟩ (bit 0) | Z (0) | 1 | **Error** (noise-induced only) | - |
| \|0⟩ (bit 0) | X (1) | 0 | Inconclusive - discard | - |
| \|0⟩ (bit 0) | X (1) | 1 | **Conclusive**: Alice sent \|0⟩ → key bit = **0** |
| \|+⟩ (bit 1) | Z (0) | 0 | Inconclusive - discard | - |
| \|+⟩ (bit 1) | Z (0) | 1 | **Conclusive**: Alice sent \|+⟩ → key bit = **1** |
| \|+⟩ (bit 1) | X (1) | 0 | Inconclusive - discard | - |
| \|+⟩ (bit 1) | X (1) | 1 | **Error** (noise-induced only) | - |

**Key bit assignment rule:** In all conclusive events Bob's raw measurement outcome is always `1`. The key bit is NOT the raw outcome - it is derived from which basis Bob used:

```python
# Conclusive mask: all positions where Bob's raw result == 1
conclusive_mask = (bob_raw_results == 1)

# Key bit for each conclusive position:
#   Bob in Z-basis (0) + outcome 1  →  Alice sent |+⟩ (bit 1)  →  key bit = 1
#   Bob in X-basis (1) + outcome 1  →  Alice sent |0⟩ (bit 0)  →  key bit = 0
sifted_key_bob = 1 - bob_bases[conclusive_mask]   # key bit = 1 - basis

# Alice's key is simply her own bit at each conclusive position:
sifted_key_alice = alice_bits[conclusive_mask]
```

Under no noise these two keys are always identical. Noise creates spurious outcome-1 events (error rows in the table above) that produce mismatched bits, which are measured as QBER.

**Noise-free sifting rate:** At zero noise, conclusive events occur only from the two non-error rows above. Each has probability `P(Alice=correct) × P(Bob=correct basis) × P(outcome 1) = 0.5 × 0.5 × 0.5 = 0.125`. Two such rows → sifting rate = 0.25 (25%).

**B92Result(QKDResult):**
- Same base fields as `QKDResult`
- Add `bob_bases: np.ndarray` (Bob's random basis choices, 0=Z, 1=X)
- Add `conclusive_mask: np.ndarray` (boolean array - True where Bob's raw result was 1)
- Note: Alice has no "bases" array; her bit directly encodes her state

**`B92Protocol.theoretical_sifting_rate()` override:**
```python
@classmethod
def theoretical_sifting_rate(cls) -> float:
    return 0.25  # noise-free approximation; actual rate is (1+p)/4 under depolarising
```

**`B92Protocol.theoretical_qber()` - derivation and implementation:**

The QBER formula for B92 under depolarising noise **is not `p/2`**. The correct formula is derived as follows.

Under Qiskit's depolarising channel (each of X, Y, Z applied with prob p/4; identity with prob 1−3p/4), the effective single-qubit channel is:

- E(|0⟩⟨0|) = (1 − p/2)|0⟩⟨0| + (p/2)|1⟩⟨1|
- E(|+⟩⟨+|) = (1 − p/2)|+⟩⟨+| + (p/2)|−⟩⟨−|

Counting conclusive events and errors across all four (Alice state, Bob basis) combinations per n qubits:

| Combination | Fraction of n | P(outcome 1) | Errors? |
|---|---|---|---|
| Alice=\|0⟩, Bob=Z | n/4 | p/2 (noise-induced) | **All errors** |
| Alice=\|0⟩, Bob=X | n/4 | 1/2 (independent of p) | None |
| Alice=\|+⟩, Bob=Z | n/4 | 1/2 (independent of p) | None |
| Alice=\|+⟩, Bob=X | n/4 | p/2 (noise-induced) | **All errors** |

Total conclusive = (n/4)(p/2 + 1/2 + 1/2 + p/2) = n(1+p)/4
Total errors     = (n/4)(p/2 + p/2)               = np/4

**QBER = np/4 ÷ n(1+p)/4 = p / (1+p)**

This formula is also correct for the bit-flip and phase-flip channels (the algebra differs but the result is the same because each channel disturbs exactly one of Alice's two states). For amplitude damping and phase damping, no simple closed form is available.

**Important - noise type string names:** The existing `NoiseType` Literal in `noise.py` uses `"bitflip"` and `"phaseflip"` (no underscores). All code in this file - including `theoretical_qber()`, YAML configs, and any string comparisons - MUST use these exact names to match the existing `NoiseModelFactory`.

Implement as:

```python
@staticmethod
def theoretical_qber(noise_type: str, strengths: np.ndarray) -> Optional[np.ndarray]:
    # B92 QBER under depolarising, bit-flip, and phase-flip channels.
    # Derivation: noise creates spurious outcome-1 events on the "wrong" states,
    # giving QBER = p/(1+p)  (NOT p/2 as in BB84).
    # Note: sifting rate also becomes noise-dependent: (1+p)/4 rather than 0.25.
    # Eve's QBER contribution is NOT modelled here (no closed form for B92 intercept-resend).
    if noise_type in ("depolarizing", "bitflip", "phaseflip"):
        p = strengths
        return p / (1.0 + p)
    return None  # No closed form for amplitude_damping or phase_damping
```

**Security formula - Shor-Preskill approximation:**

The Shor-Preskill bound was proven for BB84. Applying the same formula to B92 is a **pragmatic approximation** for comparative analysis; it is not a rigorous B92 security proof (see Tamaki et al., PRA 68, 022311, 2003 for the full B92 proof). The `theoretical_secure_key_rate()` default in the ABC handles this correctly via `theoretical_sifting_rate()` returning 0.25. Add a docstring comment in `B92Protocol` flagging this approximation.

**Known divergence at high noise:** Because `theoretical_sifting_rate()` returns a fixed 0.25 while the actual B92 sifting rate is noise-dependent `(1+p)/4`, the theoretical secure key rate curve will systematically underestimate the simulation data at moderate-to-high noise strengths (e.g. ~30% discrepancy at p=0.3). This is acceptable for comparative overlays but the plotter should include a code comment noting this limitation so it isn't misinterpreted as a simulation bug.

**Register at bottom of file:**
```python
from qkd_sim.registry import register_protocol
register_protocol("b92", B92Protocol)
```

### 4B: Ensure protocol auto-registration

In `protocols/__init__.py`, import both protocol modules so they register on package import:
```python
from . import bb84
from . import b92
```

---

## Task 5: Dependency Installation

Add `PyYAML` to the project dependencies. The YAML config loader requires it:
```
pip install pyyaml
```

Ensure existing dependencies are present: `qiskit`, `qiskit-aer`, `numpy`, `matplotlib`, `seaborn`, `tqdm`, `art` (used for the ASCII banner printed by `__main__.py` at startup).

---

## Validation Criteria

After all changes, the following must work:

### 1. BB84 single trial via YAML config
```bash
python -m qkd_sim configs/single_trial.yaml
```
Should produce a result with QBER, key rate, and secure key rate. Output should print protocol name "BB84".

### 2. BB84 noise sweep via YAML config
```bash
python -m qkd_sim configs/noise_sweep.yaml
```
Should run 30 trials × 21 noise strengths, display progress bar, and save QBER + key rate plots to the output directory.

### 3. Multi-noise comparison
```bash
python -m qkd_sim configs/comparison.yaml
```
Should benchmark all 5 noise models and produce comparison plots with theoretical overlays.

### 4. B92 single trial
Create a config with `protocol: b92` and verify:
- Sifting rate is approximately 25% (not 50%)
- QBER is ~0 with no noise and no Eve
- QBER increases with noise strength

### 5. CLI override
```bash
python -m qkd_sim configs/noise_sweep.yaml --n-trials 3 --show-plots
```
Should run with 3 trials instead of the YAML-specified 30, and display plots.

### 6. Protocol listing
```bash
python -m qkd_sim --list-protocols
```
Should print `bb84, b92`.

### 7. Scenario with protocol field
```bash
python -m qkd_sim configs/scenario.yaml
```
Should load the named scenario and run it with the correct protocol.

### 8. Import test
```python
from qkd_sim import QKDProtocol, QKDResult, BB84Protocol, B92Protocol
from qkd_sim import load_config, get_protocol, list_protocols
from qkd_sim import BenchmarkRunner, QKDPlotter, NoiseModelFactory
```
All imports should succeed without error.

---

## Non-Goals (explicitly out of scope)

- **E91 protocol implementation** - placeholder only; will be assessed at a later Go/No-Go gate
- **Multiprocessing / async execution** - unnecessary for dissertation scale
- **Database storage of results** - file export (CSV/JSON) is sufficient
- **Web dashboard** - terminal output + saved plots are the deliverables
- **Unit test suite** - desirable but not required for this refactor sprint; structure should support easy testing later
- **Distance-based photon loss modelling** - was in an older build but removed for scope; not reintroduced here

---

## Implementation Order

Execute these tasks in this order to maintain a working codebase at each step:

1. **Create `base.py`** with `QKDProtocol` ABC and `QKDResult` dataclass
2. **Create `registry.py`** with registration functions
3. **Create `protocols/` directory**, move `protocol.py` → `protocols/bb84.py`, make BB84 inherit from ABC
4. **Fix all imports** across the codebase to use relative imports and new paths
5. **Verify BB84 still works** identically via direct Python invocation
6. **Create `config.py`** with YAML loader and `SimConfig`
7. **Create `__main__.py`** with YAML-driven execution
8. **Create example YAML configs** in `configs/`
9. **Refactor `benchmark.py`** to accept `protocol_class` parameter
10. **Refactor `plotter.py`** - rename to `QKDPlotter`, move theory to protocols
11. **Refactor `eve.py`** - remove dead parameter
12. **Refactor `scenarios.py`** - add `protocol` field
13. **Update `__init__.py`** - fix PassiveEve, update exports
14. **Delete `run.py`**
15. **Implement `protocols/b92.py`**
16. **Verify all validation criteria pass**
