"""B92 protocol. The identity gate (qc.id) marks where channel noise is applied."""

from dataclasses import dataclass
from typing import Optional, List
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from ..base import QKDProtocol, QKDResult
from ..eve import EveInterceptor


@dataclass
class B92Result(QKDResult):
    bob_bases: np.ndarray = None
    conclusive_mask: np.ndarray = None


class B92Protocol(QKDProtocol):

    def __init__(self, n_qubits: int, backend: AerSimulator,
                 eve: Optional[EveInterceptor] = None):
        super().__init__(n_qubits, backend, eve)
        self._alice_bits = None
        self._bob_bases = None
        self._bob_results = None
        self._eve_intercepted = None

    @classmethod
    def protocol_name(cls) -> str:
        return "B92"

    @classmethod
    def theoretical_sifting_rate(cls) -> float:
        return 0.25

    @staticmethod
    def theoretical_qber(noise_type: str, strengths: np.ndarray) -> Optional[np.ndarray]:
        """B92 QBER: noise creates spurious outcome-1 events, giving p/(1+p)."""
        if noise_type == 'depolarizing':
            p = np.asarray(strengths, dtype=float)
            return p / (1.0 + p)
        return None

    def run(self) -> B92Result:
        circuits = self._alice_prepare()

        if self.eve is not None:
            circuits, self._eve_intercepted = self.eve.intercept_b92(circuits)

        self._bob_measure(circuits)
        return self._post_process()

    def _alice_prepare(self) -> List[QuantumCircuit]:
        self._alice_bits = np.random.randint(0, 2, size=self.n_qubits)

        circuits = []
        for i in range(self.n_qubits):
            qc = QuantumCircuit(1, 1)
            if self._alice_bits[i] == 1:
                qc.h(0)
            qc.id(0)  # channel marker
            circuits.append(qc)

        return circuits

    def _bob_measure(self, circuits: List[QuantumCircuit]) -> None:
        self._bob_bases = np.random.randint(0, 2, size=self.n_qubits)
        self._bob_results = np.zeros(self.n_qubits, dtype=int)

        for i, qc in enumerate(circuits):
            if self._bob_bases[i] == 1:
                qc.h(0)
            qc.measure(0, 0)

        job = self.backend.run(circuits, shots=1, memory=True)
        result = job.result()
        for i in range(len(circuits)):
            self._bob_results[i] = int(result.get_memory(i)[0])

    def _post_process(self) -> B92Result:
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
