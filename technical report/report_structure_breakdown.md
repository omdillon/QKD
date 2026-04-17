# Report Structure Breakdown & Rubric Analysis

**Project:** Beyond Classical Cryptography: Simulating & Benchmarking QKD
**Word Target:** ~7,000 words | **Current Combined Draft:** ~9,762 words | **Over by:** ~2,762 words

---

## Full Chapter/Section Map (with word counts)

| # | Chapter / Section | Words | Status | Rubric Target |
|---|---|---|---|---|
| **1** | **Introduction** | **~1,547** | **Written** | **Project Definition (10 pts)** |
| 1.I | A Brief History of Cryptology | ~450 | Written | |
| 1.II | The Quantum Threat to Classical Cryptography | ~150 | Written | |
| 1.III | Aims & Objectives (O1-O6) | ~950 | Written | |
| **2** | **Literature Review** | **~4,085** | **Mostly Written** | **Literature (10 pts)** |
| 2.I | The Quantum Threat to Classical Cryptography | ~550 | Written | |
| 2.II | Quantum Mechanical Foundations | ~900 | Written | |
| 2.II.A | Qubits & Superposition | | Written | |
| 2.II.B | Measurement Disturbance | | Written | |
| 2.II.C | No-cloning Theorem | | Written | |
| 2.II.D | Heisenberg's Uncertainty | | Written | |
| 2.II.E | Quantum Entanglement & Bell's Theorem | | Written | |
| 2.III | QKD Protocols | ~750 | Written | |
| 2.III.A | BB84 | | Written | |
| 2.III.B | B92 | | Written | |
| 2.III.C | E91 | | Written | |
| 2.IV | The Post-Processing Pipeline | ~414 | **NEW** | |
| 2.V | Noise Models for Modelling | ~427 | **NEW** | |
| 2.VI | QKD Simulation Frameworks | ~324 | **NEW** | |
| 2.VII | Research Gaps | ~275 | **NEW** | |
| **3** | **Methodology** | **~2,124** | **NEW (replaces skeleton)** | **Technical Content (20 pts)** |
| 3.I | Simulation Architecture | ~371 | NEW | |
| 3.I.A | Modular Package Design | | NEW | |
| 3.I.B | Configuration System | | NEW | |
| 3.I.C | Execution Pipeline | | NEW | |
| 3.II | Protocol Implementations | ~613 | NEW | |
| 3.II.A | BB84 Protocol | | NEW | |
| 3.II.B | B92 Protocol | | NEW | |
| 3.II.C | E91 Protocol | | NEW | |
| 3.III | Modelling Assumptions | ~255 | NEW | |
| 3.IV | Noise Models and Channel Simulation | ~474 | NEW | |
| 3.IV.A | Channel Marker Approach | | NEW | |
| 3.IV.B | Fibre Attenuation Model | | NEW | |
| 3.IV.C | Eavesdropper Model | | NEW | |
| 3.V | Post-Processing Implementation | ~179 | NEW | |
| 3.V.A | Error Estimation | | NEW | |
| 3.V.B | GLLP Key Rate Calculation | | NEW | |
| 3.V.C | Mutual Information | | NEW | |
| 3.VI | Performance Metrics | ~232 | NEW | |
| 3.VI.A | Statistical Methodology | | NEW | |
| **4** | **Results & Discussion** | **~863** | **NEW** | **Analysis (10 pts)** |
| 4.I | Ideal Channel Validation | ~61 | NEW | |
| 4.II | Eavesdropper Detection | ~173 | NEW | |
| 4.III | Noise Tolerance Comparison | ~277 | NEW | |
| 4.IV | Secure Key Rate and Deployment Feasibility | ~155 | NEW | |
| 4.V | Limitations and Sources of Error | ~197 | NEW | |
| **5** | **Conclusion & Future Work** | **~1,143** | **NEW** | **Project Definition (10 pts)** |
| 5.I | Achievements Against Objectives | ~226 | NEW | |
| 5.II | Key Findings | ~139 | NEW | |
| 5.III | Broader Context | ~261 | NEW | |
| 5.IV | Project Management Reflection | ~266 | NEW | |
| 5.V | Limitations | ~66 | NEW | |
| 5.VI | Future Work | ~185 | NEW | |

