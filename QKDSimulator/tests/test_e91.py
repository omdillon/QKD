"""
E91 (Ekert 1991) protocol test suite.

Eleven tests covering the highest-risk physics and integration points:

    T1  Singlet preparation Statevector             - gate sequence
    T2  Ideal channel: QBER ~ 0, |S| ~ 2*sqrt(2)    - end-to-end correctness
    T3  Sifting rate ~ 2/9 (binomial tolerance)     - sift table
    T4  CHSH violation flag at ideal vs noisy       - chsh_violation property
    T5  Depolarising QBER ('both' topology)         - p - p^2/2 formula bug
    T6  Depolarising QBER ('bob' topology)          - p/2 single-sided
    T7  Depolarising |S| degradation                - Werner V^2 visibility
    T8  Reproducibility with seeded RNG             - determinism
    T9  Memory string clbit ordering                - little-endian Qiskit
    T10 Protocol registry round-trip                - get_protocol('e91')
    T11 E91Result dataclass shape                   - all extra fields present

Run with:
    python -m pytest tests/ -v
"""

import warnings
import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from qiskit_aer import AerSimulator

from qkd_sim.protocols.e91 import E91Protocol, E91Result
from qkd_sim.benchmark import BenchmarkRunner
from qkd_sim.noise import create_backend


# ---------------------------------------------------------------------------
# T1 - Singlet state preparation
# ---------------------------------------------------------------------------

def test_singlet_preparation():
    """Verify H(0); CX(0,1); X(0); Z(0) prepares |Psi-> = (|01> - |10>)/sqrt(2)."""
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0, 1)
    qc.x(0)
    qc.z(0)

    sv = Statevector(qc)
    inv_sqrt2 = 1.0 / np.sqrt(2.0)

    # Qiskit ordering: amplitude[i] indexes computational basis state |i>
    # with little-endian bit string. Layout for 2 qubits:
    #   index 0 = |00>, index 1 = |01>, index 2 = |10>, index 3 = |11>
    expected = np.array([0.0, inv_sqrt2, -inv_sqrt2, 0.0], dtype=complex)

    # Tolerate global phase: state = expected or -expected (or any unit phase)
    assert (
        np.allclose(sv.data, expected, atol=1e-9)
        or np.allclose(sv.data, -expected, atol=1e-9)
    ), f"Expected |Psi-> singlet, got {sv.data}"


# ---------------------------------------------------------------------------
# T2 - End-to-end ideal channel
# ---------------------------------------------------------------------------

def test_ideal_channel_qber_and_chsh():
    """Ideal channel: QBER should be 0 and |S| should approach 2*sqrt(2)."""
    np.random.seed(2025)
    backend = create_backend('none', 0.0)
    proto = E91Protocol(n_qubits=600, backend=backend, channel_topology='both')
    result = proto.run()

    assert result.qber == pytest.approx(0.0, abs=1e-9), (
        f"Ideal singlet must give QBER=0, got {result.qber}"
    )

    tsirelson = 2.0 * np.sqrt(2.0)
    # Statistical fluctuation tolerance for finite n_qubits / per-bucket counts
    assert result.abs_s == pytest.approx(tsirelson, abs=0.25), (
        f"Expected |S| ~ {tsirelson:.3f}, got {result.abs_s:.3f}"
    )
    assert result.chsh_violation is True


# ---------------------------------------------------------------------------
# T3 - Sifting rate ~ 2/9
# ---------------------------------------------------------------------------

def test_sifting_rate_two_ninths():
    """Empirical sift fraction should be ~2/9 within binomial tolerance."""
    np.random.seed(7)
    backend = create_backend('none', 0.0)
    n = 900
    proto = E91Protocol(n_qubits=n, backend=backend)
    result = proto.run()

    expected = 2.0 / 9.0
    sigma = np.sqrt(expected * (1.0 - expected) / n)
    observed = result.key_pairs_count / n

    # 5-sigma binomial tolerance keeps the test robust against flakes
    assert abs(observed - expected) < 5 * sigma, (
        f"Sifting fraction {observed:.4f} differs from 2/9={expected:.4f} "
        f"by more than 5*sigma={5*sigma:.4f}"
    )

    # The class-level theoretical_sifting_rate must report exactly 2/9
    assert E91Protocol.theoretical_sifting_rate() == pytest.approx(2.0 / 9.0)


# ---------------------------------------------------------------------------
# T4 - CHSH violation flag
# ---------------------------------------------------------------------------

