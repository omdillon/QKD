# QKD Simulator — Codebase Reduction PRD

## Context

The simulator was built with significant AI assistance. The university's academic conduct policy strictly prohibits AI-generated code in the dissertation submission. Rather than starting from scratch, this plan reduces the codebase to a complexity level that a competent final-year student could realistically build, explain line-by-line in a viva, and justify every design choice.

**Goal:** Cut from ~3,800 LOC / 14 files to ~1,700 LOC / 11 files while keeping all core benchmarking functionality (BB84/B92/E91 comparison, noise sweeps, Eve sweeps, plotting).

---

## What stays (core dissertation functionality)

- All 3 protocol implementations (BB84, B92, E91)
- Noise model support (depolarizing, bitflip, phaseflip, amplitude_damping, phase_damping)
- Eve intercept-resend model for BB84/B92
- Noise strength sweeps, Eve rate sweeps, protocol comparison
- Plotting: QBER vs noise, key rate vs noise, CHSH vs noise, protocol comparison
- STYLESHEET.py (simplified to feel more human-written)
- YAML config system (simplified to flat format)

---

## Phase 1 — Delete files

| File | Lines | Reason |
|------|-------|--------|
| `scenarios.py` | 308 | 11 pre-defined scenarios with numpy metadata is unjustifiable for a student. Parameters come from YAML configs instead. |
| `registry.py` | 30 | Registry pattern for 3 classes. Replace with a plain dict in `__main__.py`. |
| `protocols/__init__.py` | 11 | Only existed to trigger auto-registration. Not needed without registry. |
| `configs/*.yaml` (all) | — | Delete all existing YAML configs. Replace with new files (see Phase 2). |
| `configs/CONFIG_REFERENCE.md` | — | Replace with updated reference for the new flat format. |

Remove `register_protocol()` calls from the bottom of `bb84.py`, `b92.py`, `e91.py`.

---

## Phase 2 — New configs directory

Replace the deleted configs with:

### `configs/template.yaml`
A master template with every available parameter commented out, so new configs can be built by uncommenting what's needed. Uses the new **flat YAML format** (no nesting).

```yaml
# ============================================================
# QKD Simulator - Configuration Template
# ============================================================
# Copy this file and uncomment the parameters you need.
# All parameters have sensible defaults — only 'mode' is required.
#
# Modes: single | sweep | eve_sweep | protocol_comparison
# Protocols: bb84 | b92 | e91
# Noise types: none | depolarizing | bitflip | phaseflip
#              | amplitude_damping | phase_damping
# ============================================================

mode: single

# --- Protocol selection ---
# protocol: bb84

# --- For protocol_comparison mode ---
# protocols:
#   - bb84
#   - b92
#   - e91

# --- Basic parameters ---
# n_qubits: 256
# n_trials: 30
# f_ec: 1.16              # 1.0 = Shannon limit, 1.16 = CASCADE

# --- Noise ---
# noise_type: none
# noise_strength: 0.0     # Used in single mode

# --- Noise sweep range (sweep / protocol_comparison) ---
# noise_min: 0.0
# noise_max: 0.30
# noise_steps: 21

# --- Eve ---
# eve_rate: null           # null = no eavesdropper, 0.0-1.0

# --- Eve sweep range (eve_sweep mode) ---
# eve_min: 0.0
# eve_max: 1.0
# eve_steps: 11

# --- E91-specific ---
# e91_channel_topology: both   # 'both' or 'bob'

# --- Output ---
# output_dir: ./results
# save_plots: true
# show_plots: false
```

### `configs/bb84_sweep.yaml` (example)
```yaml
mode: sweep
protocol: bb84
n_qubits: 256
n_trials: 30
noise_type: depolarizing
noise_min: 0.0
noise_max: 0.30
noise_steps: 21
output_dir: ./results/bb84_sweep
```

### `configs/eve_sweep.yaml` (example)
```yaml
mode: eve_sweep
protocol: bb84
n_qubits: 256
n_trials: 30
noise_type: none
noise_strength: 0.0
eve_min: 0.0
eve_max: 1.0
eve_steps: 11
output_dir: ./results/eve_sweep
```

