"""
Noise model setup for QKD simulation.

Noise is applied only to the 'id' gate (channel marker).
Supported: none, depolarizing
"""

from qiskit_aer import AerSimulator
from qiskit_aer.noise import (
    NoiseModel,
    depolarizing_error,
)


_NOISE_DESCRIPTIONS = {
    'none': 'Ideal Channel (No Noise)',
    'depolarizing': 'Depolarising Channel',
}


def create_backend(noise_type: str, strength: float = 0.0) -> AerSimulator:
    """Return an AerSimulator with noise applied to 'id' gates."""
    if noise_type == 'none':
        return AerSimulator()

    noise_model = NoiseModel()
    error = _create_error(noise_type, strength)
    noise_model.add_all_qubit_quantum_error(error, ['id'])

    return AerSimulator(noise_model=noise_model)


def _create_error(noise_type: str, strength: float):
    """Build the Qiskit QuantumError for the given noise type."""
    if noise_type == 'depolarizing':
        return depolarizing_error(strength, 1)
    else:
        raise ValueError(f"Unhandled noise type: {noise_type}")


def get_noise_description(noise_type: str) -> str:
    """Human-readable label for a noise model."""
    return _NOISE_DESCRIPTIONS.get(noise_type, f'Unknown ({noise_type})')
