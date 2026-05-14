# PRD: Per-Protocol Security Bound Implementation

**Project:** QKD Simulation Platform (`qkd_sim`)
**Scope:** Replace the universal Shor-Preskill bound with protocol-appropriate security bounds for B92 and E91.
**Files affected:** `base.py`, `protocols/b92.py`, `protocols/e91.py`, `plotter.py`
**Files NOT affected:** `bb84.py`, `eve.py`, `noise.py`, `benchmark.py`, `config.py`, `STYLESHEET.py`

---

## 1. Background

The current implementation in `base.py` applies the Shor-Preskill secure key rate formula uniformly across BB84, B92, and E91:

```
secure_key_rate = key_rate * max(0, 1 - h(e) - f_ec * h(e))
```

This formula is correct for BB84 but is mathematically inappropriate for the other two protocols:

- **B92** has a strictly lower noise tolerance because it is exposed to unambiguous state discrimination attacks not captured by symmetric error rates.
- **E91**'s security argument is the violation of the CHSH inequality, not symmetric QBER. The current code computes `s_value` but does not use it in the security verdict.

Both shortcomings are documented in the methodology critique (`security threshold validation` review, prior conversation).

---

## 2. Goals

1. Each protocol's `is_secure` flag and theoretical secure key rate use a literature-justified bound for that protocol.
2. The codebase remains internally consistent: per-trial and theoretical overlay use the same formula for the same protocol.
3. Plot overlays show the correct security thresholds per protocol.
4. Changes are additive where possible; existing BB84 behaviour is preserved exactly.

---

## 3. Per-Protocol Security Bounds

### 3.1 BB84 (no change)

- **Bound:** Shor-Preskill / GLLP, `r = R_sift * max(0, 1 - (1+f_ec) * h(e))`
- **QBER threshold:** 9.81% with `f_ec = 1.16`; 11.00% with `f_ec = 1.00`
- **Citation:** Shor & Preskill, PRL 85, 441 (2000)
- **Status:** Already correctly implemented. Do not modify.

### 3.2 B92

- **Bound:** Shor-Preskill formula with a hard QBER cap.
- **Hard QBER cap:** **6.5%** — security verdict returns `False` and `secure_key_rate = 0` above this value, regardless of what the entropy formula gives.
- **Rationale:** Matsumoto's 2013 analysis gives B92 a maximum depolarising-rate tolerance of ~6.5%. We use this as a QBER cap for simplicity. This is more conservative than the entropy formula above ~6.5% QBER and prevents the simulator from claiming security in regions where no published B92 proof guarantees it.
- **Below the cap:** Use the same Shor-Preskill formula as a comparative metric. This is an approximation (no closed-form B92 rate exists), but it is commonly used in benchmarking studies.
- **Citations:**
  - Matsumoto, R., "Improved Asymptotic Key Rate of the B92 Protocol", arXiv:1301.5083 (2013) — for the 6.5% threshold
  - Tamaki, K., Koashi, M., & Imoto, N., PRL 90, 167904 (2003) — for the original unconditional security proof
  - Tamaki, K., & Lütkenhaus, N., PRA 69, 032316 (2004) — for the lossy-channel extension
- **Note:** The current `b92.py` docstring cites "Tamaki et al., PRA 68, 022311 (2003)". This should be corrected to the PRL 90 citation above for unconditional security.

### 3.3 E91

- **Bound:** Device-independent CHSH-based key rate (Acín et al. 2007).
- **Formula:**
  ```
  r_DI = R_sift * max(0, 1 - h(Q) - chi(S))

  where chi(S) = h( (1 + sqrt((S/2)^2 - 1)) / 2 ) for |S| >= 2
        chi(S) = 1                                  for |S| <  2
  ```