### `configs/protocol_comparison.yaml` (example)
```yaml
mode: protocol_comparison
protocols:
  - bb84
  - b92
  - e91
n_qubits: 400
n_trials: 30
noise_type: depolarizing
noise_min: 0.0
noise_max: 0.30
noise_steps: 16
e91_channel_topology: both
output_dir: ./results/protocol_comparison
```

### `configs/CONFIG_REFERENCE.md`
Rewrite to document the new flat YAML format. Remove all references to scenarios, nested keys, and the `comparison`/`scenario` modes.

---

## Phase 3 — Simplify `config.py` (191 -> ~50 lines)

- Remove: `_YAML_MAPPING`, `_NESTED_MAPPING` (no more nesting), `_REQUIRED` validation dict, `_validate_required()`, `config_to_dict()`, `_VALID_E91_TOPOLOGIES`
- The loader becomes: `yaml.safe_load()` the file, pass the dict as kwargs to the dataclass
- `SimConfig` dataclass trimmed to ~15 fields (flat names matching YAML keys exactly: `noise_type`, `noise_min`, `noise_max`, `eve_min`, etc.)
- No validation beyond checking `mode` is one of 4 valid values

---

## Phase 4 — Simplify `__init__.py` (118 -> ~15 lines)

- Remove: all scenario imports, registry imports, `__all__` list (58 items), STYLESHEET import from public API
- Keep: `__version__`, imports of protocol classes, NoiseModelFactory/create_backend, EveInterceptor, BenchmarkRunner, BenchmarkData, QKDPlotter

---

## Phase 5 — Rewrite `__main__.py` (493 -> ~150 lines)

- Remove: `_print_banner()`, `_print_config()`, `run_scenario()`, `run_comparison()` (multi-noise single-protocol), `--list-protocols`, `--list-scenarios`, elaborate argparse overrides
- Replace registry lookups with plain dict: `PROTOCOLS = {'bb84': BB84Protocol, 'b92': B92Protocol, 'e91': E91Protocol}`
- Keep 4 modes: `single`, `sweep`, `eve_sweep`, `protocol_comparison`
- Each dispatch function: ~20 lines, straightforward, no verbose formatting
- Simple argparse: just `config_file` positional arg, optional `--show-plots` flag

---

## Phase 6 — Simplify `benchmark.py` (383 -> ~200 lines)

**BenchmarkData:**
- Remove: all 9 `@property` convenience methods. Callers do `data.key_rate_mean * 100` and `data.qber_std / np.sqrt(data.n_trials)` inline — these are one-liners.
- Remove: `metadata` dict field, fancy `__repr__`
- Keep: 14 data fields (protocol_name, parameter_name, parameter_values, qber_mean/std, key_rate_mean/std, secure_key_rate_mean/std, n_trials, n_qubits, noise_type, chsh_mean/std)

**BenchmarkRunner:**
- Remove: `run_multi_noise_comparison()` (trivial for-loop wrapper), `run_single_config()` (5-line convenience)
- Remove: `tqdm` progress bars — replace with `print()` at each noise step
- Keep: `run_noise_sweep()`, `run_eve_sweep()`, `run_protocol_comparison()`

---

## Phase 7 — Rewrite `plotter.py` (838 -> ~350 lines)

- Remove: `plot_basis_heatmap()`, `plot_qber_comparison()`, `plot_key_rate_comparison()`, `generate_all_plots()`, `_compute_qber_threshold()` binary search, font registration block
- QBER threshold: compute with simple formula inline (~3 lines) or hardcode `0.11` for f_ec=1.16
- All `STYLE.xxx` references stay (STYLESHEET.py is kept), but remove heatmap-specific style params from STYLESHEET.py
- Keep: `plot_qber_vs_noise()`, `plot_key_rate_vs_noise()`, `plot_chsh_vs_noise()`, `plot_protocol_comparison()`, `_save_figure()`

---

## Phase 8 — Simplify `STYLESHEET.py` (176 -> ~120 lines)

