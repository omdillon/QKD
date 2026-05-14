"""benchmarking tools the simulation"""

import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from typing import Optional
import numpy as np
from tqdm import tqdm

from .base import QKDProtocol, QKDResult
from .noise import create_backend
from .eve import EveInterceptor


@dataclass
class BenchmarkData:
    protocol_name: str
    parameter_name: str
    parameter_values: np.ndarray
    qber_mean: np.ndarray
    qber_std: np.ndarray
    key_rate_mean: np.ndarray
    key_rate_std: np.ndarray
    mutual_info_mean: np.ndarray
    mutual_info_std: np.ndarray
    n_trials: int
    n_qubits: int
    noise_type: str
    chsh_mean: Optional[np.ndarray] = None
    chsh_std: Optional[np.ndarray] = None
    secure_rate_mean: Optional[np.ndarray] = None
    secure_rate_std: Optional[np.ndarray] = None


@dataclass
class SurfaceBenchmarkData:
    protocol_name: str
    noise_strengths: np.ndarray # strucure: (S,)
    eve_rates: np.ndarray # strucure: (E,)
    qber_mean: np.ndarray # strucure: shape (S, E)
    qber_std: np.ndarray # strucure: (S, E)
    n_trials: int
    n_qubits: int
    noise_type: str
    iab_mean: Optional[np.ndarray] = None   # strucure: (S, E) - I(A;B) per qubit
    iae_mean: Optional[np.ndarray] = None   # strucure: (S, E) - I(A;E) per qubit
    skr_mean: Optional[np.ndarray] = None   # strucure: (S, E) - SKR per qubit


# needed to be module-level for the parallel core execution - PicklingError when inside the class
# windows multiprocessing couldnt pickle class methods

def _surface_cell_worker(args):
    # runs one (noise_strength, eve_rate) combination for n_trials -> returns QBER list
    protocol_class, noise_type, strength, rate, n_trials, n_qubits = args
    backend = create_backend(noise_type, strength)
    eve = EveInterceptor(rate) if rate > 0 else None
    return [ 
        protocol_class(n_qubits=n_qubits, backend=backend, eve=eve).run().qber
        for _ in range(n_trials)
    ]


def _surface_cell_worker_v4(args):
    # same as above but also collects mutual info and SKR per trial for the v4/v5 surface plots
    protocol_class, noise_type, strength, rate, n_trials, n_qubits = args
    backend = create_backend(noise_type, strength)
    eve = EveInterceptor(rate) if rate > 0 else None
    results = []
    for _ in range(n_trials):
        r = protocol_class(n_qubits=n_qubits, backend=backend, eve=eve).run()
        results.append((r.qber, r.mutual_information, r.eve_information, r.secure_key_rate))
    return results