- **Security conditions (all must hold):**
  1. `|S| > 2` (Bell inequality violation present)
  2. `r_DI > 0` (positive key rate after Eve's information bound)
- **No single QBER threshold.** Security is a 2D condition over `(Q, |S|)`. At maximum violation `S = 2*sqrt(2)`, `chi = 0` and the formula reduces to the BB84 11% bound. At the classical bound `S = 2`, `chi = 1` and no security exists for any QBER.
- **f_ec is NOT used in the DI bound.** The Acín et al. formula does not include an error-correction inefficiency term in its standard form. Document this in the docstring.
- **Citations:**
  - Acín, A., Brunner, N., Gisin, N., Massar, S., Pironio, S., & Scarani, V., PRL 98, 230501 (2007)
  - Pironio, S., Acín, A., Brunner, N., Gisin, N., Massar, S., & Scarani, V., NJP 11, 045021 (2009)

---

## 4. Implementation Tasks

### Task 1 — `base.py`

**Make `secure_key_rate` and `theoretical_secure_key_rate` overridable.** The current implementations are concrete on `QKDResult` and `QKDProtocol`. Convert them to default implementations (Shor-Preskill) that subclasses can override, OR mark BB84 as the only one using the default.

Specifically:

- Keep `_binary_entropy` as a static method on `QKDResult` (used by all subclasses).
- Keep `secure_key_rate` as a property on `QKDResult` with the current Shor-Preskill body — this becomes the BB84 default.
- Keep `theoretical_secure_key_rate` as a classmethod on `QKDProtocol` with the current body — also the BB84 default.
- No structural change needed; subclasses override these as defined in tasks 2 and 3.

### Task 2 — `protocols/b92.py`

**2a. Add a module-level constant for the QBER cap:**

```python
B92_QBER_THRESHOLD = 0.065  # Matsumoto 2013, depolarising rate tolerance
```

**2b. Override `secure_key_rate` on `B92Result`:**

```python
@property
def secure_key_rate(self) -> float:
    """B92 secure key rate with Matsumoto QBER cap.

    Above the 6.5% QBER cap, no published B92 proof guarantees security,
    so the rate is forced to zero. Below the cap, the Shor-Preskill formula
    is used as a comparative-metric approximation. See Matsumoto 2013
    (arXiv:1301.5083) and Tamaki, Koashi, Imoto PRL 90, 167904 (2003).
    """
    if self.qber > B92_QBER_THRESHOLD:
        return 0.0
    return super().secure_key_rate  # falls through to Shor-Preskill
```

**2c. Override `theoretical_secure_key_rate` on `B92Protocol`:**

```python
@classmethod
def theoretical_secure_key_rate(cls, noise_type, strengths, f_ec=1.16):
    """B92 theoretical rate with QBER cap applied pointwise."""
    rate = super().theoretical_secure_key_rate(noise_type, strengths, f_ec)
    if rate is None:
        return None
    qber = cls.theoretical_qber(noise_type, strengths)
    if qber is None:
        return rate
    rate = np.where(qber > B92_QBER_THRESHOLD, 0.0, rate)
    return rate
```

**2d. Fix the citation in the module docstring:**

Replace `"Tamaki et al., PRA 68, 022311 (2003)"` with `"Tamaki, Koashi, Imoto, PRL 90, 167904 (2003); Matsumoto, arXiv:1301.5083 (2013)"`.

### Task 3 — `protocols/e91.py`

**3a. Add a module-level constant:**

```python
_CHSH_CLASSICAL_BOUND = 2.0  # already exists as _CLASSICAL_BOUND, reuse
```

**3b. Add a static helper for the chi function:**

```python
@staticmethod
def _chi_chsh(s: float) -> float:
    """Eve's information bound for CHSH-based DIQKD (Acin et al. 2007).

    chi(S) = h( (1 + sqrt((S/2)^2 - 1)) / 2 )  for |S| >= 2
    chi(S) = 1                                    for |S| <  2 (no violation)
    """
    s = abs(s)
    if s < _CLASSICAL_BOUND:
        return 1.0
    inner = (1.0 + np.sqrt((s / 2.0) ** 2 - 1.0)) / 2.0
    return QKDResult._binary_entropy(inner)
```

**3c. Override `secure_key_rate` on `E91Result`:**

```python
@property
def secure_key_rate(self) -> float:
    """E91 device-independent secure key rate (Acin et al. 2007).

    r = R_sift * max(0, 1 - h(Q) - chi(S))

    Note: f_ec is not applied in the standard DIQKD formulation.
    Returns 0 if no Bell violation (|S| <= 2).
    """
    if self.sifted_length == 0:
        return 0.0
    if self.abs_s <= _CLASSICAL_BOUND:
        return 0.0
    h_q = self._binary_entropy(self.qber)
    chi = E91Protocol._chi_chsh(self.s_value)
    secret_fraction = max(0.0, 1.0 - h_q - chi)
    return self.key_rate * secret_fraction
```

**3d. Update `is_secure` if needed.** The base `is_secure` returns `secure_key_rate > 0` which now correctly requires both `|S| > 2` and `r_DI > 0`. No code change needed, but document the joint condition in a docstring on `E91Result`.

**3e. Override `theoretical_secure_key_rate` on `E91Protocol`:**

```python
@classmethod
def theoretical_secure_key_rate(cls, noise_type, strengths, f_ec=1.16,
                                channel_topology='both'):
    """E91 theoretical DIQKD secure key rate using CHSH bound."""
    qber = cls.theoretical_qber(noise_type, strengths, channel_topology)
    s = cls.theoretical_chsh(noise_type, strengths, channel_topology)
    if qber is None or s is None:
        return None

    sifting = cls.theoretical_sifting_rate()

    def _h(x):
        x = np.clip(x, 1e-15, 1.0 - 1e-15)
        return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

    # chi function vectorised
    s_abs = np.abs(s)
    inner = (1.0 + np.sqrt(np.clip((s_abs / 2.0) ** 2 - 1.0, 0.0, None))) / 2.0
    inner = np.clip(inner, 1e-15, 1.0 - 1e-15)
    chi = np.where(s_abs < _CLASSICAL_BOUND, 1.0, _h(inner))

    secret = np.maximum(0.0, 1.0 - _h(qber) - chi)
    return sifting * secret
```

### Task 4 — `plotter.py`

**4a. Update security threshold annotations on QBER plots.** The current plotter draws a horizontal line at the BB84 QBER threshold. For B92 and E91 plots, draw the protocol-specific threshold instead.

- BB84 plots: keep the existing threshold (9.81% or 11%).
- B92 plots: draw threshold at **6.5%**, label as "B92 security threshold (Matsumoto 2013)".
- E91 plots: do **not** draw a single horizontal QBER line. Instead, ensure the secure-key-rate plot uses the new DI bound and the CHSH plot retains the `|S| = 2` classical bound line.

**4b. For the protocol comparison plot:** allow each protocol's threshold to be drawn independently on the QBER plot. This may require adding a per-protocol threshold lookup method, e.g.:

```python
def _qber_threshold_for_protocol(name: str, f_ec: float) -> Optional[float]:
    if name == 'BB84':
        # solve 1 - (1 + f_ec) * h(e) = 0 numerically or analytically
        ...
    elif name == 'B92':
        return 0.065
    elif name == 'E91':
        return None  # 2D condition, no single horizontal line
```

### Task 5 — Tests / Validation

Add or update unit tests verifying:

1. **BB84 unchanged:** `BB84Protocol(...).run().secure_key_rate` matches its old value at e.g. QBER = 0.05, f_ec = 1.16.
2. **B92 cap engages:** A `B92Result` constructed with `qber = 0.07` returns `secure_key_rate = 0.0`. A `B92Result` with `qber = 0.05` returns the Shor-Preskill value.
3. **E91 requires Bell violation:** An `E91Result` with `qber = 0.05, s_value = 1.5` returns `secure_key_rate = 0.0`. With `qber = 0.05, s_value = 2.7` returns a positive value.
4. **E91 chi function:** `_chi_chsh(2.0) ~= 1.0`; `_chi_chsh(2 * sqrt(2)) ~= 0.0`; monotonically decreasing in between.
5. **E91 theoretical curve:** `theoretical_secure_key_rate('depolarizing', strengths)` returns zero at strengths where `theoretical_chsh < 2`.

### Task 6 — Documentation

Update the module-level docstrings of `base.py`, `b92.py`, and `e91.py` to reflect that each protocol now uses its own security bound. Include the citation list from Section 3 of this PRD.

---

## 5. Acceptance Criteria

- [ ] `BB84Protocol` results are bit-for-bit identical before and after the change at fixed seed.
- [ ] `B92Result.secure_key_rate` returns 0 for any QBER strictly above 0.065.
- [ ] `E91Result.secure_key_rate` returns 0 whenever `|s_value| <= 2.0`.
- [ ] `E91Result.secure_key_rate` matches `R_sift * max(0, 1 - h(Q) - chi(S))` for valid inputs, within floating-point tolerance.
- [ ] All existing scenarios in `scenarios.py` still run without crashing. `E91_VIOLATION_LOST` now correctly reports `is_secure = False`.
- [ ] Plot outputs render protocol-specific thresholds where applicable.
- [ ] All new unit tests pass.
- [ ] Module docstrings include the updated citations.

---

## 6. Out of Scope

- Implementing Matsumoto's full convex-optimisation B92 rate (kept as future work).
- Implementing the asymmetric-CHSH improvement (Woodhead, Acín, Pironio 2020) for E91.
- Implementing finite-key corrections (Tomamichel et al. 2012). All bounds remain asymptotic.
- Implementing an Eve model for E91. The current `NotImplementedError` should remain.

---

## 7. Risk and Rollback

The B92 and E91 changes will reduce the secure-key-rate curves on existing plots. This is the intended behaviour and reflects a more accurate security analysis. If existing report figures need to be regenerated, this should be done as a separate task after these changes land.

Rollback path: revert the overrides on `B92Result.secure_key_rate`, `B92Protocol.theoretical_secure_key_rate`, `E91Result.secure_key_rate`, and `E91Protocol.theoretical_secure_key_rate`. The base-class implementations remain intact, so reverting restores the previous behaviour exactly.
