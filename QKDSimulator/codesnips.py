## code snips for the report, not to be run as a script
"""
Here is the organized list of protocol implementations and modules, broken down by category for easier navigation:

### Protocol Implementations
* **BB84 (`bb84.py`)**
    * **Function:** `_alice_prepare()` (lines ~56–71)
    * **Highlights:** Demonstrates four-state preparation and the `qc.id(0)` channel marker, encapsulating the trusted-device assumption.
* **B92 (`b92.py`)**
    * **Function:** `_post_process()` (lines ~98–127)
    * **Highlights:** Features the conclusive-outcome sift and the `1 - bob_bases` decode logic.
* **E91 (`e91.py`)**
    * **Function:** `_prepare_pairs()` (lines ~110–133)
    * **Highlights:** Shows the singlet circuit ($H \rightarrow CNOT \rightarrow X \rightarrow Z$) and the "both vs bob" topology switch.
    * **Optional:** `CHSH correlator loop` in `_post_process()` (lines ~163–178). Shows the signed-sum calculation of `_CHSH_S_TERMS`.

---

### Noise Models and Channel Simulation
* **Noise Module (`noise.py`)**
    * **Function:** `create_backend()` (lines ~30–40)
    * **Highlights:** Contains `add_all_qubit_quantum_error(error, ['id'])`, which serves as the core of the channel-marker thesis.

---

### Eavesdropper Model
* **Intercept Strategy (`eve.py`)**
    * **Function:** `intercept()` (lines ~32–70)
    * **Highlights:** A short, self-contained implementation of the BB84-style attack.
    * **Optional:** `intercept_b92()` (lines ~72–117). Specific strategy for mimicking B92 conclusive outcomes.

---

### Post-Processing (GLLP/MI)
* **Base Logic (`base.py`)**
    * **Function:** `_binary_entropy()` + `mutual_information` property (lines ~41–59)
    * **Highlights:** The information-theoretic apparatus condensed into one small listing.
"""

### Protocol Implementations
# **BB84 (`bb84.py`)**
#    * **Function:** `_alice_prepare()` (lines ~56–71)
#    * **Highlights:** Demonstrates four-state preparation and the `qc.id(0)` channel marker, encapsulating the trusted-device assumption.
def _alice_prepare(self) -> List[QuantumCircuit]:
        """Generate random bits/bases and build one circuit per qubit."""
        self._alice_bits = np.random.randint(0, 2, size=self.n_qubits)
        self._alice_bases = np.random.randint(0, 2, size=self.n_qubits)

        circuits = []
        for i in range(self.n_qubits):
            qc = QuantumCircuit(1, 1)
            if self._alice_bits[i] == 1:
                qc.x(0)
            if self._alice_bases[i] == 1:
                qc.h(0)
            qc.id(0)  # channel marker
            circuits.append(qc)

        return circuits


# **B92 (`b92.py`)**
#    * **Function:** `_post_process()` (lines ~98–127)
#    * **Highlights:** Features the conclusive-outcome sift and the `1 - bob_bases` decode logic.
def _post_process(self) -> B92Result:
        """Sift using conclusive events (Bob result == 1)."""
        conclusive_mask = (self._bob_results == 1)
        sifted_indices = np.where(conclusive_mask)[0]

        sifted_key_alice = self._alice_bits[conclusive_mask]
        sifted_key_bob = 1 - self._bob_bases[conclusive_mask]

        sifted_length = len(sifted_key_alice)
        if sifted_length > 0:
            errors = np.sum(sifted_key_alice != sifted_key_bob)
            qber = errors / sifted_length
        else:
            qber = 0.0

        key_rate = sifted_length / self.n_qubits

        return B92Result(
            protocol_name="B92",
            n_qubits=self.n_qubits,
            alice_bits=self._alice_bits.copy(),
            bob_results=self._bob_results.copy(),
            sifted_indices=sifted_indices,
            sifted_key_alice=sifted_key_alice,
            sifted_key_bob=sifted_key_bob,
            qber=qber,
            key_rate=key_rate,
            eve_intercepted=self._eve_intercepted,
            bob_bases=self._bob_bases.copy(),
            conclusive_mask=conclusive_mask,
        )


