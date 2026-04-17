"""
Entry point for QKD simulation platform.

Usage:
    python -m qkd_sim configs/bb84_sweep.yaml
    python -m qkd_sim configs/protocol_comparison.yaml --show-plots
"""

import argparse
import sys
from pathlib import Path
import numpy as np

from .config import load_config, SimConfig
from .noise import create_backend
from .eve import EveInterceptor
from .benchmark import BenchmarkRunner
from .plotter import QKDPlotter
from .protocols.bb84 import BB84Protocol
from .protocols.b92 import B92Protocol
from .protocols.e91 import E91Protocol


PROTOCOLS = {
    'bb84': BB84Protocol,
    'b92': B92Protocol,
    'e91': E91Protocol,
}


def _e91_kwargs(config, protocol_name):
    """Return extra kwargs for E91, empty dict for others."""
    if protocol_name.lower() == 'e91':
        return {'channel_topology': config.e91_channel_topology}
    return {}


def run_single(config):
    """Run a single protocol trial."""
    protocol_class = PROTOCOLS[config.protocol]
    backend = create_backend(config.noise_type, config.noise_strength)
    eve = EveInterceptor(config.eve_rate) if config.eve_rate is not None else None

    protocol = protocol_class(
        n_qubits=config.n_qubits, backend=backend, eve=eve, f_ec=config.f_ec,
        **_e91_kwargs(config, config.protocol),
    )
    result = protocol.run()

    print(f"  {protocol_class.protocol_name()} | "
          f"QBER: {result.qber:.4f} | "
          f"Key rate: {result.key_rate:.2%} | "
          f"Secure: {'YES' if result.is_secure else 'NO'}")

    if hasattr(result, 's_value'):
        print(f"  |S| (CHSH): {result.abs_s:.4f} "
              f"(violation: {'YES' if result.chsh_violation else 'NO'})")


def run_sweep(config):
    """Run a noise strength sweep."""
    protocol_class = PROTOCOLS[config.protocol]
    strengths = np.linspace(config.noise_min, config.noise_max, config.noise_steps)

    runner = BenchmarkRunner()
    data = runner.run_noise_sweep(
        protocol_class=protocol_class,
        noise_type=config.noise_type,
        strengths=strengths,
        n_trials=config.n_trials,
        n_qubits=config.n_qubits,
        with_eve=config.eve_rate is not None,
        eve_rate=config.eve_rate if config.eve_rate else 0.0,
        f_ec=config.f_ec,
        protocol_kwargs=_e91_kwargs(config, config.protocol),
    )

    if config.save_plots or config.show_plots:
        plotter = QKDPlotter(f_ec=config.f_ec)
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        plotter.plot_qber_vs_noise(
            data, protocol_class=protocol_class,
            save_path=output_dir / f'qber_vs_{config.noise_type}.png' if config.save_plots else None,
            show=config.show_plots,
        )
        plotter.plot_key_rate_vs_noise(
            data, protocol_class=protocol_class,
            save_path=output_dir / f'keyrate_vs_{config.noise_type}.png' if config.save_plots else None,
            show=config.show_plots,
        )
        if data.chsh_mean is not None:
            plotter.plot_chsh_vs_noise(
                data, protocol_class=protocol_class,
                channel_topology=config.e91_channel_topology,
                save_path=output_dir / f'chsh_vs_{config.noise_type}.png' if config.save_plots else None,
                show=config.show_plots,
            )
            plotter.plot_chsh_qber_vs_noise(
                data,
                channel_topology=config.e91_channel_topology,
                save_path=output_dir / f'chsh_qber_vs_{config.noise_type}.png' if config.save_plots else None,
                show=config.show_plots,
            )


def run_eve_sweep(config):
    """Run an Eve interception rate sweep."""
    protocol_class = PROTOCOLS[config.protocol]
    eve_rates = np.linspace(config.eve_min, config.eve_max, config.eve_steps)

    runner = BenchmarkRunner()
    data = runner.run_eve_sweep(
        protocol_class=protocol_class,
        eve_rates=eve_rates,
        n_trials=config.n_trials,
        n_qubits=config.n_qubits,
        noise_type=config.noise_type,
        noise_strength=config.noise_strength,
        f_ec=config.f_ec,
        protocol_kwargs=_e91_kwargs(config, config.protocol),
    )

    if config.save_plots or config.show_plots:
        plotter = QKDPlotter(f_ec=config.f_ec)
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        plotter.plot_qber_vs_noise(
            data, protocol_class=protocol_class,
            save_path=output_dir / 'qber_vs_eve_rate.png' if config.save_plots else None,
            show=config.show_plots,
        )
        plotter.plot_key_rate_vs_noise(
            data, protocol_class=protocol_class,
            save_path=output_dir / 'keyrate_vs_eve_rate.png' if config.save_plots else None,
            show=config.show_plots,
        )

        if config.noise_type != 'none' and config.noise_strength > 0:
            plotter.plot_qber_noisy_eve(
                data, noise_strength=config.noise_strength,
                protocol_class=protocol_class,
                save_path=output_dir / f'qber_noisy_eve_{config.noise_type}_p{config.noise_strength:.3f}.png'
                    if config.save_plots else None,
                show=config.show_plots,
            )


def run_protocol_comparison(config):
    """Run the same noise sweep across multiple protocols."""
    protocol_classes = [PROTOCOLS[name] for name in config.protocols]
    strengths = np.linspace(config.noise_min, config.noise_max, config.noise_steps)

    proto_kwargs = {}
    for name in config.protocols:
        if name.lower() == 'e91':
            proto_kwargs['E91'] = {'channel_topology': config.e91_channel_topology}

    runner = BenchmarkRunner()
    data_dict = runner.run_protocol_comparison(
        protocol_classes=protocol_classes,
        noise_type=config.noise_type,
        strengths=strengths,
        n_trials=config.n_trials,
        n_qubits=config.n_qubits,
        f_ec=config.f_ec,
        protocol_kwargs=proto_kwargs,
    )

    if config.save_plots or config.show_plots:
        plotter = QKDPlotter(f_ec=config.f_ec)
        output_dir = Path(config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        proto_class_map = {cls.protocol_name(): cls for cls in protocol_classes}

        for kind, fname in (('qber', 'qber_comparison'), ('secure_key_rate', 'secure_key_rate_comparison')):
            plotter.plot_protocol_comparison(
                data_dict, kind=kind, protocol_classes=proto_class_map,
                save_path=output_dir / f'{fname}.png' if config.save_plots else None,
                show=config.show_plots,
            )


def main():
    parser = argparse.ArgumentParser(description='QKD Simulation Platform')
    parser.add_argument('config_file', help='Path to YAML config file')
    parser.add_argument('--show-plots', action='store_true', help='Display plots interactively')
    args = parser.parse_args()

    config = load_config(args.config_file)
    if args.show_plots:
        config.show_plots = True

    print(f"  Mode: {config.mode} | Protocol: {config.protocol} | "
          f"Qubits: {config.n_qubits} | Trials: {config.n_trials}")

    dispatch = {
        'single': run_single,
        'sweep': run_sweep,
        'eve_sweep': run_eve_sweep,
        'protocol_comparison': run_protocol_comparison,
    }
    dispatch[config.mode](config)

    if config.save_plots:
        print(f"  Plots saved to: {config.output_dir}/")
    print("  Done.")


if __name__ == '__main__':
    main()
