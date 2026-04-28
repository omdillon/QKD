"""Intercept-resend eavesdropper. At full interception, detectable ~25% QBER."""

from typing import List, Tuple
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


class EveInterceptor:

    def __init__(self, interception_rate: float = 0.5):
        self.interception_rate = interception_rate
        self._eve_backend = AerSimulator()

    def intercept(self, circuits: List[QuantumCircuit]) -> Tuple[List[QuantumCircuit], np.ndarray]:
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
            job = self._eve_backend.run(measure_circuits, shots=1, memory=True)
            result = job.result()

            for idx, (orig_i, eve_basis) in enumerate(
                zip(intercepted_indices, eve_bases)
            ):
                eve_result = int(result.get_memory(idx)[0])
                output_circuits[orig_i] = self._prepare_replacement(
                    eve_result, eve_basis)

        return output_circuits, np.array(intercepted_indices, dtype=int)

    def intercept_b92(self, circuits: List[QuantumCircuit]) -> Tuple[List[QuantumCircuit], np.ndarray]:
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
            job = self._eve_backend.run(measure_circuits, shots=1, memory=True)
            result = job.result()

            for idx, orig_i in enumerate(intercepted_indices):
                eve_result = int(result.get_memory(idx)[0])
                # Re-prepare using B92 encoding: 0 -> |0>, 1 -> |+>
                new_qc = QuantumCircuit(1, 1)
                if eve_result == 1:
                    new_qc.h(0)
                new_qc.id(0)
                output_circuits[orig_i] = new_qc

        return output_circuits, np.array(intercepted_indices, dtype=int)

    def _prepare_replacement(self, bit_value: int, basis: int) -> QuantumCircuit:
        new_qc = QuantumCircuit(1, 1)
        if bit_value == 1:
            new_qc.x(0)
        if basis == 1:
            new_qc.h(0)
        new_qc.id(0)  # channel marker for Eve->Bob noise
        return new_qc