# **E91 (`e91.py`)**
#    * **Function:** `_prepare_pairs()` (lines ~110–133)
#   * **Highlights:** Shows the singlet circuit ($H \rightarrow CNOT \rightarrow X \rightarrow Z$) and the "both vs bob" topology switch.
#    * **Optional:** `CHSH correlator loop` in `_post_process()` (lines ~163–178). Shows the signed-sum calculation of `_CHSH_S_TERMS`.
def _prepare_pairs(self) -> List[QuantumCircuit]:
        """Build singlet circuits with channel id markers."""
        self._alice_angles = np.random.randint(0, 3, size=self.n_qubits)
        self._bob_angles = np.random.randint(0, 3, size=self.n_qubits)

        circuits = []
        for _ in range(self.n_qubits):
            qc = QuantumCircuit(2, 2)
            # Singlet |Psi-> = (|01> - |10>)/sqrt(2)
            qc.h(0)
            qc.cx(0, 1)
            qc.x(0)
            qc.z(0)
            qc.barrier()

            if self.channel_topology == 'both':
                qc.id(0)
                qc.id(1)
            else:
                qc.id(1)

            circuits.append(qc)

        return circuits

# correlator loop snippet:
# CHSH correlations
def _post_process(self) -> E91Result:
        """Sift key, compute QBER, evaluate CHSH parameter."""
        sift_labels = self._SIFT_TABLE[self._alice_angles, self._bob_angles]
        key_mask = (sift_labels == 'key')
        chsh_mask = (sift_labels == 'chsh')

        sifted_indices = np.where(key_mask)[0]
        chsh_indices = np.where(chsh_mask)[0]

        sifted_key_alice = self._alice_outcomes[sifted_indices].astype(int)
        sifted_key_bob = (1 - self._bob_outcomes[sifted_indices]).astype(int)

        sifted_length = len(sifted_key_alice)
        if sifted_length > 0:
            errors = int(np.sum(sifted_key_alice != sifted_key_bob))
            qber = errors / sifted_length
        else:
            qber = 0.0

        key_rate = sifted_length / self.n_qubits

        # CHSH correlations
        correlations: Dict[Tuple[int, int], float] = {}
        s_value = 0.0
        for (ai, bi), sign in self._CHSH_S_TERMS:
            sub_mask = (self._alice_angles == ai) & (self._bob_angles == bi)
            n_sub = int(np.sum(sub_mask))
            if n_sub == 0:
                warnings.warn(
                    f"E91 CHSH bucket (a{ai+1}, b{bi+1}) is empty "
                    f"(n_qubits={self.n_qubits} too small).",
                    RuntimeWarning, stacklevel=2)
                corr = 0.0
            else:
                a_pm = 1 - 2 * self._alice_outcomes[sub_mask].astype(int)
                b_pm = 1 - 2 * self._bob_outcomes[sub_mask].astype(int)
                corr = float(np.mean(a_pm * b_pm))
            correlations[(ai, bi)] = corr
            s_value += sign * corr

        return E91Result(
            protocol_name="E91",
            n_qubits=self.n_qubits,
            alice_bits=self._alice_outcomes.copy(),
            bob_results=self._bob_outcomes.copy(),
            sifted_indices=sifted_indices,
            sifted_key_alice=sifted_key_alice,
            sifted_key_bob=sifted_key_bob,
            qber=qber,
            key_rate=key_rate,
            eve_intercepted=None,
            alice_angles=self._alice_angles.copy(),
            bob_angles=self._bob_angles.copy(),
            alice_outcomes=self._alice_outcomes.copy(),
            bob_outcomes=self._bob_outcomes.copy(),
            chsh_indices=chsh_indices,
            correlations=correlations,
            s_value=float(s_value),
            chsh_pairs_count=int(chsh_mask.sum()),
            key_pairs_count=int(key_mask.sum()),
            channel_topology=self.channel_topology,
        )
    

    ### Noise Models and Channel Simulation
# **Noise Module (`noise.py`)**
#    * **Function:** `create_backend()` (lines ~30–40)
#    * **Highlights:** Contains `add_all_qubit_quantum_error(error, ['id'])`, which serves as the core of the channel-marker thesis.
def create_backend(noise_type: str, strength: float = 0.0) -> AerSimulator:
    """Return an AerSimulator with noise applied to 'id' gates."""
    if noise_type == 'none':
        return AerSimulator()

    noise_model = NoiseModel()
    error = _create_error(noise_type, strength)
    noise_model.add_all_qubit_quantum_error(error, ['id'])

    return AerSimulator(noise_model=noise_model)



