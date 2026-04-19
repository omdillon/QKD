"""
Plotting module for QKD simulation results.

One method per experiment config in configs/. Each method hard-codes the
titles, filenames, and figure set for its scenario. Visual constants come
from STYLESHEET.py so colours/fonts/sizes remain consistent across plots.
"""

from pathlib import Path
from typing import Dict, Optional

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from .benchmark import BenchmarkData
from .protocols.bb84 import BB84Protocol
from .protocols.b92 import B92Protocol
from .protocols.e91 import E91Protocol
from .STYLESHEET import STYLE


_FONT_DIR = Path(__file__).resolve().parent.parent / 'font' / 'DM_Sans' / 'static'
if _FONT_DIR.is_dir():
    for _ttf in _FONT_DIR.glob('DMSans-*.ttf'):
        fm.fontManager.addfont(str(_ttf))

plt.rcParams.update(STYLE.get_rcparams())

# Asymptotic QBER security thresholds.
#   BB84: 11.0% - Shor & Preskill (2000)
#   B92:   6.5% - Matsumoto (2013)
#   E91 has no single QBER threshold (security is a 2D condition over Q and |S|).
_QBER_THRESHOLDS = {'BB84': 0.110, 'B92': 0.065}


def _eve_crossing_rate(eve_rates, qber_mean, threshold):
    """Linear-interpolate the Eve rate at which simulated QBER first meets threshold."""
    y = np.asarray(qber_mean)
    above = np.where(y >= threshold)[0]
    if len(above) == 0 or above[0] == 0:
        return None
    idx = int(above[0])
    x0, x1 = float(eve_rates[idx - 1]), float(eve_rates[idx])
    y0, y1 = float(y[idx - 1]), float(y[idx])
    if y1 == y0:
        return x0
    return x0 + (threshold - y0) * (x1 - x0) / (y1 - y0)


