"""B92 protocol"""

import numpy as np
from qiskit import QuantumCircuit
from ..base import QKDProtocol, QKDResult


class B92Protocol(QKDProtocol):

    def __init__(self, n_qubits: int, backend, eve=None):
        super().__init__(n_qubits, backend, eve)
        self._alice_bits = None
        self._bob_bases = None
        self._bob_results = None
        self._eve_intercepted = None

    @classmethod
    def protocol_name(cls):
        return "B92"

    @classmethod
    def theoretical_sifting_rate(cls):
        return 0.25  # Bob concludes ~50% per basis * 2 bases / (2 bases * 2) = 0.25; matches Bennett 1992 expected yield

    @staticmethod
    def theoretical_qber(noise_type, strengths):
        # B92 QBER under depolarising: p/(1+p); differs from BB84's p/2 due to the two-state encoding
        if noise_type == 'depolarizing':
            p = np.asarray(strengths, dtype=float)
            return p / (1.0 + p)
        return None

    def run(self):
        circuits = self._alice_prepare()

        if self.eve is not None:
            circuits, self._eve_intercepted = self.eve.intercept_b92(circuits)

        self._bob_measure(circuits)
        return self._post_process()

    def _alice_prepare(self):
        self._alice_bits = np.random.randint(0, 2, size=self.n_qubits)

        circuits = []
        for i in range(self.n_qubits):
            qc = QuantumCircuit(1, 1)
            # B92 uses only two non-orthogonal states: bit=0 sends |0>, bit=1 sends |+>; no X gate needed
            if self._alice_bits[i] == 1:
                qc.h(0)
            qc.id(0)  # id is a no-op; noise model attaches depolarising error here to simulate the channel
            circuits.append(qc)

        return circuits

    def _bob_measure(self, circuits):
        self._bob_bases = np.random.randint(0, 2, size=self.n_qubits)
        self._bob_results = np.zeros(self.n_qubits, dtype=int)

        # Bob applies a random basis to attempt to distinguish Alice's two states
        for i, qc in enumerate(circuits):
            if self._bob_bases[i] == 1:
                qc.h(0)
            qc.measure(0, 0)

        job = self.backend.run(circuits, shots=1, memory=True)
        result = job.result()
        for i in range(len(circuits)):
            self._bob_results[i] = int(result.get_memory(i)[0])

    def _post_process(self):
        # Bob gets a conclusive outcome only when he measures |1>; measuring |0> is ambiguous between Alice's two states
        conclusive_mask = (self._bob_results == 1)
        sifted_indices = np.where(conclusive_mask)[0]

        sifted_key_alice = self._alice_bits[conclusive_mask]
        # when Bob measures |1> in basis b, Alice's bit is inferred as (1 - b); derived from the B92 state table
        sifted_key_bob = 1 - self._bob_bases[conclusive_mask]

        sifted_length = len(sifted_key_alice)
        if sifted_length > 0:
            errors = np.sum(sifted_key_alice != sifted_key_bob)
            qber = errors / sifted_length
        else:
            qber = 0.0

        key_rate = sifted_length / self.n_qubits

        return QKDResult(
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
        )