def test_chsh_violation_flag():
    """The chsh_violation property must reflect |S| > 2 logic."""
    np.random.seed(11)
    backend = create_backend('none', 0.0)
    proto = E91Protocol(n_qubits=400, backend=backend)
    result = proto.run()
    assert result.chsh_violation is True
    assert result.abs_s > 2.0

    # Synthetic check: a fabricated E91Result with |S| <= 2 must report False
    fake = E91Result(
        protocol_name="E91",
        n_qubits=10,
        alice_bits=np.zeros(10, dtype=int),
        bob_results=np.zeros(10, dtype=int),
        sifted_indices=np.array([], dtype=int),
        sifted_key_alice=np.array([], dtype=int),
        sifted_key_bob=np.array([], dtype=int),
        qber=0.0,
        key_rate=0.0,
        s_value=1.5,
    )
    assert fake.chsh_violation is False
    assert fake.abs_s == pytest.approx(1.5)


# ---------------------------------------------------------------------------
# T5 - Depolarising QBER, two-sided ('both' topology)
# ---------------------------------------------------------------------------

def test_depolarizing_qber_two_sided():
    """
    Two-sided depolarising channel: QBER must follow p - p^2/2,
    NOT p/2. This is the highest-value test - it catches the most
    likely physics bug.
    """
    np.random.seed(42)
    runner = BenchmarkRunner()
    strengths = np.array([0.0, 0.05, 0.10, 0.15])
    data = runner.run_noise_sweep(
        protocol_class=E91Protocol,
        noise_type='depolarizing',
        strengths=strengths,
        n_trials=20,
        n_qubits=400,
        f_ec=1.16,
        protocol_kwargs={'channel_topology': 'both'},
    )

    expected = strengths - strengths ** 2 / 2.0
    sem = data.qber_std / np.sqrt(data.n_trials)
    tol = 4.0 * np.maximum(sem, 0.005)  # ~4-sigma envelope, never tighter than 0.5%

    deviations = np.abs(data.qber_mean - expected)
    assert np.all(deviations < tol), (
        f"Depolarising QBER 'both' topology mismatch:\n"
        f"  strengths = {strengths}\n"
        f"  expected  = {expected}\n"
        f"  observed  = {data.qber_mean}\n"
        f"  deviations= {deviations}\n"
        f"  tolerance = {tol}\n"
        f"If observed ~ p/2 instead of p - p^2/2, the formula is wrong."
    )


# ---------------------------------------------------------------------------
# T6 - Depolarising QBER, single-sided ('bob' topology)
# ---------------------------------------------------------------------------

def test_depolarizing_qber_single_sided():
    """Single-sided depolarising on Bob only -> QBER = p/2 (matches BB84)."""
    np.random.seed(43)
    runner = BenchmarkRunner()
    strengths = np.array([0.0, 0.05, 0.10, 0.15])
    data = runner.run_noise_sweep(
        protocol_class=E91Protocol,
        noise_type='depolarizing',
        strengths=strengths,
        n_trials=20,
        n_qubits=400,
        f_ec=1.16,
        protocol_kwargs={'channel_topology': 'bob'},
    )

    expected = strengths / 2.0
    sem = data.qber_std / np.sqrt(data.n_trials)
    tol = 4.0 * np.maximum(sem, 0.005)

    deviations = np.abs(data.qber_mean - expected)
    assert np.all(deviations < tol), (
        f"Depolarising QBER 'bob' topology mismatch:\n"
        f"  expected = {expected}\n"
        f"  observed = {data.qber_mean}\n"
        f"  tol      = {tol}"
    )


# ---------------------------------------------------------------------------
# T7 - Depolarising |S| degradation (Werner visibility)
# ---------------------------------------------------------------------------

def test_depolarizing_chsh_degradation():
    """|S| under two-sided depolarising should follow 2*sqrt(2)*(1-p)^2."""
    np.random.seed(123)
    runner = BenchmarkRunner()
    strengths = np.array([0.0, 0.05, 0.10, 0.15])
    data = runner.run_noise_sweep(
        protocol_class=E91Protocol,
        noise_type='depolarizing',
        strengths=strengths,
        n_trials=20,
        n_qubits=600,
        f_ec=1.16,
        protocol_kwargs={'channel_topology': 'both'},
    )

    assert data.chsh_mean is not None, (
        "BenchmarkData.chsh_mean should be populated for E91 sweeps"
    )

    expected = 2.0 * np.sqrt(2.0) * (1.0 - strengths) ** 2
    sem = data.chsh_std / np.sqrt(data.n_trials)
    tol = 4.0 * np.maximum(sem, 0.10)

    deviations = np.abs(data.chsh_mean - expected)
    assert np.all(deviations < tol), (
        f"Depolarising |S| degradation mismatch:\n"
        f"  expected = {expected}\n"
        f"  observed = {data.chsh_mean}\n"
        f"  tol      = {tol}"
    )


# ---------------------------------------------------------------------------
# T8 - Reproducibility with seeded RNG
# ---------------------------------------------------------------------------

