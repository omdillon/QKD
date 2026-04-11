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

# QBER threshold for f_ec=1.16 (hardcoded; the exact value from binary search is ~0.1100)
_DEFAULT_QBER_THRESHOLD = 0.11


class QKDPlotter:
    """Handles all QKD protocol plots."""

    def __init__(self, f_ec: float = 1.16):
        self.f_ec = f_ec
        self.qber_threshold = _DEFAULT_QBER_THRESHOLD

        try:
            plt.style.use(STYLE.mpl_style)
        except OSError:
            pass

    def plot_qber_vs_noise(
        self,
        data: BenchmarkData,
        protocol_class: Optional[Type[QKDProtocol]] = None,
        save_path=None,
        show: bool = True,
    ) -> plt.Figure:
        """QBER vs noise strength with SEM error bars and optional theory overlay."""
        fig, ax = plt.subplots(figsize=STYLE.figsize_single)

        colour = STYLE.noise_colours.get(data.noise_type, STYLE.default_colour)
        marker = STYLE.noise_markers.get(data.noise_type, STYLE.default_marker)
        sem = data.qber_std / np.sqrt(data.n_trials)

        ax.errorbar(
            data.parameter_values, data.qber_mean, yerr=sem,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha,
            label=f'{get_noise_description(data.noise_type)} (simulation)',
        )

        if protocol_class is not None:
            theory_x = np.linspace(data.parameter_values.min(),
                                   data.parameter_values.max(), 200)
            theory_y = protocol_class.theoretical_qber(data.noise_type, theory_x)
            if theory_y is not None:
                ax.plot(theory_x, theory_y, STYLE.theory_linestyle,
                        color=colour, alpha=STYLE.theory_alpha,
                        linewidth=STYLE.theory_linewidth,
                        label=f'{get_noise_description(data.noise_type)} (theory)')

        ax.axhline(
            y=self.qber_threshold, color=STYLE.threshold_colour,
            linestyle=STYLE.threshold_linestyle_horizontal,
            linewidth=STYLE.threshold_linewidth,
            alpha=STYLE.threshold_alpha_horizontal,
            label=f'Security Threshold ({self.qber_threshold:.1%})',
        )

        ax.set_xlabel('Noise Strength Parameter', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Quantum Bit Error Rate (QBER)', fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'QBER vs Noise Level - {data.protocol_name}\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials per point)',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad,
        )
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0%}'))
        ax.set_xlim(data.parameter_values.min() - 0.005,
                     data.parameter_values.max() + 0.005)
        y_max = max(data.qber_mean.max() * 1.3, self.qber_threshold * 1.5)
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

        colour = STYLE.noise_colours.get(data.noise_type, STYLE.default_colour)
        marker = STYLE.noise_markers.get(data.noise_type, STYLE.default_marker)
        y = data.secure_key_rate_mean * 100
        y_err = data.secure_key_rate_std / np.sqrt(data.n_trials) * 100

        ax.errorbar(
            data.parameter_values, y, yerr=y_err,
            fmt=f'{marker}-', capsize=STYLE.errorbar_capsize,
            capthick=STYLE.errorbar_capthick, linewidth=STYLE.errorbar_linewidth,
            markersize=STYLE.errorbar_markersize, color=colour, ecolor=colour,
            alpha=STYLE.errorbar_alpha,
            label=f'{get_noise_description(data.noise_type)} (simulation)',
        )

        if protocol_class is not None:
            theory_x = np.linspace(data.parameter_values.min(),
                                   data.parameter_values.max(), 200)
            theory_y = protocol_class.theoretical_secure_key_rate(
                data.noise_type, theory_x, f_ec=self.f_ec)
            if theory_y is not None:
                ax.plot(theory_x, theory_y * 100, STYLE.theory_linestyle,
                        color=colour, alpha=STYLE.theory_alpha,
                        linewidth=STYLE.theory_linewidth,
                        label=f'{get_noise_description(data.noise_type)} (theory)')

        # Threshold vertical line
        if protocol_class is not None:
            theory_qber = protocol_class.theoretical_qber(
                data.noise_type, data.parameter_values)
            if theory_qber is not None:
                idx = np.searchsorted(theory_qber, self.qber_threshold)
                if 0 < idx < len(data.parameter_values):
                    threshold_strength = data.parameter_values[idx]
                    ax.axvline(
                        x=threshold_strength, color=STYLE.threshold_colour,
                        linestyle=STYLE.threshold_linestyle_vertical,
                        linewidth=STYLE.threshold_linewidth,
                        alpha=STYLE.threshold_alpha_vertical,
                        label=f'QBER = {self.qber_threshold:.1%} threshold '
                              f'(p \u2248 {threshold_strength:.2f})',
                    )

        ax.set_xlabel('Noise Strength Parameter', fontweight=STYLE.font_weight_axis_label)
        ax.set_ylabel('Secure Key Rate (bits per 100 qubits)',
                       fontweight=STYLE.font_weight_axis_label)
        ax.set_title(
            f'Secure Key Rate vs Noise Level - {data.protocol_name}\n'
            f'({data.n_qubits} qubits, {data.n_trials} trials, '
            f'Shor-Preskill bound, $f_{{EC}}$ = {self.f_ec})',
            fontweight=STYLE.font_weight_title, pad=STYLE.title_pad,
        )
        ax.set_xlim(data.parameter_values.min() - 0.005,
                     data.parameter_values.max() + 0.005)
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
            ax.axhline(
                y=self.qber_threshold, color=STYLE.threshold_colour,
                linestyle=STYLE.threshold_linestyle_horizontal,
                linewidth=STYLE.threshold_linewidth,
                alpha=STYLE.threshold_alpha_horizontal,
                label=f'Security Threshold ({self.qber_threshold:.1%})',
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
