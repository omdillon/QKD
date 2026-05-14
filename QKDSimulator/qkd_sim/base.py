"""base classes for the protocols/results"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class QKDResult:
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
    def sifted_length(self):
        return len(self.sifted_key_alice)

    @property
    def error_count(self):
        return int(np.sum(self.sifted_key_alice != self.sifted_key_bob))

    @staticmethod
    def _binary_entropy(x):
        # avoid log2(0)
        if x <= 0.0 or x >= 1.0:
            return 0.0
        return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

    @property
    def mutual_information(self):
        # I(A;B) = sifting_rate * (1 - h(QBER))
        if self.sifted_length == 0:
            return 0.0
        h_e = self._binary_entropy(self.qber)
        return self.key_rate * (1.0 - h_e)

    @property
    def eve_information(self):
        if self.protocol_name == "BB84":
            return self.key_rate * self._binary_entropy(self.qber)
        elif self.protocol_name == "B92":
            # denominator = 1 - 1/sqrt(2); state overlap of |0> and |+> sets the USD discrimination bound
            denominator = 1.0 - (1.0 / np.sqrt(2.0))
            return self.key_rate * self._binary_entropy(self.qber / denominator)
        elif self.protocol_name == "E91":
            s_val = getattr(self, 'abs_s', 0.0)
            # Acin 2007 penalty maps CHSH value S to Eve's information bound
            penalty_term = (1.0 + np.sqrt(max(0.0, (s_val / 2.0) ** 2 - 1.0))) / 2.0
            return self.key_rate * self._binary_entropy(penalty_term)
        return 0.0

    @property
    def secure_key_rate(self):
        # Devetak-Winter bound: K = I(A;B) - I(A;E)
        # threshold values from each protocol's security proof
        if self.sifted_length == 0:
            return 0.0

        i_ab = self.mutual_information

        if self.protocol_name == "BB84":
            if self.qber >= 0.110:  # Shor & Preskill 2000; BB84 is insecure above 11% QBER under collective attacks
                return 0.0
            i_ae = self.key_rate * self._binary_entropy(self.qber)

        elif self.protocol_name == "B92":
            if self.qber >= 0.065:  # Matsumoto 2013 depolarising tolerance; B92 security cap under USD attack
                return 0.0
            # implemented for an optimal USD attack
            denominator = 1.0 - (1.0 / np.sqrt(2.0))
            i_ae = self.key_rate * self._binary_entropy(self.qber / denominator)

        elif self.protocol_name == "E91":
            s_val = getattr(self, 'abs_s', 0.0)
            if s_val <= 2.0:
                return 0.0
            # Acin 2007 device-independent bound on Eve's information via CHSH
            penalty_term = (1.0 + np.sqrt(max(0.0, (s_val / 2.0) ** 2 - 1.0))) / 2.0
            i_ae = self.key_rate * self._binary_entropy(penalty_term)

        else:
            return 0.0

        return max(0.0, i_ab - i_ae)


class QKDProtocol(ABC):
    # abstract base class
    # executed before instantiation

    def __init__(self, n_qubits: int, backend, eve=None):
        self.n_qubits = n_qubits
        self.backend = backend
        self.eve = eve

    @abstractmethod
    def run(self):
        ...

    @classmethod
    @abstractmethod
    def protocol_name(cls):
        ...

    @classmethod
    def theoretical_sifting_rate(cls):
        """BB84 default = 0.5, B92 overrides to 0.25, E91 overrides to 2/9"""
        return 0.5

    @staticmethod
    def theoretical_qber(noise_type, strengths):
        return None