### Eavesdropper Model
# **Intercept Strategy (`eve.py`)**
#    * **Function:** `intercept()` (lines ~32–70)
#    * **Highlights:** A short, self-contained implementation of the BB84-style attack.
#    * **Optional:** `intercept_b92()` (lines ~72–117). Specific strategy for mimicking B92 conclusive outcomes.
def intercept(self, circuits: List[QuantumCircuit]) -> Tuple[List[QuantumCircuit], np.ndarray]:
    """
    BB84-style intercept-resend.

    1. Decide which qubits to intercept and build measurement circuits.
    2. Batch-execute all measurements on the noisy backend.
    3. Build replacement circuits encoded in Eve's chosen basis.
    """
    output_circuits = list(circuits)
    intercepted_indices = []
    eve_bases = []
    measure_circuits = []

    for i, qc in enumerate(circuits):
        if np.random.random() < self.interception_rate:
            intercepted_indices.append(i)
            eve_basis = np.random.randint(0, 2)
            eve_bases.append(eve_basis)

            measure_qc = qc.copy()
            if eve_basis == 1:
                measure_qc.h(0)
            measure_qc.measure(0, 0)
            measure_circuits.append(measure_qc)

    if measure_circuits:
        job = self._backend.run(measure_circuits, shots=1, memory=True)
        result = job.result()

        for idx, (orig_i, eve_basis) in enumerate(
            zip(intercepted_indices, eve_bases)
        ):
            eve_result = int(result.get_memory(idx)[0])
            output_circuits[orig_i] = self._prepare_replacement(
                eve_result, eve_basis)

    return output_circuits, np.array(intercepted_indices, dtype=int)

# b92 intercept:
def intercept_b92(self, circuits: List[QuantumCircuit]) -> Tuple[List[QuantumCircuit], np.ndarray]:
    """
    B92-style intercept-resend.

    Eve mimics Bob's measurement: random Z/X basis. A conclusive
    outcome (result == 1) unambiguously identifies the state and
    therefore Alice's bit; an inconclusive outcome (result == 0)
    forces Eve to guess the bit at random. She then re-sends the
    corresponding B92 state (bit 0 -> |0>, bit 1 -> |+>).
    """
    output_circuits = list(circuits)
    intercepted_indices = []
    eve_bases = []
    measure_circuits = []

    for i, qc in enumerate(circuits):
        if np.random.random() < self.interception_rate:
            intercepted_indices.append(i)
            eve_basis = np.random.randint(0, 2)
            eve_bases.append(eve_basis)

            measure_qc = qc.copy()
            if eve_basis == 1:
                measure_qc.h(0)
            measure_qc.measure(0, 0)
            measure_circuits.append(measure_qc)

    if measure_circuits:
        job = self._backend.run(measure_circuits, shots=1, memory=True)
        result = job.result()

        for idx, (orig_i, eve_basis) in enumerate(
            zip(intercepted_indices, eve_bases)
        ):
            eve_result = int(result.get_memory(idx)[0])
            if eve_result == 1:
                # Conclusive: same rule Bob uses for sifting.
                eve_bit = 1 - eve_basis
            else:
                # Inconclusive: guess uniformly.
                eve_bit = int(np.random.randint(0, 2))
            output_circuits[orig_i] = self._prepare_b92_replacement(eve_bit)

    return output_circuits, np.array(intercepted_indices, dtype=int)


### Post-Processing (GLLP/MI)
# **Base Logic (`base.py`)**
#    * **Function:** `_binary_entropy()` + `mutual_information` property (lines ~41–59)
#    * **Highlights:** The information-theoretic apparatus condensed into one small listing.

@staticmethod
def _binary_entropy(x: float) -> float:
    if x <= 0.0 or x >= 1.0:
        return 0.0
    return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

@property
def mutual_information(self) -> float:
    """Shannon mutual information I(A;B) per transmitted qubit.

    I(A;B) = sifting_rate * (1 - h(QBER)), assuming the sifted-bit
    channel is a binary symmetric channel.
    """
    if self.sifted_length == 0:
        return 0.0
    h_e = self._binary_entropy(self.qber)
    return self.key_rate * (1.0 - h_e)