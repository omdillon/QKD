"""noise model instantiation"""

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
    if noise_type == 'none':
        return AerSimulator()

    noise_model = NoiseModel()
    error = _create_error(noise_type, strength)
    noise_model.add_all_qubit_quantum_error(error, ['id'])

    return AerSimulator(noise_model=noise_model)


def _create_error(noise_type: str, strength: float):
    if noise_type == 'depolarizing':
        return depolarizing_error(strength, 1)


def get_noise_description(noise_type: str) -> str:
    return _NOISE_DESCRIPTIONS.get(noise_type, 'undefined noise type')