---

## Word Budget Problem

You are **~2,762 words over** the 7,000-word target. Here is the recommended trimming strategy.

### What to CUT or heavily compress (~2,800 words to recover)

| Section | Current | Target | Save | Reasoning |
|---|---|---|---|---|
| 1.I History of Cryptology | ~450 | ~200 | **~250** | Nice context but not scoring you marks on any rubric criterion. Cut pre-20th century content to 2-3 sentences. |
| 2.I Quantum Threat (Lit Review) | ~550 | ~300 | **~250** | Overlaps heavily with Intro 1.II. Merge the best content into one location (Lit Review) and trim the Intro version to a 2-sentence bridge. |
| 2.II Quantum Mechanical Foundations | ~900 | ~550 | **~350** | The no-cloning proof is elegant but the formal contradiction argument can be shortened. Heisenberg section can be halved (it currently repeats points made in Measurement Disturbance). |
| 2.III QKD Protocols (BB84/B92/E91) | ~750 | ~500 | **~250** | These are well-written but descriptive. The rubric wants "critical synthesis" not protocol summaries. Tighten each to essential mechanics + one synthesis sentence linking to your simulation. |
| 2.V Noise Models (Lit Review) | ~427 | ~250 | **~177** | The equations are valuable but the prose around them can be compressed. The excluded-models paragraph is efficient already. |
| 5.I Achievements Against Objectives | ~226 | ~120 | **~106** | Currently walks through O1-O6 individually. Condense to a single paragraph hitting the key achievements. |
| 5.III Broader Context | ~261 | ~150 | **~111** | Useful for O6.2 but currently reads like a standalone essay. Tighten to the essential points. |
| 5.IV Project Management Reflection | ~266 | ~150 | **~116** | Can be more concise. Focus on 2-3 key decisions/lessons, not a chronological narrative. |
| Various small trims | | | **~1,150** | General tightening across all sections (removing redundant transitions, shortening where two sentences say what one could). |
| **Total savings** | | | **~2,760** | |

### What to KEEP at full length (these are your mark-earners)

| Section | Words | Why it's untouchable |
|---|---|---|
| **3.I Simulation Architecture** | ~371 | Directly scores "justified design approach" (20-pt criterion) |
| **3.II Protocol Implementations** | ~613 | The core of "depth of technical understanding" |
| **3.III Modelling Assumptions** | ~255 | Preempts examiner questions, shows engineering maturity |
| **3.IV Noise Models + Channel Sim** | ~474 | Your most original contribution (fibre attenuation + dark count coupling) |
| **3.V-VI Post-Processing + Metrics** | ~411 | Shows the GLLP/f_EC distinction that differentiates your work |
| **4.I-IV Results sections** | ~666 | The entire Analysis criterion (10 pts) lives here |
| **2.VII Research Gaps** | ~275 | Justifies the entire project's existence |

---

## Rubric Mapping: What Scores Where

### 1. Project Definition, Scope & Context (10 pts)
**Content needed:** Clear objectives, measurable outcomes, EDI, constraints, reflection on achievement.
**Where it lives:** Intro III (Aims & Objectives), Conclusion I (Achievements), Conclusion IV (Reflection)
**Current coverage:** STRONG. Objectives are specific and measurable. Add one EDI sentence to the Introduction if not already present.
**Missing item:** EDI sentence (the execution plan flags this). One sentence is sufficient.

