Draft this section and use the skill file provided to do so.
Section topic: Literature Review
Scope/Length: approx. 800 words
Specific content requirements: 

- use the list of findings from analysing these two papers to inform the prcoess of drafting a new section for me

    **Paper 1 (Rasay et al. — "Secure Quantum Communication: Simulation and Analysis of QKD Protocols")**

    Their literature review in Section II follows a thematic, layered structure rather than a paper-by-paper summary. It moves through several distinct layers:

    1. **Foundational origins** — They open with the seminal works (Bennett & Brassard's BB84, Ekert's E91, Bennett's B92), establishing the theoretical lineage. Each protocol is introduced with a single sentence capturing its core contribution and mechanism.

    2. **Simulation-based validation** — They then pivot to how simulation studies have tested these protocols, grouping references by protocol rather than chronologically. BB84 simulations under noise/attacks come first (refs 4–8), then E91 entanglement simulations (refs 9–11), then B92 (refs 12–13). This grouping lets them draw out comparative findings across studies.

    3. **Comparative and cross-protocol insights** — They consolidate with refs 14–16, noting that BB84 consistently ranks as the most practical, E91 offers deeper security through entanglement but at higher complexity, and B92 trades efficiency for simplicity.

    4. **Emerging threats and gaps** — They flag machine-learning-assisted attacks (ref 17) that challenge traditional intercept-resend assumptions, and networked QKD scalability limitations (ref 18). This is where the gap identification happens — they argue that classical attack models may underestimate adversaries and that hybrid architectures are needed.

    5. **Closing synthesis** — A single paragraph ties it together, positioning simulation as essential for revealing practical tradeoffs that theoretical proofs alone cannot capture.

    What's notable is how they use **assertive, evaluative language** throughout — phrases like "consistently show," "results suggest," "reinforcing the need for." They aren't just listing what each paper did; they're drawing conclusions across the body of work and pointing to where it falls short.

    ---

    **Paper 2 (Kukutla et al. — "Secure Simulation of BB84 and E91 Quantum Cryptography Protocols")**

    Their Section II takes a more **source-by-source** approach. Each paragraph typically covers one or two references and summarises what that work contributed. The structure is:

    1. **Theoretical foundations** — Portmann & Renner (ref 1) on entropy-based security proofs. This sets the mathematical grounding.

    2. **Practical implementation studies** — Muruganantham et al. (ref 2) on interfacing BB84 with classical networks, Hughes et al. (ref 3) on early experimental QKD demonstrations. These establish that real-world deployment has been attempted.

    3. **Broader context and applications** — Sergienko (ref 4) as a textbook reference, Giroti & Malhotra (ref 5) on societal implications in defence/finance.

    4. **Comparative and protocol-specific work** — Subramani & Svn (ref 6) comparing classical vs quantum methods, Dušek et al. (ref 7) on photon polarity and entanglement testing mechanics.

    5. **Hybrid and future-looking work** — Victor et al. (ref 8) on mixed cryptographic systems, Chen et al. (ref 9) on field-deployed decoy-state QKD.

    6. **Simulation and educational tools** — Escanez-Exposito et al. (refs 13–14) on interactive QKD simulators, Bildstein (ref 15) on a web-based BB84 simulator.

    7. **Gap statement** — The final paragraph explicitly states: not many platforms exist that allow side-by-side comparison of BB84 and E91 with tuneable parameters and real-time visualisation. This is their justification.

    The key difference from Paper 1 is that this review reads more like an **annotated bibliography** — each source gets its own treatment. The evaluative commentary is lighter and mostly confined to the closing paragraph.

    ---

    **Key takeaways for your own literature review:**

    **What works well in Paper 1** is the thematic grouping. By organising around themes (foundational theory → simulation validation → emerging attacks → gaps), they build a narrative arc that naturally leads to their research justification. The reader understands *why* their work matters without being told explicitly until the end.

    **What works well in Paper 2** is the breadth of coverage — they touch on theoretical, experimental, educational, and hybrid dimensions. The explicit gap statement at the end is clear and direct.

    **Where both fall short** (and where you can differentiate): neither paper deeply critiques the *methodology* of the sources they cite. They describe what was found but rarely question how robust those findings are, what assumptions were made, or how reproducible the results might be. A strong literature review should note limitations in prior work — not just gaps in coverage, but weaknesses in approach. Paper 1 gestures at this with the ML-attack point, but doesn't push further.

    For your report, I'd recommend blending both styles: use Paper 1's thematic structure to build narrative flow, but ensure each theme has the breadth of coverage Paper 2 demonstrates, and add a layer of critical evaluation that neither paper does particularly well. When you're ready to share your actual sources and the skill file, I'll be set to help you draft it.

- match the presentation style of these reviews, with short succint sections
- ensure that you do not plagurise these sources
- check the bib.bib file I provide you to see if any of the sources listed are already described in the bibliography, if not, add placeholders to the correct source as I will manually add them in

- write this new draft to a file called "litreview.tex" and update the bib.bib file

Surrounding context:
- ONLY use the sources I have provided you to develop this report
- DO NOT DEVIATE FROM THE SOURCES PROVIDED