"""
Abstract base classes for QKD protocol implementations.

QKDResult: base result container.
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
    f_ec: float = 1.16
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
    def secure_key_rate(self) -> float:
        """Asymptotic secure key rate (Shor-Preskill bound)."""
        if self.sifted_length == 0:
            return 0.0
        h_e = self._binary_entropy(self.qber)
        secret_fraction = max(0.0, 1.0 - h_e - self.f_ec * h_e)
        return self.key_rate * secret_fraction

    @property
    def is_secure(self) -> bool:
        return self.secure_key_rate > 0


class QKDProtocol(ABC):
    """Abstract contract for all QKD protocol implementations."""

    def __init__(self, n_qubits: int, backend: AerSimulator,
                 eve: Optional[EveInterceptor] = None, f_ec: float = 1.16):
        if n_qubits < 1:
            raise ValueError(f"n_qubits must be >= 1, got {n_qubits}")
        self.n_qubits = n_qubits
        self.backend = backend
        self.eve = eve
        self.f_ec = f_ec

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

    @classmethod
    def theoretical_secure_key_rate(cls, noise_type: str, strengths: np.ndarray,
                                    f_ec: float = 1.16) -> Optional[np.ndarray]:
        """Shor-Preskill: sifting_rate * max(0, 1 - (1+f_ec)*h(e))."""
        qber = cls.theoretical_qber(noise_type, strengths)
        if qber is None:
            return None
        sifting = cls.theoretical_sifting_rate()

        def _h(x):
            x = np.clip(x, 1e-15, 1.0 - 1e-15)
            return -x * np.log2(x) - (1 - x) * np.log2(1 - x)

        return sifting * np.maximum(0.0, 1.0 - (1.0 + f_ec) * _h(qber))
