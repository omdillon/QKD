# QKD Demo Slide Deck — Design Brief
**Project:** EEE3094 Capstone Demo — Om Kalyan, Newcastle University
**Narrative goal:** Tell the story of a 5-month development journey from theory to a working benchmarking framework — not a report, a story with a beginning (the problem), middle (the build), and end (the findings).
**Slide count:** 18 (down from 20)
**Duration:** 10 minutes

---

## Global Design Spec

**Palette:** Light / white primary
- Slide background: `FFFFFF` (white) — all slides including title and close
- Primary colour (titles, headers, key shapes): `1E2761` (navy)
- Card / panel backgrounds: `F4F6FA` (very light blue-grey — lifts cards off white without feeling dark)
- Accent (highlights, key numbers, callout borders, section labels): `F5A623` (amber)
- Body text: `4A5568` (dark grey)
- Muted / caption text: `8A94A6`
- Protocol colour coding (consistent across all charts and cards): BB84 = `1E2761` navy · B92 = `2D7D46` green · E91 = `C47D00` amber-gold

**Structure:** Fully light throughout — white backgrounds on every slide including title and final slide. Identity comes from consistent navy typography and amber accents, not dark backgrounds. Cards use `F4F6FA` to create depth without darkness.

**Motif:** Thin top navy rule on each slide (3px, full width, flush to top edge — like a letterhead line). Section labels in amber beneath the rule on the left. This replaces the left-side bar and feels cleaner on a white background.

**Fonts:**
- Titles: Trebuchet MS Bold, 36pt, navy (`1E2761`)
- Section labels: Trebuchet MS Bold, 13pt, amber (`F5A623`), all caps, letter-spaced
- Body: Calibri, 14pt, `4A5568`
- Key numbers / callouts: Trebuchet MS Bold, 28-36pt, navy

**Layout rule:** Vary layout every 2–3 slides. Never two identical layouts in a row. Every slide must have at least one visual element (icon, chart, callout number, diagram, or image).

---

## Slide-by-Slide Brief

---

### SLIDE 1 — Title
**Layout:** White background. Left-aligned content block, vertically centred. Right 40%: large faint geometric motif (overlapping circles or dot-grid in very light navy — decorative, not clip art).
**Content:**
- Top: 3px navy rule, full width
- Section label (amber, 13pt, all caps): `EEE3094 CAPSTONE PROJECT`
- Main title (navy, 44pt bold): `Benchmarking Quantum Key Distribution`
- Subtitle (dark grey, 20pt): `A Comparative Simulation Framework for BB84, B92, and E91`
- Amber rule, 2px, 2" wide, beneath subtitle
- Name + institution (dark grey, 14pt): `Om Kalyan · School of Engineering, Newcastle University`
- Supervisors (muted, 12pt): `Martin Johnston & Oktay Çetinkaya`

---

### SLIDE 2 — The Problem
**Layout:** Two-column. Left: large amber stat callouts stacked. Right: body text explanation.
**Section label:** `MOTIVATION`
**Title:** `Why QKD, Why Now?`
**Left column — 3 stat callouts (stacked vertically):**
- `2048` / "bits in an RSA key broken by Shor's algorithm on a quantum computer"
- `0` / "computational assumptions in information-theoretic QKD security"
- `3` / "foundational protocols — no unified benchmarking framework existed"
**Right column body:**
- Classical cryptography (RSA, ECC) relies on computational hardness. Quantum computers invalidate that assumption.
- QKD derives security from physical laws — measurement disturbance, no-cloning, entanglement — not from mathematical complexity.
- Despite decades of literature, no standardised simulation framework compared BB84, B92, and E91 under identical conditions with multivariable analysis.
- **This project builds that framework.**
**Visual:** Right column has a simple two-node diagram: "Alice" → quantum channel (wavy line, amber) → "Bob", with a small "Eve?" label below the channel.

---

