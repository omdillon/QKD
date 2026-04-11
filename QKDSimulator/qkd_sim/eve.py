"""
Eve eavesdropper - intercept-resend attack.

Eve intercepts qubits mid-flight, measures in a random basis, then
re-sends fresh qubits encoding her result. Wrong basis guesses (~50%)
introduce a detectable ~25% QBER at full interception rate.
"""

from typing import List, Tuple
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


class EveInterceptor:
    """Intercept-resend eavesdropper with configurable interception rate."""

    def __init__(self, interception_rate: float = 0.5):
        self.interception_rate = interception_rate
        self._eve_backend = AerSimulator()

    def intercept(self, circuits: List[QuantumCircuit]) -> Tuple[List[QuantumCircuit], np.ndarray]:
        """
        Apply intercept-resend to Alice's qubit stream.

        1. Decide which qubits to intercept and build measurement circuits.
        2. Batch-execute all measurements in a single simulator call.
        3. Build replacement circuits from measurement results.
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
            job = self._eve_backend.run(measure_circuits, shots=1, memory=True)
            result = job.result()

            for idx, (orig_i, eve_basis) in enumerate(
                zip(intercepted_indices, eve_bases)
            ):
                eve_result = int(result.get_memory(idx)[0])
                output_circuits[orig_i] = self._prepare_replacement(
                    eve_result, eve_basis)

        return output_circuits, np.array(intercepted_indices, dtype=int)

    def _prepare_replacement(self, bit_value: int, basis: int) -> QuantumCircuit:
        """Build a fresh qubit encoding Eve's result in the same basis."""
        new_qc = QuantumCircuit(1, 1)
        if bit_value == 1:
            new_qc.x(0)
        if basis == 1:
            new_qc.h(0)
        new_qc.id(0)  # channel marker for Eve->Bob noise
        return new_qc