### 2. Research & Use of Literature (10 pts)
**Content needed:** 25-50 high-quality sources, critical synthesis (not description), research gaps justifying your project.
**Where it lives:** All 7 Literature Review sections.
**Current coverage:** GOOD after adding the 4 new sections. The existing protocol descriptions (BB84/B92/E91) are slightly too descriptive. Each needs a "critical synthesis sentence" connecting the literature to YOUR specific approach.
**Risk area:** Quantum Mechanical Foundations (Section 2.II) is thorough but is mostly textbook reproduction. Consider whether the examiner would view this as padding vs. necessary context.

### 3. Technical Content & Engineering Implementation (20 pts) — DOUBLE WEIGHT
**Content needed:** Architecture, implementation detail, noise model justification, eavesdropper model, post-processing. Every paragraph must show engineering reasoning, not just describe what you built.
**Where it lives:** Entire Methodology chapter.
**Current coverage:** STRONG after the new content. Key mark-earners:
- Channel marker approach (novel and well-justified)
- Fibre attenuation as post-selection (shows understanding of what is/isn't a quantum channel)
- f_EC = 1.16 distinction (shows awareness of practical vs. idealised assumptions)
- Modelling assumptions section (shows what you deliberately excluded and why)
**Potential addition:** A comparison table of design decisions (e.g., "Decision | Options Considered | Choice | Rationale") could score highly here.

### 4. Analysis, Evaluation & Critical Thinking (10 pts)
**Content needed:** Results vs aims, limitations, error sources, critical comparison of protocols.
**Where it lives:** Results & Discussion chapter.
**Current coverage:** ADEQUATE but the thinnest chapter at ~863 words. This is where the execution plan's validation table, figures, and cross-protocol comparison do the heavy lifting. The prose supports the figures rather than replacing them.
**Risk area:** At 863 words this chapter feels light for a 10-pt criterion. If word budget allows after trimming, expand Section 4.III (Noise Tolerance Comparison) and 4.IV (Deployment Feasibility) by ~200 words each.

### 5. Report Quality: Structure, Presentation & Communication (10 pts)
**Content needed:** Figure quality, IEEE refs, consistent style, logical flow, ownership of voice.
**Where it lives:** Everywhere.
**Action items:** AI-detection voice pass, consistent British English, no em dashes, figure/table cross-refs all working.

---

## Sections to Consider REMOVING

| Section | Reasoning |
|---|---|
| 2.II.D Heisenberg's Uncertainty | 80% of its content restates Measurement Disturbance (2.II.B). Could be merged into one paragraph within 2.II.B with a sentence noting Heisenberg as the formal underpinning. Saves ~100 words. |
| 5.V Limitations (Conclusion) | This is a 66-word cross-reference to Chapter 4's limitations section. Either expand it to add genuine new reflection, or delete it entirely and let Chapter 4 carry the full weight. A 3-line section looks weak. |

## Sections to Consider ADDING

| Section | Reasoning | Placement | Words |
|---|---|---|---|
| EDI sentence | Rubric explicitly mentions it under Project Definition | Introduction, after Aims & Objectives | ~30 |
| Summary comparison table | A single table comparing BB84/B92/E91 across all metrics (sifting efficiency, QBER threshold, eavesdropper detection mechanism, noise sensitivity) would be a high-impact, low-word-count addition | End of Results Chapter 4 | ~50 (table, not prose) |

---

## Recommended Final Word Budget

| Chapter | Target Words | % of 7,000 |
|---|---|---|
| Introduction | ~1,100 | 16% |
| Literature Review | ~2,100 | 30% |
| Methodology | ~2,100 | 30% |
| Results & Discussion | ~1,050 | 15% |
| Conclusion & Future Work | ~650 | 9% |
| **Total** | **~7,000** | **100%** |

The heaviest weight should go to Methodology (30%) and Literature Review (30%), matching the rubric's emphasis on Technical Content (20 pts) and Literature (10 pts). Results at 15% is appropriate because figures carry much of the analytical weight. Introduction and Conclusion together at 25% cover Project Definition (10 pts).
