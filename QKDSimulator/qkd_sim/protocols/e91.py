"""
E91 (Ekert 1991) protocol implementation.

Entanglement-based QKD using singlet states and CHSH inequality.
Alice and Bob each receive one half of an EPR pair and choose one
of three measurement angles in the XZ-plane.

Singlet: |Psi-> = (|01> - |10>) / sqrt(2)

Measurement angles (Ekert 1991):
    Alice: a1=0, a2=pi/4, a3=pi/2
    Bob:   b1=pi/4, b2=pi/2, b3=3pi/4

Channel topology:
    'both': noise on both qubits independently (V^2 = (1-p)^2)
    'bob':  noise on Bob's qubit only (V = 1-p, matches BB84)
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
import warnings
import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from ..base import QKDProtocol, QKDResult
from ..eve import EveInterceptor



_CLASSICAL_BOUND = 2.0
_TSIRELSON_BOUND = 2.0 * np.sqrt(2.0)


@dataclass
class E91Result(QKDResult):
    """E91-specific result with CHSH data."""
    alice_angles: np.ndarray = None
    bob_angles: np.ndarray = None
    alice_outcomes: np.ndarray = None
    bob_outcomes: np.ndarray = None
    chsh_indices: np.ndarray = None
    correlations: Dict[Tuple[int, int], float] = field(default_factory=dict)
    s_value: float = 0.0
    chsh_pairs_count: int = 0
    key_pairs_count: int = 0
    channel_topology: str = 'both'

    @property
    def abs_s(self) -> float:
        return abs(self.s_value)

    @property
    def chsh_violation(self) -> bool:
        return self.abs_s > _CLASSICAL_BOUND


class E91Protocol(QKDProtocol):
    """
    Runs the complete E91 protocol.

    Two-qubit entangled circuits per round, three measurement angles
    per party, sifting by angle-pair lookup table, CHSH parameter
    as a security indicator.
    """

    ALICE_ANGLES = np.array([0.0, np.pi / 4, np.pi / 2])
    BOB_ANGLES = np.array([np.pi / 4, np.pi / 2, 3 * np.pi / 4])

    # Sifting lookup: [alice_angle_idx, bob_angle_idx]
    _SIFT_TABLE = np.array([
        ['chsh',    'discard', 'chsh'   ],
        ['key',     'discard', 'discard'],
        ['chsh',    'key',     'chsh'   ],
    ])

    # S = +E(a1,b1) - E(a1,b3) + E(a3,b1) + E(a3,b3)
    _CHSH_S_TERMS: List[Tuple[Tuple[int, int], int]] = [
        ((0, 0), +1),
        ((0, 2), -1),
        ((2, 0), +1),
        ((2, 2), +1),
    ]

    _VALID_TOPOLOGIES = ('both', 'bob')

    def __init__(self, n_qubits: int, backend: AerSimulator,
                 eve: Optional[EveInterceptor] = None,
                 channel_topology: str = 'both'):
        super().__init__(n_qubits, backend, eve)
        if channel_topology not in self._VALID_TOPOLOGIES:
            raise ValueError(
                f"channel_topology must be one of {self._VALID_TOPOLOGIES}, "
                f"got {channel_topology!r}")
        self.channel_topology = channel_topology
        self._alice_angles = None
        self._bob_angles = None
        self._alice_outcomes = None
        self._bob_outcomes = None

    @classmethod
    def protocol_name(cls) -> str:
        return "E91"

    @classmethod
    def theoretical_sifting_rate(cls) -> float:
        """Two of nine angle pairs are key pairs -> 2/9."""
        return 2.0 / 9.0

    @staticmethod
    def theoretical_qber(noise_type: str, strengths: np.ndarray,
                         channel_topology: str = 'both') -> Optional[np.ndarray]:
        """Analytical QBER for E91 under depolarising noise."""
        p = np.asarray(strengths, dtype=float)
        if noise_type == 'depolarizing':
            if channel_topology == 'both':
                return p - p ** 2 / 2.0
            elif channel_topology == 'bob':
                return p / 2.0
        return None

    def run(self) -> E91Result:
        """Run the full E91 protocol."""
        if self.eve is not None:
            raise NotImplementedError(
                "E91 eavesdropper model not yet supported. Run with eve=None.")

        circuits = self._prepare_pairs()
        self._measure(circuits)
        return self._post_process()

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

    def _measure(self, circuits: List[QuantumCircuit]) -> None:
        """Apply measurement rotations and batch-execute."""
        self._alice_outcomes = np.zeros(self.n_qubits, dtype=int)
        self._bob_outcomes = np.zeros(self.n_qubits, dtype=int)

        for i, qc in enumerate(circuits):
            a_theta = self.ALICE_ANGLES[self._alice_angles[i]]
            b_theta = self.BOB_ANGLES[self._bob_angles[i]]
            qc.ry(-a_theta, 0)
            qc.ry(-b_theta, 1)
            qc.measure(0, 0)
            qc.measure(1, 1)

        job = self.backend.run(circuits, shots=1, memory=True)
        result = job.result()

        for i in range(len(circuits)):
            bits = result.get_memory(i)[0].replace(' ', '')
            self._alice_outcomes[i] = int(bits[-1])
            self._bob_outcomes[i] = int(bits[-2])

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