### SLIDE 3 — Three Protocols: A Family
**Layout:** Three equal columns, each a card with a coloured top band. Horizontal rule separates the top conceptual row from the bottom spec row.
**Section label:** `BACKGROUND`
**Title:** `Three Protocols, Three Security Paradigms`
**Card 1 — BB84** (navy top band):
- Founded: 1984 · Bennett & Brassard
- Type: Prepare & Measure
- States: 4 (|0⟩ |1⟩ |+⟩ |−⟩), 2 bases
- Security: measurement disturbance + no-cloning
- "The reference standard"

**Card 2 — B92** (amber top band):
- Founded: 1992 · Bennett
- Type: Prepare & Measure
- States: 2 non-orthogonal (|0⟩ |+⟩)
- Security: non-orthogonality — no perfect discrimination
- "Simpler hardware, tighter margin"

**Card 3 — E91** (teal `028090` top band):
- Founded: 1991 · Ekert
- Type: Entanglement-Based
- States: Bell pair |Φ⁺⟩
- Security: Bell inequality violation
- "A fundamentally different paradigm"

**Below cards — one-line conceptual progression (italic, muted, centred):**
*BB84 established the foundation → B92 asked if fewer states suffice → E91 abandoned state preparation entirely*

---

### SLIDE 4 — System Architecture
**Layout:** Left 55% = architecture diagram. Right 45% = 4 stacked feature cards.
**Section label:** `DESIGN`
**Title:** `Modular Simulation Architecture`
**Left:** Reproduce the module tree diagram from the original slide (Protocols / Plotting / Modelling / Initialisation / Experiment Configuration groups with connecting lines to QKDSimulator root). Use navy boxes, amber connecting lines, ice-blue group outlines.
**Right — 4 feature cards (stacked, each with a small amber icon circle):**
1. **Modular OOP** — Protocol classes inherit from shared base; noise and Eve models apply uniformly across all three
2. **Batch + Multicore** — V.2 redeveloped circuit execution across cores; enabled high-density parameter sweeps
3. **YAML Config** — Every experiment fully reproducible from a single config file
4. **Export Pipeline** — CSV → MATLAB for 3D surface visualisation

---

### SLIDE 5 — Poster Milestone
**Layout:** Left = thumbnail of poster (image). Right = two stacked cards: "What was achieved" and "Why it mattered".
**Section label:** `MILESTONE`
**Title:** `Poster Review — Framework Validated`
**Left:** Poster image (use existing thumbnail from slide 6 of original deck)
**Right top card — "What was achieved":**
- BB84 complete with basis reconciliation and sifting
- Depolarising channel validated against theoretical QBER curve
- Devetak-Winter SKR crossing zero at exactly 11% — as predicted
- Ideal vs noisy baseline metrics established

**Right bottom card — amber accent — "Why this mattered":**
*Before extending to B92, E91, and eavesdropper models, the framework needed a validation gate. This was it. Every subsequent experiment rests on this foundation.*

---

### SLIDE 6 — The Development Journey
**Layout:** Horizontal timeline spanning full slide width. 5 nodes on a central line. Below each node: brief label. Above alternating nodes: milestone callout box (staggered for readability).
**Section label:** `JOURNEY`
**Title:** `Five Months, Five Stages`
**Timeline nodes (left to right):**
1. **Quantum Foundations** — Theory: superposition, no-cloning, measurement disturbance
2. **BB84 Build** — First Qiskit circuits; basis reconciliation; ideal channel
3. **Poster Milestone** — Depolarising channel + SKR validated ✓
4. **B92 & E91** — Three protocols operational; eavesdropper models added
5. **Multivariable Scale** — 3D sweeps; multicore; 2,907 trial points

**Visual treatment:** Navy horizontal rule. Amber filled circles at each node. Alternating callout boxes above/below. The poster node (3) has an amber highlight ring to mark it as the pivot point.
**No bullet lists anywhere on this slide — the timeline IS the content.**

---

### SLIDE 7 — Scaling the System
**Layout:** Left = version iteration table. Right = two hardware spec cards stacked.
**Section label:** `INFRASTRUCTURE`
**Title:** `Built to Scale`
**Left — compact version table:**

