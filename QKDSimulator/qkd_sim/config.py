"""
YAML configuration loader for QKD simulations.

Reads a flat YAML file into a SimConfig dataclass.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import yaml


_VALID_MODES = {'single', 'sweep', 'eve_sweep', 'protocol_comparison',
                'eve_comparison', 'surface_sweep'}


@dataclass
class SimConfig:
    """Simulation configuration loaded from YAML."""
    mode: str = "single"
    protocol: str = "bb84"
    protocols: Optional[List[str]] = None
    n_qubits: int = 256
    n_trials: int = 30
    noise_type: str = "none"
    noise_strength: float = 0.0
    noise_min: float = 0.0
    noise_max: float = 0.30
    noise_steps: int = 21
    eve_rate: Optional[float] = None
    eve_min: float = 0.0
    eve_max: float = 1.0
    eve_steps: int = 11
    e91_channel_topology: str = "both"
    output_dir: str = "./results"
    save_plots: bool = True
    show_plots: bool = False


def load_config(path: str) -> SimConfig:
    """Read a YAML file and return a SimConfig."""
    with open(path, 'r') as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"Empty config file: {path}")

    config = SimConfig(**{k: v for k, v in raw.items()
                          if hasattr(SimConfig, k)})

    if config.mode not in _VALID_MODES:
        raise ValueError(
            f"Invalid mode '{config.mode}'. "
            f"Must be one of: {sorted(_VALID_MODES)}"
        )

    return config
