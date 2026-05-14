"""E91 protocol"""

from dataclasses import dataclass, field
import numpy as np
from qiskit import QuantumCircuit

from ..base import QKDProtocol, QKDResult


_CLASSICAL_BOUND = 2.0
_TSIRELSON_BOUND = 2.0 * np.sqrt(2.0)


@dataclass
class E91Result(QKDResult):
    alice_angles: np.ndarray = None
    bob_angles: np.ndarray = None
    alice_outcomes: np.ndarray = None
    bob_outcomes: np.ndarray = None
    chsh_indices: np.ndarray = None
    correlations: dict = field(default_factory=dict)
    s_value: float = 0.0
    chsh_pairs_count: int = 0
    key_pairs_count: int = 0
    channel_topology: str = 'both'

    @property
    def abs_s(self):
        return abs(self.s_value)

    @property
    def chsh_violation(self):
        return self.abs_s > _CLASSICAL_BOUND


class E91Protocol(QKDProtocol):

    # Ekert 1991 angle sets: Alice uses {0, 45, 90}, Bob uses {45, 90, 135}
    ALICE_ANGLES = np.array([0.0, np.pi / 4, np.pi / 2])
    BOB_ANGLES = np.array([np.pi / 4, np.pi / 2, 3 * np.pi / 4])

    # angle pair roles from ekert 
    # 'key' pairs give anticorrelated outcomes and form the raw key
    # 'chsh' pairs are used for the bell inequality check
    _SIFT_TABLE = np.array([
        ['chsh',    'discard', 'chsh'   ],
        ['key',     'discard', 'discard'],
        ['chsh',    'key',     'chsh'   ],
    ])

    # S = E(a1,b1) - E(a1,b3) + E(a3,b1) + E(a3,b3); Ekert 1991 Table 1 - |S|>2 rules out local hidden variables
    _CHSH_S_TERMS = [
        ((0, 0), +1),
        ((0, 2), -1),
        ((2, 0), +1),
        ((2, 2), +1),
    ]

    def __init__(self, n_qubits: int, backend, eve=None, channel_topology='both'):
        super().__init__(n_qubits, backend, eve)
        self.channel_topology = channel_topology
        self._alice_angles = None
        self._bob_angles = None
        self._alice_outcomes = None
        self._bob_outcomes = None

    @classmethod
    def protocol_name(cls):
        return "E91"

    @classmethod
    def theoretical_sifting_rate(cls):
        """two of nine angle pairs are key pairs -> 2/9"""
        return 2.0 / 9.0

    @staticmethod
    def theoretical_qber(noise_type, strengths, channel_topology='both'):
        p = np.asarray(strengths, dtype=float)
        
        if noise_type == 'depolarizing': 
            if channel_topology == 'both':
                # two-sided noise: each qubit sees depolarising p independently
                return p - p ** 2 / 2.0
            elif channel_topology == 'bob':
                return p / 2.0
        return None

    def run(self):
        if self.eve is not None:
            raise NotImplementedError(
                "no E91 eavesdropper model - run with eve=None")

        circuits = self._prepare_pairs()
        self._measure(circuits)
        return self._post_process()

    def _prepare_pairs(self):
        self._alice_angles = np.random.randint(0, 3, size=self.n_qubits)
        self._bob_angles = np.random.randint(0, 3, size=self.n_qubits)

        circuits = []
        for _ in range(self.n_qubits):
            qc = QuantumCircuit(2, 2)
            # H then CX gives (|00>+|11>)/sqrt(2); X then Z on q0 flips and phases q0 to give singlet (|01>-|10>)/sqrt(2)
            qc.h(0)
            qc.cx(0, 1)
            qc.x(0)
            qc.z(0)
            qc.barrier()

            # id gates are no-ops; noise model targets them to inject depolarising error on Alice's (q0) or Bob's (q1) leg
            if self.channel_topology == 'both':
                qc.id(0)
                qc.id(1)
            else:
                qc.id(1)

            circuits.append(qc)

        return circuits

    def _measure(self, circuits):
        self._alice_outcomes = np.zeros(self.n_qubits, dtype=int)
        self._bob_outcomes = np.zeros(self.n_qubits, dtype=int)

        for i, qc in enumerate(circuits):
            a_theta = self.ALICE_ANGLES[self._alice_angles[i]]
            b_theta = self.BOB_ANGLES[self._bob_angles[i]]
            # negative Ry angle: rotates measurement axis by -theta, equivalent to measuring along the theta direction
            qc.ry(-a_theta, 0)
            qc.ry(-b_theta, 1)
            qc.measure(0, 0)
            qc.measure(1, 1)

        job = self.backend.run(circuits, shots=1, memory=True)
        result = job.result()

        # Qiskit returns bit strings in reverse qubit order: bits[-1] is q0 (Alice), bits[-2] is q1 (Bob)
        for i in range(len(circuits)):
            bits = result.get_memory(i)[0].replace(' ', '')
            self._alice_outcomes[i] = int(bits[-1])
            self._bob_outcomes[i] = int(bits[-2])

    def _post_process(self):
        sift_labels = self._SIFT_TABLE[self._alice_angles, self._bob_angles]
        key_mask = (sift_labels == 'key')
        chsh_mask = (sift_labels == 'chsh')

        sifted_indices = np.where(key_mask)[0]
        chsh_indices = np.where(chsh_mask)[0]

        sifted_key_alice = self._alice_outcomes[sifted_indices].astype(int)
        # singlet is anticorrelated: Bob's raw outcome is flipped to align with Alice's key bit
        sifted_key_bob = (1 - self._bob_outcomes[sifted_indices]).astype(int)

        sifted_length = len(sifted_key_alice)
        if sifted_length > 0:
            errors = int(np.sum(sifted_key_alice != sifted_key_bob))
            qber = errors / sifted_length
        else:
            qber = 0.0

        key_rate = sifted_length / self.n_qubits

        correlations = {}
        s_value = 0.0
        for (ai, bi), sign in self._CHSH_S_TERMS:
            sub_mask = (self._alice_angles == ai) & (self._bob_angles == bi)
            n_sub = int(np.sum(sub_mask))
            if n_sub == 0:
                print(f"E91 CHSH (a{ai+1}, b{bi+1}) empty ", f"- n_qubits={self.n_qubits} too small")
                corr = 0.0
            else:
                # CHSH uses +/-1 outcomes; map {0,1} -> {+1,-1} via 1 - 2*x before computing correlators
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