| Version | Grid | BB84 | B92 | Key change |
|---------|------|------|-----|------------|
| V.1 | 16×21 | 16:47 | 16:27 | Baseline · SHEILA · single-core |
| V.2–V.3 | Denser | ~14m | ~11m | Stephenson · multicore logic |
| V.4 | As V.3 | 14:28 | 11:50 | +MI & SKR surfaces |
| **V.5** | **31×41** | **1:03:52** | **53:27** | **2,907 points · Gaussian smoothed** |

V.5 row bold/amber highlight.

**Right top card — SHEILA:**
- i5-8265U · 16GB RAM
- Single-core · V.1 experiments
- "The prototype machine"

**Right bottom card — STEPHENSON (amber accent border):**
- i7-8700 · 32GB RAM · Quadro P2000
- Multicore enabled · ~25% faster
- "Made V.5 possible"

**Bottom callout (full width, amber background, navy text, 16pt):**
`2,907 trial points across noise strength × Eve interception rate — infeasible without the multicore rewrite`

---

### SLIDE 8 — Experiment 1: Baseline
**Layout:** Left = bar chart (reproduce from original). Right = two stacked cards.
**Section label:** `EXPERIMENT 1 · BB84 · B92 · E91`
**Title:** `Baseline Protocol Verification`
**Subtitle (muted):** Mutual Information under ideal channel conditions (n = 1000, 50 trials)
**Left:** Bar chart — three bars (navy / green / amber for BB84 / B92 / E91). QBER = 0%.
**Right top — Expected vs Result:**
- Expected: MI converges to sifting efficiency ceilings — BB84 ~50, B92 ~25, E91 ~22 bits/100 qubits
- Result: Matches exactly ✓ — framework validated against theory

**Right bottom — Why the values differ:**
- BB84 50%: 2-basis match probability = 1/2
- B92 25%: conclusive outcomes ≈ half of rounds
- E91 22.2%: 2 of 9 angle-pair combinations are compatible

---

### SLIDE 9 — Experiment 2: Noise Resilience
**Layout:** Left = line chart (reproduce from original — three protocols overlaid). Right = key observations.
**Section label:** `EXPERIMENT 2 · BB84 · B92 · E91`
**Title:** `Protocol Resilience under Depolarising Noise`
**Subtitle:** SKR vs noise strength — all protocols overlaid (n = 1000, 30 trials/point)
**Left:** Three-line chart with threshold markers. Navy = BB84. Green = B92. Amber = E91.
**Right — 3 observation cards stacked:**
1. **BB84** sustains SKR longest — threshold at p ≈ 0.28. Highest noise tolerance of the three.
2. **E91** outperforms B92 above p ≈ 2.5% despite near-identical QBER — entanglement provides additional correlation strength per sifted bit.
3. **B92** degrades fastest — smallest noise budget before SKR collapses to zero.

---

### SLIDE 10 — Experiment 3: Eavesdropping
**Layout:** Left = line chart (Eve rate vs QBER, both protocols). Right = iteration story + key result.
**Section label:** `EXPERIMENT 3 · BB84 · B92`
**Title:** `Intercept & Resend Attack Vulnerability`
**Subtitle:** Eve interception rate vs QBER — Devetak-Winter threshold lines (n = 1000, 30 trials/point)
**Left:** Two-line chart. Navy = BB84. Green = B92. Horizontal dashed thresholds at 11% and 6.5%.
**Right top — Iteration story card:**
V.1 required 3 attempts (73 min debugging): misaligned Eve logic → incorrect threshold lines → correct. *Shown here: the evidence of genuine engineering work.*

**Right bottom — amber callout with key number:**
Large: `3×` — "B92 is more than three times more vulnerable to interception than BB84"
- BB84 threshold: Eve ≈ 0.44
- B92 threshold: Eve ≈ 0.13
- Root cause: smaller state space gives Eve less ambiguity per intercepted qubit

---