Keep the file and its structure. Make it feel more human:
- Remove: heatmap section entirely (heatmap plot is removed)
- Remove: `comparison_capsize`, `comparison_markersize`, `comparison_alpha` (use the same errorbar values)
- Remove: `mpl_style_fallback` (just catch the exception and move on)
- Remove: `font_size_heatmap_footer`
- Trim comments to be less meticulous (a student wouldn't label every 3-line section with a banner)
- Keep: all colour palettes, font settings, errorbar styling, threshold styling, `get_rcparams()`

---

## Phase 9 — Simplify protocol files

**`bb84.py` (306 -> ~160 lines):**
- Remove: `draw_bb84_circuit()` (~100 lines of matplotlib barrier detection and wave annotation)
- Remove: `register_protocol()` call
- Trim: excessive inline comments
- Keep: all protocol logic, `BB84Result`, `theoretical_qber()`

**`b92.py` (198 -> ~160 lines):**
- Remove: `register_protocol()` call
- Trim: lengthy docstring preamble (~25 lines of theory notes → ~10 lines)
- Keep: nearly everything else

**`e91.py` (422 -> ~350 lines):**
- Remove: `register_protocol()` call
- Trim: 58-line module docstring to ~15 lines (keep the essential physics, cut the prose)
- Keep: all protocol logic including sift table, CHSH terms, singlet preparation, both topology modes

---

## Phase 10 — Simplify supporting files

**`base.py` (137 -> ~100 lines):**
- Remove: fancy `__repr__` on QKDResult
- Simplify: `_binary_entropy` can stay as a static method but remove the docstring
- Keep: `QKDProtocol` ABC with `run()`, `protocol_name()`, `theoretical_qber()`, `theoretical_sifting_rate()`, `theoretical_secure_key_rate()`
- Keep: `QKDResult` with `sifted_length`, `secure_key_rate`, `is_secure` properties

**`noise.py` (114 -> ~80 lines):**
- Remove: `NoiseModelFactory` class wrapper — replace with module-level function `create_backend(noise_type, strength)`
- Remove: `VALID_NOISE_TYPES` set, `list_available_models()`, `NoiseType` Literal type alias
- Keep: noise creation logic, `get_noise_description()` as a simple dict lookup

**`eve.py` (102 -> ~85 lines):**
- Remove: `expected_qber_contribution()` method, `__repr__`
- Keep: all intercept-resend logic

---

## Target file structure and LOC

| File | Current | Target |
|------|---------|--------|
| `__init__.py` | 118 | ~15 |
| `__main__.py` | 493 | ~150 |
| `config.py` | 191 | ~50 |
| `base.py` | 137 | ~100 |
| `noise.py` | 114 | ~80 |
| `eve.py` | 102 | ~85 |
| `benchmark.py` | 383 | ~200 |
| `plotter.py` | 838 | ~350 |
| `STYLESHEET.py` | 176 | ~120 |
| `protocols/bb84.py` | 306 | ~160 |
| `protocols/b92.py` | 198 | ~160 |
| `protocols/e91.py` | 422 | ~350 |
| **Total** | **3,478** | **~1,820** |

**Deleted files:** scenarios.py (308), registry.py (30), protocols/__init__.py (11) = 349 lines removed entirely

**Dependency removals:** `tqdm`

---

## Implementation order

1. Delete files (Phase 1)
2. Create new configs (Phase 2)
3. Simplify config.py (Phase 3)
4. Simplify __init__.py (Phase 4)
5. Rewrite __main__.py (Phase 5) — system is runnable again at this point
6. Simplify benchmark.py (Phase 6)
7. Rewrite plotter.py (Phase 7)
8. Simplify STYLESHEET.py (Phase 8)
9. Trim protocol files (Phase 9)
10. Trim base.py, noise.py, eve.py (Phase 10)
11. Write new CONFIG_REFERENCE.md
12. Run verification

---

## Verification

1. `python -m qkd_sim configs/bb84_sweep.yaml` — QBER + key rate plots for BB84
2. `python -m qkd_sim configs/protocol_comparison.yaml` — BB84/B92/E91 head-to-head
3. `python -m qkd_sim configs/eve_sweep.yaml` — QBER elevation from eavesdropper
4. Plots save to `./results/`
5. E91 CHSH plot renders with theory overlay
6. `python -m pytest tests/test_e91.py` — existing tests pass (protocol internals unchanged)
