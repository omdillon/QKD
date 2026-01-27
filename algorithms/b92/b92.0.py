import numpy as np
from art import text2art
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, depolarizing_error, pauli_error, amplitude_damping_error, phase_damping_error

# data visualisation libraries
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Tuple, List
from tqdm import tqdm  # Progress bar library

# hello test

# Console art width
global console_width
console_width = 85