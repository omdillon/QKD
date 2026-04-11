"""
Benchmarking tools for QKD protocol simulation.

Runs protocols across noise strength or Eve rate ranges and
aggregates QBER / key rate statistics for plotting.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Type
import numpy as np

from .base import QKDProtocol, QKDResult
from .noise import create_backend
from .eve import EveInterceptor


@dataclass
class BenchmarkData:
    """Aggregated results from a parameter sweep."""
    protocol_name: str
    parameter_name: str
    parameter_values: np.ndarray
    qber_mean: np.ndarray
    qber_std: np.ndarray
    key_rate_mean: np.ndarray
    key_rate_std: np.ndarray
    secure_key_rate_mean: np.ndarray
    secure_key_rate_std: np.ndarray
    n_trials: int
    n_qubits: int
    noise_type: str
    chsh_mean: Optional[np.ndarray] = None
    chsh_std: Optional[np.ndarray] = None


class BenchmarkRunner:
    """Runs multi-trial sweeps over noise strength or Eve interception rate."""

    def run_noise_sweep(
        self,
        protocol_class: Type[QKDProtocol],
        noise_type: str,
        strengths: np.ndarray,
        n_trials: int = 30,
        n_qubits: int = 100,
        with_eve: bool = False,
        eve_rate: float = 0.5,
        f_ec: float = 1.16,
        protocol_kwargs: Optional[Dict[str, Any]] = None,
    ) -> BenchmarkData:
        """Sweep across noise strengths, running n_trials at each point."""
        strengths = np.asarray(strengths)
        n_strengths = len(strengths)
        extra_kwargs = protocol_kwargs or {}

        qber_results = np.zeros((n_strengths, n_trials))
        key_rate_results = np.zeros((n_strengths, n_trials))
        secure_rate_results = np.zeros((n_strengths, n_trials))
        chsh_results: Optional[np.ndarray] = None

        for i, strength in enumerate(strengths):
            print(f"  {protocol_class.protocol_name()} | "
                  f"{noise_type} p={strength:.3f} [{i+1}/{n_strengths}]")

            backend = create_backend(noise_type, strength)
            eve = EveInterceptor(eve_rate) if with_eve else None

            for j in range(n_trials):
                protocol = protocol_class(
                    n_qubits=n_qubits, backend=backend, eve=eve, f_ec=f_ec,
                    **extra_kwargs,
                )
                result = protocol.run()

                qber_results[i, j] = result.qber
                key_rate_results[i, j] = result.key_rate
                secure_rate_results[i, j] = result.secure_key_rate

                s_val = getattr(result, 's_value', None)
                if s_val is not None:
                    if chsh_results is None:
                        chsh_results = np.zeros((n_strengths, n_trials))
                    chsh_results[i, j] = abs(s_val)

        chsh_mean = np.mean(chsh_results, axis=1) if chsh_results is not None else None
        chsh_std = np.std(chsh_results, axis=1) if chsh_results is not None else None

        return BenchmarkData(
            protocol_name=protocol_class.protocol_name(),
            parameter_name='noise_strength',
            parameter_values=strengths,
            qber_mean=np.mean(qber_results, axis=1),
            qber_std=np.std(qber_results, axis=1),
            key_rate_mean=np.mean(key_rate_results, axis=1),
            key_rate_std=np.std(key_rate_results, axis=1),
            secure_key_rate_mean=np.mean(secure_rate_results, axis=1),
            secure_key_rate_std=np.std(secure_rate_results, axis=1),
            n_trials=n_trials,
            n_qubits=n_qubits,
            noise_type=noise_type,
            chsh_mean=chsh_mean,
            chsh_std=chsh_std,
        )

    def run_eve_sweep(
        self,
        protocol_class: Type[QKDProtocol],
        eve_rates: np.ndarray,
        n_trials: int = 30,
        n_qubits: int = 100,
        noise_type: str = 'none',
        noise_strength: float = 0.0,
        f_ec: float = 1.16,
        protocol_kwargs: Optional[Dict[str, Any]] = None,
    ) -> BenchmarkData:
        """Sweep across Eve interception rates."""
        eve_rates = np.asarray(eve_rates)
        n_rates = len(eve_rates)
        extra_kwargs = protocol_kwargs or {}

        qber_results = np.zeros((n_rates, n_trials))
        key_rate_results = np.zeros((n_rates, n_trials))
        secure_rate_results = np.zeros((n_rates, n_trials))
        chsh_results: Optional[np.ndarray] = None

        backend = create_backend(noise_type, noise_strength)

        for i, rate in enumerate(eve_rates):
            print(f"  {protocol_class.protocol_name()} | "
                  f"Eve rate={rate:.2f} [{i+1}/{n_rates}]")

            eve = EveInterceptor(rate) if rate > 0 else None

            for j in range(n_trials):
                protocol = protocol_class(
                    n_qubits=n_qubits, backend=backend,
                    eve=eve, f_ec=f_ec, **extra_kwargs,
                )
                result = protocol.run()

                qber_results[i, j] = result.qber
                key_rate_results[i, j] = result.key_rate
                secure_rate_results[i, j] = result.secure_key_rate

                s_val = getattr(result, 's_value', None)
                if s_val is not None:
                    if chsh_results is None:
                        chsh_results = np.zeros((n_rates, n_trials))
                    chsh_results[i, j] = abs(s_val)

        chsh_mean = np.mean(chsh_results, axis=1) if chsh_results is not None else None
        chsh_std = np.std(chsh_results, axis=1) if chsh_results is not None else None

        return BenchmarkData(
            protocol_name=protocol_class.protocol_name(),
            parameter_name='eve_interception_rate',
            parameter_values=eve_rates,
            qber_mean=np.mean(qber_results, axis=1),
            qber_std=np.std(qber_results, axis=1),
            key_rate_mean=np.mean(key_rate_results, axis=1),
            key_rate_std=np.std(key_rate_results, axis=1),
            secure_key_rate_mean=np.mean(secure_rate_results, axis=1),
            secure_key_rate_std=np.std(secure_rate_results, axis=1),
            n_trials=n_trials,
            n_qubits=n_qubits,
            noise_type=noise_type,
            chsh_mean=chsh_mean,
            chsh_std=chsh_std,
        )

    def run_protocol_comparison(
        self,
        protocol_classes: List[Type[QKDProtocol]],
        noise_type: str,
        strengths: np.ndarray,
        n_trials: int = 30,
        n_qubits: int = 100,
        f_ec: float = 1.16,
        protocol_kwargs: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Dict[str, BenchmarkData]:
        """Run the same noise sweep on multiple protocols."""
        per_proto_kwargs = protocol_kwargs or {}
        results: Dict[str, BenchmarkData] = {}

        for proto_cls in protocol_classes:
            name = proto_cls.protocol_name()
            extra = {}
            for key, val in per_proto_kwargs.items():
                if key.lower() == name.lower():
                    extra = val
                    break

            print(f"\n  === {name} ===")
            results[name] = self.run_noise_sweep(
                protocol_class=proto_cls,
                noise_type=noise_type,
                strengths=strengths,
                n_trials=n_trials,
                n_qubits=n_qubits,
                with_eve=False,
                f_ec=f_ec,
                protocol_kwargs=extra,
            )

        return results
