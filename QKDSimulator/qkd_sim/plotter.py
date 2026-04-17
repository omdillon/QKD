"""
Plotting module for QKD simulation results.

Generates:
    1. QBER vs noise strength (with SEM error bars + theory overlay)
    2. Secure key rate vs noise strength
    3. CHSH parameter vs noise (E91)
    4. Multi-protocol comparison

Uses DM Sans from the local font directory.
All visual parameters are controlled by the STYLE object in STYLESHEET.py.
"""

from typing import Optional, Dict, Type
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

from .base import QKDProtocol
from .benchmark import BenchmarkData
from .noise import get_noise_description
from .STYLESHEET import STYLE


# Register DM Sans font
_FONT_DIR = Path(__file__).resolve().parent.parent / 'font' / 'DM_Sans' / 'static'
if _FONT_DIR.is_dir():
    for _ttf in _FONT_DIR.glob('DMSans-*.ttf'):
        fm.fontManager.addfont(str(_ttf))

plt.rcParams.update(STYLE.get_rcparams())

# Asymptotic QBER security thresholds per protocol.
#   BB84: 11.0% - Shor & Preskill (2000)
#   B92:   6.5% - Matsumoto (2013), hard QBER cap for depolarising channel
#   E91:  None  - security is a 2D condition over (QBER, |S|), no single threshold
_QBER_THRESHOLDS = {'BB84': 0.110, 'B92': 0.065, 'E91': None}
_DEFAULT_QBER_THRESHOLD = 0.110


def _threshold_for(protocol_name: str) -> Optional[float]:
    return _QBER_THRESHOLDS.get(protocol_name, _DEFAULT_QBER_THRESHOLD)