class BenchmarkRunner:

    def run_noise_sweep(
        self,
        protocol_class,
        noise_type: str,
        strengths: np.ndarray,
        n_trials: int = 30,
        n_qubits: int = 100,
        with_eve: bool = False,
        eve_rate: float = 0.5,
        protocol_kwargs: Optional[dict] = None,
    ) -> BenchmarkData:
        strengths = np.asarray(strengths)
        n_strengths = len(strengths)
        extra_kwargs = protocol_kwargs or {}

        qber_results = np.zeros((n_strengths, n_trials))
        key_rate_results = np.zeros((n_strengths, n_trials))
        mutual_info_results = np.zeros((n_strengths, n_trials))
        secure_rate_results = np.zeros((n_strengths, n_trials))
        chsh_results: Optional[np.ndarray] = None

        desc = f"{protocol_class.protocol_name()} {noise_type} sweep"
        for i, strength in enumerate(tqdm(strengths, desc=desc, unit="pt")):
            backend = create_backend(noise_type, strength)
            eve = EveInterceptor(eve_rate) if with_eve else None

            for j in range(n_trials):
                protocol = protocol_class( n_qubits=n_qubits, backend=backend, eve=eve, **extra_kwargs)
                result = protocol.run()

                qber_results[i, j] = result.qber
                key_rate_results[i, j] = result.key_rate
                mutual_info_results[i, j] = result.mutual_information
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
            mutual_info_mean=np.mean(mutual_info_results, axis=1),
            mutual_info_std=np.std(mutual_info_results, axis=1),
            n_trials=n_trials,
            n_qubits=n_qubits,
            noise_type=noise_type,
            chsh_mean=chsh_mean,
            chsh_std=chsh_std,
            secure_rate_mean=np.mean(secure_rate_results, axis=1),
            secure_rate_std=np.std(secure_rate_results, axis=1),
        )

    def run_eve_sweep(
        self,
        protocol_class,
        eve_rates: np.ndarray,
        n_trials: int = 30,
        n_qubits: int = 100,
        noise_type: str = 'none',
        noise_strength: float = 0.0,
        protocol_kwargs: Optional[dict] = None,
    ) -> BenchmarkData:
        eve_rates = np.asarray(eve_rates)
        n_rates = len(eve_rates)
        extra_kwargs = protocol_kwargs or {}

        qber_results = np.zeros((n_rates, n_trials))
        key_rate_results = np.zeros((n_rates, n_trials))
        mutual_info_results = np.zeros((n_rates, n_trials))
        secure_rate_results = np.zeros((n_rates, n_trials))
        chsh_results: Optional[np.ndarray] = None

        backend = create_backend(noise_type, noise_strength)

        desc = f"{protocol_class.protocol_name()} eve sweep"
        for i, rate in enumerate(tqdm(eve_rates, desc=desc, unit="pt")):
            eve = EveInterceptor(rate) if rate > 0 else None

            for j in range(n_trials):
                protocol = protocol_class( n_qubits=n_qubits, backend=backend, eve=eve, **extra_kwargs)
                result = protocol.run()

                qber_results[i, j] = result.qber
                key_rate_results[i, j] = result.key_rate
                mutual_info_results[i, j] = result.mutual_information
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
            mutual_info_mean=np.mean(mutual_info_results, axis=1),
            mutual_info_std=np.std(mutual_info_results, axis=1),
            n_trials=n_trials,
            n_qubits=n_qubits,
            noise_type=noise_type,
            chsh_mean=chsh_mean,
            chsh_std=chsh_std,
            secure_rate_mean=np.mean(secure_rate_results, axis=1),
            secure_rate_std=np.std(secure_rate_results, axis=1),
        )

    def run_protocol_comparison(
        self,
        protocol_classes: list,
        noise_type: str,
        strengths: np.ndarray,
        n_trials: int = 30,
        n_qubits: int = 100,
        protocol_kwargs: Optional[dict] = None,
    ) -> dict:
        per_proto_kwargs = protocol_kwargs or {}
        results = {}

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
                protocol_kwargs=extra,
            )

        return results

    def run_surface_sweep(
        self,
        protocol_class,
        noise_type: str,
        strengths: np.ndarray,
        eve_rates: np.ndarray,
        n_trials: int = 30,
        n_qubits: int = 100,
    ) -> SurfaceBenchmarkData:
        strengths = np.asarray(strengths)
        eve_rates = np.asarray(eve_rates)
        n_s, n_e = len(strengths), len(eve_rates)
        qber_results = np.zeros((n_s, n_e, n_trials))

        # task list - noise is outer loop, eve is inner lopp, to match (n_s, n_e) structure of the results
        tasks = [
            (protocol_class, noise_type, float(s), float(e), n_trials, n_qubits)
            for s in strengths for e in eve_rates
        ]
        desc = f"{protocol_class.protocol_name()} surface sweep"
        # processes not threads - tried threading first - no actual speedup occured
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
            flat = list(tqdm(pool.map(_surface_cell_worker, tasks), total=len(tasks), desc=desc, unit="cell"))
        # pool.map preserves order so divmod(idx, n_e) gives back (noise_idx, eve_idx)
        for idx, qbers in enumerate(flat):
            i, j = divmod(idx, n_e)
            qber_results[i, j, :] = qbers

        return SurfaceBenchmarkData(
            protocol_name=protocol_class.protocol_name(),
            noise_strengths=strengths,
            eve_rates=eve_rates,
            qber_mean=np.mean(qber_results, axis=2),
            qber_std=np.std(qber_results, axis=2),
            n_trials=n_trials,
            n_qubits=n_qubits,
            noise_type=noise_type,
        )

    def run_surface_sweep_v4(
        self,
        protocol_class,
        noise_type: str,
        strengths: np.ndarray,
        eve_rates: np.ndarray,
        n_trials: int = 30,
        n_qubits: int = 100,
    ) -> SurfaceBenchmarkData:
        strengths = np.asarray(strengths)
        eve_rates = np.asarray(eve_rates)
        n_s, n_e = len(strengths), len(eve_rates)

        qber_results = np.zeros((n_s, n_e, n_trials))
        iab_results  = np.zeros((n_s, n_e, n_trials))
        iae_results  = np.zeros((n_s, n_e, n_trials))
        skr_results  = np.zeros((n_s, n_e, n_trials))

        # same flat task list approach as run_surface_sweep 
        tasks = [
            (protocol_class, noise_type, float(s), float(e), n_trials, n_qubits)
            for s in strengths for e in eve_rates
        ]
        desc = f"{protocol_class.protocol_name()} surface sweep v4"
        # processes for GIL bypass, same as above
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
            flat = list(tqdm(pool.map(_surface_cell_worker_v4, tasks), total=len(tasks), desc=desc, unit="cell"))

        # each flat element is n_trials 4-tuples; divmod recovers (i, j) grid positioning
        for idx, cell in enumerate(flat):
            i, j = divmod(idx, n_e)
            for k, (q, iab, iae, skr) in enumerate(cell):
                # restructuing the 3d arrays - indexed by (noise_idx, eve_idx, trial_idx)
                qber_results[i, j, k] = q
                iab_results[i, j, k]  = iab
                iae_results[i, j, k]  = iae
                skr_results[i, j, k]  = skr

        return SurfaceBenchmarkData(
            protocol_name=protocol_class.protocol_name(),
            noise_strengths=strengths,
            eve_rates=eve_rates,
            qber_mean=np.mean(qber_results, axis=2),
            qber_std=np.std(qber_results, axis=2),
            n_trials=n_trials,
            n_qubits=n_qubits,
            noise_type=noise_type,
            iab_mean=np.mean(iab_results, axis=2),
            iae_mean=np.mean(iae_results, axis=2),
            skr_mean=np.mean(skr_results, axis=2),
        )