### SLIDE 11 — Experiment 4: E91 Bell Parameter
**Layout:** Left = dual-axis chart (CHSH + QBER vs noise). Right = security thresholds card + interpretation.
**Section label:** `EXPERIMENT 4 · E91`
**Title:** `E91 Bell Parameter Analysis`
**Subtitle:** CHSH S-parameter & QBER vs noise strength (n = 1000, 30 trials/point)
**Left:** Dual-axis chart. Amber line = |S| (CHSH). Red markers = QBER. Two horizontal dashed lines: Tsirelson bound (S = 2√2, amber dashed), classical bound (S = 2, grey dashed).
**Right top — Threshold card:**
- Tsirelson bound: S = 2√2 ≈ 2.83 (quantum maximum)
- Classical bound: S = 2 (security fails)
- D-W SKR → 0 at p ≈ 0.130
- CHSH classical failure at p ≈ 0.165

**Right bottom — interpretation:**
*The D-W bound is more conservative than CHSH — it forces the key rate to zero before entanglement formally fails. This is by design: security should be abandoned before the Bell test is lost.*

---

### SLIDE 12 — Experiment 5: BB84 3D Surface
**Layout:** Left = 3D QBER surface (large, ~60% of slide width). Right = version progression cards.
**Section label:** `EXPERIMENT 5 · BB84 MULTIVARIABLE`
**Title:** `BB84 QBER Surface — Noise × Eve × Security`
**Subtitle:** 500 qubits · 40 trials/point · 2,907 points · Gaussian smoothed
**Left:** 3D surface image from MATLAB. Axes: Eve Interception Rate (%), Noise Strength (%), QBER (%). Yellow threshold plane at 11%.
**Right — V.1 through V.5 progression (5 small stacked cards, V.5 highlighted amber):**
- V.1: 5,040 runs · 16:47 · SHEILA
- V.2–V.3: Denser grid · ~14 min · Big PC
- V.4: +MI & SKR surfaces · 3 plots
- **V.5: 2,907 points · 1:03:52 · Gaussian smoothed**

---

### SLIDE 13 — Experiment 5: BB84 MI & SKR Surfaces
**Layout:** Two equal panels side by side. Each is a 3D surface image with a caption below.
**Section label:** `EXPERIMENT 5 — SURFACES`
**Title:** `BB84 — Mutual Information & Secure Key Rate`
**Left panel:** MI surface image (I(A;B) blue / I(A;E) red intersecting). Caption: "Mutual Information"
**Right panel:** SKR surface image. Caption: "Secure Key Rate"
**Full-width caption below both (italic, muted):**
*The I(A;B)/I(A;E) intersection ridge marks the security boundary — SKR collapses non-linearly, with combined interference accelerating the decay beyond what either noise or eavesdropping causes alone.*

---

### SLIDE 14 — Experiment 6: B92 3D Surface
**Layout:** Mirror of slide 12.
**Section label:** `EXPERIMENT 6 · B92 MULTIVARIABLE`
**Title:** `B92 QBER Surface — Noise × Eve × Security`
**Subtitle:** 500 qubits · 40 trials/point · 2,907 points · Gaussian smoothed
**Left:** B92 3D QBER surface. Threshold plane at 6.5% (purple/pink).
**Right:** V.1–V.5 progression cards. V.5 highlighted.

---

### SLIDE 15 — Experiment 6: B92 MI & SKR Surfaces
**Layout:** Mirror of slide 13.
**Section label:** `EXPERIMENT 6 — SURFACES`
**Title:** `B92 — Mutual Information & Secure Key Rate`
**Caption below:** *B92's compressed I(A;B) ceiling and earlier I(A;E) crossover confirm the protocol requires near-ideal conditions — it is fundamentally unsuited to noisy or adversarial environments.*

---

### SLIDE 16 — Synthesis: What This Tells Us [NEW SLIDE]
**Layout:** Three-column protocol cards (same visual language as slide 3), each with a "Deploy when..." recommendation. Below all three: a single summary statement.
**Section label:** `FINDINGS`
**Title:** `A Protocol Selection Framework`
**Card 1 — BB84 (navy):**
- Noise threshold: p ≈ 0.28 (highest)
- Eve threshold: ε ≈ 0.44 (highest)
- SKR ceiling: ~50 bits/100 qubits
- **Deploy when:** channel noise is significant or distance is long. Best all-round performer.

