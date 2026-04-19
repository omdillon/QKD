# Red Flags — Viva Defence Audit

This document catalogues the points in the QKD simulator where a sharp examiner
is most likely to press you during a system demonstration or viva. Each entry
describes the issue, why it matters, and what you need to be ready to say.

Nothing here is a "the system is wrong and the results are garbage" finding —
the protocol physics is implemented correctly end-to-end. These are modelling
choices, simplifications, and fragilities that an examiner can legitimately
challenge, and where "I didn't think about that" is the wrong answer.

Entries are ordered by how hard they will be to defend, not by how subtle they
are to spot.

---

## 1. Eve's Alice→Eve channel is noiseless — physics inconsistency

**Location:** [qkd_sim/eve.py:20](../qkd_sim/eve.py#L20), [qkd_sim/eve.py:48](../qkd_sim/eve.py#L48)

`EveInterceptor.__init__` instantiates `self._eve_backend = AerSimulator()` with
**no noise model**. Eve's measurement circuit is `qc.copy()` of Alice's prepared
circuit — which already contains the `id(0)` channel marker — and is executed on
this noiseless backend. Eve then builds a fresh replacement circuit (also with
an `id(0)` marker) which Bob executes on the *noisy* backend.

Net effect: when a noise sweep is run *with* Eve, the Alice→Eve leg is perfectly
clean, and only the Eve→Bob leg suffers channel noise. This is not physical.
Eve sits somewhere *in* the fibre; both halves of the journey should see a
comparable fraction of the noise.

**Why it matters:**
- QBER under "noise + Eve" is biased low compared to what a realistic
  eavesdropper would produce, because Eve's measurements are cleaner than they
  should be.
- The `plot_qber_noisy_eve` figure in particular reports a metric derived from
  this inconsistent noise distribution.

**What the examiner will ask:** "Where does Eve physically sit in your channel
model, and why does she enjoy a noise-free receive leg?"

**Defensible answers:**
- "Eve is modelled at Alice's output, so the full channel noise is attributed
  to the Eve→Bob leg. This over-credits Eve's ability to measure cleanly but
  accurately represents the noise Bob sees." — Honest and defensible.
- "A more realistic split would attach half the noise strength to Alice→Eve
  and half to Eve→Bob. This was out of scope for this report." — Also fine.

**What not to say:** "The channel is only one `id` gate, so it can only be on
one side." That ducks the question.

---

## 2. Three incompatible secure-key-rate definitions compared on the same axis

**Location:**
- BB84: [qkd_sim/base.py:49-56](../qkd_sim/base.py#L49-L56) (Shor–Preskill)
- B92: [qkd_sim/protocols/b92.py:33-44](../qkd_sim/protocols/b92.py#L33-L44) (Shor–Preskill + 6.5% hard cap)
- E91: [qkd_sim/protocols/e91.py:74-90](../qkd_sim/protocols/e91.py#L74-L90) (Acín et al. DIQKD bound, no f_ec)

Every `plot_protocol_comparison` figure puts the three protocols' secure key
rates on the same y-axis. But:

- BB84 uses a **trusted-device** Shor–Preskill bound with `f_ec`.
- B92 uses the **same trusted-device formula as BB84**, hard-capped at 6.5%
  QBER — this is an acknowledged approximation (Matsumoto 2013 proves security
  below the cap, but *not* that the Shor–Preskill expression is tight for B92).
- E91 uses a **device-independent** bound with **no `f_ec`**, because DIQKD
  proofs don't canonically include reconciliation inefficiency.

These are three different security notions operating under three different
threat models. The comparison is directionally informative but not a
like-for-like race.

**Why it matters:** If the figure is headlined "secure key rate comparison",
an examiner can argue the axes aren't commensurable.

**What the examiner will ask:**
- "Is E91's device-independent rate comparable to BB84's device-dependent rate?"
- "Why does E91 not include the error-correction penalty that the other two do?"
- "The B92 formula is a BB84 formula — on what grounds does it apply to B92?"

**Defensible answers:**
- Acknowledge all three are **upper bounds** on achievable secret key rate
  under their respective threat models.
- State clearly that the B92 Shor–Preskill expression is used as a
  **comparative metric** and not as a tight security proof. (Your docstring
  already says this. Make sure it's in the report.)
- Either (a) omit `f_ec` from all three for fairness, or (b) include it in E91
  and document that you've added a practical reconciliation penalty on top of
  the DI bound. Pick one and be explicit.

---

## 3. B92's 6.5% QBER threshold is used across all noise types, but the
   Matsumoto proof is for depolarising channels

**Location:** [qkd_sim/protocols/b92.py:22-24](../qkd_sim/protocols/b92.py#L22-L24)

`B92_QBER_THRESHOLD = 0.065` is cited from Matsumoto 2013, who analyses B92
under a depolarising channel. Your code applies this threshold uniformly for
bitflip, phaseflip, and depolarising noise sweeps. Different noise types in
principle allow different B92 tolerances.

**Why it matters:** An examiner familiar with the literature will know the
proof is channel-specific.

**What to say:** "The 6.5% figure is the most stringent published QBER cap for
B92 under any commonly-analysed single-qubit channel. Applying it to all noise
types is conservative — it may underreport the achievable key rate under
bitflip/phaseflip but never falsely claims security." That's actually true.

---

## 4. E91 has no Eve model — explicit `NotImplementedError`

**Location:** [qkd_sim/protocols/e91.py:199-201](../qkd_sim/protocols/e91.py#L199-L201)

`E91Protocol.run()` raises `NotImplementedError` if an `EveInterceptor` is
passed in. This means your eavesdropping analysis is exclusively about BB84
and B92, not the full three-way comparison your report may imply.

**Why it matters:** The narrative around protocol comparison *under attack* is
incomplete. If your report argues that E91's CHSH monitoring gives it a
security advantage, the simulator contains no direct demonstration of this.

**What the examiner will ask:** "Your comparison tables include all three
protocols, but your eavesdropping results only cover two. How do you justify
security claims about E91 empirically?"

**Defensible answers:**
- "E91 security is demonstrated via the CHSH inequality: |S| dropping below 2
  under noise is the operational signature that would also occur under
  tampering. This is shown in the CHSH-vs-noise figure."
- "Intercept-resend on E91 requires a different attack model (e.g., Eve
  intercepts one arm of the EPR pair, measures, and forwards a product state).
  This was scoped out."

---

## 5. Intercept-resend is the only Eve model

**Location:** [qkd_sim/eve.py](../qkd_sim/eve.py)

Intercept-resend is the pedagogical attack — it's the one you can explain in a
paragraph and demonstrate in a figure. Real QKD security proofs defend against
**coherent attacks**, where Eve performs joint measurements on many qubits
together with her ancilla. BB84's unconditional security proofs
(Shor–Preskill, Mayers, Lo–Chau) all address coherent attacks.

**Why it matters:** Your QBER-under-Eve plots demonstrate *detectability of
intercept-resend*, not *unconditional security*. The two are not the same.

**What the examiner will ask:** "What class of attacks does your simulator
defend against? Does a 25% QBER at full interception demonstrate security, or
just the detection of one specific attack?"

**Defensible answer:** "Intercept-resend is the canonical individual attack
used for pedagogical QBER analysis. The published security proofs for BB84 and
B92 cover coherent attacks and are cited but not re-demonstrated — our secure
key rate formulas assume those proofs hold, and the simulator empirically
validates QBER behaviour under the simplest attack."

---

## 6. Fractional Eve interception rate is a didactic artefact

**Location:** [qkd_sim/eve.py:18](../qkd_sim/eve.py#L18), used throughout Eve sweeps

The `interception_rate` parameter lets Eve intercept some random subset of
qubits. In reality an eavesdropper either is or isn't on the channel — she
doesn't dice-roll per photon. Partial interception is a purely didactic tool
for producing a smooth "QBER rises as Eve's activity rises" curve.

**Why it matters:** It's not a realistic attack. An examiner may ask what
operational scenario it corresponds to.

**Defensible answer:** "The interception rate parameterises the *expected
fraction* of qubits Eve can access; it's used here as a didactic interpolation
between the no-Eve and full-Eve extremes, not as a literal attack." Fine.

---

## 7. QBER is estimated using the full sifted key, not a sacrificed subset

**Location:** [qkd_sim/protocols/bb84.py:115-118](../qkd_sim/protocols/bb84.py#L115-L118)
(and analogous code in B92, E91)

In a real QKD protocol, Alice and Bob publicly compare a **subset** of their
sifted key to estimate QBER, and discard those bits. The remaining sifted bits
become the raw key. Your simulator computes QBER over **all** sifted bits and
then reports "secure key rate" as if the same bits are still key material.

**Why it matters:** Strictly speaking, the simulated "secure key rate" double-
counts: bits used to estimate error cannot also be used as key. In a real
protocol this costs you a fraction of the sifted key (typically ~5-10%).

**What the examiner will ask:** "Where is the parameter-estimation subset
accounted for in your rate computation?"

**Defensible answer:** "Parameter estimation overhead is not modelled; the
reported rate is an upper bound on what a real implementation would achieve
after subtracting the estimation sample. For the n_qubits regime used (up to
1000), this overhead is within the Monte-Carlo variance of the reported
values."

---

## 8. Theoretical overlays use noise-free sifting rate

**Location:** [qkd_sim/base.py:93-106](../qkd_sim/base.py#L93-L106), used by B92 override

`theoretical_secure_key_rate` multiplies by `cls.theoretical_sifting_rate()`,
which returns the **noise-free** sifting ratio (0.5 for BB84, 0.25 for B92,
2/9 for E91). Under noise, the actual sifting rate drifts:

- **B92 under depolarising p:** true conclusive rate is `(1+p)/4`, not `1/4`.
  Under noise the simulator sifts more bits than theory predicts, so the
  simulated secure key rate will sit **above** the theoretical curve at
  non-trivial `p`. The overlay undersells B92.
- **BB84 under most Pauli channels:** sifting rate is unchanged at 0.5. Safe.
- **E91:** sifting rate 2/9 is determined purely by angle-pair statistics, not
  by channel noise. Safe.

**Why it matters:** Your B92 theoretical overlay will visibly disagree with
the simulated curve at moderate noise, and a sharp eye will notice.

**Defensible answer:** "The theoretical curve uses the noise-free sifting rate
as a baseline; the simulated curve captures the noise-induced increase in
conclusive events, which is why they diverge." Explain it before they ask.

---

## 9. Noise is attached to `id` gates — a fragile Qiskit idiom

**Location:** [qkd_sim/noise.py:36](../qkd_sim/noise.py#L36), marker in every protocol

Aer's `NoiseModel.add_all_qubit_quantum_error(error, ['id'])` attaches the
quantum error to `id` instructions. This works under current Qiskit/Aer
versions because Aer's noise attachment runs *after* transpilation and *does
not* eliminate identity gates when a noise model references them. But:

- Any future transpiler pass that folds identity gates away before the noise
  model is applied would silently switch off your noise.
- If someone runs your circuits through `transpile(..., optimization_level=3)`
  before handing them to the backend, Qiskit will remove identity gates and
  your noise sweeps will suddenly return QBER ≈ 0.

You said the gate name isn't your concern — what matters is "where the noise
is applied". Fair. But for the viva: the answer to "where is the noise
applied?" is "to the `id` gate, which is Aer-protected from transpilation
because it's listed in the noise model". Say that precisely. Don't say "it's
applied to the channel" without explaining the mechanism, because the examiner
will push.

**What to verify before the demo:** run a bitflip sweep at p=0.5. Expected
BB84 QBER ≈ 0.25 (0.5 × 0.5 averaging over matched Z/X bases). If you see
that, the noise is live. If you see QBER = 0, the noise was elided.

---

## 10. No channel loss, no photon-number statistics, no dark counts

**Location:** entire system

Real optical QKD is dominated by **channel loss** (key rate ~ transmittance,
which is exponential in fibre length), not by Pauli noise. Your simulator
models "every qubit sent is received by Bob", with some probability of error
due to the channel. There is no:

- Photon loss / detection inefficiency
- Decoy-state analysis (for BB84 with weak coherent pulses)
- Dark counts
- Basis-dependent detector efficiency
- Distance parameter

**Why it matters:** Key-rate numbers from this simulator are **per sent
qubit**, not **per sent pulse in an optical channel**. An experimental-physics
examiner will absolutely ask about this.

**Defensible answer:** "The simulator models the logical-channel layer: noise
on an idealised single-photon qubit. Photon-level effects (loss, dark counts,
multi-photon components) are abstracted out. This is the standard abstraction
level for protocol comparison papers; decoy-state and detection-efficiency
analyses are orthogonal and would apply uniformly across all three protocols."

Have this answer ready. It's the most likely probing question in an
engineering-leaning viva.

---

## 11. Qiskit depolarising channel convention

**Location:** [qkd_sim/noise.py:43](../qkd_sim/noise.py#L43)

`depolarizing_error(p, 1)` in Qiskit has a specific convention: the **output**
at `p=1` is the fully depolarised state `I/2`. Equivalent to
`E(ρ) = (1 − p)ρ + p · I/2`. Some textbooks define depolarising probability
with a `3p/4` or `p/3` convention.

**Why it matters:** Your analytical BB84 QBER `p/2` and B92 QBER `p/(1+p)` are
*derived under Qiskit's convention*. If an examiner reads your report with a
different textbook convention in mind, the formulas will look wrong by a
factor.

**What to say:** State the convention explicitly in the methodology section of
the report. One sentence: "`p` denotes Qiskit's depolarising parameter, where
`p=1` produces the fully depolarised state."

---

## 12. No RNG seeding; trials are not reproducible

**Location:** every protocol's `_prepare` / `_measure` uses `np.random.*`
without a seed.

Monte Carlo results are only statistically reproducible (via error bars), not
bit-for-bit reproducible. That's a standard choice for statistical
simulations, but an examiner may ask.

**What to say:** "Trials are independent draws; reproducibility is statistical
and shown by standard-deviation bands in the plots. A fixed seed can be added
for exact reproduction." Fine.

---

## 13. Eve uses a BB84-flavoured attack against B92

**Location:** [qkd_sim/eve.py:38-44](../qkd_sim/eve.py#L38-L44)

`EveInterceptor` picks a basis from `{Z, X}` uniformly at random. That is
correct for BB84. For B92, the optimal intercept-resend attack isn't a
coin-flip between Z and X — it's the minimum-error-discrimination POVM
between `|0⟩` and `|+⟩`, which is a different measurement entirely. Using the
BB84 Eve against B92 gives Eve a *weaker* attack than optimal, which means
your QBER-under-Eve curve for B92 **understates** Eve's detectability (because
a weaker attack introduces more detectable error? No — because a suboptimal
attack may introduce either more or less QBER depending on the specifics).

**Why it matters:** Your B92 eavesdropping numbers don't correspond to the
best-known classical attack on B92.

**What the examiner will ask:** "Is this the optimal intercept-resend strategy
for B92?"

**Defensible answer:** "The simulator uses a generic Z/X basis intercept-
resend, which is the canonical attack for BB84. Applied to B92 it's not
optimal — the optimal unambiguous-state-discrimination attack would produce
different QBER and a different detection profile. Implementing a B92-specific
Eve was out of scope."

---

## 14. The `n_qubits` reported throughout is "rounds of the protocol", not
    "physical photons sent"

This is obvious to you but easy for an examiner to miss in your favour and
then hold against you later. Under any photon-level model, `n_qubits` and
"photons sent" differ by a factor of many orders of magnitude (weak coherent
pulses, detector efficiencies, etc.).

**What to say:** Make sure the report glossary defines `n_qubits` as "number
of protocol rounds at the logical-qubit level", not "photons transmitted". One
sentence of hygiene.

---

## 15. E91 secure-rate formula applies only when |S| > 2

**Location:** [qkd_sim/protocols/e91.py:82-90](../qkd_sim/protocols/e91.py#L82-L90)

`secure_key_rate` returns 0 when `|S| ≤ 2`. Correct per Acín 2007. But the
finite-statistics issue is that at small `n_qubits`, the empirical `|S|` has
non-trivial variance around the true value — you may see `|S| < 2` on
individual trials even when the underlying state would give `|S| = 2√2`.

**Why it matters:** Low-`n_qubits` E91 runs will randomly report
`secure_key_rate = 0` on trials where the CHSH estimate fluctuates below 2,
even though nothing adversarial happened.

**What the examiner will ask:** "How do you distinguish a finite-statistics
CHSH fluctuation from a real security failure?"

**Defensible answer:** "This is a finite-sample effect; `|S|` has standard
error roughly `2/√N_CHSH`. In the asymptotic limit the rate is well-defined;
for practical `n_qubits` we report mean and standard deviation across trials."
Acceptable.

---

## 16. `f_ec = 1.16` is an uncited magic number in the config

**Location:** [qkd_sim/config.py:23](../qkd_sim/config.py#L23), [qkd_sim/base.py:32](../qkd_sim/base.py#L32)

1.16 is a widely-cited reconciliation-inefficiency figure corresponding to
~16% overhead above the Shannon limit for realistic LDPC-based error
correction. But it appears in the code as a magic number.

**What to say in the report:** "`f_ec = 1.16` corresponds to practical
error-correcting codes operating within ~16% of the Shannon limit, e.g.
LDPC-based post-processing as reported in [cite]." One sentence, one citation.

---

## Summary — what to prepare before the demo

The three questions most likely to catch you are:

1. **"Where does Eve sit in your noise model?"** — You need a clean answer.
   The current implementation is inconsistent; either fix it (split noise) or
   own the simplification explicitly.
2. **"Are these three secure key rates really comparable?"** — They are not,
   strictly. Have your "different threat models, upper bounds, comparative
   metric" speech ready.
3. **"Where is the physical channel?"** — There is none; you model a logical
   channel with lumped noise. Say so, and cite that this is the standard
   protocol-comparison abstraction.

Everything else in this document is defensible with a one-sentence answer as
long as you've thought about it in advance. Don't get caught flat-footed.
