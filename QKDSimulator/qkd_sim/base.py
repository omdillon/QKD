"""
Abstract base classes for QKD protocol implementations.

QKDResult: base result container exposing Shannon mutual information I(A;B)
per transmitted qubit as the protocol-agnostic performance metric.
QKDProtocol: abstract contract all protocols inherit from.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import numpy as np
from qiskit_aer import AerSimulator

from .eve import EveInterceptor


@dataclass
class QKDResult:
    """Base result container for any QKD protocol run."""
    protocol_name: str
    n_qubits: int
    alice_bits: np.ndarray
    bob_results: np.ndarray
    sifted_indices: np.ndarray
    sifted_key_alice: np.ndarray
    sifted_key_bob: np.ndarray
    qber: float
    key_rate: float
    eve_intercepted: Optional[np.ndarray] = None

    @property
    def sifted_length(self) -> int:
        return len(self.sifted_key_alice)

    @property
    def error_count(self) -> int:
        return int(np.sum(self.sifted_key_alice != self.sifted_key_bob))

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

    @property
    def eve_information(self) -> float:
        """Eve's accessible information I(A;E) per transmitted qubit."""
        if self.protocol_name == "BB84":
            return self.key_rate * self._binary_entropy(self.qber)
        elif self.protocol_name == "B92":
            denominator = 1.0 - (1.0 / np.sqrt(2.0))
            return self.key_rate * self._binary_entropy(self.qber / denominator)
        elif self.protocol_name == "E91":
            s_val = getattr(self, 'abs_s', 0.0)
            penalty_term = (1.0 + np.sqrt(max(0.0, (s_val / 2.0) ** 2 - 1.0))) / 2.0
            return self.key_rate * self._binary_entropy(penalty_term)
        return 0.0

    @property
    def secure_key_rate(self) -> float:
        """Devetak-Winter secure key rate: K = I(A;B) - I(A;E)."""
        if self.sifted_length == 0:
            return 0.0

        i_ab = self.mutual_information

        if self.protocol_name == "BB84":
            if self.qber >= 0.110:
                return 0.0
            i_ae = self.key_rate * self._binary_entropy(self.qber)

        elif self.protocol_name == "B92":
            if self.qber >= 0.065:
                return 0.0
            # USD attack penalty; states separated by 45°, overlap = 1/√2
            denominator = 1.0 - (1.0 / np.sqrt(2.0))
            i_ae = self.key_rate * self._binary_entropy(self.qber / denominator)

        elif self.protocol_name == "E91":
            s_val = getattr(self, 'abs_s', 0.0)
            if s_val <= 2.0:
                return 0.0
            penalty_term = (1.0 + np.sqrt(max(0.0, (s_val / 2.0) ** 2 - 1.0))) / 2.0
            i_ae = self.key_rate * self._binary_entropy(penalty_term)

        else:
            return 0.0

        return max(0.0, i_ab - i_ae)


class QKDProtocol(ABC):
    """Abstract contract for all QKD protocol implementations."""

    def __init__(self, n_qubits: int, backend: AerSimulator,
                 eve: Optional[EveInterceptor] = None):
        if n_qubits < 1:
            raise ValueError(f"n_qubits must be >= 1, got {n_qubits}")
        self.n_qubits = n_qubits
        self.backend = backend
        self.eve = eve

    @abstractmethod
    def run(self) -> QKDResult:
        ...

    @classmethod
    @abstractmethod
    def protocol_name(cls) -> str:
        ...

    @classmethod
    def theoretical_sifting_rate(cls) -> float:
        """BB84 default = 0.5. B92 overrides to 0.25."""
        return 0.5

    @staticmethod
    def theoretical_qber(noise_type: str, strengths: np.ndarray) -> Optional[np.ndarray]:
        return None
