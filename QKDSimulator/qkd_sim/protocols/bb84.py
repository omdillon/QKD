"""BB84 protocol"""

import numpy as np
from qiskit import QuantumCircuit

from ..base import QKDProtocol, QKDResult


class BB84Protocol(QKDProtocol):

    def __init__(self, n_qubits: int, backend, eve=None):
        super().__init__(n_qubits, backend, eve)
        self._alice_bits = None
        self._alice_bases = None
        self._bob_bases = None
        self._bob_results = None
        self._eve_intercepted = None

    @classmethod
    def protocol_name(cls):
        return "BB84"

    @staticmethod
    def theoretical_qber(noise_type, strengths):
        p = np.asarray(strengths, dtype=float)

        if noise_type == 'depolarizing':
            return p / 2.0
        return None

    def run(self):
        circuits = self._alice_prepare()

        if self.eve is not None:
            circuits, self._eve_intercepted = self.eve.intercept(circuits)

        self._bob_measure(circuits)
        return self._post_process()

    def _alice_prepare(self):
        self._alice_bits = np.random.randint(0, 2, size=self.n_qubits)
        self._alice_bases = np.random.randint(0, 2, size=self.n_qubits)

        circuits = []
        for i in range(self.n_qubits):
            qc = QuantumCircuit(1, 1)
            # bit=1: X puts qubit in |1>; basis=1: H rotates to diagonal basis {|+>,|->}
            if self._alice_bits[i] == 1:
                qc.x(0)
            if self._alice_bases[i] == 1:
                qc.h(0)
            qc.id(0)  # id is a no-op; noise model attaches depolarising error to this gate to model the quantum channel
            circuits.append(qc)

        return circuits

    def _bob_measure(self, circuits):
        self._bob_bases = np.random.randint(0, 2, size=self.n_qubits)
        self._bob_results = np.zeros(self.n_qubits, dtype=int)

        for i, qc in enumerate(circuits):
            # basis=1: H rotates diagonal basis back to computational before measuring
            if self._bob_bases[i] == 1:
                qc.h(0)
            qc.measure(0, 0)

        # shots=1: each qubit is a single physical transmission; memory=True returns the raw bit, not a count histogram
        job = self.backend.run(circuits, shots=1, memory=True)
        result = job.result()
        for i in range(len(circuits)):
            self._bob_results[i] = int(result.get_memory(i)[0])

    def _post_process(self):
        # only matching bases give a deterministic outcome; mismatched bases discard that qubit
        matching_mask = self._alice_bases == self._bob_bases
        sifted_indices = np.where(matching_mask)[0]
        sifted_key_alice = self._alice_bits[matching_mask]
        sifted_key_bob = self._bob_results[matching_mask]

        sifted_length = len(sifted_key_alice)
        if sifted_length > 0:
            errors = np.sum(sifted_key_alice != sifted_key_bob)
            qber = errors / sifted_length
        else:
            # guard: zero sifted bits means no key, QBER undefined - treated as 0 to avoid division by zero
            qber = 0.0

        key_rate = sifted_length / self.n_qubits

        return QKDResult(
            protocol_name="BB84",
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