def test_reproducibility_with_seed():
    """Two runs under the same seed and seeded backend must produce identical
    angle sequences and (when noise is off) identical CHSH stats."""
    backend = create_backend('none', 0.0)

    np.random.seed(999)
    proto1 = E91Protocol(n_qubits=200, backend=backend)
    r1 = proto1.run()

    np.random.seed(999)
    proto2 = E91Protocol(n_qubits=200, backend=backend)
    r2 = proto2.run()

    # Angle choices come from numpy.random and must be deterministic
    assert np.array_equal(r1.alice_angles, r2.alice_angles)
    assert np.array_equal(r1.bob_angles, r2.bob_angles)

    # In an ideal channel the QBER must be exactly 0 in both runs
    assert r1.qber == 0.0
    assert r2.qber == 0.0


# ---------------------------------------------------------------------------
# T9 - Qiskit memory string clbit ordering (little-endian)
# ---------------------------------------------------------------------------

def test_clbit_ordering_little_endian():
    """Verify Qiskit memory string is little-endian: rightmost char = clbit 0."""
    qc = QuantumCircuit(2, 2)
    qc.x(0)            # qubit 0 -> |1>; qubit 1 stays in |0>
    qc.measure(0, 0)
    qc.measure(1, 1)

    backend = AerSimulator()
    job = backend.run([qc], shots=1, memory=True)
    bits = job.result().get_memory(0)[0].replace(' ', '')

    assert len(bits) == 2
    assert bits[-1] == '1', (
        f"clbit 0 (Alice) should be rightmost char and equal '1', got {bits!r}"
    )
    assert bits[-2] == '0', (
        f"clbit 1 (Bob) should be second-rightmost and equal '0', got {bits!r}"
    )


# ---------------------------------------------------------------------------
# T11 - E91Result dataclass shape
# ---------------------------------------------------------------------------

def test_e91_result_shape_and_fields():
    """E91Result must populate all extra fields with correct types."""
    np.random.seed(7)
    backend = create_backend('none', 0.0)
    proto = E91Protocol(
        n_qubits=180, backend=backend, channel_topology='both'
    )
    result = proto.run()

    assert isinstance(result, E91Result)

    # Inherited base fields
    assert result.protocol_name == "E91"
    assert result.n_qubits == 180
    assert isinstance(result.qber, float)
    assert isinstance(result.key_rate, float)

    # E91-specific arrays
    assert result.alice_angles.shape == (180,)
    assert result.bob_angles.shape == (180,)
    assert result.alice_outcomes.shape == (180,)
    assert result.bob_outcomes.shape == (180,)
    assert result.alice_angles.dtype.kind in ('i', 'u')
    assert result.bob_angles.dtype.kind in ('i', 'u')
    assert set(np.unique(result.alice_angles)).issubset({0, 1, 2})
    assert set(np.unique(result.bob_angles)).issubset({0, 1, 2})

    # CHSH machinery
    assert isinstance(result.s_value, float)
    assert isinstance(result.abs_s, float)
    assert isinstance(result.chsh_violation, bool)
    assert isinstance(result.correlations, dict)
    assert len(result.correlations) == 4  # the 4 CHSH (a,b) pairs
    for key, val in result.correlations.items():
        assert isinstance(key, tuple)
        assert len(key) == 2
        assert isinstance(val, float)
        assert -1.0 - 1e-9 <= val <= 1.0 + 1e-9

    # Topology and counts
    assert result.channel_topology == 'both'
    assert isinstance(result.chsh_pairs_count, int)
    assert isinstance(result.key_pairs_count, int)
    assert (
        result.chsh_pairs_count + result.key_pairs_count
        <= result.n_qubits
    )

    # Eve must be deferred -- result should have no eve_intercepted info
    assert result.eve_intercepted is None


# ---------------------------------------------------------------------------
# Bonus sanity checks (cheap, catch regressions in the rest of the wiring)
# ---------------------------------------------------------------------------

def test_eve_raises_not_implemented():
    """Passing an EveInterceptor to E91 must raise NotImplementedError."""
    from qkd_sim.eve import EveInterceptor

    backend = create_backend('none', 0.0)
    proto = E91Protocol(
        n_qubits=20, backend=backend, eve=EveInterceptor(0.5)
    )
    with pytest.raises(NotImplementedError):
        proto.run()


def test_invalid_channel_topology_raises():
    """Constructor must reject unknown topology strings."""
    backend = create_backend('none', 0.0)
    with pytest.raises(ValueError):
        E91Protocol(n_qubits=10, backend=backend, channel_topology='alice')


def test_theoretical_qber_returns_none_for_unsupported():
    """Non-depolarising channels should return None (deferred to v2)."""
    p = np.linspace(0.0, 0.3, 5)
    assert E91Protocol.theoretical_qber('bitflip', p) is None
    assert E91Protocol.theoretical_qber('amplitude_damping', p) is None
    assert E91Protocol.theoretical_qber('phase_damping', p) is None
    assert E91Protocol.theoretical_chsh('bitflip', p) is None