**Card 2 — E91 (teal):**
- Dual security metric: QBER + CHSH
- Superior SKR above B92 despite similar sifting efficiency
- Intrinsic eavesdropper detection via Bell test
- **Deploy when:** maximum security assurance is required in low-noise environments. Future: device-independent QKD.

**Card 3 — B92 (amber):**
- Simplest hardware requirement (2 states)
- QBER threshold: 6.5% — tightest margin
- Requires near-ideal channel
- **Deploy when:** hardware simplicity is the constraint and channel conditions are near-perfect.

**Full-width bottom statement (large, italic, navy, centred):**
*"The simulation confirms that no single protocol dominates across all conditions — the optimal choice is always deployment-context dependent."*

---

### SLIDE 17 — Limitations & Trade-offs
**Layout:** Two-column. Left = known limitations (4 items). Right = design trade-offs (3 items). Each item has an amber icon circle.
**Section label:** `EVALUATION`
**Title:** `Limitations & Design Trade-offs`

**Left — Known Limitations:**
1. **Shannon Capacity assumed** — classical error correction (Cascade/LDPC) excluded; SKR represents a theoretical upper bound. Real rates would be lower.
2. **E91 eavesdropper not implemented** — entanglement-swapping attacks require density matrix formalism beyond current scope. CHSH serves as implicit detection.
3. **Ideal hardware abstraction** — no detector dark counts, fibre attenuation, or timing jitter. Qiskit AerSimulator only.
4. **No finite-key effects** — asymptotic analysis used; finite-key security proofs tighten bounds significantly for short keys.

**Right — Design Trade-offs:**
1. **Worst-case QBER attribution** — all channel disturbance attributed to Eve. Conservative but necessary for valid SKR bounds.
2. **Monte Carlo stability vs compute cost** — 40–50 trials/point gives negligible SEM reduction beyond this; diminishing returns verified empirically.
3. **B92 USD attack** — not simulated, but D-W bound assigns maximum theoretical penalty regardless — thresholds remain conservative.

---

### SLIDE 18 — Future Work
**Layout:** White background (mirrors title slide). Five numbered item cards in two columns, navy text throughout. Same 3px navy top rule as all other slides.
**Section label:** `NEXT STEPS`
**Title (navy):** `Extensions & Future Work`
**Five cards (`F4F6FA` background, navy text, amber numbered circles):**
1. **E91 Eavesdropper** — Entanglement-swapping or collective attack to complete the three-protocol security benchmark
2. **Hardware Noise Integration** — IBM Quantum real device noise models; evolve from theoretical to device-specific
3. **Advanced Protocols** — Expand beyond DV-QKD to MDI-QKD, CV-QKD, and decoy-state variants
4. **Network Topology** — Multi-node quantum networks; trusted-node routing; quantum repeater modelling
5. **Digital Twin Deployment** — Systems engineering model of real-world QKD deployment viability and operational constraints

**Bottom (muted, italic, centred):**
*"The modular architecture was designed precisely to make these extensions tractable."*

---

## Notes for Implementation

- All 3D surface plots and charts are reproduced from existing MATLAB/Python outputs — use the images from the original slide deck as source material
- Speaker notes should be added to each slide summarising the 30-second verbal narrative for that slide
- The 3px navy top rule and amber section label are the consistent identity motif across all 18 slides — apply to every slide without exception
- Card / panel backgrounds use `F4F6FA` throughout; never use a coloured background on any slide
- Slide numbers: small, bottom-right, muted `8A94A6`, Calibri 11pt
- Do not add any decorative underlines, header bars, coloured stripes, or full-width rectangles
- Protocol colour coding must be consistent across every chart, card, and reference: BB84 = navy `1E2761`, B92 = green `2D7D46`, E91 = amber-gold `C47D00`
