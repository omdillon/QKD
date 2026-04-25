"""
Entry point for QKD simulation platform.

Usage:
    python -m qkd_sim configs/bb84_sweep.yaml
    python -m qkd_sim configs/noise_comparison.yaml --show-plots

Dispatch is keyed on the YAML filename stem. Each experiment has a
dedicated plotting method on QKDPlotter; see plotter.py.
"""

import argparse
from pathlib import Path
import numpy as np

from .config import load_config
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


# YAML stem -> (run-mode, QKDPlotter method name)
EXPERIMENT_PLOTTERS = {
    'bb84_sweep':       ('sweep',               'plot_bb84_sweep'),
    'bb84_eve':         ('eve_sweep',           'plot_bb84_eve'),
    'bb84_noisy_eve':   ('eve_sweep',           'plot_bb84_noisy_eve'),
    'b92_sweep':        ('sweep',               'plot_b92_sweep'),
    'b92_eve':          ('eve_sweep',           'plot_b92_eve'),
    'b92_noisy_eve':    ('eve_sweep',           'plot_b92_noisy_eve'),
    'e91_sweep':        ('sweep',               'plot_e91_sweep'),
    'noise_comparison': ('protocol_comparison', 'plot_noise_comparison'),
    'baseline':         ('protocol_comparison', 'plot_baseline_comparison'),
}


def _e91_kwargs(config, protocol_name):
    if protocol_name.lower() == 'e91':
        return {'channel_topology': config.e91_channel_topology}
    return {}


def _output_dir(config):
    return Path(config.output_dir) if config.save_plots else None


def run_single(config):
    """Run a single protocol trial (no plotting)."""
    protocol_class = PROTOCOLS[config.protocol]
    backend = create_backend(config.noise_type, config.noise_strength)
    eve = EveInterceptor(config.eve_rate, backend) if config.eve_rate is not None else None

    protocol = protocol_class(
        n_qubits=config.n_qubits, backend=backend, eve=eve,
        **_e91_kwargs(config, config.protocol),
    )
    result = protocol.run()

    print(f"  {protocol_class.protocol_name()} | "
          f"QBER: {result.qber:.4f} | "
          f"Key rate: {result.key_rate:.2%} | "
          f"I(A;B): {result.mutual_information:.4f}")

    if hasattr(result, 's_value'):
        print(f"  |S| (CHSH): {result.abs_s:.4f} "
              f"(violation: {'YES' if result.chsh_violation else 'NO'})")


def run_sweep(config, plot_method_name):
    """Run a noise strength sweep and dispatch to the per-experiment plot method."""
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
        protocol_kwargs=_e91_kwargs(config, config.protocol),
    )

    if not (config.save_plots or config.show_plots):
        return

    plotter = QKDPlotter()
    method = getattr(plotter, plot_method_name)
    if config.protocol.lower() == 'e91':
        method(data, output_dir=_output_dir(config), show=config.show_plots,
               channel_topology=config.e91_channel_topology)
    else:
        method(data, output_dir=_output_dir(config), show=config.show_plots)


def run_eve_sweep(config, plot_method_name):
    """Run an Eve interception rate sweep and dispatch to its plot method."""
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
        protocol_kwargs=_e91_kwargs(config, config.protocol),
    )

    if not (config.save_plots or config.show_plots):
        return

    plotter = QKDPlotter()
    method = getattr(plotter, plot_method_name)
    if 'noisy_eve' in plot_method_name:
        method(data, noise_strength=config.noise_strength,
               output_dir=_output_dir(config), show=config.show_plots)
    else:
        method(data, output_dir=_output_dir(config), show=config.show_plots)


def run_protocol_comparison(config, plot_method_name):
    """Run the same noise sweep across multiple protocols and dispatch to plot."""
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
        protocol_kwargs=proto_kwargs,
    )

    if not (config.save_plots or config.show_plots):
        return

    plotter = QKDPlotter()
    method = getattr(plotter, plot_method_name)
    method(data_dict, output_dir=_output_dir(config), show=config.show_plots)


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

    if config.mode == 'single':
        run_single(config)
    else:
        stem = Path(args.config_file).stem
        if stem not in EXPERIMENT_PLOTTERS:
            valid = ', '.join(sorted(EXPERIMENT_PLOTTERS.keys()))
            raise ValueError(
                f"Unknown experiment '{stem}'. Add it to EXPERIMENT_PLOTTERS "
                f"in qkd_sim/__main__.py. Valid: {valid}"
            )
        expected_mode, plot_method_name = EXPERIMENT_PLOTTERS[stem]
        if config.mode != expected_mode:
            raise ValueError(
                f"Config '{stem}' uses mode '{config.mode}' but experiment "
                f"expects '{expected_mode}'"
            )
        if config.mode == 'sweep':
            run_sweep(config, plot_method_name)
        elif config.mode == 'eve_sweep':
            run_eve_sweep(config, plot_method_name)
        elif config.mode == 'protocol_comparison':
            run_protocol_comparison(config, plot_method_name)
        else:
            raise ValueError(f"Unhandled mode: {config.mode}")

    if config.save_plots:
        print(f"  Plots saved to: {config.output_dir}/")
    print("  Done.")


if __name__ == '__main__':
    main()