class QKDPlotter:
    """One plotting method per experiment config."""

    def __init__(self, f_ec: float = 1.16):
        self.f_ec = f_ec
        try:
            plt.style.use(STYLE.mpl_style)
        except OSError:
            pass
        plt.rcParams.update(STYLE.get_rcparams())

    # --------------------------------------------------------------
    # BB84 experiments
    # --------------------------------------------------------------

    def plot_bb84_sweep(self, data: BenchmarkData,
                        output_dir: Optional[Path] = None,
                        show: bool = False) -> None:
        """BB84 depolarising-noise sweep: QBER and secure key rate."""
        colour = STYLE.protocol_colours['BB84']
        marker = STYLE.protocol_markers['BB84']
        threshold = _QBER_THRESHOLDS['BB84']
        theory_x = np.linspace(data.parameter_values.min(), data.parameter_values.max(), 200)

        # --- QBER figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        sem = data.qber_std / np.sqrt(data.n_trials)
        ax.errorbar(
            data.parameter_values, data.qber_mean, yerr=sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label='Depolarising Channel',
        )
        theory_y = BB84Protocol.theoretical_qber('depolarizing', theory_x)
        ax.plot(theory_x, theory_y, STYLE.theory_linestyle, color=colour,
                alpha=STYLE.theory_alpha, linewidth=STYLE.theory_linewidth,
                label='Depolarising Channel (Theoretical)')
        ax.axhline(y=threshold, color=STYLE.threshold_colour,
                   linestyle=STYLE.threshold_linestyle_horizontal,
                   linewidth=STYLE.threshold_linewidth,
                   alpha=STYLE.threshold_alpha_horizontal,
                   label=f'BB84 Protocol Security Threshold ({threshold:.1%})')
        ax.set_xlabel('Depolarising Noise Strength', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('QBER (%)', fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'BB84 Protocol - Depolarising Channel - QBER\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
        ax.set_xlim(data.parameter_values.min() - 0.005, data.parameter_values.max() + 0.005)
        ax.set_ylim(0, min(max(data.qber_mean.max() * 1.3, threshold * 1.5), 0.5))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc=STYLE.legend_loc_qber, framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'qber.png', show)

        # --- Secure key rate figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        y = data.secure_key_rate_mean * 100
        y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100
        ax.errorbar(
            data.parameter_values, y, yerr=y_err,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label='Depolarising channel (simulation)',
        )
        theory_y = BB84Protocol.theoretical_secure_key_rate(
            'depolarizing', theory_x, f_ec=self.f_ec)
        ax.plot(theory_x, theory_y * 100, STYLE.theory_linestyle, color=colour,
                alpha=STYLE.theory_alpha, linewidth=STYLE.theory_linewidth,
                label='Depolarising Channel (Theoretical)')
        theory_qber = BB84Protocol.theoretical_qber('depolarizing', data.parameter_values)
        idx = int(np.searchsorted(theory_qber, threshold))
        if 0 < idx < len(data.parameter_values):
            p_crit = float(data.parameter_values[idx])
            ax.axvline(x=p_crit, color=STYLE.threshold_colour,
                       linestyle=STYLE.threshold_linestyle_vertical,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_vertical,
                       label=f'QBER Threshold = {threshold:.1%} @ Intercept Rate = \u2248 {p_crit:.2f}')
        ax.set_xlabel('Depolarising Noise Strength', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Secure Key Rate (bits per 100 qubits)',
                       fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'BB84 Protocol - Depolarising Channel - Secure Key Rate\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials, '
            f'Shor-Preskill Bound @ $f_{{EC}}$ = {self.f_ec})',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.set_xlim(data.parameter_values.min() - 0.005, data.parameter_values.max() + 0.005)
        ax.set_ylim(0, y.max() * 1.15)
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc=STYLE.legend_loc_keyrate, framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'keyrate.png', show)

    def plot_bb84_eve(self, data: BenchmarkData,
                      output_dir: Optional[Path] = None,
                      show: bool = False) -> None:
        """BB84 intercept-resend sweep on a clean channel."""
        colour = STYLE.protocol_colours['BB84']
        marker = STYLE.protocol_markers['BB84']
        threshold = _QBER_THRESHOLDS['BB84']

        # --- QBER figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        sem = data.qber_std / np.sqrt(data.n_trials)
        ax.errorbar(
            data.parameter_values, data.qber_mean, yerr=sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label='Intercept-Resend Attack',
        )
        ax.axhline(y=threshold, color=STYLE.threshold_colour,
                   linestyle=STYLE.threshold_linestyle_horizontal,
                   linewidth=STYLE.threshold_linewidth,
                   alpha=STYLE.threshold_alpha_horizontal,
                   label=f'BB84 Security Threshold ({threshold:.1%})')
        e_crit = _eve_crossing_rate(data.parameter_values, data.qber_mean, threshold)
        if e_crit is not None:
            ax.axvline(x=e_crit, color=STYLE.threshold_colour,
                       linestyle=STYLE.threshold_linestyle_vertical,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_vertical,
                       label=f'QBER Threshold (Intercept Rate = \u2248 {e_crit:.2f})')
        ax.set_xlabel('Eve Interception Rate', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('QBER (%)', fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'BB84 Protocol - Intercept-Resend Attack - QBER\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
        ax.set_xlim(data.parameter_values.min() - 0.01, data.parameter_values.max() + 0.01)
        ax.set_ylim(0, min(max(data.qber_mean.max() * 1.3, threshold * 1.5), 0.5))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc=STYLE.legend_loc_qber, framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'qber.png', show)

        # --- Secure key rate figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        y = data.secure_key_rate_mean * 100
        y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100
        ax.errorbar(
            data.parameter_values, y, yerr=y_err,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label='Intercept-Resend Attack',
        )
        if e_crit is not None:
            ax.axvline(x=e_crit, color=STYLE.threshold_colour,
                       linestyle=STYLE.threshold_linestyle_vertical,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_vertical,
                       label=f'QBER Threshold = {threshold:.1%} @ Intercept Rate = \u2248 {e_crit:.2f}')
        ax.set_xlabel('Eve Interception Rate', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Secure Key Rate (bits per 100 qubits)',
                       fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'BB84 Protocol - Intercept-Resend Attack - Secure Key Rate\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials, '
            f'Shor-Preskill Bound @ $f_{{EC}}$ = {self.f_ec})',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.set_xlim(data.parameter_values.min() - 0.01, data.parameter_values.max() + 0.01)
        ax.set_ylim(0, max(y.max() * 1.15, 1.0))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='upper right', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'keyrate.png', show)

    def plot_bb84_noisy_eve(self, data: BenchmarkData, noise_strength: float,
                            output_dir: Optional[Path] = None,
                            show: bool = False) -> None:
        """BB84 Eve sweep on a fixed-noise depolarising channel."""
        colour = STYLE.protocol_colours['BB84']
        marker = STYLE.protocol_markers['BB84']
        threshold = _QBER_THRESHOLDS['BB84']
        p_label = f'Depolarising Noise Strength (p = {noise_strength:.3f})'

        # --- QBER figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        sem = data.qber_std / np.sqrt(data.n_trials)
        ax.errorbar(
            data.parameter_values, data.qber_mean, yerr=sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label=f'Intercept Attack + {p_label}',
        )
        ax.axhline(y=threshold, color=STYLE.threshold_colour,
                   linestyle=STYLE.threshold_linestyle_horizontal,
                   linewidth=STYLE.threshold_linewidth,
                   alpha=STYLE.threshold_alpha_horizontal,
                   label=f'BB84 Security Threshold ({threshold:.1%})')
        e_crit = _eve_crossing_rate(data.parameter_values, data.qber_mean, threshold)
        if e_crit is not None:
            ax.axvline(x=e_crit, color=STYLE.threshold_colour,
                       linestyle=STYLE.threshold_linestyle_vertical,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_vertical,
                       label=f'QBER Threshold (Intercept Rate = \u2248 {e_crit:.2f})')
        ax.set_xlabel('Eve Interception Rate', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('QBER (%)', fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'BB84 Protocol - Intercept-Resend Attack + {p_label} - QBER\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
        ax.set_xlim(data.parameter_values.min() - 0.01, data.parameter_values.max() + 0.01)
        ax.set_ylim(0, min(max(data.qber_mean.max() * 1.3, threshold * 1.5), 0.5))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='upper right', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'qber.png', show)

        # --- Secure key rate figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        y = data.secure_key_rate_mean * 100
        y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100
        ax.errorbar(
            data.parameter_values, y, yerr=y_err,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label=f'Intercept-Resend Attack + {p_label}')
        
        if e_crit is not None:
            ax.axvline(x=e_crit, color=STYLE.threshold_colour,
                       linestyle=STYLE.threshold_linestyle_vertical,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_vertical,
                       label=f'QBER Threshold = {threshold:.1%} @ Intercept Rate = \u2248 {e_crit:.2f}')
        ax.set_xlabel('Eve Interception Rate', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Secure Key Rate (bits per 100 qubits)',
                       fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'BB84 Protocol - Intercept-Resend Attack + {p_label} - Secure Key Rate\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials, '
            f'Shor-Preskill Bound @ $f_{{EC}}$ = {self.f_ec})',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
    


        ax.set_xlim(data.parameter_values.min() - 0.01, data.parameter_values.max() + 0.01)
        ax.set_ylim(0, max(y.max() * 1.15, 1.0))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='upper right', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'keyrate.png', show)

    # --------------------------------------------------------------
    # B92 experiments
    # --------------------------------------------------------------

    def plot_b92_sweep(self, data: BenchmarkData,
                       output_dir: Optional[Path] = None,
                       show: bool = False) -> None:
        """B92 depolarising-noise sweep: QBER and secure key rate."""
        colour = STYLE.protocol_colours['B92']
        marker = STYLE.protocol_markers['B92']
        threshold = _QBER_THRESHOLDS['B92']
        theory_x = np.linspace(data.parameter_values.min(),
                               data.parameter_values.max(), 200)

        # --- QBER figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        sem = data.qber_std / np.sqrt(data.n_trials)
        ax.errorbar(
            data.parameter_values, data.qber_mean, yerr=sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label='Depolarising Channel',
        )
        theory_y = B92Protocol.theoretical_qber('depolarizing', theory_x)
        ax.plot(theory_x, theory_y, STYLE.theory_linestyle, color=colour,
                alpha=STYLE.theory_alpha, linewidth=STYLE.theory_linewidth,
                label='Depolarising Channel (Theoretical)')
        ax.axhline(y=threshold, color=STYLE.threshold_colour,
                   linestyle=STYLE.threshold_linestyle_horizontal,
                   linewidth=STYLE.threshold_linewidth,
                   alpha=STYLE.threshold_alpha_horizontal,
                   label=f'B92 Security Threshold ({threshold:.1%})')
        ax.set_xlabel('Depolarising Noise Strength', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('QBER (%)', fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'B92 Protocol - Depolarising Channel - QBER\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
        ax.set_xlim(data.parameter_values.min() - 0.005, data.parameter_values.max() + 0.005)
        ax.set_ylim(0, min(max(data.qber_mean.max() * 1.3, threshold * 1.5), 0.5))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc=STYLE.legend_loc_qber, framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'qber.png', show)

        # --- Secure key rate figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        y = data.secure_key_rate_mean * 100
        y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100
        ax.errorbar(
            data.parameter_values, y, yerr=y_err,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label='Depolarising Channel',
        )
        theory_y = B92Protocol.theoretical_secure_key_rate(
            'depolarizing', theory_x, f_ec=self.f_ec)
        ax.plot(theory_x, theory_y * 100, STYLE.theory_linestyle, color=colour,
                alpha=STYLE.theory_alpha, linewidth=STYLE.theory_linewidth,
                label='Depolarising Channel (Theoretical)')
        theory_qber = B92Protocol.theoretical_qber('depolarizing', data.parameter_values)
        idx = int(np.searchsorted(theory_qber, threshold))
        if 0 < idx < len(data.parameter_values):
            p_crit = float(data.parameter_values[idx])
            ax.axvline(x=p_crit, color=STYLE.threshold_colour,
                       linestyle=STYLE.threshold_linestyle_vertical,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_vertical,
                       label=f'QBER = {threshold:.1%} threshold (p \u2248 {p_crit:.2f})')
        ax.set_xlabel('Depolarising Noise Strength', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Secure Key Rate (bits/100 qubits)',
                       fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'B92 Protocol - Depolarising Channel - Secure Key Rate\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials, '
            f'6.5% QBER Threshold)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.set_xlim(data.parameter_values.min() - 0.005, data.parameter_values.max() + 0.005)
        ax.set_ylim(0, max(y.max() * 1.15, 1.0))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='upper right', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'keyrate.png', show)

    def plot_b92_eve(self, data: BenchmarkData,
                     output_dir: Optional[Path] = None,
                     show: bool = False) -> None:
        """B92 intercept-resend sweep on a clean channel."""
        colour = STYLE.protocol_colours['B92']
        marker = STYLE.protocol_markers['B92']
        threshold = _QBER_THRESHOLDS['B92']

        # --- QBER figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        sem = data.qber_std / np.sqrt(data.n_trials)
        ax.errorbar(
            data.parameter_values, data.qber_mean, yerr=sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label='Intercept-Resend Attack',
        )
        ax.axhline(y=threshold, color=STYLE.threshold_colour,
                   linestyle=STYLE.threshold_linestyle_horizontal,
                   linewidth=STYLE.threshold_linewidth,
                   alpha=STYLE.threshold_alpha_horizontal,
                   label=f'B92 Security Threshold ({threshold:.1%})')
        e_crit = _eve_crossing_rate(data.parameter_values, data.qber_mean, threshold)
        if e_crit is not None:
            ax.axvline(x=e_crit, color=STYLE.threshold_colour,
                       linestyle=STYLE.threshold_linestyle_vertical,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_vertical,
                       label=f'QBER Threshold (Intercept Rate = \u2248 {e_crit:.2f})')
        ax.set_xlabel('Eve Interception Rate', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('QBER (%)', fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'B92 Protocol - Intercept-Resend Attack - QBER\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
        ax.set_xlim(data.parameter_values.min() - 0.01, data.parameter_values.max() + 0.01)
        ax.set_ylim(0, min(max(data.qber_mean.max() * 1.3, threshold * 1.5), 0.5))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='upper right', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'qber.png', show)

        # --- Secure key rate figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        y = data.secure_key_rate_mean * 100
        y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100
        ax.errorbar(
            data.parameter_values, y, yerr=y_err,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label='Intercept-Resend',
        )
        if e_crit is not None:
            ax.axvline(x=e_crit, color=STYLE.threshold_colour,
                       linestyle=STYLE.threshold_linestyle_vertical,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_vertical,
                       label=f'QBER Threshold = {threshold:.1%} @ Intercept Rate = \u2248 {e_crit:.2f}')
        ax.set_xlabel('Eve Interception Rate', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Secure Key Rate (bits per 100 qubits)',
                       fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'B92 Protocol - Intercept-Resend Attack - Secure Key Rate\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials, '
            f'6.5% QBER Threshold)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
            
        ax.set_xlim(data.parameter_values.min() - 0.01, data.parameter_values.max() + 0.01)
        ax.set_ylim(0, max(y.max() * 1.15, 1.0))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='upper right', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'keyrate.png', show)

    def plot_b92_noisy_eve(self, data: BenchmarkData, noise_strength: float,
                           output_dir: Optional[Path] = None,
                           show: bool = False) -> None:
        """B92 Eve sweep on a fixed-noise depolarising channel."""
        colour = STYLE.protocol_colours['B92']
        marker = STYLE.protocol_markers['B92']
        threshold = _QBER_THRESHOLDS['B92']
        p_label = f'Depolarising Noise Strength (p = {noise_strength:.3f})'

        # --- QBER figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        sem = data.qber_std / np.sqrt(data.n_trials)
        ax.errorbar(
            data.parameter_values, data.qber_mean, yerr=sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label=f'Intercept Attack + {p_label}',
        )
        ax.axhline(y=threshold, color=STYLE.threshold_colour,
                   linestyle=STYLE.threshold_linestyle_horizontal,
                   linewidth=STYLE.threshold_linewidth,
                   alpha=STYLE.threshold_alpha_horizontal,
                   label=f'B92 Protocol Security Threshold ({threshold:.1%})')
        e_crit = _eve_crossing_rate(data.parameter_values, data.qber_mean, threshold)
        if e_crit is not None:
            ax.axvline(x=e_crit, color=STYLE.threshold_colour,
                       linestyle=STYLE.threshold_linestyle_vertical,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_vertical,
                       label=f'QBER Threshold (Intercept Rate = \u2248 {e_crit:.2f})')
        ax.set_xlabel('Eve Interception Rate', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('QBER (%)', fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'B92 Protocol - Intercept-Resend Attack + {p_label} - QBER\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
        ax.set_xlim(data.parameter_values.min() - 0.01, data.parameter_values.max() + 0.01)
        ax.set_ylim(0, min(max(data.qber_mean.max() * 1.3, threshold * 1.5), 0.5))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='center', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'qber.png', show)

        # --- Secure key rate figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        y = data.secure_key_rate_mean * 100
        y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100
        ax.errorbar(
            data.parameter_values, y, yerr=y_err,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label=f'Intercept-Resend Attack + {p_label}')
        
        if e_crit is not None:
            ax.axvline(x=e_crit, color=STYLE.threshold_colour,
                       linestyle=STYLE.threshold_linestyle_vertical,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_vertical,
                       label=f'QBER Threshold = {threshold:.1%} @ Intercept Rate = \u2248 {e_crit:.2f}')
        ax.set_xlabel('Eve Interception Rate', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Secure Key Rate (bits per 100 qubits)',
                       fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'B92 Protocol - Intercept-Resend Attack + {p_label} - Secure Key Rate\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials, '
            f'6.5% QBER Threshold)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        
        
        ax.set_xlim(data.parameter_values.min() - 0.01, data.parameter_values.max() + 0.01)
        ax.set_ylim(0, max(y.max() * 1.15, 1.0))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='upper right', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'keyrate.png', show)

    # --------------------------------------------------------------
    # E91 experiment
    # --------------------------------------------------------------

    def plot_e91_sweep(self, data: BenchmarkData,
                       output_dir: Optional[Path] = None,
                       show: bool = False,
                       channel_topology: str = 'both') -> None:
        """E91 depolarising-noise sweep: QBER, key rate, CHSH, CHSH+QBER."""
        colour = STYLE.protocol_colours['E91']
        marker = STYLE.protocol_markers['E91']
        theory_x = np.linspace(data.parameter_values.min(),
                               data.parameter_values.max(), 200)
        topo_str = f' ({channel_topology}-side noise)'

        # --- Secure key rate figure ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)
        y = data.secure_key_rate_mean * 100
        y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100
        ax.errorbar(
            data.parameter_values, y, yerr=y_err,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label='Depolarising Channel',
        )
        theory_y = E91Protocol.theoretical_secure_key_rate(
            'depolarizing', theory_x, f_ec=self.f_ec,
            channel_topology=channel_topology)
        ax.plot(theory_x, theory_y * 100, STYLE.theory_linestyle, color=colour,
                alpha=STYLE.theory_alpha, linewidth=STYLE.theory_linewidth,
                label='Depolarising Channel (Theoretical)')
        ax.set_xlabel('Depolarising Noise Strength', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Secure Key Rate (bits per 100 qubits)',
                       fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'E91 Protocol - Depolarising Channel {topo_str} - Secure Key Rate\n'
            f'({data.n_qubits} photon pairs, {data.n_trials} trials)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.set_xlim(data.parameter_values.min() - 0.005, data.parameter_values.max() + 0.005)
        ax.set_ylim(0, max(y.max() * 1.15, 1.0))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='upper right', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'keyrate.png', show)

        if data.chsh_mean is None:
            return

        # --- CHSH + QBER twin-axis figure ---
        fig, ax_chsh = plt.subplots(figsize=STYLE.figsize_single)
        ax_qber = ax_chsh.twinx()
        qber_colour = STYLE.noise_colours['depolarizing']
        qber_sem_pct = data.qber_std / np.sqrt(data.n_trials) * 100
        chsh_sem = data.chsh_std / np.sqrt(data.n_trials)
    
        ax_chsh.errorbar(
            data.parameter_values, data.chsh_mean, yerr=chsh_sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label='|S| (CHSH)',
        )
        ax_qber.errorbar(
            data.parameter_values, data.qber_mean * 100, yerr=qber_sem_pct,
            fmt='s--', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=qber_colour, ecolor=qber_colour,
            alpha=STYLE.errorbar_alpha, label='QBER',
        )
        ax_chsh.axhline(y=2.0, color='#0e365f',
                        linestyle=STYLE.threshold_linestyle_horizontal,
                        linewidth=STYLE.threshold_linewidth,
                        alpha=STYLE.threshold_alpha_horizontal,
                        label='Classical Bound (|S| = 2)')
        ax_chsh.axhline(y=2 * np.sqrt(2), color="#ff9500", linestyle=STYLE.threshold_linestyle_horizontal,
                        linewidth=STYLE.threshold_linewidth, alpha=STYLE.threshold_alpha_horizontal,
                        label=r'Tsirelson Bound (|S| = 2$\sqrt{2}$)', xmax=0.666)
        ax_chsh.set_xlabel('Depolarising Noise Strength', fontweight=STYLE.font_weight_axis_label)
        ax_chsh.set_ylabel('|S| (CHSH Parameter)', fontweight=STYLE.font_weight_axis_label)
        ax_qber.set_ylabel('QBER (%)', fontweight=STYLE.font_weight_axis_label)
        ax_chsh.set_title(
            f'E91 Protocol - Depolarising Channel {topo_str} - CHSH + QBER\n'
            f'({data.n_qubits} photon pairs, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax_chsh.set_xlim(data.parameter_values.min() - 0.005,
                          data.parameter_values.max() + 0.005)
        ax_chsh.set_ylim(1.5, 3.0)
        ax_qber.set_ylim(0, 50)
        n_ticks = 6
        ax_chsh.set_yticks(np.linspace(1.5, 3.0, n_ticks))
        ax_qber.set_yticks(np.linspace(0, 50, n_ticks))
        ax_chsh.grid(True, alpha=STYLE.grid_alpha)
        ax_qber.grid(False)
        h_c, l_c = ax_chsh.get_legend_handles_labels()
        h_q, l_q = ax_qber.get_legend_handles_labels()
        ax_chsh.legend(h_c + h_q, l_c + l_q,
                       loc='upper right', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'chsh_qber.png', show)

    # --------------------------------------------------------------
    # Three-protocol comparison
    # --------------------------------------------------------------

    def plot_noise_comparison(self, data_dict: Dict[str, BenchmarkData],
                              output_dir: Optional[Path] = None,
                              show: bool = False) -> None:
        """BB84/B92/E91 overlay under depolarising noise: QBER and key rate."""
        proto_classes = {'BB84': BB84Protocol, 'B92': B92Protocol, 'E91': E91Protocol}
        sample_data = next(iter(data_dict.values()))

        # --- QBER comparison ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_comparison)
        for proto_name, data in data_dict.items():
            colour = STYLE.protocol_colours.get(proto_name, STYLE.default_colour)
            marker = STYLE.protocol_markers.get(proto_name, STYLE.default_marker)
            sem = data.qber_std / np.sqrt(data.n_trials)
            ax.errorbar(
                data.parameter_values, data.qber_mean, yerr=sem,
                fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
                linewidth=STYLE.errorbar_linewidth,
                markersize=STYLE.errorbar_markersize,
                color=colour, alpha=STYLE.errorbar_alpha,
                label=f'{proto_name} Protocol',
            )
            cls = proto_classes.get(proto_name)
            if cls is not None:
                theory_x = np.linspace(data.parameter_values.min(),
                                       data.parameter_values.max(), 200)
                theory_y = cls.theoretical_qber('depolarizing', theory_x)
                if theory_y is not None:
                    ax.plot(theory_x, theory_y, STYLE.theory_linestyle,
                            color=colour, alpha=STYLE.theory_alpha,
                            linewidth=STYLE.theory_linewidth)

        for proto_name, thresh in _QBER_THRESHOLDS.items():
            if proto_name not in data_dict:
                continue
            proto_colour = STYLE.protocol_colours.get(proto_name, STYLE.default_colour)
            ax.axhline(y=thresh, color=proto_colour,
                       linestyle=STYLE.threshold_linestyle_horizontal,
                       linewidth=STYLE.threshold_linewidth,
                       alpha=STYLE.threshold_alpha_horizontal,
                       label=f'{proto_name} Security Threshold ({thresh:.1%})')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
        ax.set_xlabel('Depolarising Noise Strength', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('QBER (%)',
                      fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'Three-Protocol Benchmark - Depolarising Channel - QBER\n'
            f'({sample_data.n_trials} trials/point, '
            f'{sample_data.n_qubits} qubits per trial)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'qber_vs_noise.png', show)

        # --- Secure key rate comparison ---
        fig, ax = plt.subplots(figsize=STYLE.figsize_comparison)
        all_y_max = 0.0
        for proto_name, data in data_dict.items():
            colour = STYLE.protocol_colours.get(proto_name, STYLE.default_colour)
            marker = STYLE.protocol_markers.get(proto_name, STYLE.default_marker)
            y = data.secure_key_rate_mean * 100
            y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100
            all_y_max = max(all_y_max, float(y.max()))
            ax.errorbar(
                data.parameter_values, y, yerr=y_err,
                fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
                linewidth=STYLE.errorbar_linewidth,
                markersize=STYLE.errorbar_markersize,
                color=colour, alpha=STYLE.errorbar_alpha,
                label=f'{proto_name} Protocol',
            )
            cls = proto_classes.get(proto_name)
            if cls is not None:
                theory_x = np.linspace(data.parameter_values.min(),
                                       data.parameter_values.max(), 200)
                theory_y = cls.theoretical_secure_key_rate(
                    'depolarizing', theory_x, f_ec=self.f_ec)
                if theory_y is not None:
                    ax.plot(theory_x, theory_y * 100, STYLE.theory_linestyle,
                            color=colour, alpha=STYLE.theory_alpha,
                            linewidth=STYLE.theory_linewidth)
        ax.set_xlabel('Depolarising Noise Strength', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Secure Key Rate (bits per 100 qubits)',
                      fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'Three-Protocol Benchmark - Depolarising Channel - Secure Key Rate\n'
            f'({sample_data.n_trials} trials/point, '
            f'{sample_data.n_qubits} qubits per trial)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad)
        ax.set_ylim(0, max(all_y_max * 1.15, 1.0))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(framealpha=STYLE.legend_framealpha)
        plt.tight_layout()
        self._finalise(fig, output_dir, 'keyrate_vs_noise.png', show)

    # --------------------------------------------------------------

    def _finalise(self, fig: plt.Figure,
                  output_dir: Optional[Path], filename: str,
                  show: bool) -> None:
        """Save and close (or show) a figure."""
        if output_dir is not None:
            path = Path(output_dir) / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(path, dpi=STYLE.save_dpi, bbox_inches=STYLE.save_bbox,
                        facecolor=STYLE.save_facecolor, edgecolor=STYLE.save_edgecolor)
            print(f"  Saved: {path}")
        if show:
            plt.show()
        else:
            plt.close(fig)