class QKDPlotter:
    """Handles all QKD protocol plots."""

    def __init__(self, f_ec: float = 1.16):
        self.f_ec = f_ec
        self.qber_threshold = _DEFAULT_QBER_THRESHOLD

        try:
            plt.style.use(STYLE.mpl_style)
        except OSError:
            pass
        plt.rcParams.update(STYLE.get_rcparams())

    def plot_qber_vs_noise(
        self,
        data: BenchmarkData,
        protocol_class: Optional[Type[QKDProtocol]] = None,
        save_path=None,
        show: bool = True,
    ) -> plt.Figure:
        """QBER vs noise strength with SEM error bars and optional theory overlay."""
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)

        colour = STYLE.protocol_colours.get(data.protocol_name, STYLE.default_colour)
        marker = STYLE.protocol_markers.get(data.protocol_name, STYLE.default_marker)
        sem = data.qber_std / np.sqrt(data.n_trials)

        is_eve = data.parameter_name == 'eve_interception_rate'
        sim_label = 'Eve intercept-resend (simulation)' if is_eve \
            else f'{get_noise_description(data.noise_type)} (simulation)'

        ax.errorbar(
            data.parameter_values, data.qber_mean, yerr=sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label=sim_label,
        )

        if protocol_class is not None and not is_eve:
            theory_x = np.linspace(data.parameter_values.min(),
                                   data.parameter_values.max(), 200)
            theory_y = protocol_class.theoretical_qber(data.noise_type, theory_x)
            if theory_y is not None:
                ax.plot(theory_x, theory_y, STYLE.theory_linestyle,
                        color=colour, alpha=STYLE.theory_alpha,
                        linewidth=STYLE.theory_linewidth,
                        label=f'{get_noise_description(data.noise_type)} (theory)')

        # E91 has no single QBER threshold (security is a 2D condition over Q and |S|)
        threshold = _threshold_for(data.protocol_name)
        if threshold is not None:
            ax.axhline(
                y=threshold, color=STYLE.threshold_colour,
                linestyle=STYLE.threshold_linestyle_horizontal,
                linewidth=STYLE.threshold_linewidth,
                alpha=STYLE.threshold_alpha_horizontal,
                label=f'{data.protocol_name} Security Threshold ({threshold:.1%})',
            )

        xlabel = 'Eve Interception Rate' if is_eve else 'Noise Strength Parameter'
        title_axis = 'Eve Interception Rate' if is_eve else 'Noise Level'
        ax.set_xlabel(xlabel, fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Quantum Bit Error Rate (QBER)', fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'QBER vs {title_axis} - {data.protocol_name}\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad,
        )
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
        ax.set_xlim(data.parameter_values.min() - 0.005,
                     data.parameter_values.max() + 0.005)
        y_max_threshold = threshold * 1.5 if threshold is not None else 0.2
        y_max = max(data.qber_mean.max() * 1.3, y_max_threshold)
        ax.set_ylim(0, min(y_max, 0.5))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc=STYLE.legend_loc_qber, framealpha=STYLE.legend_framealpha)
        plt.tight_layout()

        if save_path:
            self._save_figure(fig, save_path)
        if show:
            plt.show()
        return fig

    def plot_key_rate_vs_noise(
        self,
        data: BenchmarkData,
        protocol_class: Optional[Type[QKDProtocol]] = None,
        save_path=None,
        show: bool = True,
    ) -> plt.Figure:
        """Secure key rate (bits per 100 qubits) vs noise strength."""
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)

        colour = STYLE.protocol_colours.get(data.protocol_name, STYLE.default_colour)
        marker = STYLE.protocol_markers.get(data.protocol_name, STYLE.default_marker)
        y = data.secure_key_rate_mean * 100
        y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100

        is_eve = data.parameter_name == 'eve_interception_rate'
        sim_label = 'Eve intercept-resend (simulation)' if is_eve \
            else f'{get_noise_description(data.noise_type)} (simulation)'

        ax.errorbar(
            data.parameter_values, y, yerr=y_err,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label=sim_label,
        )

        if protocol_class is not None and not is_eve:
            theory_x = np.linspace(data.parameter_values.min(),
                                   data.parameter_values.max(), 200)
            theory_y = protocol_class.theoretical_secure_key_rate(
                data.noise_type, theory_x, f_ec=self.f_ec)
            if theory_y is not None:
                ax.plot(theory_x, theory_y * 100, STYLE.theory_linestyle,
                        color=colour, alpha=STYLE.theory_alpha,
                        linewidth=STYLE.theory_linewidth,
                        label=f'{get_noise_description(data.noise_type)} (theory)')

        # Threshold vertical line (noise sweeps only; not meaningful for eve rate or E91)
        threshold = _threshold_for(data.protocol_name)
        if threshold is not None and protocol_class is not None and not is_eve:
            theory_qber = protocol_class.theoretical_qber(
                data.noise_type, data.parameter_values)
            if theory_qber is not None:
                idx = np.searchsorted(theory_qber, threshold)
                if 0 < idx < len(data.parameter_values):
                    threshold_strength = data.parameter_values[idx]
                    ax.axvline(
                        x=threshold_strength, color=STYLE.threshold_colour,
                        linestyle=STYLE.threshold_linestyle_vertical,
                        linewidth=STYLE.threshold_linewidth,
                        alpha=STYLE.threshold_alpha_vertical,
                        label=f'QBER = {threshold:.1%} threshold '
                              f'(p \u2248 {threshold_strength:.2f})',
                    )

        xlabel = 'Eve Interception Rate' if is_eve else 'Noise Strength Parameter'
        title_axis = 'Eve Interception Rate' if is_eve else 'Noise Level'
        ax.set_xlabel(xlabel, fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Secure Key Rate (bits per 100 qubits)',
                       fontweight=STYLE.font_weight_axis_label)
        if data.protocol_name == 'E91':
            bound_label = 'DIQKD bound'
        else:
            bound_label = f'Shor-Preskill bound, $f_{{EC}}$ = {self.f_ec}'
        ax.set_title(
            f'Secure Key Rate vs {title_axis} - {data.protocol_name}\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials, {bound_label})',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad,
        )

        if data.protocol_name == 'B92':
                ax.set_xlim(0, 0.2)
                ax.set_ylim(0, max(55, y.max() * 1.15))
        else:
            ax.set_xlim(data.parameter_values.min() - 0.005, data.parameter_values.max() + 0.005)
            ax.set_ylim(0, max(55, y.max() * 1.15))
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc=STYLE.legend_loc_keyrate, framealpha=STYLE.legend_framealpha)
        plt.tight_layout()

        if save_path:
            self._save_figure(fig, save_path)
        if show:
            plt.show()
        return fig

    def plot_chsh_vs_noise(
        self,
        data: BenchmarkData,
        protocol_class: Optional[Type[QKDProtocol]] = None,
        channel_topology: str = 'both',
        save_path=None,
        show: bool = True,
    ) -> Optional[plt.Figure]:
        """|S| (CHSH parameter) vs noise strength. E91 only."""
        if data.chsh_mean is None:
            return None

        fig, ax = plt.subplots(figsize=STYLE.figsize_single)

        colour = STYLE.protocol_colours.get(data.protocol_name, STYLE.default_colour)
        marker = STYLE.protocol_markers.get(data.protocol_name, STYLE.default_marker)
        sem = data.chsh_std / np.sqrt(data.n_trials) if data.chsh_std is not None else None

        ax.errorbar(
            data.parameter_values, data.chsh_mean, yerr=sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha, label=f'{data.protocol_name} simulation',
        )

        # Theory overlay
        if protocol_class is not None and hasattr(protocol_class, 'theoretical_chsh'):
            theory_x = np.linspace(data.parameter_values.min(),
                                   data.parameter_values.max(), 200)
            try:
                theory_y = protocol_class.theoretical_chsh(
                    data.noise_type, theory_x, channel_topology=channel_topology)
            except TypeError:
                theory_y = protocol_class.theoretical_chsh(data.noise_type, theory_x)
            if theory_y is not None:
                ax.plot(theory_x, theory_y, STYLE.theory_linestyle,
                        color=colour, alpha=STYLE.theory_alpha,
                        linewidth=STYLE.theory_linewidth,
                        label=f'{data.protocol_name} theory')

        # Reference bounds
        ax.axhline(y=2.0, color=STYLE.threshold_colour,
                   linestyle=STYLE.threshold_linestyle_horizontal,
                   linewidth=STYLE.threshold_linewidth,
                   alpha=STYLE.threshold_alpha_horizontal,
                   label='Classical bound (|S| = 2)')
        ax.axhline(y=2 * np.sqrt(2), color='gray', linestyle=':',
                   linewidth=STYLE.threshold_linewidth, alpha=0.6,
                   label=r'Tsirelson bound (|S| = 2$\sqrt{2}$)')

        ax.set_xlabel('Noise Strength Parameter', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('|S| (CHSH parameter)', fontweight=STYLE.font_weight_axis_label)
        topo_str = f' ({channel_topology}-side noise)' if data.protocol_name == 'E91' else ''
        ax.set_title(
            f'CHSH Parameter vs Noise - {data.protocol_name}{topo_str}\n'
            f'({data.n_qubits} pairs, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad,
        )
        ax.set_xlim(data.parameter_values.min() - 0.005,
                     data.parameter_values.max() + 0.005)
        ax.set_ylim(0, 3.0)
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='upper right', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()

        if save_path:
            self._save_figure(fig, save_path)
        if show:
            plt.show()
        return fig

    def plot_qber_noisy_eve(
        self,
        data: BenchmarkData,
        noise_strength: float,
        protocol_class: Optional[Type[QKDProtocol]] = None,
        save_path=None,
        show: bool = True,
    ) -> plt.Figure:
        """QBER vs Eve rate under a fixed noisy channel. Shows noise floor + Eve contribution."""
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)

        colour = STYLE.protocol_colours.get(data.protocol_name, STYLE.default_colour)
        marker = STYLE.protocol_markers.get(data.protocol_name, STYLE.default_marker)
        sem = data.qber_std / np.sqrt(data.n_trials) * 100

        ax.errorbar(
            data.parameter_values, data.qber_mean * 100, yerr=sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha,
            label=f'{data.protocol_name} (noise + Eve)',
        )

        # Noise-only baseline (QBER contribution from the channel alone)
        if protocol_class is not None:
            baseline = protocol_class.theoretical_qber(
                data.noise_type, np.array([noise_strength]))
            if baseline is not None:
                ax.axhline(
                    y=float(baseline[0]) * 100, color='#0e365f',
                    linestyle=':', linewidth=STYLE.threshold_linewidth,
                    alpha=0.7,
                    label=f'Noise-only QBER baseline ({float(baseline[0]):.1%})',
                )

        threshold = _threshold_for(data.protocol_name)
        if threshold is not None:
            ax.axhline(
                y=threshold * 100, color=STYLE.threshold_colour,
                linestyle=STYLE.threshold_linestyle_horizontal,
                linewidth=STYLE.threshold_linewidth,
                alpha=STYLE.threshold_alpha_horizontal,
                label=f'{data.protocol_name} Security Threshold ({threshold:.1%})',
            )

        ax.set_xlabel('Eve Interception Rate', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('QBER (%)', fontweight=STYLE.font_weight_axis_label)
        noise_desc = get_noise_description(data.noise_type)
        ax.set_title(
            f'QBER under Channel Noise + Eve Interception - {data.protocol_name}\n'
            f'({noise_desc}, p = {noise_strength:.3f}; '
            f'{data.n_qubits} qubits, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad,
        )
        ax.set_xlim(data.parameter_values.min() - 0.01,
                     data.parameter_values.max() + 0.01)
        ax.set_ylim(0, 50)
        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(loc='upper left', framealpha=STYLE.legend_framealpha)
        plt.tight_layout()

        if save_path:
            self._save_figure(fig, save_path)
        if show:
            plt.show()
        return fig

    def plot_chsh_qber_vs_noise(
        self,
        data: BenchmarkData,
        channel_topology: str = 'both',
        save_path=None,
        show: bool = True,
    ) -> Optional[plt.Figure]:
        """|S| (CHSH) and QBER on twin y-axes vs noise strength. E91 only."""
        if data.chsh_mean is None:
            return None

        fig, ax_chsh = plt.subplots(figsize=STYLE.figsize_single)
        ax_qber = ax_chsh.twinx()

        chsh_colour = STYLE.protocol_colours.get(data.protocol_name, STYLE.default_colour)
        qber_colour = STYLE.noise_colours.get(data.noise_type, '#dd1634')
        marker = STYLE.protocol_markers.get(data.protocol_name, STYLE.default_marker)

        chsh_sem = data.chsh_std / np.sqrt(data.n_trials) if data.chsh_std is not None else None
        qber_sem = data.qber_std / np.sqrt(data.n_trials) * 100

        ax_chsh.errorbar(
            data.parameter_values, data.chsh_mean, yerr=chsh_sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=chsh_colour, ecolor=chsh_colour,
            alpha=STYLE.errorbar_alpha, label='|S| (CHSH)',
        )
        ax_qber.errorbar(
            data.parameter_values, data.qber_mean * 100, yerr=qber_sem,
            fmt=f's--', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=qber_colour, ecolor=qber_colour,
            alpha=STYLE.errorbar_alpha, label='QBER',
        )

        ax_chsh.axhline(y=2.0, color=STYLE.threshold_colour,
                        linestyle=STYLE.threshold_linestyle_horizontal,
                        linewidth=STYLE.threshold_linewidth,
                        alpha=STYLE.threshold_alpha_horizontal,
                        label='Classical bound (|S| = 2)')
        ax_chsh.axhline(y=2 * np.sqrt(2), color='#0e365f', linestyle=':',
                        linewidth=STYLE.threshold_linewidth, alpha=0.6,
                        label=r'Tsirelson bound (|S| = 2$\sqrt{2}$)')

        ax_chsh.set_xlabel('Noise Strength Parameter', fontweight=STYLE.font_weight_axis_label)
        ax_chsh.set_ylabel('|S| (CHSH parameter)', fontweight=STYLE.font_weight_axis_label)
        ax_qber.set_ylabel('QBER (%)', fontweight=STYLE.font_weight_axis_label)

        topo_str = f' ({channel_topology}-side noise)' if data.protocol_name == 'E91' else ''
        ax_chsh.set_title(
            f'CHSH and QBER vs Noise - {data.protocol_name}{topo_str}\n'
            f'({data.n_qubits} pairs, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad,
        )
        ax_chsh.set_xlim(data.parameter_values.min() - 0.005,
                         data.parameter_values.max() + 0.005)
        ax_chsh.set_ylim(1.5, 3.0)
        ax_qber.set_ylim(0, 50)

        n_ticks = 6
        ax_chsh.set_yticks(np.linspace(1.5, 3.0, n_ticks))
        ax_qber.set_yticks(np.linspace(0, 50, n_ticks))
        ax_chsh.grid(True, alpha=STYLE.grid_alpha)
        ax_qber.grid(False)

        handles_c, labels_c = ax_chsh.get_legend_handles_labels()
        handles_q, labels_q = ax_qber.get_legend_handles_labels()
        ax_chsh.legend(handles_c + handles_q, labels_c + labels_q,
                       loc='upper right', bbox_to_anchor = (0.6, 0.6), framealpha=STYLE.legend_framealpha)
        plt.tight_layout()

        if save_path:
            self._save_figure(fig, save_path)
        if show:
            plt.show()
        return fig

    def plot_protocol_comparison(
        self,
        data_dict: Dict[str, BenchmarkData],
        kind: str = 'qber',
        protocol_classes: Optional[Dict[str, Type[QKDProtocol]]] = None,
        save_path=None,
        show: bool = True,
    ) -> plt.Figure:
        """Multi-protocol overlay. kind: 'qber' or 'secure_key_rate'."""
        fig, ax = plt.subplots(figsize=STYLE.figsize_comparison)

        for proto_name, data in data_dict.items():
            colour = STYLE.protocol_colours.get(proto_name, STYLE.default_colour)
            marker = STYLE.protocol_markers.get(proto_name, STYLE.default_marker)

            if kind == 'qber':
                y = data.qber_mean
                y_err = data.qber_std / np.sqrt(data.n_trials)
            else:
                y = data.secure_key_rate_mean * 100
                y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100

            ax.errorbar(
                data.parameter_values, y, yerr=y_err,
                fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
                linewidth=STYLE.errorbar_linewidth,
                markersize=STYLE.errorbar_markersize,
                color=colour, alpha=STYLE.errorbar_alpha,
                label=f'{proto_name} simulation',
            )

            # Theory overlay
            if protocol_classes is not None:
                proto_cls = protocol_classes.get(proto_name)
                if proto_cls is not None:
                    theory_x = np.linspace(data.parameter_values.min(),
                                           data.parameter_values.max(), 200)
                    if kind == 'qber':
                        theory_y = proto_cls.theoretical_qber(data.noise_type, theory_x)
                        scale = 1.0
                    else:
                        theory_y = proto_cls.theoretical_secure_key_rate(
                            data.noise_type, theory_x, f_ec=self.f_ec)
                        scale = 100.0

                    if theory_y is not None:
                        ax.plot(theory_x, theory_y * scale, STYLE.theory_linestyle,
                                color=colour, alpha=STYLE.theory_alpha,
                                linewidth=STYLE.theory_linewidth)

        if kind == 'qber':
            # One threshold line per protocol, in the protocol's colour
            drawn_thresholds = set()
            for proto_name in data_dict.keys():
                t = _threshold_for(proto_name)
                if t is None or t in drawn_thresholds:
                    continue
                drawn_thresholds.add(t)
                proto_colour = STYLE.protocol_colours.get(proto_name, STYLE.default_colour)
                ax.axhline(
                    y=t, color=proto_colour,
                    linestyle=STYLE.threshold_linestyle_horizontal,
                    linewidth=STYLE.threshold_linewidth,
                    alpha=STYLE.threshold_alpha_horizontal,
                    label=f'{proto_name} Security Threshold ({t:.1%})',
                )
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
            ax.set_ylabel('Quantum Bit Error Rate (QBER)',
                          fontweight=STYLE.font_weight_axis_label)
        else:
            ax.set_ylabel('Secure Key Rate (bits per 100 qubits)',
                          fontweight=STYLE.font_weight_axis_label)

        ax.set_xlabel('Noise Strength Parameter', fontweight=STYLE.font_weight_axis_label)

        sample_data = next(iter(data_dict.values()))
        metric_label = 'QBER' if kind == 'qber' else 'Secure Key Rate'
        proto_list = ', '.join(data_dict.keys())
        ax.set_title(
            f'Multi-Protocol Comparison - {metric_label}\n'
            f'({proto_list} | {sample_data.noise_type} noise, '
            f'{sample_data.n_trials} trials/point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad,
        )

        ax.grid(True, alpha=STYLE.grid_alpha)
        ax.legend(framealpha=STYLE.legend_framealpha)
        plt.tight_layout()

        if save_path:
            self._save_figure(fig, save_path)
        if show:
            plt.show()
        return fig

    def _save_figure(self, fig: plt.Figure, path) -> None:
        """Save figure, creating parent directories if needed."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=STYLE.save_dpi, bbox_inches=STYLE.save_bbox,
                    facecolor=STYLE.save_facecolor, edgecolor=STYLE.save_edgecolor)
        print(f"  Saved: {path}")
